from __future__ import annotations

import argparse
import asyncio
import ctypes
import ctypes.util
import json
import math
import os
import random
import re
import statistics
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

ROOT = Path(os.environ.get("PIE_ROOT") or Path.home() / "pie").resolve()
BENCH_SYSTEM = "You are a helpful benchmarking assistant."
BENCH_PROMPT = "Write a short story about a robot."


def resolve_local_model(model: str) -> str:
    candidate = Path(model).expanduser()
    if candidate.exists():
        return str(candidate.resolve())
    pie_home = Path(os.environ.get("PIE_HOME", "~/.pie")).expanduser()
    for slug in (model, model.replace("/", "--")):
        art_dir = pie_home / "artifacts" / slug
        if art_dir.is_dir() and any(art_dir.glob("*.zt")):
            return model
    encoded = f"models--{model.replace('/', '--')}"
    roots = []
    if cache := os.environ.get("HF_HUB_CACHE"):
        roots.append(Path(cache).expanduser())
    if home := os.environ.get("HF_HOME"):
        roots.append(Path(home).expanduser() / "hub")
    roots.extend(
        (
            Path(os.environ.get("XDG_CACHE_HOME", "~/.cache")).expanduser()
            / "huggingface"
            / "hub",
            Path("~/.pie/programs").expanduser(),
        )
    )
    for root in roots:
        repository = root / encoded
        revision = None
        for ref_name in ("main", "master"):
            ref = repository / "refs" / ref_name
            if ref.is_file():
                revision = ref.read_text().strip()
                break
        if revision:
            snapshot = repository / "snapshots" / revision
            if snapshot.is_dir():
                return str(snapshot.resolve())
    raise FileNotFoundError(
        f"no local snapshot for {model!r}; download it before benchmarking"
    )


@dataclass
class RequestResult:
    ok: bool
    latency_s: float
    output_tokens: int
    prompt_tokens: int | None = None
    error: str | None = None
    ttft_s: float | None = None
    intertoken_us: list[int] | None = None
    client_send_s: float | None = None
    token_arrival_s: list[float] | None = None
    token_arrival_monotonic_ns: list[int] | None = None
    client_return_s: float | None = None
    process_id: str | None = None
    prologue_us: list[int] | None = None
    speculation: dict[str, Any] | None = None
    output_token_sha256: str | None = None
    output_token_ids: list[int] | None = None
    output_text: str | None = None


@dataclass
class BenchSummary:
    mode: str
    engine: str
    model: str
    requests: int
    completed: int
    failed: int
    wall_s: float
    output_tokens: int
    prompt_tokens: int | None
    req_per_s: float
    output_tok_per_s: float
    latency_mean_ms: float | None
    latency_p50_ms: float | None
    latency_p95_ms: float | None
    latency_p99_ms: float | None
    config: dict[str, Any]
    ttft_mean_ms: float | None = None
    ttft_p50_ms: float | None = None
    ttft_p95_ms: float | None = None
    ttft_p99_ms: float | None = None
    intertoken_p50_ms: float | None = None
    intertoken_p99_ms: float | None = None
    intertoken_max_ms: float | None = None


def end_trace() -> None:
    """Ends a CUPTI-profiled round (profiler/cupti.py) while an in-process engine still runs: at shutdown SGLang kills
    its scheduler process, and with it the device records CUPTI has not handed over yet."""
    d = os.environ.get("PIE_CUPTI_DIR")
    on = Path(d) / "on" if d else None
    if on is None or not on.exists():
        return
    try:
        n = on.read_text().strip()
        on.unlink()
    except OSError:
        return
    started = list(Path(d).glob(f"*-{n}.bin"))
    deadline = time.time() + 30
    while time.time() < deadline and not all(b.with_suffix(".done").exists() for b in started):
        time.sleep(0.05)


def percentile(xs: list[float], q: float) -> float | None:
    if not xs:
        return None
    s = sorted(xs)
    k = (len(s) - 1) * q
    lo = math.floor(k)
    hi = math.ceil(k)
    if lo == hi:
        return s[int(k)]
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


def arrival_schedule(
    n: int, rate: float, process: str, seed: int
) -> list[float]:
    if rate <= 0:
        return [0.0] * n
    rng = random.Random(seed)
    offsets: list[float] = []
    t = 0.0
    for _ in range(n):
        offsets.append(t)
        t += rng.expovariate(rate) if process == "poisson" else 1.0 / rate
    return offsets


class ArrivalPacer:

    def __init__(self, offsets: list[float]) -> None:
        self._offsets = offsets
        self._t0: float | None = None
        self.lag_s: list[float] = []

    @property
    def enabled(self) -> bool:
        return any(o > 0.0 for o in self._offsets)

    def start(self) -> None:
        self._t0 = time.perf_counter()

    async def wait(self, index: int) -> None:
        if self._t0 is None or index >= len(self._offsets):
            return
        due = self._t0 + self._offsets[index]
        delay = due - time.perf_counter()
        if delay > 0:
            await asyncio.sleep(delay)
        self.lag_s.append(max(0.0, time.perf_counter() - due))

    def stats(self) -> dict[str, Any]:
        if not self.lag_s:
            return {}
        return {
            "arrival_lag_p50_ms": (percentile(self.lag_s, 0.50) or 0.0) * 1e3,
            "arrival_lag_p99_ms": (percentile(self.lag_s, 0.99) or 0.0) * 1e3,
            "arrival_lag_max_ms": max(self.lag_s) * 1e3,
            "arrival_span_s": self._offsets[-1] if self._offsets else 0.0,
        }


def mac_thermal_state() -> str | None:
    if sys.platform != "darwin":
        return None
    try:
        objc = ctypes.cdll.LoadLibrary(ctypes.util.find_library("objc"))
        ctypes.cdll.LoadLibrary("/System/Library/Frameworks/Foundation.framework/Foundation")
        objc.objc_getClass.restype = ctypes.c_void_p
        objc.objc_getClass.argtypes = [ctypes.c_char_p]
        objc.sel_registerName.restype = ctypes.c_void_p
        objc.sel_registerName.argtypes = [ctypes.c_char_p]
        obj = ctypes.CFUNCTYPE(ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p)(("objc_msgSend", objc))
        num = ctypes.CFUNCTYPE(ctypes.c_long, ctypes.c_void_p, ctypes.c_void_p)(("objc_msgSend", objc))
        info = obj(objc.objc_getClass(b"NSProcessInfo"), objc.sel_registerName(b"processInfo"))
        return ("nominal", "fair", "serious", "critical")[num(info, objc.sel_registerName(b"thermalState"))]
    except Exception:
        return None


def cool_before_request(timeout_s: float = 600, poll_s: float = 5) -> float:
    if os.environ.get("PIE_BENCH_SETTLE", "1") == "0":
        return 0.0
    t0 = time.monotonic()
    while mac_thermal_state() not in (None, "nominal") and time.monotonic() - t0 < timeout_s:
        time.sleep(poll_s)
    return time.monotonic() - t0


def summarize(
    *,
    mode: str,
    engine: str,
    model: str,
    results: list[RequestResult],
    wall_s: float,
    config: dict[str, Any],
) -> BenchSummary:
    ok = [r for r in results if r.ok]
    lats = [r.latency_s for r in ok if r.latency_s > 0.0]
    output_tokens = sum(r.output_tokens for r in ok)
    prompt_known = [r.prompt_tokens for r in ok if r.prompt_tokens is not None]
    prompt_tokens = sum(prompt_known) if len(prompt_known) == len(ok) else None
    ttfts = [r.ttft_s for r in ok if getattr(r, "ttft_s", None) is not None]
    gaps_ms = [
        g / 1000.0
        for r in ok
        for g in (getattr(r, "intertoken_us", None) or [])
    ]
    return BenchSummary(
        mode=mode,
        engine=engine,
        model=model,
        requests=len(results),
        completed=len(ok),
        failed=len(results) - len(ok),
        wall_s=wall_s,
        output_tokens=output_tokens,
        prompt_tokens=prompt_tokens,
        req_per_s=(len(ok) / wall_s) if wall_s > 0 else 0.0,
        output_tok_per_s=(output_tokens / wall_s) if wall_s > 0 else 0.0,
        latency_mean_ms=(statistics.fmean(lats) * 1000.0) if lats else None,
        latency_p50_ms=(percentile(lats, 0.50) * 1000.0) if lats else None,
        latency_p95_ms=(percentile(lats, 0.95) * 1000.0) if lats else None,
        latency_p99_ms=(percentile(lats, 0.99) * 1000.0) if lats else None,
        config=config,
        ttft_mean_ms=(statistics.fmean(ttfts) * 1000.0) if ttfts else None,
        ttft_p50_ms=(percentile(ttfts, 0.50) * 1000.0) if ttfts else None,
        ttft_p95_ms=(percentile(ttfts, 0.95) * 1000.0) if ttfts else None,
        ttft_p99_ms=(percentile(ttfts, 0.99) * 1000.0) if ttfts else None,
        intertoken_p50_ms=percentile(gaps_ms, 0.50) if gaps_ms else None,
        intertoken_p99_ms=percentile(gaps_ms, 0.99) if gaps_ms else None,
        intertoken_max_ms=max(gaps_ms) if gaps_ms else None,
    )


def print_summary(s: BenchSummary) -> None:
    print()
    print("-" * 52)
    print(f"mode:              {s.mode}")
    print(f"engine:            {s.engine}")
    print(f"model:             {s.model}")
    print(f"completed:         {s.completed}/{s.requests}  failed={s.failed}")
    print(f"wall:              {s.wall_s:.3f} s")
    print(f"requests/sec:      {s.req_per_s:.2f}")
    print(f"output tokens:     {s.output_tokens}")
    if s.prompt_tokens is not None:
        print(f"prompt tokens:     {s.prompt_tokens}")
    print(f"output tok/sec:    {s.output_tok_per_s:.2f}")
    if s.latency_mean_ms is not None:
        print(f"lat mean/p50:      {s.latency_mean_ms:.1f} / {s.latency_p50_ms:.1f} ms")
        print(f"lat p95/p99:       {s.latency_p95_ms:.1f} / {s.latency_p99_ms:.1f} ms")
    if s.ttft_mean_ms is not None:
        print(f"ttft mean/p50:     {s.ttft_mean_ms:.1f} / {s.ttft_p50_ms:.1f} ms")
        print(f"ttft p95/p99:      {s.ttft_p95_ms:.1f} / {s.ttft_p99_ms:.1f} ms")
    if s.intertoken_p50_ms is not None:
        print(
            f"intertoken p50/p99/max: {s.intertoken_p50_ms:.2f} / "
            f"{s.intertoken_p99_ms:.2f} / {s.intertoken_max_ms:.2f} ms"
        )
    spec_keys = (
        "spec attempted",
        "spec hits",
        "spec misses",
        "spec rule skipped",
        "spec budget skipped",
        "spec dropped orphan",
        "spec need pages",
        "spec chain now",
        "spec chain peak",
        "spec longest chain",
        "total batches",
        "cumulative batch latency us",
        "avg batch latency us",
        "last batch latency us",
        "system spec draft tokens proposed",
        "system spec draft tokens accepted",
        "system spec draft tokens proposed per pos",
        "system spec draft tokens accepted per pos",
        "bypass hits",
        "chain submits",
        "chain drops",
        "total requests",
        "max forward requests",
        "batch size hist",
        "runtime launch ack mean ms",
        "runtime launch ack p50 ms",
        "runtime launch ack p95 ms",
        "runtime launch ack max ms",
        "runtime launch ack before start ms",
        "runtime first launch ack ms",
        "runtime all launch ack ms",
        "runtime ready before start ms",
        "runtime all ready ms",
        "runtime first return ms",
        "runtime last return ms",
        "runtime engine cumulative ms",
        "runtime wall minus engine ms",
        "runtime non-engine after launch ms",
        "vllm spec drafts",
        "vllm spec draft tokens",
        "vllm spec accepted tokens",
        "vllm spec accepted per position",
        "vllm spec acceptance rate",
        "vllm spec mean acceptance length",
    )
    if any(k in s.config for k in spec_keys):
        for k in spec_keys:
            if k in s.config:
                print(f"{k+':':<18} {s.config[k]}")
        hits = s.config.get("spec hits", 0)
        misses = s.config.get("spec misses", 0)
        attempted = s.config.get("spec attempted", 0)
        depth_cap = s.config.get("max chain depth")
        total_calls = hits + misses + attempted
        if total_calls > 0:
            print(f"{'spec hit rate:':<18} {hits / total_calls:.1%}")
        if depth_cap and attempted > 0:
            theoretical = attempted * depth_cap
            print(f"{'spec chain yield:':<18} {hits / theoretical:.1%}")
    print("-" * 52)


def write_json(path: str | None, summary: BenchSummary, results: list[RequestResult]) -> None:
    if not path:
        return
    out = {"summary": asdict(summary), "requests": [asdict(r) for r in results]}
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(out, indent=2))


def add_mode_subcommands(parser: argparse.ArgumentParser) -> None:
    sub = parser.add_subparsers(dest="mode", required=True)
    latency = sub.add_parser("latency", help="single-request latency")
    add_common_args(latency)
    latency.add_argument("--requests", type=int, default=16)
    latency.set_defaults(num_requests=0, concurrency=1)

    tput = sub.add_parser("tput", help="many-request throughput")
    add_common_args(tput)
    tput.add_argument("--num-requests", type=int, default=512)
    tput.add_argument(
        "--concurrency",
        type=int,
        default=0,
        help="Throughput concurrency cap. 0 means unlimited.",
    )
    tput.set_defaults(requests=0)


def add_common_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--model", default="Qwen/Qwen3-0.6B")
    p.add_argument("--prompt", default=BENCH_PROMPT)
    p.add_argument("--system", default=BENCH_SYSTEM)
    p.add_argument(
        "--think", action=argparse.BooleanOptionalAction, default=None,
        help="Pass enable_thinking to the chat template (Qwen3 family): --think / --no-think; "
             "absent, the template's own default applies.",
    )
    p.add_argument("--max-tokens", type=int, default=128)
    p.add_argument("--temperature", type=float, default=0.0)
    p.add_argument("--top-p", type=float, default=1.0)
    p.add_argument("--ignore-eos", action=argparse.BooleanOptionalAction, default=True)
    p.add_argument("--unique-prompts", action=argparse.BooleanOptionalAction, default=True)
    p.add_argument(
        "--prompts-file",
        default=None,
        help="JSON list of exact prompt strings, one per request (warmup first). "
             "Replaces --prompt and every shared-prefix rule, so the caller "
             "controls each prompt byte for byte (cold-cache runs).",
    )
    p.add_argument(
        "--shared-prefix-words",
        type=int,
        default=0,
        help="Prefix-heavy shape: prepend a deterministic shared block of "
             "roughly this many tokens to every prompt (unique tails kept). "
             "Pair with prefix caching on engines that support it.",
    )
    p.add_argument(
        "--output-spread",
        type=float,
        default=0.0,
        help="Fan per-request output budgets out over "
             "[max_tokens*(1-F), max_tokens*(1+F)] on a deterministic "
             "sawtooth with mean exactly max_tokens. Breaks the lockstep a "
             "uniform shape imposes on a closed-loop client without changing "
             "the total work.",
    )
    p.add_argument(
        "--mixed-phase",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Mixed-phase shape: even-indexed requests are prefill-heavy "
             "(long prompt, --mixed-short-output tokens out), odd-indexed "
             "are decode-heavy (short prompt, --max-tokens out). Run with "
             "prefix caching OFF on both engines.",
    )
    p.add_argument(
        "--mixed-long-prompt-words",
        type=int,
        default=400,
        help="Word count of the long prompt body in --mixed-phase.",
    )
    p.add_argument(
        "--mixed-short-output",
        type=int,
        default=16,
        help="max_tokens for the prefill-heavy half in --mixed-phase.",
    )
    p.add_argument(
        "--arrival-rate",
        type=float,
        default=0.0,
        help="Open-loop offered load in requests/second. 0 (the default) "
             "offers every request at t=0, which measures saturation only. "
             "A finite rate makes the load exogenous so queueing delay shows "
             "up in TTFT instead of being absorbed by the arrival process.",
    )
    p.add_argument(
        "--arrival-process",
        choices=["poisson", "uniform"],
        default="poisson",
        help="Inter-arrival distribution for --arrival-rate.",
    )
    p.add_argument(
        "--arrival-seed",
        type=int,
        default=20260730,
        help="Seeds the arrival schedule. Engines compared against each "
             "other must share this so they see the identical pattern.",
    )
    p.add_argument("--warmup", type=int, default=2)
    p.add_argument(
        "--warmup-seconds",
        type=float,
        default=0.0,
        help="Keep repeating the warmup set until this much wall time has "
             "elapsed, on top of --warmup. Off by default: on this hardware "
             "the run-to-run spread came from CPU pinning, not from a short "
             "warmup, and a longer warmup did not reduce it.",
    )
    p.add_argument(
        "--warmup-max-tokens",
        type=int,
        default=None,
        help="Override max_tokens only for warmup requests.",
    )
    p.add_argument("--json-out", default=None)
    p.add_argument(
        "--cuda-profiler-capture",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Call cudaProfilerStart/Stop around the measured section. Use with "
             "`nsys profile --capture-range=cudaProfilerApi` to exclude setup "
             "and warmup from the trace.",
    )
    p.add_argument(
        "--cuda-profiler-delay-s",
        type=float,
        default=0.0,
        help="Delay cudaProfilerStart after measured work begins.",
    )
    p.add_argument(
        "--cuda-profiler-duration-s",
        type=float,
        default=0.0,
        help="Stop a delayed profiler capture after this duration. Zero keeps "
        "the legacy whole-measured-window capture.",
    )
    p.add_argument(
        "--request-timeout",
        type=float,
        default=300.0,
        help="Seconds a request may wait; pie_bench counts them from the last event any request of the run heard.",
    )
    p.add_argument("--tp-size", type=int, default=1)
    p.add_argument(
        "--dp-size",
        type=int,
        default=1,
        help="Data-parallel replicas. Each replica is its own tp-size-wide "
             "shard group, so the run occupies tp_size * dp_size devices. "
             "PIE derives this from the device list (world_size / tp_size); "
             "vLLM takes it as data_parallel_size.",
    )
    p.add_argument(
        "--cpu-affinity",
        default="auto",
        help="CPU affinity for the benchmark process. Use 'auto' to pin to "
             "the GPU-local CPUs from `nvidia-smi topo -m`, 'none' to disable, "
             "or an explicit list like '80-87,208-215'.",
    )
    p.add_argument("--gpu-mem-util", type=float, default=0.90)
    p.add_argument(
        "--engine-option",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Extra [model.engine.options] entries, handed straight to the "
             "engine's own options struct (deny_unknown_fields still rules). "
             "Values parse as TOML scalars: true/false, ints, floats, else "
             "strings. Repeatable. pie cuda only; other engines "
             "ignore it.",
    )
    p.add_argument("--max-model-len", type=int, default=2048)
    p.add_argument("--sglang-attention-backend", default=None)
    p.add_argument("--sglang-sampling-backend", default=None)
    p.add_argument(
        "--sglang-moe-runner-backend",
        default=None,
        help="SGLang's MoE runner. Its auto pick for DeepSeek-V4.1's MXFP4 experts "
             "(flashinfer_mxfp4) wants 128-multiple widths a tp4 share is not.",
    )
    p.add_argument(
        "--sglang-flashinfer-mxfp4-moe-precision",
        default=None,
        help="SGLang's flashinfer_mxfp4 MoE activations. Its default on SM100 quantizes them "
             "to MXFP8; bf16 keeps gpt-oss at pie's and vLLM's W4A16.",
    )
    p.add_argument(
        "--sglang-kv-cache-dtype",
        default=None,
        help="SGLang's KV cache dtype. Its auto pick for DSA models on SM100 and newer "
             "(SM120 too) is fp8_e4m3; bfloat16 keeps the cache at pie's and vLLM's precision.",
    )
    p.add_argument(
        "--sglang-dsa-backend",
        default=None,
        help="SGLang's DSA prefill and decode kernels. Its auto pick on an "
             "SM120 card at a bf16 KV cache is trtllm-gen, which runs on SM100 only.",
    )
    p.add_argument(
        "--sglang-max-total-tokens",
        type=int,
        default=None,
        help="Pin SGLang's KV pool to this many tokens. The cross-engine "
             "analogue of pie's `--device-kv-budget` and vLLM's "
             "`--num-gpu-blocks-override P --block-size B`: without it the "
             "pool is sized from --gpu-mem-util and the three engines are "
             "not given the same KV budget.",
    )
    p.add_argument(
        "--sglang-page-size",
        type=int,
        default=None,
        help="SGLang KV page size in tokens. Defaults to SGLang's own "
             "default (1). Set to 16 to match vLLM's --block-size and pie's "
             "page granularity so internal fragmentation is comparable too.",
    )
    p.add_argument(
        "--sglang-cuda-graph-max-bs",
        type=int,
        default=None,
        help="Largest decode batch SGLang captures a CUDA graph for. "
             "SGLang's default is a hardware-tier heuristic keyed on total "
             "GPU memory (32 on an L40S at tp<4), so a decode batch of 128 "
             "runs eager and a small model loses most of its throughput to "
             "launch overhead. vLLM captures up to max_num_seqs, so leaving "
             "this at SGLang's default measures the heuristic, not the "
             "engine. Set it to the concurrency.",
    )
    p.add_argument("--sglang-disable-cuda-graph", action=argparse.BooleanOptionalAction, default=False)
    p.add_argument("--sglang-disable-piecewise-cuda-graph", action=argparse.BooleanOptionalAction, default=False)
    p.add_argument(
        "--sglang-disable-hybrid-swa-memory",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Size one uniform KV pool instead of SGLang's split "
             "sliding-window/full-attention pools. On a sliding-window model "
             "(Gemma) the hybrid sizer derives a token budget from the cheap "
             "SWA layers and then refuses to start because the full-attention "
             "layers cannot hold that many tokens — SGLang aborts where vLLM "
             "just sizes the pool from free memory and schedules within it. "
             "Set this to get a run at all, and to put both engines on the "
             "same pool policy.",
    )
    p.add_argument(
        "--wasm-delay-us",
        type=int,
        default=0,
        help="Busy-spin in the bench inferlet's WASM between every "
             "execute() call (microseconds). Simulates per-token "
             "WASM work — useful for measuring the wall-clock benefit "
             "of async chain firing on W>0 workloads. Default 0.",
    )
    p.add_argument(
        "--run-ahead-frames",
        type=int,
        default=None,
        help="Decode frames each pie lane keeps queued in the engine. "
             "The wave quorum waits for every lane, so deeper queues hide "
             "guest turnaround. pie only; unset means the engine sizes the "
             "window itself via model.channel-capacity().",
    )


FIXED_PREFILL = dict(batch=32, input_len=4096, output_len=1)
FIXED_DECODE_BATCHES = (1, 8, 64)
FIXED_DECODE_INPUT, FIXED_DECODE_OUTPUT = 512, 256
FIXED_SERVE = dict(num_prompts=256, input_len=1024, output_len=256)


def fixed_prompt_ids(rng: random.Random, vocab: int, batch: int, input_len: int) -> list[list[int]]:
    return [[rng.randrange(100, vocab - 100) for _ in range(input_len)] for _ in range(batch)]


def tokenizer_vocab_size(snapshot: str) -> int:
    path = Path(snapshot)
    if not (path / "tokenizer.json").exists() and (path / "tiktoken.model").exists():
        with open(path / "config.json", encoding="utf-8") as f:
            cfg = json.load(f)
        return int(cfg.get("text_config", cfg)["vocab_size"])
    with open(path / "tokenizer.json", encoding="utf-8") as f:
        return len(json.load(f)["model"]["vocab"])


def _gpu_compute_apps() -> tuple[int, dict[int, int]]:
    used = subprocess.run(
        ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
        capture_output=True, text=True, timeout=10).stdout.split()
    procs = subprocess.run(
        ["nvidia-smi", "--query-compute-apps=pid,used_memory", "--format=csv,noheader,nounits"],
        capture_output=True, text=True, timeout=10).stdout.splitlines()
    apps = {}
    for line in procs:
        if "," in line:
            pid, mib = (x.strip() for x in line.split(",", 1))
            apps[int(pid)] = int(mib) if mib.isdigit() else 0
    return sum(int(u) for u in used), apps


def _descends_from(pid: int, root: int) -> bool:
    while pid > 1:
        if pid == root:
            return True
        try:
            with open(f"/proc/{pid}/stat") as f:
                pid = int(f.read().rsplit(")", 1)[1].split()[1])
        except (OSError, ValueError, IndexError):
            return False
    return False


class MemSampler:

    def __init__(self, path: str, period: float = 1.0) -> None:
        import threading

        self.path, self.period = path, period
        self.peak = 0
        self.foreign: set[int] = set()
        self._measuring = threading.Event()
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def _run(self) -> None:
        me = os.getpid()
        with open(self.path, "w") as f:
            f.write("t,memory_used_mib,util_pct,processes\n")
            t0 = time.time()
            while not self._stop.is_set():
                try:
                    used, util = subprocess.run(
                        ["nvidia-smi", "--query-gpu=memory.used,utilization.gpu", "--format=csv,noheader,nounits"],
                        capture_output=True, text=True, timeout=10).stdout.split(",")[:2]
                    _, apps = _gpu_compute_apps()
                    if self._measuring.is_set():
                        self.foreign |= {pid for pid in apps if not _descends_from(pid, me)}
                    used = int(used)
                    self.peak = max(self.peak, used)
                    procs = " ".join(f"{pid}:{mib}" for pid, mib in apps.items())
                    f.write(f"{time.time() - t0:.1f},{used},{util.strip()},{procs}\n")
                    f.flush()
                except Exception:
                    pass
                self._stop.wait(self.period)

    def measuring(self) -> None:
        self._measuring.set()

    def __enter__(self) -> MemSampler:
        self._thread.start()
        return self

    def __exit__(self, *exc) -> None:
        self._stop.set()
        self._thread.join()


def gpu_clock_state() -> list[dict[str, Any]]:
    try:
        out = subprocess.run(
            ["nvidia-smi",
             "--query-gpu=index,clocks.sm,clocks.max.sm,utilization.gpu",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5, check=True).stdout
    except Exception:
        return []
    state = []
    for line in out.strip().splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) != 4:
            continue
        try:
            state.append({
                "index": int(parts[0]),
                "sm_mhz": int(parts[1]),
                "sm_max_mhz": int(parts[2]),
                "util_pct": int(parts[3]),
            })
        except ValueError:
            continue
    return state


async def run_timed_warmup(run_once, seconds: float, label: str = "pie") -> int:
    if seconds <= 0:
        return 0
    import time as _time
    start = _time.monotonic()
    passes = 0
    while _time.monotonic() - start < seconds:
        await run_once()
        passes += 1
    print(f"[{label}-bench] warmup: {passes} extra pass(es) over "
          f"{_time.monotonic() - start:.1f}s", flush=True)
    return passes


def run_timed_warmup_sync(run_once, seconds: float, label: str = "vllm") -> int:
    if seconds <= 0:
        return 0
    import time as _time
    start = _time.monotonic()
    passes = 0
    while _time.monotonic() - start < seconds:
        run_once()
        passes += 1
    print(f"[{label}-bench] warmup: {passes} extra pass(es) over "
          f"{_time.monotonic() - start:.1f}s", flush=True)
    return passes


def _filler_words(count: int) -> str:
    base = (
        "the quick brown fox jumps over the lazy dog and then walks "
        "back home again to rest before the next long day begins"
    ).split()
    return " ".join(base[i % len(base)] for i in range(count))


OUTPUT_SPREAD_PERIOD = 16


def request_max_tokens(args: argparse.Namespace, i: int) -> int:
    if getattr(args, "mixed_phase", False) and i % 2 == 0:
        return args.mixed_short_output
    spread = getattr(args, "output_spread", 0.0) or 0.0
    if spread > 0.0:
        frac = (i % OUTPUT_SPREAD_PERIOD) / (OUTPUT_SPREAD_PERIOD - 1)
        return max(1, round(args.max_tokens * (1.0 + spread * (2.0 * frac - 1.0))))
    return args.max_tokens


def request_max_tokens_varies(args: argparse.Namespace) -> bool:
    if getattr(args, "mixed_phase", False):
        return True
    return (getattr(args, "output_spread", 0.0) or 0.0) > 0.0


def hash_output_tokens(token_ids: list[int]) -> str:
    import hashlib

    digest = hashlib.sha256()
    for token in token_ids:
        digest.update(int(token).to_bytes(4, "little", signed=False))
    return digest.hexdigest()


def add_output_dump_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--dump-first-text", action="store_true")
    p.add_argument("--dump-all-token-ids", action="store_true")
    p.add_argument("--dump-all-texts", action="store_true")


def print_first_output(args: argparse.Namespace, text: str | None) -> None:
    if not getattr(args, "dump_first_text", False) or text is None:
        return
    import hashlib

    sha = hashlib.sha256(text.encode()).hexdigest()[:16]
    print(f"\nFIRST REQUEST OUTPUT (sha256[:16]={sha}):")
    print(text)
    print(f"END OUTPUT (chars={len(text)})")


def make_prompts(args: argparse.Namespace, n: int) -> list[str]:
    prompts_file = getattr(args, "prompts_file", None)
    if prompts_file:
        with open(prompts_file, encoding="utf-8") as f:
            prompts = json.load(f)
        if not isinstance(prompts, list) or not all(isinstance(x, str) for x in prompts):
            raise SystemExit(f"--prompts-file {prompts_file}: expected a JSON list of strings")
        if len(prompts) < n:
            raise SystemExit(f"--prompts-file {prompts_file}: {len(prompts)} prompts, {n} needed")
        return prompts[:n]
    if getattr(args, "mixed_phase", False):
        long_body = _filler_words(getattr(args, "mixed_long_prompt_words", 400))
        return [
            f"{long_body}. {args.prompt} (Request #{i})"
            if i % 2 == 0
            else f"{args.prompt} (Request #{i})"
            for i in range(n)
        ]
    shared_words = getattr(args, "shared_prefix_words", 0) or 0
    if shared_words > 0:
        base = (
            "the quick brown fox jumps over the lazy dog and then walks "
            "back home again to rest before the next long day begins"
        ).split()
        filler = " ".join(base[i % len(base)] for i in range(shared_words))
        shared = (
            "You will answer questions about the following policy. "
            + filler
            + ". Policy ends. "
        )
        return [f"{shared}{args.prompt} (Request #{i})" for i in range(n)]
    if args.unique_prompts:
        return [f"{args.prompt} (Request #{i})" for i in range(n)]
    return [args.prompt for _ in range(n)]


def _render_chat(tok, system: str, prompts: list[str], enable_thinking: bool | None = None) -> list[str]:
    if getattr(tok, "chat_template", None):
        extra = {} if enable_thinking is None else {"enable_thinking": enable_thinking}
        return [
            tok.apply_chat_template(
                [{"role": "system", "content": system},
                 {"role": "user", "content": p}],
                tokenize=False,
                add_generation_prompt=True,
                **extra,
            )
            for p in prompts
        ]
    return [f"{system}\n\n{p}" if system else p for p in prompts]


def hf_chat_prompts_and_counts(
    model: str, system: str, prompts: list[str], enable_thinking: bool | None = None
) -> tuple[list[str], list[int]]:
    from transformers import AutoTokenizer

    tok = AutoTokenizer.from_pretrained(str(Path(model).parent) if Path(model).is_file() else model, trust_remote_code=True)
    rendered = _render_chat(tok, system, prompts, enable_thinking)
    counts = [len(tok.encode(p, add_special_tokens=False)) for p in rendered]
    return rendered, counts


def hf_chat_token_ids_and_counts(
    model: str, system: str, prompts: list[str], enable_thinking: bool | None = None
) -> tuple[list[list[int]], list[int]]:
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(str(Path(model).parent) if Path(model).is_file() else model, trust_remote_code=True)
    rendered = _render_chat(tok, system, prompts, enable_thinking)
    token_ids = [tok.encode(p, add_special_tokens=False) for p in rendered]
    return token_ids, [len(ids) for ids in token_ids]


def finish(summary: BenchSummary, results: list[RequestResult], json_out: str | None) -> None:
    print_summary(summary)
    write_json(json_out, summary, results)
    if summary.failed:
        print(f"{summary.failed} request(s) failed; inspect JSON output for details.")


def _load_cudart():
    candidates = []
    if override := os.environ.get("CUDART_LIBRARY"):
        candidates.append(override)
    for env_name in ("CUDA_HOME", "CUDA_PATH"):
        if cuda_root := os.environ.get(env_name):
            candidates.extend(
                (
                    str(Path(cuda_root) / "lib64" / "libcudart.so"),
                    str(
                        Path(cuda_root)
                        / "targets"
                        / "x86_64-linux"
                        / "lib"
                        / "libcudart.so"
                    ),
                )
            )
    found = ctypes.util.find_library("cudart")
    if found:
        candidates.append(found)
    candidates.extend(
        [
            "libcudart.so",
            "libcudart.so.13",
            "/usr/local/cuda/lib64/libcudart.so",
            "/usr/local/cuda-13.0/lib64/libcudart.so",
        ]
    )
    last_error: Exception | None = None
    for candidate in candidates:
        try:
            return ctypes.CDLL(candidate)
        except OSError as exc:
            last_error = exc
    raise RuntimeError(f"could not load CUDA runtime: {last_error}")


def cuda_profiler_start(enabled: bool) -> None:
    if not enabled:
        return
    cudart = _load_cudart()
    rc = int(cudart.cudaProfilerStart())
    if rc != 0:
        raise RuntimeError(f"cudaProfilerStart failed with CUDA error {rc}")


def cuda_profiler_stop(enabled: bool) -> None:
    if not enabled:
        return
    cudart = _load_cudart()
    rc = int(cudart.cudaProfilerStop())
    if rc != 0:
        raise RuntimeError(f"cudaProfilerStop failed with CUDA error {rc}")


def xla_trace(action: str, folder: str | None = None) -> None:
    """Under the profiler (PIE_BENCH_JAX_TRACE_DIR), starts or stops the device trace of every engine process armed
    there and alive, and waits until each has started or written it. pie's server (pie-<pid>.pid, profiler/
    xla_trace.c) takes SIGUSR1 and SIGUSR2; processes that imported jax (<pid>.pid, profiler/jax_site) watch the
    folder's `command` file from a thread of their own, as a signal reaches Python only in a main thread that may be
    blocked. An engine that runs inside its bench client (pie's server, vLLM's engine core) is traced this way around
    the measured requests only; the profiler does the same around the whole round for a server already up."""
    import signal

    folder = folder or os.environ.get("PIE_BENCH_JAX_TRACE_DIR")
    if not folder or not (Path(folder) / "recording").exists():  # a benchmark round beside the profiled one runs untraced
        return
    # a trace starts in a second or two; writing one can take minutes
    marker, sig, timeout_s = {"start": ("started", signal.SIGUSR1, 120), "stop": ("done", signal.SIGUSR2, 900)}[action]
    seq = str(time.time_ns())
    names = []
    for p in Path(folder).glob("*.pid"):
        pid = int(p.stem.removeprefix("pie-"))
        try:
            os.kill(pid, 0)
        except OSError:
            continue
        names.append(p.stem)
        if p.stem.startswith("pie-"):
            (p.parent / f"{p.stem}.{marker}").unlink(missing_ok=True)
            os.kill(pid, sig)
    tmp = Path(folder) / f".command-{os.getpid()}"
    tmp.write_text(f"{seq} {action}")
    tmp.replace(Path(folder) / "command")
    deadline = time.monotonic() + timeout_s
    for name in names:
        path, jax = Path(folder) / f"{name}.{marker}", not name.startswith("pie-")
        while True:
            words = (path.read_text() if path.exists() else "").split()
            if words and (not jax or words[0] == seq):
                break
            if time.monotonic() > deadline:
                raise RuntimeError(f"{name}: no trace {marker} marker after {timeout_s} s")
            time.sleep(0.05)
        if words[jax:][:1] == ["error"]:
            raise RuntimeError(f"{name}: trace {marker}: {' '.join(words)}")


def _parse_cpu_list(spec: str) -> set[int]:
    cpus: set[int] = set()
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            lo, hi = part.split("-", 1)
            cpus.update(range(int(lo), int(hi) + 1))
        else:
            cpus.add(int(part))
    return cpus


def _format_cpu_list(cpus: set[int]) -> str:
    if not cpus:
        return ""
    xs = sorted(cpus)
    ranges: list[str] = []
    start = prev = xs[0]
    for x in xs[1:]:
        if x == prev + 1:
            prev = x
            continue
        ranges.append(f"{start}-{prev}" if start != prev else str(start))
        start = prev = x
    ranges.append(f"{start}-{prev}" if start != prev else str(start))
    return ",".join(ranges)


def _numa_node_cpus(node: int) -> set[int]:
    try:
        text = Path(
            f"/sys/devices/system/node/node{node}/cpulist").read_text()
    except OSError:
        return set()
    return _parse_cpu_list(text.strip())


def gpu_local_cpu_affinity(gpu_ids: list[int]) -> set[int]:
    if not gpu_ids:
        return set()
    try:
        topo = subprocess.check_output(
            ["nvidia-smi", "topo", "-m"],
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        return set()
    ansi = re.compile(r"\x1b\[[0-9;]*m")
    lines = [ansi.sub("", line).strip() for line in topo.splitlines() if line.strip()]
    if not lines:
        return set()
    header = lines[0].split()
    gpu_cols = sum(1 for tok in header if re.fullmatch(r"(?:GPU|NIC)\d+", tok))
    affinity_by_gpu: dict[int, set[int]] = {}
    numa_by_gpu: dict[int, int] = {}
    for line in lines[1:]:
        toks = line.split()
        if len(toks) <= gpu_cols + 1 or not re.fullmatch(r"GPU\d+", toks[0]):
            continue
        gpu = int(toks[0][3:])
        affinity_by_gpu[gpu] = _parse_cpu_list(toks[1 + gpu_cols])
        if len(toks) > gpu_cols + 2:
            try:
                numa_by_gpu[gpu] = int(toks[2 + gpu_cols])
            except ValueError:
                pass
    cpus: set[int] = set()
    for gpu in gpu_ids:
        node = numa_by_gpu.get(gpu)
        node_cpus = _numa_node_cpus(node) if node is not None else set()
        cpus.update(node_cpus or affinity_by_gpu.get(gpu, set()))
    if hasattr(os, "sched_getaffinity"):
        cpus &= set(os.sched_getaffinity(0))
    return cpus


def visible_cuda_devices(tp_size: int, dp_size: int = 1) -> list[int]:
    world = max(1, tp_size) * max(1, dp_size)
    visible = os.environ.get("CUDA_VISIBLE_DEVICES")
    if visible:
        ids: list[int] = []
        for item in visible.split(","):
            item = item.strip()
            if item.isdigit():
                ids.append(int(item))
        if ids:
            return ids[:world]
    return list(range(world))


def maybe_set_cpu_affinity(args: argparse.Namespace, gpu_ids: list[int]) -> str | None:
    mode = getattr(args, "cpu_affinity", "auto")
    if mode in (None, "", "none") or not hasattr(os, "sched_setaffinity"):
        return None
    cpus = gpu_local_cpu_affinity(gpu_ids) if mode == "auto" else _parse_cpu_list(mode)
    if not cpus or not hasattr(os, "sched_setaffinity"):
        return None
    os.sched_setaffinity(0, cpus)
    return _format_cpu_list(cpus)
