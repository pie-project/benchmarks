"""Write mobile/shared/workloads.json: the prompts a phone sends, made by the harness's own code.

    .venv/bin/python mobile/tools/gen_workloads.py

Each phone workload is a matrix workload (raw-512-256, c4, pf4-512). Its prompts come from
pie_evals.node.workloads.synthetic and pie_evals.node.fair exactly as a Mac run makes them: the same
seeded word block, the same cold tags per round. Each model's chat template (system + user, thinking off,
as scripts/bench/common.py renders it) is stored as the text around the user message, with the token
count every prompt must come to, so a phone engine can check it read the same prompt.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from pie_evals.node.fair import COLD_SEED, cold_prompts, cold_request_count
from pie_evals.node.workloads.synthetic import prompt_words_for_tokens
from pie_evals.plan.matrix import Matrix

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "mobile" / "shared" / "workloads.json"
SYSTEM = "You are a helpful benchmarking assistant."  # scripts/bench/common.py BENCH_SYSTEM
ROUNDS = 3
PHONE_WORKLOADS = ["raw-512-256", "c4", "pf4-512"]
# site model id -> the tokenizer whose chat template renders its prompts (the one the Mac rows use)
TOKENIZERS = {
    "qwen3.5-0.8b": "mlx-community/Qwen3.5-0.8B-4bit",
    "qwen3.5-4b": "mlx-community/Qwen3.5-4B-4bit",
    "gemma-4-e2b": "mlx-community/gemma-4-e2b-it-4bit",
    "gemma-4-e4b": "mlx-community/gemma-4-e4b-it-4bit",
    "gemma-4-12b": "mlx-community/gemma-4-12B-it-4bit",
}
SPLIT = "\x00USER\x00"


def round_prompts(wl, r: int) -> tuple[list[str], list[str]]:
    p = wl.params
    conc = int(p.get("concurrency", 1))
    n = int(p.get("num_requests") or p.get("requests") or 1)
    warm = conc if conc > 1 else int(p.get("warmup", 1))
    body = str(p["prompt"]) if p.get("prompt") else prompt_words_for_tokens(int(p.get("prefill", 128)), salt=wl.id)
    if p.get("cold_cache"):
        seed = COLD_SEED if r == 0 else f"{COLD_SEED}|round{r}"
        prompts = cold_prompts(body, workload_id=wl.id, seed=seed, count=cold_request_count(p))
    else:  # common.py --unique-prompts: the same prompt, a request number after it
        prompts = [f"{body} (Request #{i})" for i in range(warm + n)]
    return prompts[:warm], prompts[warm:warm + n]


def main() -> None:
    from transformers import AutoTokenizer

    m = Matrix.load(ROOT / "matrix")
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    workloads = []
    for wid in PHONE_WORKLOADS:
        wl = m.workloads[wid]
        p = wl.params
        rounds = [dict(zip(("warmup", "measured"), round_prompts(wl, r))) for r in range(ROUNDS)]
        workloads.append({
            "id": wid, "kind": str(wl.kind), "concurrency": int(p.get("concurrency", 1)),
            "prefill": int(p.get("prefill", 128)), "decode": int(p.get("decode", 64)),
            "requests": len(rounds[0]["measured"]), "warmup": len(rounds[0]["warmup"]),
            "cold_cache": bool(p.get("cold_cache")), "temperature": 0.0, "ignore_eos": True,
            "rounds": rounds,
        })
    templates = {}
    for model, repo in TOKENIZERS.items():
        tok = AutoTokenizer.from_pretrained(repo)
        msgs = lambda u: [{"role": "system", "content": SYSTEM}, {"role": "user", "content": u}]  # noqa: E731
        full = tok.apply_chat_template(msgs(SPLIT), tokenize=False, add_generation_prompt=True, enable_thinking=False)
        prefix, suffix = full.split(SPLIT)
        counts = {}
        for w in workloads:
            per_round = []
            for rnd in w["rounds"]:
                ids = []
                for text in rnd["measured"]:
                    rendered = tok.apply_chat_template(msgs(text), tokenize=False, add_generation_prompt=True, enable_thinking=False)
                    assert rendered == prefix + text + suffix, (model, w["id"])
                    ids.append(len(tok.encode(rendered, add_special_tokens=False)))
                per_round.append(ids)
            counts[w["id"]] = per_round
        templates[model] = {"tokenizer": repo, "prefix": prefix, "suffix": suffix, "prompt_tokens": counts}
        print(model, {k: v[0][:2] for k, v in counts.items()}, file=sys.stderr)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"schema": "pie-evals-phone-workloads/1", "harness_commit": commit, "system": SYSTEM,
                               "rounds": ROUNDS, "workloads": workloads, "templates": templates}, ensure_ascii=False, indent=1) + "\n")
    print(OUT, OUT.stat().st_size, "bytes")


if __name__ == "__main__":
    main()
