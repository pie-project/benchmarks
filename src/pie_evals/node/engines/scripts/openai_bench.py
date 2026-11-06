#!/usr/bin/env python3
"""Latency/throughput benchmark for any server that streams OpenAI's
``/v1/completions`` (llama.cpp, mlx-lm) or, with ``--chat``,
``/v1/chat/completions`` (Splash), on pie's common client so the prompts and
the summary match pie's own."""
from __future__ import annotations

import argparse
import asyncio
import errno
import json
import random
import statistics
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from common import (
    RequestResult,
    add_mode_subcommands,
    add_output_dump_args,
    finish,
    hf_chat_prompts_and_counts,
    make_prompts,
    request_max_tokens,
    summarize,
)


def post_stream(url: str, payload: dict[str, Any], timeout: float, on_chunk) -> None:
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        for line in resp:
            line = line.strip()
            if not line.startswith(b"data:"):
                continue
            body = line[5:].strip()
            if body == b"[DONE]":
                break
            obj = json.loads(body)
            if obj.get("error"):
                raise RuntimeError(f"server: {obj['error']}")
            on_chunk(obj)


#: errors a connect or send can end in when the server's accept queue is full;
#: the request never reached the server, so sending it again is safe
CONNECT_ERRNOS = {errno.ECONNRESET, errno.EPIPE, errno.EINVAL, errno.ECONNREFUSED}
CONNECT_TRIES = 5


def refused_before_sent(e: Exception) -> bool:
    """urllib raises ``URLError`` only for failures while connecting or sending
    the request; a failure after that surfaces as the raw ``OSError``."""
    return isinstance(e, urllib.error.URLError) and isinstance(e.reason, OSError) and e.reason.errno in CONNECT_ERRNOS


def post_stream_retrying(url: str, payload: dict[str, Any], timeout: float, on_chunk, retries: list[int]) -> None:
    """``post_stream``, sent again when the connection was reset before the
    server read the request (mlx-lm's Python server listens with a backlog of 5,
    and some Macs reset what overflows it when 32 requests open at once)."""
    for attempt in range(CONNECT_TRIES):
        try:
            return post_stream(url, payload, timeout, on_chunk)
        except Exception as e:  # noqa: BLE001
            if attempt == CONNECT_TRIES - 1 or not refused_before_sent(e):
                raise
            retries.append(1)
            time.sleep(0.05 * (attempt + 1))


def payload_for(args: argparse.Namespace, prompt: str, max_tokens: int) -> dict[str, Any]:
    """``prompt`` is the rendered chat template, or with ``--chat`` the user's
    words, which the server then renders itself."""
    payload: dict[str, Any] = {
        "max_tokens": max_tokens, "temperature": args.temperature, "top_p": args.top_p,
        "seed": args.seed, "stream": True, "stream_options": {"include_usage": True},
    }
    if args.chat:
        payload["messages"] = [{"role": "system", "content": args.system}, {"role": "user", "content": prompt}]
    else:
        payload["prompt"] = prompt
    if args.api_model:
        payload["model"] = args.api_model
    payload.update(json.loads(args.extra_body) if args.extra_body else {})
    return payload


def run_one(args: argparse.Namespace, endpoint: str, prompt: str, prompt_count: int, max_tokens: int, server: list[dict[str, Any]],
            retries: list[int] | None = None) -> RequestResult:
    start = time.perf_counter()
    stamps: list[float] = []
    seen: dict[str, Any] = {"usage": {}, "timings": {}}

    def on_chunk(obj: dict[str, Any]) -> None:
        if obj.get("usage"):
            seen["usage"] = obj["usage"]
        if obj.get("timings"):
            seen["timings"] = obj["timings"]
        for c in obj.get("choices") or []:
            delta = c.get("delta") or {}
            if c.get("text") or delta.get("content") or delta.get("reasoning_content"):
                stamps.append(time.perf_counter())
                break

    try:
        post_stream_retrying(endpoint, payload_for(args, prompt, max_tokens), args.request_timeout, on_chunk, [] if retries is None else retries)
    except Exception as e:  # noqa: BLE001
        return RequestResult(False, time.perf_counter() - start, 0, error=f"{type(e).__name__}: {e}")
    end = time.perf_counter()
    usage, timings = seen["usage"], seen["timings"]
    counted = usage.get("completion_tokens") is not None
    n_out = int(usage["completion_tokens"]) if counted else len(stamps)
    n_in = int(usage.get("prompt_tokens") or prompt_count)
    server.append({
        "prompt_tokens": n_in, "output_tokens": n_out, "max_tokens": max_tokens, "hf_prompt_tokens": prompt_count, "usage_reported": counted,
        "cached_tokens": int(timings.get("cache_n") or (usage.get("prompt_tokens_details") or {}).get("cached_tokens") or 0),
        "prefill_tok_s": timings.get("prompt_per_second"), "decode_tok_s": timings.get("predicted_per_second"),
    })
    ttft = (stamps[0] - start) if stamps else None
    gaps = [int((b - a) * 1e6) for a, b in zip(stamps, stamps[1:])]
    return RequestResult(True, end - start, n_out, n_in, ttft_s=ttft, intertoken_us=gaps)


def shuffled(prompt: str, seed: int) -> str:
    words = prompt.split()
    random.Random(seed).shuffle(words)
    return " ".join(words)


def _median(xs: list[float]) -> float | None:
    return float(statistics.median(xs)) if xs else None


async def run(args: argparse.Namespace):
    latency = args.mode == "latency"
    n = args.requests if latency else args.num_requests
    batch = 1 if latency else max(1, getattr(args, "concurrency", 0) or args.num_requests)
    raw = make_prompts(args, n + args.warmup)
    # a cold prompts file is already unique per request and is what pie is sent: every engine gets it as written
    if args.flush_cache and not getattr(args, "prompts_file", None):
        # a fresh word order per request, so no server finds a prefix it has seen
        salt = random.SystemRandom().getrandbits(32)
        raw = [shuffled(p, salt + i) for i, p in enumerate(raw)]
    prompts, counts = hf_chat_prompts_and_counts(args.model, args.system, raw, getattr(args, "think", None))
    if args.chat:
        prompts = raw  # the counts stay those of the rendered template, to compare with what the server reports
    elif args.token_ids:
        # the rendered template already holds the BOS; a server that tokenizes the text adds a second one
        # (llama.cpp: 1 token more per request than pie), so it gets the ids the counts are taken from
        from pathlib import Path

        from transformers import AutoTokenizer
        tok = AutoTokenizer.from_pretrained(str(Path(args.model).parent) if Path(args.model).is_file() else args.model, trust_remote_code=True)
        prompts = [tok.encode(p, add_special_tokens=False) for p in prompts]
    budgets = [request_max_tokens(args, i) for i in range(len(prompts))]
    endpoint = args.url.rstrip("/") + ("/v1/chat/completions" if args.chat else "/v1/completions")
    server: list[dict[str, Any]] = []
    retries: list[int] = []
    # asyncio's default pool holds min(32, cpus + 4) threads, which would cap
    # c32 at 18 requests in flight on a 14-core Mac; size it to the batch
    pool = ThreadPoolExecutor(max_workers=batch)
    loop = asyncio.get_running_loop()

    for i in range(args.warmup):
        await loop.run_in_executor(pool, run_one, args, endpoint, prompts[i], counts[i], budgets[i], [], retries)

    gate = asyncio.Semaphore(batch)

    async def one(p: str, c: int, m: int) -> RequestResult:
        async with gate:
            return await loop.run_in_executor(pool, run_one, args, endpoint, p, c, m, server, retries)

    t0 = time.perf_counter()
    try:
        results = await asyncio.gather(*(one(p, c, m) for p, c, m in zip(prompts[args.warmup:], counts[args.warmup:], budgets[args.warmup:])))
    finally:
        pool.shutdown(wait=False)
    wall = time.perf_counter() - t0

    cached = sum(s["cached_tokens"] for s in server)
    evaluated = sum(s["prompt_tokens"] for s in server)
    config = {
        "api_model": args.api_model or "",
        "client_in_flight": batch,
        "connect_retries": len(retries),
        "raw_prompt": not args.chat,
        "flush_cache": bool(args.flush_cache),
        "prompt_shuffled": bool(args.flush_cache),
        # exact length: the server honours ignore_eos, or every token it could stop on is blocked
        "ignore_eos": bool(json.loads(args.extra_body or "{}").get("ignore_eos", False) or json.loads(args.extra_body or "{}").get("logit_bias")),
        "short_responses": sum(1 for s in server if s["output_tokens"] < s["max_tokens"]),
        "usage_reported": all(s["usage_reported"] for s in server),
        "cached_prompt_tokens": cached,
        "cached_prompt_fraction": (cached / evaluated) if evaluated else 0.0,
        "hf_prompt_tokens": sum(s["hf_prompt_tokens"] for s in server),
        "temperature": args.temperature,
        "top_p": args.top_p,
        "extra_body": args.extra_body or "",
    }
    for key in ("prefill_tok_s", "decode_tok_s"):
        value = _median([float(s[key]) for s in server if s[key]])
        if value is not None:
            config[f"server_{key}"] = value
    summary = summarize(mode=args.mode, engine=args.engine_name, model=args.api_model or args.model, results=results, wall_s=wall, config=config)
    return summary, results


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="OpenAI-compatible completions benchmark on pie's common client")
    add_mode_subcommands(parser)
    for sp in parser._subparsers._group_actions[0].choices.values():
        add_output_dump_args(sp)
        sp.add_argument("--url", required=True, help="server base url, e.g. http://127.0.0.1:8080")
        sp.add_argument("--engine-name", default="openai", help="name written into the summary")
        sp.add_argument("--api-model", default="", help="value of the request's `model` field; --model is the HF tokenizer")
        sp.add_argument("--seed", type=int, default=0)
        sp.add_argument("--extra-body", default="", help="extra request fields as JSON")
        sp.add_argument("--chat", action="store_true", help="send chat messages and let the server render its own template")
        sp.add_argument("--token-ids", action="store_true", help="send the rendered prompt as token ids, not text")
        sp.add_argument("--flush-cache", action=argparse.BooleanOptionalAction, default=True, help="shuffle each prompt so no request reuses a cached prefix")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.mode == "latency" and not hasattr(args, "num_requests"):
        args.num_requests = args.requests
    summary, results = asyncio.run(run(args))
    finish(summary, results, args.json_out)


if __name__ == "__main__":
    sys.exit(main())
