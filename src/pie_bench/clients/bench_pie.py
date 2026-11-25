#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import contextlib
import hashlib
import inspect
import json
import os
import socket
import subprocess
import sys
import time
import tomllib
from collections import Counter
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from bench_args import add_mode_subcommands
from bench_devices import (
    gpu_clock_state,
    maybe_set_cpu_affinity,
    resolve_local_model,
    visible_cuda_devices,
)
from bench_pacing import ArrivalPacer, arrival_schedule, cool_before_request, run_timed_warmup
from bench_prompts import hf_chat_token_ids_and_counts, make_prompts, request_max_tokens
from bench_replicas import run_replicas
from bench_results import RequestResult, finish, hash_output_tokens, print_first_output, summarize
from bench_tracing import (
    monotonic_ns,
    seconds_after,
    start_measured_profiler,
    stop_measured_profiler,
    xla_trace,
)

ROOT = Path(os.environ.get("PIE_ROOT") or Path.home() / "pie").resolve()
SERVER_PY = ROOT / "packages" / "python" / "server" / "python"
if str(SERVER_PY) not in sys.path:
    sys.path.insert(0, str(SERVER_PY))

PIE_BENCH_DEFAULT_DEVICE = "cuda:0"
PIE_MAX_FORWARD_TOKENS_DEFAULT = 10240
PIE_MAX_FORWARD_REQUESTS_DEFAULT = 512
STARTUP_TAIL_LINES = 80
REPLICA_FLAGS = {"--dp-size", "--json-out", "--requests", "--num-requests", "--device"}

ENGINE_SOURCE_SUFFIXES = {".c", ".cc", ".cpp", ".cu", ".cuh", ".h", ".hpp", ".rs"}

SURFACED_PREFIXES = (
    "ane: ",
    "[fire ",
    "[pie-fire-timing] ",
    "[sched-fire ",
    "[outer-fire ",
    "[sched-batch ",
    "[pie-spec] ",
    "[pie-engine-cuda] sampled tokens ",
)
SURFACED_FRAGMENTS = (
    "panicked at",
    "[pie-engine-cuda] memory planner:",
    "[pie-engine-cuda] forward_limits:",
    "[pie-engine-cuda] kv_cache:",
    "[pie-engine-cuda] CUDA graph upfront capture:",
    " xqa_decode=",
    " WARN ",
    " ERROR ",
    "Batch response count mismatch",
    "fire_batch failed",
    "exceeds workspace",
    "graph captured",
)

SPECULATION_FIELDS = (
    "rounds",
    "drafted",
    "accepted",
    "plain_fires",
    "verify",
    "prices_ms",
    "budget_model",
    "budget_expected",
)

CUMULATIVE_STATUS_KEYS = {
    "batch_size_hist",
    "bypass_hits",
    "chain_drops",
    "chain_submits",
    "cumulative_batch_latency_us",
    "escape_fires",
    "readiness_miss",
    "spec_attempted",
    "spec_budget_skipped",
    "spec_dropped_orphan",
    "spec_hits",
    "spec_misses",
    "spec_need_pages",
    "spec_rule_skipped",
    "submit_ahead_fires",
    "total_batches",
    "total_requests_processed",
    "total_tokens_processed",
    "wave_fires",
    "device_idle_us",
    "device_idle_gaps",
    "idle_break_control",
    "idle_break_depth",
    "idle_park_control_us",
    "idle_park_other_us",
    "accept_us",
    "accept_calls",
    "turnaround_sum_us",
    "turnaround_n",
    "lane_launch_us",
    "lane_launch_n",
    "lane_prefill_us",
    "lane_prefill_n",
    "lane_control_us",
    "lane_control_n",
    "seal_events",
    "seal_while_executing",
    "dispatch_blocked_holds",
}

PER_BATCH_AVERAGES = (
    ("default.cumulative_batch_latency_us", "default.avg_batch_latency_us"),
    ("default.fire.accumulate.accum_loop_us_sum", "default.fire.accumulate.accum_loop_us"),
    ("default.fire.pre_dispatch.fire_prepare_us_sum", "default.fire.pre_dispatch.fire_prepare_us"),
    ("default.fire.execute.total_us_sum", "default.fire.execute.total_us"),
    ("default.fire.execute.batch_build_us_sum", "default.fire.execute.batch_build_us"),
    ("default.fire.execute.engine_fire_us_sum", "default.fire.execute.engine_fire_us"),
    (
        "default.fire.post_dispatch.context_tick_us_sum",
        "default.fire.post_dispatch.context_tick_us",
    ),
    (
        "default.fire.post_dispatch.stats_update_us_sum",
        "default.fire.post_dispatch.stats_update_us",
    ),
    ("default.fire.quorum.inter_batch_bubble_us_sum", "default.fire.quorum.inter_batch_bubble_us"),
    ("default.fire.quorum.quorum_latency_us_sum", "default.fire.quorum.quorum_latency_us"),
)
PER_GAP_AVERAGES = (
    ("default.fire.inter_fire_us_sum", "default.fire.inter_fire_us"),
    ("default.fire.post_dispatch_to_fire_us_sum", "default.fire.post_dispatch_to_fire_us"),
    ("default.fire.recv_block_wait_us_sum", "default.fire.recv_block_wait_us"),
)
PER_WAVE_AVERAGES = (
    ("default.fire.quorum.wave_active_sum", "default.fire.quorum.avg_active_pipelines_at_fire"),
    ("default.fire.quorum.wave_missing_sum", "default.fire.quorum.avg_missing_at_fire"),
)

STATUS_LABELS = (
    ("default.spec_attempted", "spec attempted"),
    ("default.spec_hits", "spec hits"),
    ("default.spec_misses", "spec misses"),
    ("default.spec_rule_skipped", "spec rule skipped"),
    ("default.spec_budget_skipped", "spec budget skipped"),
    ("default.spec_dropped_orphan", "spec dropped orphan"),
    ("default.spec_need_pages", "spec need pages"),
    ("default.spec_chain_entries", "spec chain now"),
    ("default.spec_chain_entries_high_water", "spec chain peak"),
    ("default.spec_longest_chain", "spec longest chain"),
    ("default.total_batches", "total batches"),
    ("default.avg_batch_latency_us", "avg batch latency us"),
    ("default.fire.inter_fire_us", "fire.inter_fire_us"),
    ("default.fire.post_dispatch_to_fire_us", "fire.post_dispatch_to_fire_us"),
    ("default.fire.accumulate.accum_loop_us", "fire.accumulate.accum_loop_us"),
    ("default.fire.pre_dispatch.fire_prepare_us", "fire.pre_dispatch.fire_prepare_us"),
    ("default.fire.execute.total_us", "fire.execute.total_us"),
    ("default.fire.execute.batch_build_us", "fire.execute.batch_build_us"),
    ("default.fire.execute.engine_fire_us", "fire.execute.engine_fire_us"),
    ("default.fire.quorum.avg_active_pipelines_at_fire", "wave avg active pipelines"),
    ("default.fire.quorum.avg_missing_at_fire", "wave avg missing pipelines"),
    ("default.fire.quorum.wave_fires", "wave fires"),
    ("default.fire.quorum.seal_events", "seal events"),
    ("default.fire.quorum.seal_while_executing", "seals while executing"),
    ("default.fire.quorum.dispatch_blocked_holds", "sealed-queue blocked holds"),
    ("default.fire.quorum.device_idle_us", "device idle us"),
    ("default.fire.quorum.device_idle_gaps", "device idle gaps"),
    ("default.fire.quorum.idle_break_control", "idle breaks (control holds launches)"),
    ("default.fire.quorum.idle_break_depth", "idle breaks (depth cap)"),
    ("default.fire.quorum.idle_park_control_us", "idle park us (control holds launches)"),
    ("default.fire.quorum.idle_park_other_us", "idle park us (other)"),
    ("default.fire.quorum.accept_us", "accept us total"),
    ("default.fire.quorum.turnaround_sum_us", "turnaround sum us"),
    ("default.fire.quorum.turnaround_max_us", "turnaround max us"),
    ("default.fire.quorum.turnaround_n", "turnaround n"),
    ("default.fire.quorum.lane_launch_us", "lane launch us"),
    ("default.fire.quorum.lane_launch_n", "lane launch n"),
    ("default.fire.quorum.lane_prefill_us", "lane prefill us"),
    ("default.fire.quorum.lane_prefill_n", "lane prefill n"),
    ("default.fire.quorum.lane_control_us", "lane control us"),
    ("default.fire.quorum.lane_control_n", "lane control n"),
    ("default.fire.quorum.lane_control_max_us", "lane control max us"),
    ("default.fire.quorum.accept_calls", "accept calls"),
    ("default.process.completed", "processes completed"),
    ("default.process.avg_admission_wait_us", "process avg admission wait us"),
    ("default.process.avg_instantiate_us", "process avg instantiate us"),
    ("default.process.avg_wasm_run_us", "process avg wasm run us"),
    ("default.cumulative_batch_latency_us", "cumulative_batch_latency_us"),
    ("default.fire.post_dispatch.context_tick_us", "fire.post_dispatch.context_tick_us"),
    ("default.fire.post_dispatch.stats_update_us", "fire.post_dispatch.stats_update_us"),
    ("default.last_batch_latency_us", "last batch latency us"),
    ("default.bypass_hits", "bypass hits"),
    ("default.chain_submits", "chain submits"),
    ("default.chain_ext_avg_wake_us", "chain ext avg wake us"),
    ("default.chain_ext_avg_work_us", "chain ext avg work us"),
    ("default.chain_drops", "chain drops"),
    ("default.total_requests_processed", "total requests"),
    ("default.max_forward_requests_observed", "max forward requests"),
    ("default.batch_size_hist", "batch size hist"),
)
WAVE_KEY_FRAGMENTS = ("wave", "active_pipelines", "missing_at_fire", "straggler")


def reconstruct_token_arrivals(
    first_arrival_s: float, intertoken_us: list[int], output_tokens: int
) -> list[float]:
    arrivals = [first_arrival_s]
    for gap_us in intertoken_us:
        arrivals.append(arrivals[-1] + gap_us / 1_000_000.0)
    if len(arrivals) != output_tokens:
        raise ValueError(f"token timing count is {len(arrivals)}, expected {output_tokens}")
    return arrivals


def output_token_count(obj: dict) -> int:
    for key in ("num_output_tokens", "count"):
        if key in obj:
            return int(obj[key])
    return len(obj.get("token_ids") or [])


def _wasm_candidates(inferlet_dir: Path, rel: Path) -> list[Path]:
    candidates = [inferlet_dir / rel]
    for parent in inferlet_dir.parents:
        candidates.append(parent / rel)
        manifest = parent / "Cargo.toml"
        if manifest.exists() and "[workspace]" in manifest.read_text():
            break
    return candidates


def bench_inferlet_wasm(inferlet_dir: str | None) -> Path:
    if not inferlet_dir:
        raise FileNotFoundError(
            "text-completion-bench is not part of the curated inferlets; pass "
            "--inferlet-dir or set PIE_BENCH_INFERLET_DIR"
        )
    inferlet_dir = Path(inferlet_dir).expanduser().resolve()
    pkg = tomllib.loads((inferlet_dir / "Cargo.toml").read_text())["package"]
    rel = Path("target") / "wasm32-wasip3" / "release" / f"{pkg['name'].replace('-', '_')}.wasm"
    candidates = _wasm_candidates(inferlet_dir, rel)
    wasm = next((c for c in candidates if c.exists()), candidates[0])
    if not wasm.exists():
        raise FileNotFoundError(
            f"missing {wasm}; build with: cd {inferlet_dir} && cargo build --target wasm32-wasip3 --release"
        )
    newest_src = max(
        (p.stat().st_mtime_ns for p in (inferlet_dir / "src").rglob("*.rs")), default=0
    )
    if newest_src and wasm.stat().st_mtime_ns < newest_src:
        raise RuntimeError(
            f"{wasm} is older than {inferlet_dir}/src; rebuild with: "
            f"cd {inferlet_dir} && cargo build --target wasm32-wasip3 --release"
        )
    return wasm


def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return int(s.getsockname()[1])


def _is_engine_source(path: Path, root: Path, skip_roots: tuple[Path, ...]) -> bool:
    return (
        path.is_file()
        and path.suffix in ENGINE_SOURCE_SUFFIXES
        and "target" not in path.parts
        and "bench" not in path.relative_to(root).parts
        and not any(path.is_relative_to(s) for s in skip_roots)
    )


def _newest_engine_source() -> Path:
    source_roots = [ROOT / "crates", ROOT / "packages" / "python" / "server" / "src"]
    skip_roots = () if sys.platform == "darwin" else (ROOT / "crates" / "engine-metal",)
    return max(
        (
            path
            for root in source_roots
            for path in root.rglob("*")
            if _is_engine_source(path, root, skip_roots)
        ),
        key=lambda path: path.stat().st_mtime_ns,
    )


def _sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def embedded_engine_identity() -> dict[str, str]:
    from pie import _engine

    engine_path = Path(_engine.__file__).resolve()
    newest_source = _newest_engine_source()
    if engine_path.stat().st_mtime_ns < newest_source.stat().st_mtime_ns:
        raise RuntimeError(
            f"embedded engine {engine_path} is older than {newest_source}; "
            "rebuild with PIE_COMPILER_LAUNCHER=env CARGO_BUILD_JOBS=2 "
            "CMAKE_BUILD_PARALLEL_LEVEL=2 uv --project packages/python/server sync "
            "--reinstall-package pie-server"
        )
    return {"embedded engine": str(engine_path), "embedded engine sha256": _sha256_of(engine_path)}


def is_cumulative_status_key(key: str) -> bool:
    suffix = key.rsplit(".", 1)[-1]
    return suffix.endswith("_sum") or suffix in CUMULATIVE_STATUS_KEYS


def measured_average(
    status: dict[str, Any], numerator_key: str, denominator: int | float, output_key: str
) -> None:
    numerator = status.get(numerator_key)
    if isinstance(numerator, (int, float)) and denominator > 0:
        status[output_key] = numerator / denominator


def toml_scalar(text: str) -> Any:
    if text in ("true", "false"):
        return text == "true"
    for kind in (int, float):
        try:
            return kind(text)
        except ValueError:
            pass
    return text


def int_or_text(text: str) -> int | str:
    try:
        return int(text)
    except ValueError:
        return text


def key_value_pairs(raw: list[str] | None, parse, wanted: str) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for item in raw or []:
        key, sep, value = item.partition("=")
        if not sep:
            raise SystemExit(f"{wanted}, got {item!r}")
        out[key] = parse(value)
    return out


def engine_option_pairs(args: argparse.Namespace, parse) -> dict[str, Any]:
    return key_value_pairs(args.engine_option, parse, "--engine-option wants KEY=VALUE")


def device_list(args: argparse.Namespace) -> list[str]:
    device = args.device
    if device == PIE_BENCH_DEFAULT_DEVICE and args.tp_size > 1:
        device = ",".join(f"cuda:{i}" for i in range(args.tp_size))
    return [d.strip() for d in device.split(",")] if "," in device else [device]


def cuda_engine_options(args: argparse.Namespace) -> dict[str, Any]:
    options: dict[str, Any] = {}
    if args.max_forward_tokens != PIE_MAX_FORWARD_TOKENS_DEFAULT:
        options["max_forward_tokens"] = args.max_forward_tokens
    options.update(engine_option_pairs(args, toml_scalar))
    if args.max_forward_requests != PIE_MAX_FORWARD_REQUESTS_DEFAULT:
        options["max_forward_requests"] = args.max_forward_requests
    elif args.mode == "tput" and args.concurrency > 0:
        options["max_forward_requests"] = args.concurrency
    if args.swap_pool_size:
        options["swap_pool_size"] = args.swap_pool_size
    options["max_model_len"] = args.max_model_len
    return options


def metal_engine_options(args: argparse.Namespace) -> dict[str, Any]:
    options: dict[str, Any] = {}
    if args.max_forward_tokens:
        options["max_forward_tokens"] = args.max_forward_tokens
    if args.max_forward_requests:
        options["max_forward_requests"] = args.max_forward_requests
    chosen = engine_option_pairs(args, int_or_text)
    sized = {
        "max_model_len": args.max_model_len,
        "max_state_slots": max(1, args.max_forward_requests) * 2,
    }
    return {**options, **chosen, **sized} | chosen


ENGINE_OPTIONS = {"cuda": cuda_engine_options, "metal": metal_engine_options}


def max_concurrent_processes(args: argparse.Namespace) -> int | None:
    if cap := os.environ.get("PIE_BENCH_ADMISSION_CAP"):
        return int(cap)
    if args.mode == "latency":
        return 1
    return args.concurrency or None


def scheduler_kwargs(
    args: argparse.Namespace, runtime_config, max_processes: int | None
) -> dict[str, Any]:
    requested = {
        "default_token_limit": args.default_token_limit,
        "default_endowment_pages": args.default_endowment_pages,
        "admission_oversubscription_factor": args.admission_oversubscription_factor,
        "frame_size": args.frame_size,
        "frame_submit_depth": args.frame_submit_depth,
        "frame_dispatch_depth": args.frame_dispatch_depth,
        "submit_deadline": args.submit_deadline,
        "max_concurrent_processes": max_processes,
    }
    accepted = inspect.signature(runtime_config).parameters
    return {k: v for k, v in requested.items() if v is not None and k in accepted}


def _sandbox_kwargs(args: argparse.Namespace, max_processes: int | None) -> dict[str, Any]:
    kwargs: dict[str, Any] = {"max_instances": max(4096, (max_processes or 0) * 4)}
    if args.wasm_warm_slots:
        kwargs["warm_slots"] = args.wasm_warm_slots
    if args.wasm_warm_memory_mb is not None:
        kwargs["warm_memory_mb"] = args.wasm_warm_memory_mb
    return kwargs


def _model_kwargs(args: argparse.Namespace, resolved_model: str) -> dict[str, Any]:
    kwargs: dict[str, Any] = {"name": "default", "source": resolved_model}
    if args.device_weight_budget:
        kwargs["device_weight_budget"] = args.device_weight_budget
    if args.host_weight_budget:
        kwargs["host_weight_budget"] = args.host_weight_budget
    kwargs.update(
        device_kv_budget=args.device_kv_budget,
        weight_precision=args.precision,
        kv_dtype=args.kv,
        device_memory_share=args.gpu_mem_util,
    )
    return kwargs


def build_config(args: argparse.Namespace):
    from pie.config import (
        Config,
        EngineConfig,
        ModelConfig,
        RuntimeConfig,
        SandboxConfig,
        ServerConfig,
        TelemetryConfig,
    )

    device = device_list(args)
    engine_options = ENGINE_OPTIONS[args.engine](args)
    max_processes = max_concurrent_processes(args)
    resolved_model = resolve_local_model(args.model)
    threads = {"worker_threads": args.worker_threads} if args.worker_threads else {}
    cfg = Config(
        server=ServerConfig(listen="127.0.0.1:0", verbose=True, **threads),
        telemetry=TelemetryConfig(),
        runtime=RuntimeConfig(**scheduler_kwargs(args, RuntimeConfig, max_processes)),
        sandbox=SandboxConfig(**_sandbox_kwargs(args, max_processes)),
        model=ModelConfig(**_model_kwargs(args, resolved_model)),
        engine=EngineConfig(
            type=args.engine,
            device=device,
            tensor_parallel_size=args.tp_size,
            options=engine_options,
        ),
    )
    config_blob = {"engine": args.engine, "resolved model": resolved_model, **engine_options}
    if args.warmup_max_tokens is not None:
        config_blob["warmup max tokens"] = args.warmup_max_tokens
    config_blob["warmup seconds"] = args.warmup_seconds
    return cfg, config_blob


@asynccontextmanager
async def in_process_server_client(args: argparse.Namespace):
    from pie.server import Server

    cfg, engine_config = build_config(args)
    engine_identity = embedded_engine_identity()
    if url := os.environ.get("PIE_BENCH_SERVER_URL"):
        from pie_client import PieClient

        client = PieClient(url)
        await client.connect()
        try:
            yield client, {**engine_config, **engine_identity}
        finally:
            await client.close()
        return
    async with Server(cfg) as server:
        if os.environ.get("PIE_BENCH_SERVE_ONLY") == "1":
            print(f"PIE_BENCH_SERVER_URL={server.url}", flush=True)
            await asyncio.Event().wait()
        yield await server.connect(), {**engine_config, **engine_identity}


def surfaces(line: str) -> bool:
    return line.startswith(SURFACED_PREFIXES) or any(
        fragment in line for fragment in SURFACED_FRAGMENTS
    )


class PieServerOutput:
    def __init__(self) -> None:
        self.startup: list[str] = []
        self.file = None
        if log_path := os.environ.get("PIE_BENCH_SERVER_LOG"):
            path = Path(log_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            self.file = path.open("w", encoding="utf-8")
        self.spawned = time.perf_counter()

    def take(self, raw: bytes) -> str:
        text = raw.decode("utf-8", errors="replace")
        if self.file is not None:
            self.file.write(text)
            self.file.flush()
        if surfaces(text):
            sys.stderr.write(self.stamped(text))
            sys.stderr.flush()
        return text

    def stamped(self, text: str) -> str:
        if text.startswith("ane: ") or "panicked at" in text:
            return f"[{time.perf_counter() - self.spawned:7.1f}s] {text}"
        return text

    def startup_tail(self) -> str:
        return "".join(self.startup[-STARTUP_TAIL_LINES:])

    def close(self) -> None:
        if self.file is not None:
            self.file.close()


async def _await_pie_ready(proc, output: PieServerOutput, timeout_s: float) -> None:
    deadline = time.perf_counter() + timeout_s
    while time.perf_counter() < deadline:
        try:
            line = await asyncio.wait_for(
                proc.stdout.readline(), timeout=max(0.1, deadline - time.perf_counter())
            )
        except TimeoutError as exc:
            raise TimeoutError(
                "timed out waiting for pie serve startup:\n" + output.startup_tail()
            ) from exc
        if not line:
            raise RuntimeError(
                "pie serve exited before startup completed:\n" + output.startup_tail()
            )
        text = output.take(line)
        output.startup.append(text)
        if "Server ready at " in text:
            return
        if proc.returncode is not None:
            raise RuntimeError(
                f"pie serve exited with {proc.returncode}:\n" + output.startup_tail()
            )
    raise TimeoutError("timed out waiting for pie serve startup:\n" + output.startup_tail())


async def _forward_pie_output(proc, output: PieServerOutput) -> None:
    while line := await proc.stdout.readline():
        output.take(line)


async def _stop_pie(proc, forwarder: asyncio.Task | None, output: PieServerOutput) -> None:
    if proc.returncode is None:
        proc.terminate()
        try:
            await asyncio.wait_for(proc.wait(), timeout=10.0)
        except TimeoutError:
            proc.kill()
            await proc.wait()
    if forwarder is not None:
        forwarder.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await forwarder
    output.close()


def _write_pie_config(args: argparse.Namespace, cfg) -> Path:
    cfg.server.port = find_free_port()
    cfg.server.listen = f"127.0.0.1:{cfg.server.port}"
    cfg_path = ROOT / ".tmp" / "benches" / f"pie-{args.engine}-{cfg.server.port}.toml"
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    cfg_path.write_text(cfg.to_toml())
    return cfg_path


@asynccontextmanager
async def pie_binary_client(args: argparse.Namespace):
    from pie_client import PieClient

    cfg, engine_config = build_config(args)
    cfg_path = _write_pie_config(args, cfg)
    pie_bin = Path(args.pie_bin)
    if not pie_bin.exists():
        raise FileNotFoundError(
            f"missing {pie_bin}; build with: cargo build --release -p pie --no-default-features --features metal"
        )
    launched = time.perf_counter()
    proc = await asyncio.create_subprocess_exec(
        str(pie_bin),
        "--config",
        str(cfg_path),
        "serve",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    output = PieServerOutput()
    forwarder: asyncio.Task | None = None
    try:
        await _await_pie_ready(proc, output, args.server_startup_timeout)
        engine_config["server load s"] = round(time.perf_counter() - launched, 3)
        forwarder = asyncio.create_task(_forward_pie_output(proc, output))
        client = PieClient(f"ws://127.0.0.1:{cfg.server.port}")
        await client.connect()
        try:
            yield client, {**engine_config, "pie_bin": str(pie_bin)}
        finally:
            await client.close()
    finally:
        await _stop_pie(proc, forwarder, output)


def pie_client(args: argparse.Namespace):
    if args.engine == "metal":
        return pie_binary_client(args)
    return in_process_server_client(args)


def speculation_of(obj: dict) -> dict[str, Any] | None:
    if "rounds" not in obj:
        return None
    return {field: obj.get(field) for field in SPECULATION_FIELDS}


def _failed(start: float, error: str) -> RequestResult:
    return RequestResult(False, time.perf_counter() - start, 0, error=error)


def _error_text(e: Exception) -> str:
    return f"{type(e).__name__}: {e}"


class Session:
    def __init__(
        self, args, client, pkg, prompts: list[str], prompt_token_ids: list[list[int]] | None
    ):
        self.args = args
        self.client = client
        self.pkg = pkg
        self.prompts = prompts
        self.prompt_token_ids = prompt_token_ids
        self.single_batch = args.mode == "tput" and args.single_process_batch
        self.first_output_text: str | None = None
        self.output_token_ids: dict[str, list[int]] = {}
        self.epoch_ns: int | None = None
        self.heard = time.perf_counter()

    def client_seconds(self, ns: int) -> float | None:
        if self.args.report_timing or self.args.report_arrivals:
            return seconds_after(self.epoch_ns, ns)
        return None

    def request_input(self, max_tokens: int | None = None) -> dict[str, Any]:
        args = self.args
        return {
            "system": args.system,
            "max_tokens": args.max_tokens if max_tokens is None else max_tokens,
            "temperature": args.temperature,
            "top_p": args.top_p,
            "ignore_eos": args.ignore_eos,
            "no_think": args.think is False,
            "wasm_delay_us": args.wasm_delay_us,
            **({"host_first_token": True} if args.host_first_token else {}),
            **({"run_ahead_frames": args.run_ahead_frames} if args.run_ahead_frames else {}),
            "return_text": args.dump_first_text or args.dump_all_texts,
            "report_timing": args.report_timing,
            "report_arrivals": args.report_arrivals,
            "wait_for_start": args.defer_start,
            **(
                {"batch_concurrency": args.concurrency}
                if args.concurrency and args.concurrency > 0
                else {}
            ),
            **(args.extra_input or {}),
            **(
                {"system_speculation": args.system_speculation}
                if args.system_speculation is not None
                else {}
            ),
        }

    async def recv(self, proc):
        timeout = self.args.request_timeout
        while True:
            idle = time.perf_counter() - self.heard
            try:
                event = await asyncio.wait_for(proc.recv(), timeout=max(0.0, timeout - idle))
            except TimeoutError:
                if time.perf_counter() - self.heard >= timeout:
                    raise
                continue
            self.heard = time.perf_counter()
            return event

    async def launch(self, i: int, *, max_tokens: int | None = None):
        if max_tokens is None:
            max_tokens = request_max_tokens(self.args, i)
        inp = {**self.request_input(max_tokens), "prompt": self.prompts[i]}
        if self.prompt_token_ids is not None:
            inp["prompt_tokens"] = self.prompt_token_ids[i]
        start = time.perf_counter()
        client_send_s = self.client_seconds(monotonic_ns())
        try:
            proc = await self.client.launch_process(self.pkg, input=inp)
            self.heard = time.perf_counter()
            return i, start, proc, client_send_s
        except Exception as e:
            return _failed(start, _error_text(e))

    async def wait(self, launched) -> RequestResult:
        from pie_client import Event

        if isinstance(launched, RequestResult):
            return launched
        i, start, proc, client_send_s = launched
        ttft_s: float | None = None
        first_arrival_s: float | None = None
        try:
            while True:
                ev, msg = await self.recv(proc)
                if ev == Event.Message and str(msg) == "t0":
                    now = time.perf_counter()
                    now_ns = monotonic_ns()
                    ttft_s = now - start
                    first_arrival_s = self.client_seconds(now_ns)
                    continue
                if ev == Event.Return:
                    return self._returned(
                        i, start, proc, client_send_s, ttft_s, first_arrival_s, msg
                    )
                if ev == Event.Error:
                    return _failed(start, str(msg))
        except Exception as e:
            return _failed(start, _error_text(e))

    def _returned(
        self, i, start, proc, client_send_s, ttft_s, first_arrival_s, msg
    ) -> RequestResult:
        returned = time.perf_counter()
        returned_ns = monotonic_ns()
        obj = json.loads(msg)
        if i == self.args.warmup and self.first_output_text is None:
            self.first_output_text = obj.get("text", "")
        output_tokens = output_token_count(obj)
        token_ids = [int(token) for token in obj.get("token_ids") or []]
        if "token_ids" in obj and len(token_ids) != output_tokens:
            raise ValueError(f"output token count {len(token_ids)}, expected {output_tokens}")
        self.output_token_ids[str(proc.process_id)] = token_ids
        gaps = obj.get("intertoken_us") or []
        arrival_ns = self._arrival_ns(obj)
        return RequestResult(
            True,
            returned - start,
            output_tokens,
            int(obj.get("num_prompt_tokens") or 0),
            ttft_s=ttft_s,
            intertoken_us=gaps or None,
            client_send_s=client_send_s,
            token_arrival_s=self._arrivals(first_arrival_s, gaps, output_tokens, arrival_ns),
            token_arrival_monotonic_ns=arrival_ns or None,
            client_return_s=seconds_after(self.epoch_ns, returned_ns),
            process_id=str(proc.process_id),
            prologue_us=obj.get("prologue_us") or None,
            speculation=speculation_of(obj),
            output_text=obj.get("text", "") if self.args.dump_all_texts else None,
        )

    def _arrival_ns(self, obj: dict) -> list[int]:
        arrival_ns = [int(value) for value in (obj.get("token_monotonic_ns") or [])]
        epoch = self.epoch_ns
        if epoch is not None and arrival_ns and arrival_ns[-1] < epoch:
            return [epoch + value for value in arrival_ns]
        return arrival_ns

    def _arrivals(
        self, first_arrival_s, gaps, output_tokens: int, arrival_ns: list[int]
    ) -> list[float] | None:
        epoch = self.epoch_ns
        if epoch is None:
            return None
        if first_arrival_s is not None and (gaps or output_tokens == 1):
            return reconstruct_token_arrivals(first_arrival_s, gaps, output_tokens)
        if not self.args.report_arrivals:
            return None
        if len(arrival_ns) != output_tokens:
            raise ValueError(
                f"shared-clock token timing count is {len(arrival_ns)}, expected {output_tokens}"
            )
        return [(int(value) - epoch) / 1_000_000_000.0 for value in arrival_ns]

    async def _until_ready(self, proc) -> str | None:
        from pie_client import Event

        while True:
            ev, msg = await self.recv(proc)
            if ev == Event.Message and str(msg) == "ready":
                return None
            if ev == Event.Return:
                return "returned before start"
            if ev == Event.Error:
                return str(msg)

    def _batch_input(self, indices: list[int], max_tokens: int | None) -> dict[str, Any]:
        inp = {
            **self.request_input(max_tokens),
            "wait_for_start": True,
            "prompt": self.prompts[indices[0]] if indices else self.args.prompt,
            "prompts": [self.prompts[i] for i in indices],
        }
        if self.args.concurrency and self.args.concurrency > 0:
            inp["batch_concurrency"] = self.args.concurrency
        if self.prompt_token_ids is not None:
            inp["prompt_tokens_batch"] = [self.prompt_token_ids[i] for i in indices]
        return inp

    def _batch_results(self, indices: list[int], obj: dict, elapsed: float) -> list[RequestResult]:
        if self.first_output_text is None:
            self.first_output_text = obj.get("text", "")
        req_out = obj.get("request_output_tokens") or []
        req_prompt = obj.get("request_prompt_tokens") or []
        if len(req_out) == len(indices) and len(req_prompt) == len(indices):
            return [
                RequestResult(True, elapsed, int(out), int(prompt))
                for out, prompt in zip(req_out, req_prompt)
            ]
        per_out = output_token_count(obj) // max(1, len(indices))
        per_prompt = int(obj.get("num_prompt_tokens") or 0) // max(1, len(indices))
        return [RequestResult(True, elapsed, per_out, per_prompt) for _ in indices]

    async def batch(self, indices, *, max_tokens: int | None = None) -> list[RequestResult]:
        from pie_client import Event

        indices = list(indices)
        inp = self._batch_input(indices, max_tokens)
        start = time.perf_counter()
        try:
            proc = await self.client.launch_process(self.pkg, input=inp)
            self.heard = time.perf_counter()
            not_ready = await self._until_ready(proc)
            if not_ready is not None:
                return [RequestResult(False, 0.0, 0, error=not_ready) for _ in indices]
            start = time.perf_counter()
            await proc.signal("start")
            while True:
                ev, msg = await self.recv(proc)
                if ev == Event.Return:
                    return self._batch_results(
                        indices, json.loads(msg), time.perf_counter() - start
                    )
                if ev == Event.Error:
                    return [_failed(start, str(msg)) for _ in indices]
        except Exception as e:
            return [_failed(start, _error_text(e)) for _ in indices]

    async def one(self, i: int, *, max_tokens: int | None = None) -> RequestResult:
        return await self.wait(await self.launch(i, max_tokens=max_tokens))

    async def _seated(self, indices, max_tokens: int | None) -> list[RequestResult]:
        seats = asyncio.Semaphore(self.args.concurrency)

        async def seated(i: int) -> RequestResult:
            queued = time.perf_counter()
            async with seats:
                waited = time.perf_counter() - queued
                result = await self.one(i, max_tokens=max_tokens)
            result.latency_s += waited
            if result.ttft_s is not None:
                result.ttft_s += waited
            return result

        return await asyncio.gather(*(seated(i) for i in indices))

    async def _ready_or_failed(self, launched):
        if isinstance(launched, RequestResult):
            return launched
        i, _start, proc, _client_send_s = launched
        try:
            not_ready = await self._until_ready(proc)
        except Exception as e:
            return RequestResult(False, 0.0, 0, error=_error_text(e))
        return (i, proc) if not_ready is None else RequestResult(False, 0.0, 0, error=not_ready)

    async def _start_together(self, launched: list) -> list[RequestResult]:
        waited = await asyncio.gather(*(self._ready_or_failed(item) for item in launched))
        ready = [w for w in waited if not isinstance(w, RequestResult)]
        failed = [w for w in waited if isinstance(w, RequestResult)]
        start = time.perf_counter()
        await asyncio.gather(*(proc.signal("start") for _i, proc in ready))
        started = [
            (i, start, proc, seconds_after(self.epoch_ns, monotonic_ns())) for i, proc in ready
        ]
        return failed + await asyncio.gather(*(self.wait(item) for item in started))

    async def many(self, indices, *, max_tokens: int | None = None) -> list[RequestResult]:
        if self.single_batch:
            return await self.batch(indices, max_tokens=max_tokens)
        if self.args.concurrency > 0 and not self.args.defer_start:
            return await self._seated(indices, max_tokens)
        launched = await asyncio.gather(*(self.launch(i, max_tokens=max_tokens) for i in indices))
        if self.args.defer_start and self.args.mode == "tput":
            return await self._start_together(launched)
        return await asyncio.gather(*(self.wait(item) for item in launched))

    async def many_paced(self, indices, pacer: ArrivalPacer) -> list[RequestResult]:
        pacer.start()

        async def offer(k: int, i: int) -> RequestResult:
            await pacer.wait(k)
            return await self.one(i)

        return await asyncio.gather(*(offer(k, i) for k, i in enumerate(indices)))

    async def warm_up_once(self) -> None:
        max_tokens = self.args.warmup_max_tokens or self.args.max_tokens
        if self.args.mode == "tput":
            await self.many(range(self.args.warmup), max_tokens=max_tokens)
            return
        for i in range(self.args.warmup):
            await self.one(i, max_tokens=max_tokens)

    async def warm_up(self) -> None:
        await self.warm_up_once()
        await run_timed_warmup(self.warm_up_once, self.args.warmup_seconds, label="pie")

    async def measured(self, n: int, pacer: ArrivalPacer) -> tuple[list[RequestResult], float]:
        indices = range(self.args.warmup, self.args.warmup + n)
        if self.args.mode == "latency":
            results, cooled = [], 0.0
            for i in indices:
                cooled += await asyncio.to_thread(cool_before_request)
                results.append(await self.one(i))
            return results, cooled
        if pacer.enabled:
            return await self.many_paced(indices, pacer), 0.0
        return await self.many(indices), 0.0

    def attach_output_tokens(self, results: list[RequestResult]) -> None:
        for result in results:
            if result.process_id is None:
                continue
            token_ids = self.output_token_ids[result.process_id]
            result.output_token_sha256 = hash_output_tokens(token_ids)
            if self.args.dump_all_token_ids:
                result.output_token_ids = token_ids


async def model_status(client) -> dict[str, Any]:
    try:
        ok, body = await client.query("model_status", "")
        if ok:
            return json.loads(body)
    except Exception:
        pass
    return {}


def status_since(now: dict[str, Any], before: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in now.items():
        pre = before.get(key)
        cumulative = is_cumulative_status_key(key)
        if cumulative and isinstance(value, (int, float)) and isinstance(pre, (int, float)):
            out[key] = value - pre
        elif (
            cumulative
            and isinstance(value, list)
            and isinstance(pre, list)
            and len(value) == len(pre)
        ):
            out[key] = [a - b for a, b in zip(value, pre)]
        else:
            out[key] = value
    return out


def add_status_averages(status: dict[str, Any], before: dict[str, Any]) -> None:
    batches = status.get("default.total_batches", 0)
    if isinstance(batches, (int, float)):
        for sum_key, average_key in PER_BATCH_AVERAGES:
            measured_average(status, sum_key, batches, average_key)
        pre_batches = before.get("default.total_batches", 0)
        gaps = (
            batches
            if isinstance(pre_batches, (int, float)) and pre_batches > 0
            else max(batches - 1, 0)
        )
        for sum_key, average_key in PER_GAP_AVERAGES:
            measured_average(status, sum_key, gaps, average_key)
    wave_fires = status.get("default.fire.quorum.wave_fires", 0)
    if isinstance(wave_fires, (int, float)):
        for sum_key, average_key in PER_WAVE_AVERAGES:
            measured_average(status, sum_key, wave_fires, average_key)


async def record_model_status(
    client, before: dict[str, Any], engine_config: dict[str, Any]
) -> None:
    try:
        ok, body = await client.query("model_status", "")
        if not ok:
            return
        status = status_since(json.loads(body), before)
        add_status_averages(status, before)
        for key, label in STATUS_LABELS:
            if key in status:
                engine_config[label] = status[key]
        for key, value in status.items():
            if any(fragment in key for fragment in WAVE_KEY_FRAGMENTS):
                engine_config[key] = value
    except Exception:
        pass


def report_failures(results: list[RequestResult]) -> None:
    seen = Counter((r.error or "?")[:200] for r in results if not r.ok)
    for why, count in list(seen.items())[:4]:
        print(f"[pie-bench] {count} failed: {why}", file=sys.stderr, flush=True)


def stamps_clock(args: argparse.Namespace) -> bool:
    return args.report_timing or args.report_arrivals or args.report_wall_clock


async def run(args: argparse.Namespace):
    cpu_affinity = maybe_set_cpu_affinity(args, visible_cuda_devices(args.tp_size, args.dp_size))
    n = args.requests if args.mode == "latency" else args.num_requests
    prompts = make_prompts(args, n + args.warmup)
    prompt_token_ids: list[list[int]] | None = None
    if args.pretokenized_prompts:
        prompt_token_ids, _ = hf_chat_token_ids_and_counts(
            args.model, args.system, prompts, args.think
        )
    wasm = bench_inferlet_wasm(args.inferlet_dir)

    async with pie_client(args) as (client, engine_config):
        session = Session(
            args, client, await client.install_program(wasm), prompts, prompt_token_ids
        )
        pacer = ArrivalPacer(
            arrival_schedule(n, args.arrival_rate, args.arrival_process, args.arrival_seed)
        )
        if args.warmup:
            await session.warm_up()
        before = await model_status(client)
        clocks_at_start = gpu_clock_state()
        await asyncio.to_thread(xla_trace, "start")
        print("[pie-bench] measured-start", flush=True)
        profiler_window = start_measured_profiler(args)
        epoch_unix_s: float | None = None
        if stamps_clock(args):
            epoch_unix_s = time.time()
            session.epoch_ns = monotonic_ns()
        start = time.perf_counter()
        try:
            results, cooled = await session.measured(n, pacer)
        finally:
            elapsed = time.perf_counter() - start
            await stop_measured_profiler(args, profiler_window)
            clocks_at_end = gpu_clock_state()
            await asyncio.to_thread(xla_trace, "stop")
            print("[pie-bench] measured-end", flush=True)
        wall = elapsed - cooled
        session.attach_output_tokens(results)
        report_failures(results)
        if args.mode == "tput" and (args.defer_start or session.single_batch):
            measured = [r.latency_s for r in results if r.ok]
            if measured:
                wall = max(measured)
        await record_model_status(client, before, engine_config)

    print_first_output(args, session.first_output_text)
    clock = {}
    if stamps_clock(args):
        clock = {
            "client timing epoch unix s": epoch_unix_s,
            "client timing epoch monotonic ns": session.epoch_ns,
        }
    summary = summarize(
        mode=args.mode,
        engine="pie",
        model=args.model,
        results=results,
        wall_s=wall,
        config={
            "system": args.system,
            "prompt": args.prompt,
            "max_tokens": args.max_tokens,
            "temperature": args.temperature,
            "top_p": args.top_p,
            "ignore_eos": args.ignore_eos,
            "unique_prompts": args.unique_prompts,
            "cuda profiler capture": args.cuda_profiler_capture,
            "arrival_rate": args.arrival_rate,
            "arrival_process": args.arrival_process,
            "cooled_s": round(cooled, 1),
            **pacer.stats(),
            **clock,
            "cpu affinity": cpu_affinity,
            "gpu clocks at start": clocks_at_start,
            "gpu clocks at end": clocks_at_end,
            **engine_config,
        },
    )
    return summary, results


def _add_engine_args(sp: argparse.ArgumentParser) -> None:
    sp.add_argument(
        "--inferlet-dir",
        default=os.environ.get("PIE_BENCH_INFERLET_DIR"),
        help="Path to a built text-completion-bench inferlet project (or set PIE_BENCH_INFERLET_DIR).",
    )
    sp.add_argument("--device", default=PIE_BENCH_DEFAULT_DEVICE)
    sp.add_argument("--engine", default="cuda", choices=["cuda", "metal"])


def _add_admission_args(sp: argparse.ArgumentParser) -> None:
    sp.add_argument("--default-token-limit", type=int, default=200_000)
    sp.add_argument("--default-endowment-pages", type=int, default=64)
    sp.add_argument("--admission-oversubscription-factor", type=float, default=4.0)


def _add_memory_args(sp: argparse.ArgumentParser) -> None:
    sp.add_argument("--precision", default=None, help="[model] weight_precision, e.g. bf16+nvfp4a4")
    sp.add_argument("--kv", default=None, help="[model] kv, e.g. e4m3 (DeepSeek-V4's fp8 rows)")
    sp.add_argument(
        "--device-kv-budget",
        default=None,
        help="[model] device_kv_budget: device bytes for the kv pages and "
        'state slots, with a unit ("8GiB"). Omit to fill what '
        "--gpu-mem-util ([model] device_memory_share) leaves.",
    )
    sp.add_argument(
        "--swap-pool-size",
        type=int,
        default=0,
        help="Host-side swap pages (cuda engine option). Must be "
        ">0 to arm the suspend/restore rung; 0 leaves the residency "
        "planner with pool-only reclaim.",
    )


def _add_frame_args(sp: argparse.ArgumentParser) -> None:
    sp.add_argument(
        "--frame-size",
        type=int,
        default=None,
        help="Waves per frame (pie scheduler `frame_size`). Omit for the engine default (2).",
    )
    sp.add_argument(
        "--frame-submit-depth",
        type=int,
        default=None,
        help="Frames a guest keeps queued in the engine. Omit for the "
        "engine default (3). This is the guest running ahead of the "
        "engine; too few collapses the pipeline to lockstep.",
    )
    sp.add_argument(
        "--frame-dispatch-depth",
        type=int,
        default=None,
        help="Frames the engine keeps posted to the engine. Omit for the "
        "engine default (2). The worker's config notes this is a "
        "two-sided trade-off that a fully batched fleet can lose.",
    )
    sp.add_argument(
        "--submit-deadline",
        default=None,
        help="How long a wave waits on a straggler lane before sealing "
        "without it, with unit (e.g. '50ms'). Omit for the engine "
        "default.",
    )


def _add_forward_args(sp: argparse.ArgumentParser) -> None:
    sp.add_argument("--max-forward-tokens", type=int, default=PIE_MAX_FORWARD_TOKENS_DEFAULT)
    sp.add_argument("--max-forward-requests", type=int, default=PIE_MAX_FORWARD_REQUESTS_DEFAULT)
    sp.add_argument("--worker-threads", type=int, default=None)
    sp.add_argument(
        "--extra-input",
        action="append",
        default=None,
        metavar="KEY=VALUE",
        help="Extra inferlet input field (typed like --engine-option); repeatable.",
    )
    sp.add_argument(
        "--device-weight-budget",
        default=None,
        help="[model] device_weight_budget, e.g. 20GiB (metal residency)",
    )
    sp.add_argument(
        "--host-weight-budget", default=None, help="[model] host_weight_budget, e.g. 8GiB"
    )


def _add_guest_args(sp: argparse.ArgumentParser) -> None:
    sp.add_argument(
        "--wasm-warm-slots",
        type=int,
        default=None,
        help="Prepared-but-idle guest slots kept for fast respawn. Default: the engine's (100).",
    )
    sp.add_argument(
        "--wasm-warm-memory-mb",
        type=int,
        default=None,
        help="MiB of a guest's linear memory kept resident across its exit "
        "instead of decommitted. Default: the engine's (0).",
    )
    sp.add_argument(
        "--host-first-token",
        action="store_true",
        help="Hand the prefill's first token to the decode pass "
        "through the HOST (out on g0, back as the decode's seed) "
        "instead of across the device-only channel the two "
        "passes share. Costs one host hop per request and none "
        "per token. Default: the device handoff, which both "
        "engines now serve.",
    )


def _add_output_args(sp: argparse.ArgumentParser) -> None:
    sp.add_argument(
        "--dump-first-text",
        action="store_true",
        help="Print the first request's full output text + its sha256 prefix. "
        "Use to A/B-compare spec vs no-spec runs at temperature=0.",
    )
    sp.add_argument(
        "--dump-all-token-ids",
        action="store_true",
        help="Include every measured request's emitted token IDs in JSON output.",
    )
    sp.add_argument(
        "--dump-all-texts",
        action="store_true",
        help="Include every measured request's decoded output in JSON output.",
    )
    sp.add_argument(
        "--report-timing",
        action="store_true",
        help="Collect per-request TTFT (launch-inclusive, client-stamped on "
        "the inferlet's t0 message) and inter-token gap distributions; "
        "adds ttft/intertoken summaries to the output.",
    )
    sp.add_argument(
        "--report-arrivals",
        action="store_true",
        help="Collect per-token guest-drain timestamps from the shared "
        "host monotonic clock without sending a live first-token client "
        "message. Intended for non-perturbing occupancy reconstruction.",
    )
    sp.add_argument(
        "--report-wall-clock",
        action="store_true",
        help="Record only the measured wall's shared monotonic epoch; "
        "adds no per-request or per-token client timing.",
    )


def _add_launch_args(sp: argparse.ArgumentParser) -> None:
    sp.add_argument(
        "--pretokenized-prompts",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Pre-render chat prompts to token IDs before timing and send raw tokens "
        "to the benchmark inferlet.",
    )
    sp.add_argument(
        "--single-process-batch",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="For throughput mode, launch one benchmark inferlet that drives all "
        "requests concurrently inside one WASM process.",
    )
    sp.add_argument(
        "--defer-start",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="For throughput mode, prelaunch inferlets and start timed generation "
        "after each process reports ready.",
    )
    sp.add_argument(
        "--system-speculation",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Override system speculation. Omit to use the model default; "
        "--no-system-speculation forces the no-spec baseline.",
    )


def _add_binary_args(sp: argparse.ArgumentParser) -> None:
    sp.add_argument("--pie-bin", default=str(ROOT / "target" / "release" / "pie"))
    sp.add_argument("--server-startup-timeout", type=float, default=300.0)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Pie canonical latency/throughput benchmark")
    for sp in add_mode_subcommands(p):
        _add_engine_args(sp)
        _add_admission_args(sp)
        _add_memory_args(sp)
        _add_frame_args(sp)
        _add_forward_args(sp)
        _add_guest_args(sp)
        _add_output_args(sp)
        _add_launch_args(sp)
        _add_binary_args(sp)
    return p


def refuse_if_a_wedged_pie_is_still_dying() -> None:
    if sys.platform != "darwin" or os.environ.get("PIE_BENCH_ALLOW_WEDGED") == "1":
        return
    try:
        out = subprocess.run(
            ["ps", "-eo", "pid,stat,comm"], capture_output=True, text=True, timeout=10
        ).stdout
    except Exception:
        return
    wedged = [
        line.split()[0]
        for line in out.splitlines()[1:]
        if "(pie)" in line and "E" in line.split()[1]
    ]
    if wedged:
        raise SystemExit(
            f"pie_bench: refusing to start — {len(wedged)} wedged pie "
            f"process(es) still hold GPU memory: {', '.join(wedged)}.\n"
            "They are blocked in the kernel awaiting GPU work and cannot be "
            "killed; their memory is unreclaimable. Retrying will only add "
            "another. Reboot the machine."
        )


def main() -> None:
    args = build_parser().parse_args()
    args.extra_input = key_value_pairs(args.extra_input, toml_scalar, "want KEY=VALUE")
    refuse_if_a_wedged_pie_is_still_dying()
    if args.dp_size > 1:
        summary, results = run_replicas(args, "pie", os.path.abspath(__file__), REPLICA_FLAGS)
    else:
        summary, results = asyncio.run(run(args))
    finish(summary, results, args.json_out)


if __name__ == "__main__":
    main()
