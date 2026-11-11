#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import errno
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from contextlib import asynccontextmanager
from typing import Any

from common import (
    RequestResult,
    add_mode_subcommands,
    finish,
    hf_chat_prompts_and_counts,
    make_prompts,
    request_max_tokens,
    summarize,
)

PINNED_ENV = os.path.expanduser("~/.cache/pie-metal/mlxenv/bin/python")


def http_json(url: str, payload: dict[str, Any], timeout: float) -> dict[str, Any]:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def refused(err: Exception) -> bool:
    if isinstance(err, urllib.error.HTTPError):
        return False
    cause = err.reason if isinstance(err, urllib.error.URLError) else err
    if isinstance(cause, TimeoutError):
        return False
    if isinstance(cause, ConnectionError):
        return True
    return isinstance(cause, OSError) and cause.errno in (errno.EINVAL, errno.EPIPE)


def health(url: str) -> None:
    with urllib.request.urlopen(url.rstrip("/") + "/v1/models", timeout=5.0) as resp:
        resp.read()


@asynccontextmanager
async def maybe_server(args: argparse.Namespace, batch: int):
    proc: subprocess.Popen[str] | None = None
    url = args.url
    if args.spawn:
        python = args.python or PINNED_ENV
        if not os.path.exists(python):
            raise RuntimeError(
                f"no interpreter at {python}. The pinned mlx-lm is what every "
                "recorded answer in this tree came from:\n"
                "  python3.14 -m venv ~/.cache/pie-metal/mlxenv\n"
                "  ~/.cache/pie-metal/mlxenv/bin/pip install -r "
                "crates/engine-metal/csrc/tests/parity/requirements.txt\n"
                "or point --python at another one."
            )
        url = f"http://127.0.0.1:{args.port}"
        module = (args.server_module or "mlx_lm server").split()
        cmd = [
            python, "-m", *module,
            "--model", args.model,
            "--host", "127.0.0.1",
            "--port", str(args.port),
            "--decode-concurrency", str(batch),
            "--prompt-concurrency", str(args.prompt_concurrency),
            "--prompt-cache-size", str(args.prompt_cache_size),
            "--log-level", "ERROR",
            *args.server_extra.split(),
        ]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        deadline = time.time() + args.startup_timeout
        while time.time() < deadline:
            if proc.poll() is not None:
                out = proc.stdout.read() if proc.stdout else ""
                raise RuntimeError(f"mlx-lm server exited during startup:\n{out}")
            try:
                health(url)
                break
            except Exception:
                await asyncio.sleep(0.5)
        else:
            proc.terminate()
            raise RuntimeError(
                f"mlx-lm server did not answer /v1/models within {args.startup_timeout}s"
            )
    else:
        health(url)
    try:
        yield url
    finally:
        if proc:
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()


async def run(args: argparse.Namespace):
    if args.ignore_eos:
        sys.exit(
            "mlx-lm's server has no `ignore_eos`, so it cannot be held to a fixed\n"
            "output length. Sending the field anyway would be measured as if it\n"
            "had been honoured. Run both engines with --no-ignore-eos."
        )
    n = args.requests if args.mode == "latency" else args.num_requests
    if args.mode == "latency":
        batch = 1
    elif args.concurrency == 0:
        batch = max(1, args.num_requests)
    else:
        batch = args.concurrency
    prompts, prompt_counts = hf_chat_prompts_and_counts(args.model, args.system, make_prompts(args, n + args.warmup), getattr(args, 'think', None))
    gate = asyncio.Semaphore(batch)
    retries = [0]
    async with maybe_server(args, batch) as base_url:
        endpoint = base_url.rstrip("/") + "/v1/completions"

        async def one(prompt: str, prompt_count: int, max_tokens: int) -> RequestResult:
            payload = {
                "model": args.model,
                "prompt": prompt,
                "max_tokens": max_tokens,
                "temperature": args.temperature,
                "top_p": args.top_p,
                "stream": False,
            }
            async with gate:
                start = time.perf_counter()
                for attempt in range(args.connect_retries + 1):
                    try:
                        obj = await asyncio.to_thread(
                            http_json, endpoint, payload, args.request_timeout
                        )
                        usage = obj.get("usage", {})
                        return RequestResult(
                            True,
                            time.perf_counter() - start,
                            int(usage.get("completion_tokens", 0)),
                            int(usage.get("prompt_tokens", prompt_count)),
                        )
                    except Exception as e:
                        if attempt == args.connect_retries or not refused(e):
                            return RequestResult(
                                False, time.perf_counter() - start, 0,
                                error=f"{type(e).__name__}: {e}",
                            )
                        retries[0] += 1
                        wait = min(
                            args.connect_backoff_ms * (2 ** attempt),
                            args.connect_backoff_cap_ms,
                        )
                        await asyncio.sleep(wait / 1000.0)
                raise AssertionError("unreachable: the loop returns on every path")

        budgets = [request_max_tokens(args, i) for i in range(len(prompts))]

        for i in range(args.warmup):
            await one(prompts[i], prompt_counts[i], budgets[i])

        run_prompts = prompts[args.warmup:]
        run_counts = prompt_counts[args.warmup:]
        run_budgets = budgets[args.warmup:]
        start = time.perf_counter()
        if args.mode == "latency":
            results = [
                await one(p, c, m)
                for p, c, m in zip(run_prompts, run_counts, run_budgets)
            ]
        else:
            results = await asyncio.gather(
                *(one(p, c, m)
                  for p, c, m in zip(run_prompts, run_counts, run_budgets))
            )
        wall = time.perf_counter() - start

    summary = summarize(
        mode=args.mode,
        engine="mlx-lm",
        model=args.model,
        results=results,
        wall_s=wall,
        config={
            "decode_concurrency": batch,
            "client_in_flight": batch,
            "connect_retries_spent": retries[0],
            "prompt_concurrency": args.prompt_concurrency,
            "prompt_cache_size": args.prompt_cache_size,
            "ignore_eos": "unsupported by mlx-lm; every request stopped at EOS "
                          "or --max-tokens",
            "temperature": args.temperature,
            "top_p": args.top_p,
            "unique_prompts": args.unique_prompts,
        },
    )
    return summary, results


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="mlx-lm canonical latency/throughput benchmark"
    )
    add_mode_subcommands(parser)
    for sp in parser._subparsers._group_actions[0].choices.values():
        sp.add_argument("--url", default="http://127.0.0.1:8080")
        sp.add_argument(
            "--spawn",
            action=argparse.BooleanOptionalAction,
            default=True,
            help="Start the server here. --no-spawn measures one already running "
                 "at --url, whose flags this cannot then report.",
        )
        sp.add_argument("--port", type=int, default=8080)
        sp.add_argument("--server-module", default=None,
                        help="python -m target for the server: `mlx_lm server` (default) or `mlx_vlm.server`")
        sp.add_argument("--server-extra", default="",
                        help="Extra server flags, space-separated (draft model, draft kind, ...)")
        sp.add_argument(
            "--python",
            default=None,
            help=f"Interpreter with mlx-lm. Defaults to {PINNED_ENV}, the pinned "
                 "environment every recorded answer in this tree came from.",
        )
        sp.add_argument("--prompt-concurrency", type=int, default=8)
        sp.add_argument(
            "--connect-retries",
            type=int,
            default=12,
            help="How many times a request refused at the socket may be "
                 "offered again. mlx-lm's listen backlog is five deep and its "
                 "accept loop starves under load; a refused request was never "
                 "admitted, so retrying it measures the engine.",
        )
        sp.add_argument("--connect-backoff-ms", type=float, default=50.0)
        sp.add_argument("--connect-backoff-cap-ms", type=float, default=2000.0)
        sp.add_argument(
            "--prompt-cache-size",
            type=int,
            default=0,
            help="0 keeps the cache out of the measurement, which is what the "
                 "other harnesses do with theirs.",
        )
        sp.add_argument("--startup-timeout", type=float, default=300.0)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    summary, results = asyncio.run(run(args))
    finish(summary, results, args.json_out)


if __name__ == "__main__":
    main()
