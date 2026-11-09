"""The share of a mixture of experts' routed experts one batched-decode step reads, on the bench's own prompts.

The site's batched-decode limit (Pie.batchedCeiling) charges a step for every expert its requests route to. Without a
measurement it takes each request's k picks as independent and uniform, 1 - (1 - k)^requests: at 256 requests of
Qwen3.6-35B-A3B (8 of 256 experts) that is 99.97% of the experts. Real routes concentrate, the more so when the
answers start alike, and a step reads fewer. This measures it: it renders a finished c-cell round's cold prompts as the
bench did (bench/common.py: system prompt, chat template, --no-think), decodes greedy answers with the model's
Hugging Face reference (EOS held off, as --ignore-eos does) in lock-step groups, and records the top-k experts each
request picks at each MoE layer in each decode step. A step of n requests reads the union of their picks; groups
decoded side by side are unioned step by step. It prints the `routes` pairs for architectures.js (pie-project/website public/benchmarks/assets/js/config):
the share averaged over every layer and decode step, at 1 to the largest power of two of requests it was given.

Run it on a GPU pod from a checkout of this repo (for bench/common.py) with a Python that has torch and a transformers
that knows the model, e.g. a competitor baseline's venv:

    python tools/moe_routes.py <model dir> <cell round dir with cold_prompts.json> <out.json> \
        [--requests 1024] [--group 128] [--steps 256]
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("model")
    ap.add_argument("round_dir", type=Path)
    ap.add_argument("out", type=Path)
    ap.add_argument("--requests", type=int, default=1024)
    ap.add_argument("--group", type=int, default=128, help="requests decoded at once (the GPU's memory sets it)")
    ap.add_argument("--steps", type=int, default=256, help="answer tokens a request decodes (the shape's output)")
    args = ap.parse_args()

    import torch

    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "bench"))
    import common  # the bench's own prompt rendering
    from transformers import (
        AutoConfig,
        AutoModelForCausalLM,
        AutoModelForImageTextToText,
        AutoTokenizer,
    )

    n, group = args.requests, args.group
    prompts = json.loads((args.round_dir / "cold_prompts.json").read_text())[:n]
    if len(prompts) < n:
        raise SystemExit(f"{args.round_dir}: {len(prompts)} prompts, {n} asked")
    ids, counts = common.hf_chat_token_ids_and_counts(args.model, common.BENCH_SYSTEM, prompts, enable_thinking=False)
    print(f"{n} prompts, {min(counts)}-{max(counts)} tokens (mean {sum(counts) / n:.1f})", flush=True)
    tok = AutoTokenizer.from_pretrained(args.model)
    cfg = AutoConfig.from_pretrained(args.model)
    tcfg = getattr(cfg, "text_config", cfg)
    experts, k = tcfg.num_experts, tcfg.num_experts_per_tok
    try:
        model = AutoModelForImageTextToText.from_pretrained(args.model, dtype=torch.bfloat16, device_map="cuda")
    except (ValueError, KeyError):
        model = AutoModelForCausalLM.from_pretrained(args.model, dtype=torch.bfloat16, device_map="cuda")
    model.eval()
    gates = [m for name, m in model.named_modules() if name.endswith("mlp.gate")]
    layers = len(gates)
    calls: dict[int, list] = {}

    def hook_for(li):
        def hook(_m, _inp, out):
            cand = out if isinstance(out, (tuple, list)) else (out,)
            idx = next((t for t in cand if torch.is_tensor(t) and not t.is_floating_point() and t.shape[-1] == k), None)
            if idx is None:  # a router that returns its logits only
                idx = next(t for t in cand if torch.is_tensor(t) and t.is_floating_point() and t.shape[-1] == experts).float().topk(k, dim=-1).indices
            calls.setdefault(li, []).append(idx.reshape(-1, k))
        return hook

    for li, m in enumerate(gates):
        m.register_forward_hook(hook_for(li))

    # groups[g][s]: bool [layers, rows, experts], the experts each request of group g picked in decode step s
    groups, t0 = [], time.time()
    pad = tok.pad_token_id if tok.pad_token_id is not None else 0
    for g0 in range(0, n, group):
        rows = ids[g0:g0 + group]
        width = max(len(r) for r in rows)
        x = torch.tensor([[pad] * (width - len(r)) + r for r in rows], device="cuda")
        mask = torch.tensor([[0] * (width - len(r)) + [1] * len(r) for r in rows], device="cuda")
        calls.clear()
        with torch.inference_mode():
            model.generate(input_ids=x, attention_mask=mask, max_new_tokens=args.steps, min_new_tokens=args.steps, do_sample=False)
        # call 0 is the prompts' pass; call s >= 1 is decode step s, one token a request
        groups.append([torch.stack([torch.zeros(len(rows), experts, dtype=torch.bool, device="cuda").scatter_(1, calls[li][s].long(), True)
                                    for li in range(layers)]) for s in range(1, len(calls[0]))])
        print(f"group {g0 // group}: {len(rows)} requests, {len(calls[0]) - 1} decode steps, {time.time() - t0:.0f}s", flush=True)

    steps = min(len(g) for g in groups)
    res = {"model": args.model, "prompts": str(args.round_dir / "cold_prompts.json"), "requests": n, "experts": experts, "k": k,
           "layers": layers, "steps": steps, "routes": [], "uniform": []}
    m = 1
    while m <= n:
        share = 0.0
        for s in range(steps):
            if m <= group:
                touched = groups[0][s][:, :m].any(dim=1)
            else:
                touched = torch.stack([g[s].any(dim=1) for g in groups[: m // group]]).any(dim=0)
            share += touched.float().mean().item()
        res["routes"].append([m, round(share / steps, 4)])
        res["uniform"].append([m, round(1 - (1 - k / experts) ** m, 4)])
        m *= 2
    args.out.write_text(json.dumps(res))
    print(json.dumps(res), flush=True)
    print("routes: " + json.dumps(res["routes"]).replace(" ", ""), flush=True)


if __name__ == "__main__":
    main()
