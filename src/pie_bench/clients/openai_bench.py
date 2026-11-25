#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import errno
import json
import statistics
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from bench_args import add_mode_subcommands, add_output_dump_args
from bench_pacing import cool_before_request
from bench_prompts import (
    hf_chat_prompts_and_counts,
    load_tokenizer,
    make_prompts,
    request_max_tokens,
    shuffled_against_prefix_cache,
)
from bench_results import RequestResult, finish, summarize
from bench_tracing import monotonic_ns


def post_stream(url: str, payload: dict[str, Any], timeout: float, on_chunk) -> None:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
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


CONNECT_ERRNOS = {errno.ECONNRESET, errno.EPIPE, errno.EINVAL, errno.ECONNREFUSED}
CONNECT_TRIES = 5


def refused_before_sent(e: Exception) -> bool:
    return (
        isinstance(e, urllib.error.URLError)
        and isinstance(e.reason, OSError)
        and e.reason.errno in CONNECT_ERRNOS
    )


def post_stream_retrying(
    url: str, payload: dict[str, Any], timeout: float, on_chunk, retries: list[int]
) -> None:
    for attempt in range(CONNECT_TRIES):
        try:
            return post_stream(url, payload, timeout, on_chunk)
        except Exception as e:
            if attempt == CONNECT_TRIES - 1 or not refused_before_sent(e):
                raise
            retries.append(1)
            time.sleep(0.05 * (attempt + 1))


def payload_for(args: argparse.Namespace, prompt: str, max_tokens: int) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "max_tokens": max_tokens,
        "temperature": args.temperature,
        "top_p": args.top_p,
        "stream": True,
        "stream_options": {"include_usage": True},
    }
    if args.temperature > 0:
        payload["seed"] = args.seed
    if args.chat:
        payload["messages"] = [
            {"role": "system", "content": args.system},
            {"role": "user", "content": prompt},
        ]
    else:
        payload["prompt"] = prompt
    if args.api_model:
        payload["model"] = args.api_model
    payload.update(json.loads(args.extra_body) if args.extra_body else {})
    return payload


def run_one(
    args: argparse.Namespace,
    endpoint: str,
    prompt: str,
    prompt_count: int,
    max_tokens: int,
    server: list[dict[str, Any]],
    retries: list[int] | None = None,
) -> RequestResult:
    start = time.perf_counter()
    sent_ns = monotonic_ns()
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
        post_stream_retrying(
            endpoint,
            payload_for(args, prompt, max_tokens),
            args.request_timeout,
            on_chunk,
            [] if retries is None else retries,
        )
    except Exception as e:
        return RequestResult(
            False, time.perf_counter() - start, 0, error=f"{type(e).__name__}: {e}"
        )
    end = time.perf_counter()
    usage, timings = seen["usage"], seen["timings"]
    counted = usage.get("completion_tokens") is not None
    n_out = max(int(usage["completion_tokens"]), len(stamps)) if counted else len(stamps)
    n_in = int(usage.get("prompt_tokens") or prompt_count)
    server.append(
        {
            "prompt_tokens": n_in,
            "output_tokens": n_out,
            "max_tokens": max_tokens,
            "hf_prompt_tokens": prompt_count,
            "usage_reported": counted,
            "cached_tokens": int(
                timings.get("cache_n")
                or (usage.get("prompt_tokens_details") or {}).get("cached_tokens")
                or 0
            ),
            "prefill_tok_s": timings.get("prompt_per_second"),
            "decode_tok_s": timings.get("predicted_per_second"),
        }
    )
    ttft = (stamps[0] - start) if stamps else None
    gaps = [int((b - a) * 1e6) for a, b in zip(stamps, stamps[1:])]
    return RequestResult(
        True, end - start, n_out, n_in, ttft_s=ttft, intertoken_us=gaps, client_send_s=sent_ns / 1e9
    )


def _median(xs: list[float]) -> float | None:
    return float(statistics.median(xs)) if xs else None


def _request_prompts(args: argparse.Namespace, n: int) -> tuple[list, list[int]]:
    raw = shuffled_against_prefix_cache(args, make_prompts(args, n + args.warmup))
    prompts, counts = hf_chat_prompts_and_counts(args.model, args.system, raw, args.think)
    if args.chat:
        return raw, counts
    if args.token_ids:
        tok = load_tokenizer(args.model)
        return [tok.encode(p, add_special_tokens=False) for p in prompts], counts
    return prompts, counts


def _ignores_eos(extra_body: str) -> bool:
    body = json.loads(extra_body or "{}")
    return bool(body.get("ignore_eos", False) or body.get("logit_bias"))


def _summary_config(
    args, batch: int, retries: list[int], cooled: float, server: list[dict[str, Any]]
) -> dict[str, Any]:
    cached = sum(s["cached_tokens"] for s in server)
    evaluated = sum(s["prompt_tokens"] for s in server)
    return {
        "api_model": args.api_model or "",
        "client_in_flight": batch,
        "connect_retries": len(retries),
        "cooled_s": round(cooled, 1),
        "raw_prompt": not args.chat,
        "flush_cache": bool(args.flush_cache),
        "prompt_shuffled": bool(args.flush_cache),
        "ignore_eos": _ignores_eos(args.extra_body),
        "short_responses": sum(1 for s in server if s["output_tokens"] < s["max_tokens"]),
        "usage_reported": all(s["usage_reported"] for s in server),
        "cached_prompt_tokens": cached,
        "cached_prompt_fraction": (cached / evaluated) if evaluated else 0.0,
        "hf_prompt_tokens": sum(s["hf_prompt_tokens"] for s in server),
        "temperature": args.temperature,
        "top_p": args.top_p,
        "extra_body": args.extra_body or "",
    }


async def run(args: argparse.Namespace):
    latency = args.mode == "latency"
    n = args.requests if latency else args.num_requests
    batch = 1 if latency else max(1, args.concurrency or args.num_requests)
    prompts, counts = _request_prompts(args, n)
    budgets = [request_max_tokens(args, i) for i in range(len(prompts))]
    endpoint = args.url.rstrip("/") + ("/v1/chat/completions" if args.chat else "/v1/completions")
    server: list[dict[str, Any]] = []
    retries: list[int] = []
    pool = ThreadPoolExecutor(max_workers=batch)
    loop = asyncio.get_running_loop()

    def send(prompt, count: int, max_tokens: int, log: list[dict[str, Any]]):
        return loop.run_in_executor(
            pool, run_one, args, endpoint, prompt, count, max_tokens, log, retries
        )

    for i in range(args.warmup):
        await send(prompts[i], counts[i], budgets[i], [])
    if not latency and batch > 1 and args.warmup:
        await asyncio.gather(
            *(send(prompts[k % args.warmup], counts[k % args.warmup], 8, []) for k in range(batch))
        )

    gate = asyncio.Semaphore(batch)
    cooled = [0.0]

    async def one(prompt, count: int, max_tokens: int) -> RequestResult:
        queued = time.perf_counter()
        async with gate:
            if latency:
                cooled[0] += await loop.run_in_executor(pool, cool_before_request)
            waited = 0.0 if latency else time.perf_counter() - queued
            result = await send(prompt, count, max_tokens, server)
        result.latency_s += waited
        if result.ttft_s is not None:
            result.ttft_s += waited
        result.client_send_s = (
            result.client_send_s - waited - epoch_ns / 1e9
            if args.report_timing and result.client_send_s is not None
            else None
        )
        return result

    epoch_unix_s, epoch_ns = time.time(), monotonic_ns()
    t0 = time.perf_counter()
    measured = zip(prompts[args.warmup :], counts[args.warmup :], budgets[args.warmup :])
    try:
        results = await asyncio.gather(*(one(p, c, m) for p, c, m in measured))
    finally:
        pool.shutdown(wait=False)
    wall = time.perf_counter() - t0 - cooled[0]

    config = _summary_config(args, batch, retries, cooled[0], server)
    if args.report_timing:
        config["client timing epoch unix s"] = epoch_unix_s
        config["client timing epoch monotonic ns"] = epoch_ns
    for key in ("prefill_tok_s", "decode_tok_s"):
        value = _median([float(s[key]) for s in server if s[key]])
        if value is not None:
            config[f"server_{key}"] = value
    summary = summarize(
        mode=args.mode,
        engine=args.engine_name,
        model=args.api_model or args.model,
        results=results,
        wall_s=wall,
        config=config,
    )
    return summary, results


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="OpenAI-compatible completions benchmark on pie's common client"
    )
    for sp in add_mode_subcommands(parser):
        add_output_dump_args(sp)
        sp.add_argument("--url", required=True, help="server base url, e.g. http://127.0.0.1:8080")
        sp.add_argument("--engine-name", default="openai", help="name written into the summary")
        sp.add_argument(
            "--api-model",
            default="",
            help="value of the request's `model` field; --model is the HF tokenizer",
        )
        sp.add_argument("--seed", type=int, default=0)
        sp.add_argument("--extra-body", default="", help="extra request fields as JSON")
        sp.add_argument(
            "--chat",
            action="store_true",
            help="send chat messages and let the server render its own template",
        )
        sp.add_argument(
            "--token-ids",
            action="store_true",
            help="send the rendered prompt as token ids, not text",
        )
        sp.add_argument(
            "--flush-cache",
            action=argparse.BooleanOptionalAction,
            default=True,
            help="shuffle each prompt so no request reuses a cached prefix",
        )
        sp.add_argument(
            "--report-timing",
            action="store_true",
            help="each request's send time on a monotonic epoch, for a profiler",
        )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    summary, results = asyncio.run(run(args))
    finish(summary, results, args.json_out)


if __name__ == "__main__":
    sys.exit(main())
