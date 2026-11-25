#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import json
import sys
import threading
import time
import traceback
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import openai_bench
from bench_results import RequestResult, finish
from bench_tracing import monotonic_ns


def client(argv: list[str]) -> int:
    url = argv[argv.index("--url") + 1].rstrip("/")
    req = urllib.request.Request(
        url + "/bench",
        data=json.dumps({"argv": argv}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=None) as resp:
        body = json.loads(resp.read())
    if body.get("error"):
        print(body["error"], file=sys.stderr)
        return 1
    print(body.get("log", ""))
    return 0


def _server_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--model", required=True)
    p.add_argument("--port", type=int, required=True)
    p.add_argument("--options", required=True, help="LLM API options (yaml)")
    p.add_argument("--tp-size", type=int, default=1)
    p.add_argument("--max-batch-size", type=int, required=True)
    p.add_argument("--max-seq-len", type=int, required=True)
    p.add_argument("--max-num-tokens", type=int, default=8192)
    return p.parse_args(argv)


def _load_llm(a: argparse.Namespace):
    import yaml
    from tensorrt_llm import LLM
    from tensorrt_llm.llmapi import CudaGraphConfig, KvCacheConfig, MoeConfig

    with open(a.options) as f:
        opts = yaml.safe_load(f) or {}
    typed = {
        "kv_cache_config": KvCacheConfig,
        "cuda_graph_config": CudaGraphConfig,
        "moe_config": MoeConfig,
    }
    kw = {k: (typed[k](**v) if k in typed and isinstance(v, dict) else v) for k, v in opts.items()}
    return LLM(
        model=a.model,
        backend="pytorch",
        tensor_parallel_size=a.tp_size,
        max_batch_size=a.max_batch_size,
        max_seq_len=a.max_seq_len,
        max_num_tokens=a.max_num_tokens,
        trust_remote_code=True,
        **kw,
    )


async def _stream(llm, prompt: str, sp) -> tuple[float, list[float], int, int | None, int]:
    start = time.perf_counter()
    sent_ns = monotonic_ns()
    stamps: list[float] = []
    n, n_in = 0, None
    async for out in llm.generate_async(prompt, sampling_params=sp, streaming=True):
        k = len(out.outputs[0].token_ids)
        if k > n:
            stamps.append(time.perf_counter())
            n = k
        if n_in is None and getattr(out, "prompt_token_ids", None) is not None:
            n_in = len(out.prompt_token_ids)
    return start, stamps, n, n_in, sent_ns


def _in_process_run_one(llm, loop: asyncio.AbstractEventLoop):
    from tensorrt_llm import SamplingParams

    def run_one(args, endpoint, prompt, prompt_count, max_tokens, server, retries=None):
        body = json.loads(args.extra_body or "{}")
        sp = SamplingParams(
            max_tokens=max_tokens,
            temperature=args.temperature,
            top_p=args.top_p,
            ignore_eos=bool(body.get("ignore_eos", False)),
            add_special_tokens=bool(body.get("add_special_tokens", True)),
        )
        t0 = time.perf_counter()
        try:
            start, stamps, n_out, n_in, sent_ns = asyncio.run_coroutine_threadsafe(
                _stream(llm, prompt, sp), loop
            ).result()
        except Exception as e:
            return RequestResult(
                False, time.perf_counter() - t0, 0, error=f"{type(e).__name__}: {e}"
            )
        end = time.perf_counter()
        n_in = n_in if n_in is not None else prompt_count
        server.append(
            {
                "prompt_tokens": n_in,
                "output_tokens": n_out,
                "max_tokens": max_tokens,
                "hf_prompt_tokens": prompt_count,
                "usage_reported": True,
                "cached_tokens": 0,
                "prefill_tok_s": None,
                "decode_tok_s": None,
            }
        )
        ttft = (stamps[0] - start) if stamps else None
        gaps = [int((b - a) * 1e6) for a, b in zip(stamps, stamps[1:])]
        return RequestResult(
            True,
            end - start,
            n_out,
            n_in,
            ttft_s=ttft,
            intertoken_us=gaps,
            client_send_s=sent_ns / 1e9,
        )

    return run_one


class BenchHandler(BaseHTTPRequestHandler):
    lock = threading.Lock()

    def log_message(self, *_):
        pass

    def _send(self, code: int, obj: dict) -> None:
        data = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        self._send(200 if self.path in ("/health", "/v1/models") else 404, {"ok": True})

    def do_POST(self):
        if self.path != "/bench":
            return self._send(404, {"error": "unknown path"})
        req = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)))
        with self.lock:
            try:
                args = openai_bench.build_parser().parse_args(req["argv"])
                summary, results = asyncio.run(openai_bench.run(args))
                summary.config["in_process_client"] = 1.0
                finish(summary, results, args.json_out)
                self._send(200, {"ok": True})
            except Exception as e:
                self._send(
                    200, {"error": f"{type(e).__name__}: {e}\n{traceback.format_exc()[-2000:]}"}
                )


def serve(argv: list[str]) -> int:
    a = _server_args(argv)
    llm = _load_llm(a)
    loop = asyncio.new_event_loop()
    threading.Thread(target=loop.run_forever, daemon=True).start()
    openai_bench.run_one = _in_process_run_one(llm, loop)
    ThreadingHTTPServer(("127.0.0.1", a.port), BenchHandler).serve_forever()
    return 0


def main() -> int:
    argv = sys.argv[1:]
    if argv and argv[0] == "serve":
        return serve(argv[1:])
    return client(argv)


if __name__ == "__main__":
    sys.exit(main())
