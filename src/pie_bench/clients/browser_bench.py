#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from typing import Any

from bench_args import add_mode_subcommands, add_output_dump_args
from bench_prompts import (
    load_tokenizer,
    make_prompts,
    render_chat,
    request_max_tokens,
    shuffled_against_prefix_cache,
)
from bench_results import RequestResult, finish, summarize


def post(url: str, body: dict[str, Any], timeout: float) -> dict[str, Any]:
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read())


def _job(args: argparse.Namespace, batch: int, n: int) -> dict[str, Any]:
    raw = shuffled_against_prefix_cache(args, make_prompts(args, n + args.warmup))
    tok = load_tokenizer(args.model)
    rendered = render_chat(tok, args.system, raw, args.think)
    ids = [tok.encode(p, add_special_tokens=False) for p in rendered]
    budgets = [request_max_tokens(args, i) for i in range(len(rendered))]
    reqs = [{"prompt": p, "ids": t, "max_tokens": m} for p, t, m in zip(rendered, ids, budgets)]
    sampling = {
        "temperature": args.temperature,
        "top_p": args.top_p,
        "seed": args.seed,
        "ignore_eos": bool(args.ignore_eos),
    }
    return {
        "warmup": reqs[: args.warmup],
        "requests": reqs[args.warmup :],
        "concurrency": batch,
        "sampling": sampling,
    }


def _result(r: dict[str, Any], want: dict[str, Any]) -> RequestResult:
    if not r.get("ok"):
        return RequestResult(
            False, (r.get("end_s") or 0) - (r.get("send_s") or 0), 0, error=r.get("error")
        )
    stamps = [s for s in (r.get("stamps_s") or []) if s is not None]
    gaps = [int((b - a) * 1e6) for a, b in zip(stamps, stamps[1:])]
    ttft = (r["first_s"] - r["send_s"]) if r.get("first_s") is not None else None
    return RequestResult(
        True,
        r["end_s"] - r["send_s"],
        int(r.get("output_tokens") or 0),
        int(r["prompt_tokens"]) if r.get("prompt_tokens") is not None else len(want["ids"]),
        ttft_s=ttft,
        intertoken_us=gaps,
        client_send_s=r["send_s"],
        client_return_s=r["end_s"],
    )


def _summary_config(
    args, batch: int, job: dict, results: list[RequestResult], out: dict
) -> dict[str, Any]:
    hf_tokens = sum(len(q["ids"]) for q in job["requests"])
    engine_tokens = sum(x.prompt_tokens or 0 for x in results if x.ok)
    config = {
        "client_in_flight": batch,
        "raw_prompt": True,
        "flush_cache": bool(args.flush_cache),
        "prompt_shuffled": bool(args.flush_cache),
        "ignore_eos": bool(args.ignore_eos),
        "short_responses": sum(
            1
            for x, q in zip(results, job["requests"])
            if x.ok and x.output_tokens < q["max_tokens"]
        ),
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
    return config


def run(args: argparse.Namespace):
    latency = args.mode == "latency"
    n = args.requests if latency else args.num_requests
    batch = 1 if latency else max(1, args.concurrency or args.num_requests)
    job = _job(args, batch, n)
    total = len(job["warmup"]) + len(job["requests"])
    out = post(args.url.rstrip("/") + "/run", job, args.request_timeout * max(1, total))
    if out.get("error"):
        raise SystemExit(f"browser: {out['error']}")
    results = [_result(r, want) for r, want in zip(out["results"], job["requests"])]
    summary = summarize(
        mode=args.mode,
        engine=args.engine_name,
        model=args.api_model or args.model,
        results=results,
        wall_s=float(out.get("wall_s") or 0.0),
        config=_summary_config(args, batch, job, results, out),
    )
    return summary, results


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Browser-engine benchmark on pie's common client")
    for sp in add_mode_subcommands(parser):
        add_output_dump_args(sp)
        sp.add_argument("--url", required=True, help="bridge base url, e.g. http://127.0.0.1:8080")
        sp.add_argument("--engine-name", default="browser", help="name written into the summary")
        sp.add_argument(
            "--api-model",
            default="",
            help="name written into the summary; --model is the HF tokenizer",
        )
        sp.add_argument("--seed", type=int, default=0)
        sp.add_argument(
            "--extra-body", default="", help="accepted for the served-engine argv; unused"
        )
        sp.add_argument(
            "--flush-cache",
            action=argparse.BooleanOptionalAction,
            default=True,
            help="shuffle each prompt so no request reuses a cached prefix",
        )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    summary, results = run(args)
    finish(summary, results, args.json_out)


if __name__ == "__main__":
    sys.exit(main())
