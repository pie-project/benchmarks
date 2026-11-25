#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import random
import sys
import urllib.request
from pathlib import Path
from typing import Any

from bench_args import add_mode_subcommands, add_output_dump_args
from bench_prompts import _render_chat, make_prompts, request_max_tokens
from bench_results import RequestResult, finish, summarize


def shuffled(prompt: str, seed: int) -> str:
    words = prompt.split()
    random.Random(seed).shuffle(words)
    return " ".join(words)


def post(url: str, body: dict[str, Any], timeout: float) -> dict[str, Any]:
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read())


def run(args: argparse.Namespace):
    latency = args.mode == "latency"
    n = args.requests if latency else args.num_requests
    batch = 1 if latency else max(1, getattr(args, "concurrency", 0) or args.num_requests)
    raw = make_prompts(args, n + args.warmup)
    if args.flush_cache and not getattr(args, "prompts_file", None):
        salt = random.SystemRandom().getrandbits(32)
        raw = [shuffled(p, salt + i) for i, p in enumerate(raw)]
    from transformers import AutoTokenizer

    tok = AutoTokenizer.from_pretrained(str(Path(args.model).parent) if Path(args.model).is_file() else args.model, trust_remote_code=True)
    rendered = _render_chat(tok, args.system, raw, getattr(args, "think", None))
    ids = [tok.encode(p, add_special_tokens=False) for p in rendered]
    budgets = [request_max_tokens(args, i) for i in range(len(rendered))]
    reqs = [{"prompt": p, "ids": t, "max_tokens": m} for p, t, m in zip(rendered, ids, budgets)]
    sampling = {"temperature": args.temperature, "top_p": args.top_p, "seed": args.seed, "ignore_eos": bool(args.ignore_eos)}
    job = {"warmup": reqs[: args.warmup], "requests": reqs[args.warmup:], "concurrency": batch, "sampling": sampling}
    out = post(args.url.rstrip("/") + "/run", job, args.request_timeout * max(1, len(reqs)))
    if out.get("error"):
        raise SystemExit(f"browser: {out['error']}")
    results: list[RequestResult] = []
    for r, want in zip(out["results"], job["requests"]):
        if not r.get("ok"):
            results.append(RequestResult(False, (r.get("end_s") or 0) - (r.get("send_s") or 0), 0, error=r.get("error")))
            continue
        stamps = [s for s in (r.get("stamps_s") or []) if s is not None]
        gaps = [int((b - a) * 1e6) for a, b in zip(stamps, stamps[1:])]
        ttft = (r["first_s"] - r["send_s"]) if r.get("first_s") is not None else None
        results.append(RequestResult(
            True, r["end_s"] - r["send_s"], int(r.get("output_tokens") or 0),
            int(r["prompt_tokens"]) if r.get("prompt_tokens") is not None else len(want["ids"]),
            ttft_s=ttft, intertoken_us=gaps, client_send_s=r["send_s"], client_return_s=r["end_s"],
        ))
    hf_tokens = sum(len(q["ids"]) for q in job["requests"])
    engine_tokens = sum(x.prompt_tokens or 0 for x in results if x.ok)
    config = {
        "client_in_flight": batch,
        "raw_prompt": True,
        "flush_cache": bool(args.flush_cache),
        "prompt_shuffled": bool(args.flush_cache),
        "ignore_eos": bool(args.ignore_eos),
        "short_responses": sum(1 for x, q in zip(results, job["requests"]) if x.ok and x.output_tokens < q["max_tokens"]),
        "hf_prompt_tokens": hf_tokens,
        "engine_prompt_tokens": engine_tokens,
        "prompt_token_mismatch": abs(engine_tokens - hf_tokens),
        "cached_prompt_tokens": 0,
        "temperature": args.temperature,
        "top_p": args.top_p,
        "tab_wall_s": out.get("wall_s"),
    }
    for k, v in (out.get("stats") or {}).items():
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            config[f"engine_{k}"] = v
    wall = float(out.get("wall_s") or 0.0)
    summary = summarize(mode=args.mode, engine=args.engine_name, model=args.api_model or args.model, results=results, wall_s=wall, config=config)
    return summary, results


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Browser-engine benchmark on pie's common client")
    add_mode_subcommands(parser)
    for sp in parser._subparsers._group_actions[0].choices.values():
        add_output_dump_args(sp)
        sp.add_argument("--url", required=True, help="bridge base url, e.g. http://127.0.0.1:8080")
        sp.add_argument("--engine-name", default="browser", help="name written into the summary")
        sp.add_argument("--api-model", default="", help="name written into the summary; --model is the HF tokenizer")
        sp.add_argument("--seed", type=int, default=0)
        sp.add_argument("--extra-body", default="", help="accepted for the served-engine argv; unused")
        sp.add_argument("--flush-cache", action=argparse.BooleanOptionalAction, default=True, help="shuffle each prompt so no request reuses a cached prefix")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.mode == "latency" and not hasattr(args, "num_requests"):
        args.num_requests = args.requests
    summary, results = run(args)
    finish(summary, results, args.json_out)


if __name__ == "__main__":
    sys.exit(main())
