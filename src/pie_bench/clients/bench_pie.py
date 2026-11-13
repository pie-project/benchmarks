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
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from common import (
    ROOT,
    ArrivalPacer,
    RequestResult,
    add_mode_subcommands,
    arrival_schedule,
    cool_before_request,
    cuda_profiler_start,
    cuda_profiler_stop,
    finish,
    gpu_clock_state,
    hash_output_tokens,
    hf_chat_token_ids_and_counts,
    make_prompts,
    maybe_set_cpu_affinity,
    request_max_tokens,
    resolve_local_model,
    run_timed_warmup,
    summarize,
    visible_cuda_devices,
)

SERVER_PY = ROOT / "packages" / "python" / "server" / "python"
if str(SERVER_PY) not in sys.path:
    sys.path.insert(0, str(SERVER_PY))



def monotonic_ns() -> int:
    """CLOCK_MONOTONIC, the clock a profiler stamps in, where the OS has it; Windows's monotonic clock elsewhere."""
    return time.clock_gettime_ns(time.CLOCK_MONOTONIC) if hasattr(time, "clock_gettime_ns") else time.monotonic_ns()

EMBEDDED_CLI_ENGINES: set[str] = {
    "dummy",
    "metal",
    "vulkan",
    "vllm",
    "sglang",
    "tensorrt_llm",
}


def reconstruct_token_arrivals(
    first_arrival_s: float,
    intertoken_us: list[int],
    output_tokens: int,
) -> list[float]:
    arrivals = [first_arrival_s]
    for gap_us in intertoken_us:
        arrivals.append(arrivals[-1] + gap_us / 1_000_000.0)
    if len(arrivals) != output_tokens:
        raise ValueError(
            f"token timing count is {len(arrivals)}, expected {output_tokens}"
        )
    return arrivals


PIE_BENCH_DEFAULT_DEVICE = "cuda:0"

PIE_MAX_FORWARD_TOKENS_DEFAULT = 10240
PIE_MAX_FORWARD_REQUESTS_DEFAULT = 512


def _output_token_count(obj: dict) -> int:
    for key in ("num_output_tokens", "count"):
        if key in obj:
            return int(obj[key])
    return len(obj.get("token_ids") or [])


def bench_inferlet_wasm(inferlet_dir: str | None) -> Path:
    if not inferlet_dir:
        raise FileNotFoundError(
            "text-completion-bench is not part of the curated inferlets; pass "
            "--inferlet-dir or set PIE_BENCH_INFERLET_DIR"
        )
    inferlet_dir = Path(inferlet_dir).expanduser().resolve()
    pkg = tomllib.loads((inferlet_dir / "Cargo.toml").read_text())["package"]
    rel = Path("target") / "wasm32-wasip3" / "release" / f"{pkg['name'].replace('-', '_')}.wasm"
    candidates = [inferlet_dir / rel]
    for parent in inferlet_dir.parents:
        candidates.append(parent / rel)
        if (parent / "Cargo.toml").exists() and "[workspace]" in (
            parent / "Cargo.toml"
        ).read_text():
            break
    wasm = next((c for c in candidates if c.exists()), candidates[0])
    if not wasm.exists():
        raise FileNotFoundError(
            f"missing {wasm}; build with: cd {inferlet_dir} && "
            "cargo build --target wasm32-wasip3 --release"
        )
    newest_src = max(
        (p.stat().st_mtime_ns for p in (inferlet_dir / "src").rglob("*.rs")),
        default=0,
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


def embedded_engine_identity() -> dict[str, str]:
    from pie import _engine

    engine_path = Path(_engine.__file__).resolve()
    source_suffixes = {".c", ".cc", ".cpp", ".cu", ".cuh", ".h", ".hpp", ".rs"}
    source_roots = [
        ROOT / "crates",
        ROOT / "packages" / "python" / "server" / "src",
    ]
    skip_roots = () if sys.platform == "darwin" else (ROOT / "crates" / "engine-metal",)
    newest_source = max(
        (
            path
            for root in source_roots
            for path in root.rglob("*")
            if path.is_file()
            and path.suffix in source_suffixes
            and "target" not in path.parts
            and "bench" not in path.relative_to(root).parts
            and not any(path.is_relative_to(s) for s in skip_roots)
        ),
        key=lambda path: path.stat().st_mtime_ns,
    )
    if engine_path.stat().st_mtime_ns < newest_source.stat().st_mtime_ns:
        raise RuntimeError(
            f"embedded engine {engine_path} is older than {newest_source}; "
            "rebuild with PIE_COMPILER_LAUNCHER=env CARGO_BUILD_JOBS=2 "
            "CMAKE_BUILD_PARALLEL_LEVEL=2 uv --project packages/python/server sync "
            "--reinstall-package pie-server"
        )
    digest = hashlib.sha256()
    with engine_path.open("rb") as engine:
        for chunk in iter(lambda: engine.read(1024 * 1024), b""):
            digest.update(chunk)
    return {
        "embedded engine": str(engine_path),
        "embedded engine sha256": digest.hexdigest(),
    }


def is_cumulative_status_key(key: str) -> bool:
    suffix = key.rsplit(".", 1)[-1]
    return (
        suffix.endswith("_sum")
        or suffix
        in {
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
    )


def measured_average(
    status: dict[str, Any],
    numerator_key: str,
    denominator: int | float,
    output_key: str,
) -> None:
    numerator = status.get(numerator_key)
    if isinstance(numerator, (int, float)) and denominator > 0:
        status[output_key] = numerator / denominator


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

    if args.engine == "xla" and args.device == PIE_BENCH_DEFAULT_DEVICE:
        args.device = (
            ",".join(f"tpu:{i}" for i in range(args.tp_size))
            if args.tp_size > 1
            else "tpu:0"
        )
    elif args.device == PIE_BENCH_DEFAULT_DEVICE and args.tp_size > 1:
        args.device = ",".join(f"cuda:{i}" for i in range(args.tp_size))
    device = [d.strip() for d in args.device.split(",")] if "," in args.device else [args.device]
    engine_options: dict[str, Any]
    if args.engine in ("cuda", "xla"):
        engine_options = {}
        if args.max_forward_tokens != PIE_MAX_FORWARD_TOKENS_DEFAULT:
            engine_options["max_forward_tokens"] = args.max_forward_tokens
        for raw in getattr(args, "engine_option", []) or []:
            key, sep, value = raw.partition("=")
            if not sep:
                raise SystemExit(f"--engine-option wants KEY=VALUE, got {raw!r}")
            if value in ("true", "false"):
                parsed: Any = value == "true"
            else:
                try:
                    parsed = int(value)
                except ValueError:
                    try:
                        parsed = float(value)
                    except ValueError:
                        parsed = value
            engine_options[key] = parsed
        if args.max_forward_requests != PIE_MAX_FORWARD_REQUESTS_DEFAULT:
            engine_options["max_forward_requests"] = args.max_forward_requests
        elif args.mode == "tput" and args.concurrency > 0:
            engine_options["max_forward_requests"] = args.concurrency
        if args.engine == "cuda" and getattr(args, "swap_pool_size", 0):
            engine_options["swap_pool_size"] = args.swap_pool_size
        engine_options["max_model_len"] = args.max_model_len
    elif args.engine == "metal":
        engine_options = {}
        if getattr(args, "max_forward_tokens", 0):
            engine_options["max_forward_tokens"] = args.max_forward_tokens
        if getattr(args, "max_forward_requests", 0):
            engine_options["max_forward_requests"] = args.max_forward_requests
        for raw in getattr(args, "engine_option", []) or []:
            key, sep, value = raw.partition("=")
            if not sep:
                raise SystemExit(f"--engine-option wants KEY=VALUE, got {raw!r}")
            if value in ("true", "false"):
                parsed: Any = value == "true"
            else:
                try:
                    parsed = int(value)
                except ValueError:
                    try:
                        parsed = float(value)
                    except ValueError:
                        parsed = value
            engine_options[key] = parsed
        engine_options["max_model_len"] = args.max_model_len
        engine_options["max_state_slots"] = max(1, args.max_forward_requests) * 2
        for raw in getattr(args, "engine_option", []) or []:
            key, sep, value = raw.partition("=")
            if not sep:
                raise SystemExit(f"--engine-option wants KEY=VALUE, got {raw!r}")
            try:
                engine_options[key] = int(value)
            except ValueError:
                engine_options[key] = value
    elif args.engine == "vllm":
        engine_options = {
            "gpu_memory_utilization": args.gpu_mem_util,
        }
        if args.vllm_max_num_seqs is not None:
            engine_options["max_num_seqs"] = args.vllm_max_num_seqs
        if args.vllm_max_num_batched_tokens is not None:
            engine_options["max_num_batched_tokens"] = args.vllm_max_num_batched_tokens
        if args.vllm_max_model_len is not None:
            engine_options["max_model_len"] = args.vllm_max_model_len
        if getattr(args, "vllm_spec_ngram", False):
            engine_options["spec_ngram_enabled"] = True
            engine_options["spec_ngram_num_drafts"] = args.vllm_spec_ngram_num_drafts
            engine_options["spec_ngram_min_n"] = args.vllm_spec_ngram_min_n
            engine_options["spec_ngram_max_n"] = args.vllm_spec_ngram_max_n
        if getattr(args, "venv", None):
            engine_options["venv"] = args.venv
        if args.vllm_attention_backend:
            engine_options["attention_backend"] = args.vllm_attention_backend
    elif args.engine == "sglang":
        engine_options = {
            "mem_fraction_static": args.gpu_mem_util,
            "disable_cuda_graph": args.sglang_disable_cuda_graph,
            "disable_radix_cache": True,
            "cpu_mem_budget_in_gb": args.cpu_mem_budget,
        }
        if getattr(args, "venv", None):
            engine_options["venv"] = args.venv
        if args.sglang_attention_backend:
            engine_options["attention_backend"] = args.sglang_attention_backend
    elif args.engine == "tensorrt_llm":
        engine_options = {}
        if getattr(args, "venv", None):
            engine_options["venv"] = args.venv
        if args.trtllm_backend:
            engine_options["backend"] = args.trtllm_backend
        if args.trtllm_attn_backend:
            engine_options["attn_backend"] = args.trtllm_attn_backend
        if args.trtllm_lookahead_tokens is not None:
            engine_options["lookahead_tokens"] = args.trtllm_lookahead_tokens
        if args.trtllm_execution_mode:
            engine_options["execution_mode"] = args.trtllm_execution_mode
        if args.trtllm_pyexecutor_max_tokens is not None:
            engine_options["pyexecutor_max_tokens"] = args.trtllm_pyexecutor_max_tokens
        if args.trtllm_pyexecutor_lookahead:
            engine_options["pyexecutor_lookahead"] = True
        if args.trtllm_pyexecutor_lookahead_min_batch_size is not None:
            engine_options["pyexecutor_lookahead_min_batch_size"] = (
                args.trtllm_pyexecutor_lookahead_min_batch_size
            )
        if args.trtllm_pyexecutor_direct_token_limit is not None:
            engine_options["pyexecutor_direct_token_limit"] = (
                args.trtllm_pyexecutor_direct_token_limit
            )
        if args.trtllm_pyexecutor_speculative_lookahead:
            engine_options["pyexecutor_speculative_lookahead"] = True
        if args.trtllm_max_seq_len is not None:
            engine_options["max_seq_len"] = args.trtllm_max_seq_len
        if args.trtllm_max_batch_size is not None:
            engine_options["max_batch_size"] = args.trtllm_max_batch_size
        if args.trtllm_max_num_tokens is not None:
            engine_options["max_num_tokens"] = args.trtllm_max_num_tokens
        if args.trtllm_kv_cache_free_gpu_memory_fraction is not None:
            engine_options["kv_cache_free_gpu_memory_fraction"] = (
                args.trtllm_kv_cache_free_gpu_memory_fraction
            )
    else:
        engine_options = {}

    if args.mode == "latency":
        max_concurrent_processes: int | None = 1
    elif args.concurrency == 0:
        max_concurrent_processes = None
    else:
        max_concurrent_processes = args.concurrency
    _cap_override = os.environ.get("PIE_BENCH_ADMISSION_CAP")
    if _cap_override:
        max_concurrent_processes = int(_cap_override)
    requested_scheduler_kwargs = {
        "default_token_limit": args.default_token_limit,
        "default_endowment_pages": args.default_endowment_pages,
        "admission_oversubscription_factor": args.admission_oversubscription_factor,
        "frame_size": args.frame_size,
        "frame_submit_depth": args.frame_submit_depth,
        "frame_dispatch_depth": args.frame_dispatch_depth,
        "submit_deadline": args.submit_deadline,
        "max_concurrent_processes": max_concurrent_processes,
    }
    requested_scheduler_kwargs = {
        k: v for k, v in requested_scheduler_kwargs.items() if v is not None
    }
    scheduler_parameters = inspect.signature(RuntimeConfig).parameters
    scheduler_kwargs = {
        key: value
        for key, value in requested_scheduler_kwargs.items()
        if key in scheduler_parameters
    }

    resolved_model = resolve_local_model(args.model)
    cfg = Config(
        server=ServerConfig(
            listen="127.0.0.1:0",
            verbose=True,
            **({"worker_threads": args.worker_threads} if args.worker_threads else {}),
        ),
        telemetry=TelemetryConfig(),
        runtime=RuntimeConfig(**scheduler_kwargs),
        sandbox=SandboxConfig(
            max_instances=max(4096, (max_concurrent_processes or 0) * 4),
            **({"warm_slots": args.wasm_warm_slots}
               if getattr(args, "wasm_warm_slots", None) else {}),
            **({"warm_memory_mb": args.wasm_warm_memory_mb}
               if getattr(args, "wasm_warm_memory_mb", None) is not None else {}),
        ),
        model=ModelConfig(
            name="default",
            source=resolved_model,
            device_weight_budget=getattr(args, "device_weight_budget", None),
            host_weight_budget=getattr(args, "host_weight_budget", None),
            device_kv_budget=getattr(args, "device_kv_budget", None),
            weight_precision=getattr(args, "precision", None),
            kv_dtype=getattr(args, "kv", None),
            device_memory_share=args.gpu_mem_util,
        ),
        engine=EngineConfig(
            type=args.engine,
            device=device,
            tensor_parallel_size=args.tp_size,
            options=engine_options,
        ),
    )
    config_blob = {
        "engine": args.engine,
        "resolved model": resolved_model,
        **engine_options,
    }
    if args.warmup_max_tokens is not None:
        config_blob["warmup max tokens"] = args.warmup_max_tokens
    config_blob["warmup seconds"] = args.warmup_seconds
    return cfg, config_blob


@asynccontextmanager
async def python_pie_client(args: argparse.Namespace):
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


@asynccontextmanager
async def cli_pie_client(args: argparse.Namespace):
    from pie_client import PieClient

    cfg, engine_config = build_config(args)
    cfg.server.port = find_free_port()
    cfg.server.listen = f"127.0.0.1:{cfg.server.port}"
    cfg_path = ROOT / ".tmp" / "benches" / f"pie-{args.engine}-{cfg.server.port}.toml"
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    cfg_path.write_text(cfg.to_toml())

    pie_bin = Path(args.pie_bin)
    if not pie_bin.exists():
        feature = {"metal": "metal", "xla": "xla"}.get(args.engine, "cuda")
        raise FileNotFoundError(
            f"missing {pie_bin}; build with: cargo build --release -p pie "
            f"--no-default-features --features {feature}"
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
    startup_lines: list[str] = []
    server_lines: list[str] = startup_lines
    drain_task: asyncio.Task[None] | None = None
    server_ready = False
    server_log_file = None
    if server_log_path := os.environ.get("PIE_BENCH_SERVER_LOG"):
        path = Path(server_log_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        server_log_file = path.open("w", encoding="utf-8")

    spawned = time.perf_counter()

    def should_surface_server_line(txt: str) -> bool:
        return (
            txt.startswith("ane: ")
            or "panicked at" in txt
            or txt.startswith("[fire ")
            or txt.startswith("[pie-fire-timing] ")
            or txt.startswith("[sched-fire ")
            or txt.startswith("[outer-fire ")
            or txt.startswith("[sched-batch ")
            or txt.startswith("[pie-spec] ")
            or txt.startswith("[pie-engine-cuda] sampled tokens ")
            or "[pie-engine-cuda] memory planner:" in txt
            or "[pie-engine-cuda] forward_limits:" in txt
            or "[pie-engine-cuda] kv_cache:" in txt
            or "[pie-engine-cuda] CUDA graph upfront capture:" in txt
            or " xqa_decode=" in txt
            or " WARN " in txt
            or " ERROR " in txt
            or "Batch response count mismatch" in txt
            or "fire_batch failed" in txt
            or "exceeds workspace" in txt
            or "graph captured" in txt
        )

    def stamped(txt: str) -> str:
        if txt.startswith("ane: ") or "panicked at" in txt:
            return f"[{time.perf_counter() - spawned:7.1f}s] {txt}"
        return txt

    async def drain_stdout() -> None:
        assert proc.stdout is not None
        import sys
        while True:
            line = await proc.stdout.readline()
            if not line:
                return
            txt = line.decode("utf-8", errors="replace")
            server_lines.append(txt)
            del server_lines[:-200]
            if server_log_file is not None:
                server_log_file.write(txt)
                server_log_file.flush()
            if should_surface_server_line(txt):
                sys.stderr.write(stamped(txt))
                sys.stderr.flush()

    try:
        assert proc.stdout is not None
        deadline = time.perf_counter() + args.server_startup_timeout
        while time.perf_counter() < deadline:
            try:
                line = await asyncio.wait_for(
                    proc.stdout.readline(),
                    timeout=max(0.1, deadline - time.perf_counter()),
                )
            except TimeoutError as exc:
                raise TimeoutError(
                    "timed out waiting for pie serve startup:\n"
                    + "".join(startup_lines[-80:])
                ) from exc
            if not line:
                raise RuntimeError(
                    "pie serve exited before startup completed:\n"
                    + "".join(startup_lines[-80:])
                )
            text = line.decode("utf-8", errors="replace")
            startup_lines.append(text)
            if server_log_file is not None:
                server_log_file.write(text)
                server_log_file.flush()
            if should_surface_server_line(text):
                sys.stderr.write(stamped(text))
                sys.stderr.flush()
            if "Server ready at " in text:
                server_ready = True
                engine_config["server load s"] = round(time.perf_counter() - launched, 3)
                break
            if proc.returncode is not None:
                raise RuntimeError(
                    f"pie serve exited with {proc.returncode}:\n"
                    + "".join(startup_lines[-80:])
                )
        if not server_ready:
            raise TimeoutError(
                "timed out waiting for pie serve startup:\n" + "".join(startup_lines[-80:])
            )

        drain_task = asyncio.create_task(drain_stdout())
        client = PieClient(f"ws://127.0.0.1:{cfg.server.port}")
        await client.connect()
        try:
            yield client, {**engine_config, "pie_bin": str(pie_bin)}
        finally:
            await client.close()
    finally:
        if proc.returncode is None:
            proc.terminate()
            try:
                await asyncio.wait_for(proc.wait(), timeout=10.0)
            except TimeoutError:
                proc.kill()
                await proc.wait()
        if drain_task is not None:
            drain_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await drain_task
        if server_log_file is not None:
            server_log_file.close()


def pie_client(args: argparse.Namespace):
    if args.engine in EMBEDDED_CLI_ENGINES:
        return cli_pie_client(args)
    return python_pie_client(args)


async def run(args: argparse.Namespace):
    from pie_client import Event

    cpu_affinity = maybe_set_cpu_affinity(
        args, visible_cuda_devices(args.tp_size, args.dp_size))

    n = args.requests if args.mode == "latency" else args.num_requests
    prompts = make_prompts(args, n + args.warmup)
    prompt_token_ids: list[list[int]] | None = None
    if args.pretokenized_prompts:
        prompt_token_ids, _ = hf_chat_token_ids_and_counts(
            args.model, args.system, prompts, getattr(args, "think", None)
        )
    wasm = bench_inferlet_wasm(args.inferlet_dir)

    async with pie_client(args) as (client, engine_config):
        pkg = await client.install_program(wasm)

        first_output_text: list[str | None] = [None]
        output_token_ids_by_process: dict[str, list[int]] = {}
        measured_epoch: float | None = None
        measured_epoch_unix_s: float | None = None
        measured_epoch_monotonic_ns: int | None = None

        def common_input(max_tokens: int | None = None) -> dict[str, Any]:
            return {
                "system": args.system,
                "max_tokens": args.max_tokens if max_tokens is None else max_tokens,
                "temperature": args.temperature,
                "top_p": args.top_p,
                "ignore_eos": args.ignore_eos,
                "no_think": getattr(args, "think", None) is False,
                "wasm_delay_us": args.wasm_delay_us,
                **({"host_first_token": True} if getattr(args, "host_first_token", False) else {}),
                **(
                    {"run_ahead_frames": args.run_ahead_frames}
                    if getattr(args, "run_ahead_frames", None)
                    else {}
                ),
                "return_text": args.dump_first_text or args.dump_all_texts,
                "report_timing": args.report_timing,
                "report_arrivals": args.report_arrivals,
                "wait_for_start": args.defer_start,
                **(
                    {"batch_concurrency": args.concurrency}
                    if getattr(args, "concurrency", 0) and args.concurrency > 0
                    else {}
                ),
                **{k: v for k, v in (getattr(args, "extra_input", None) or {}).items()},
                **(
                    {"system_speculation": args.system_speculation}
                    if args.system_speculation is not None
                    else {}
                ),
            }

        heard = [time.perf_counter()]

        async def recv(proc):
            while True:
                idle = time.perf_counter() - heard[0]
                try:
                    event = await asyncio.wait_for(
                        proc.recv(), timeout=max(0.0, args.request_timeout - idle)
                    )
                except TimeoutError:
                    if time.perf_counter() - heard[0] >= args.request_timeout:
                        raise
                    continue
                heard[0] = time.perf_counter()
                return event

        async def launch_one(i: int, *, max_tokens: int | None = None):
            if max_tokens is None:
                max_tokens = request_max_tokens(args, i)
            inp = {
                **common_input(max_tokens),
                "prompt": prompts[i],
            }
            if prompt_token_ids is not None:
                inp["prompt_tokens"] = prompt_token_ids[i]
            start = time.perf_counter()
            send_monotonic_ns = monotonic_ns()
            client_send_s = (
                (send_monotonic_ns - measured_epoch_monotonic_ns)
                / 1_000_000_000.0
                if measured_epoch_monotonic_ns is not None
                and (args.report_timing or args.report_arrivals)
                else None
            )
            try:
                proc = await client.launch_process(pkg, input=inp)
                heard[0] = time.perf_counter()
                return i, start, proc, client_send_s
            except Exception as e:
                return RequestResult(False, time.perf_counter() - start, 0, error=f"{type(e).__name__}: {e}")

        async def wait_one(launched) -> RequestResult:
            if isinstance(launched, RequestResult):
                return launched
            i, start, proc, client_send_s = launched
            ttft_s: float | None = None
            first_arrival_s: float | None = None
            try:
                while True:
                    ev, msg = await recv(proc)
                    if ev == Event.Message and str(msg) == "t0":
                        now = time.perf_counter()
                        now_monotonic_ns = monotonic_ns()
                        ttft_s = now - start
                        first_arrival_s = (
                            (
                                now_monotonic_ns
                                - measured_epoch_monotonic_ns
                            )
                            / 1_000_000_000.0
                            if measured_epoch_monotonic_ns is not None
                            and (args.report_timing or args.report_arrivals)
                            else None
                        )
                        continue
                    if ev == Event.Return:
                        returned = time.perf_counter()
                        returned_monotonic_ns = monotonic_ns()
                        obj = json.loads(msg)
                        if i == args.warmup and first_output_text[0] is None:
                            first_output_text[0] = obj.get("text", "")
                        output_tokens = int(_output_token_count(obj))
                        token_ids = [int(token) for token in obj.get("token_ids") or []]
                        if "token_ids" in obj and len(token_ids) != output_tokens:
                            raise ValueError(
                                f"output token count {len(token_ids)}, expected {output_tokens}"
                            )
                        output_token_ids_by_process[str(proc.process_id)] = token_ids
                        gaps = obj.get("intertoken_us") or []
                        arrivals = None
                        arrival_monotonic_ns = [
                            int(value)
                            for value in (obj.get("token_monotonic_ns") or [])
                        ]
                        if (
                            measured_epoch_monotonic_ns is not None
                            and arrival_monotonic_ns
                            and arrival_monotonic_ns[-1]
                            < measured_epoch_monotonic_ns
                        ):
                            arrival_monotonic_ns = [
                                measured_epoch_monotonic_ns + value
                                for value in arrival_monotonic_ns
                            ]
                        if measured_epoch_monotonic_ns is not None:
                            if first_arrival_s is not None and (gaps or output_tokens == 1):
                                arrivals = reconstruct_token_arrivals(
                                    first_arrival_s, gaps, output_tokens
                                )
                            elif args.report_arrivals:
                                if len(arrival_monotonic_ns) != output_tokens:
                                    raise ValueError(
                                        "shared-clock token timing count is "
                                        f"{len(arrival_monotonic_ns)}, "
                                        f"expected {output_tokens}"
                                    )
                                arrivals = [
                                    (
                                        int(value)
                                        - measured_epoch_monotonic_ns
                                    )
                                    / 1_000_000_000.0
                                    for value in arrival_monotonic_ns
                                ]
                        return RequestResult(
                            True,
                            returned - start,
                            output_tokens,
                            int(obj.get("num_prompt_tokens") or 0),
                            ttft_s=ttft_s,
                            intertoken_us=gaps or None,
                            client_send_s=client_send_s,
                            token_arrival_s=arrivals,
                            token_arrival_monotonic_ns=(
                                arrival_monotonic_ns or None
                            ),
                            client_return_s=(
                                (
                                    returned_monotonic_ns
                                    - measured_epoch_monotonic_ns
                                )
                                / 1_000_000_000.0
                                if measured_epoch_monotonic_ns is not None
                                else None
                            ),
                            process_id=str(proc.process_id),
                            prologue_us=obj.get("prologue_us") or None,
                            speculation=(
                                {
                                    "rounds": obj.get("rounds"),
                                    "drafted": obj.get("drafted"),
                                    "accepted": obj.get("accepted"),
                                    "plain_fires": obj.get("plain_fires"),
                                    "verify": obj.get("verify"),
                                    "prices_ms": obj.get("prices_ms"),
                                    "budget_model": obj.get("budget_model"),
                                    "budget_expected": obj.get("budget_expected"),
                                }
                                if "rounds" in obj
                                else None
                            ),
                            output_text=(
                                obj.get("text", "") if args.dump_all_texts else None
                            ),
                        )
                    if ev == Event.Error:
                        return RequestResult(False, time.perf_counter() - start, 0, error=str(msg))
            except Exception as e:
                return RequestResult(False, time.perf_counter() - start, 0, error=f"{type(e).__name__}: {e}")

        async def batch(indices, *, max_tokens: int | None = None) -> list[RequestResult]:
            indices = list(indices)
            inp = {
                **common_input(max_tokens),
                "wait_for_start": True,
                "prompt": prompts[indices[0]] if indices else args.prompt,
                "prompts": [prompts[i] for i in indices],
            }
            if args.concurrency and args.concurrency > 0:
                inp["batch_concurrency"] = args.concurrency
            if prompt_token_ids is not None:
                inp["prompt_tokens_batch"] = [prompt_token_ids[i] for i in indices]
            start = time.perf_counter()
            try:
                proc = await client.launch_process(pkg, input=inp)
                heard[0] = time.perf_counter()
                while True:
                    ev, msg = await recv(proc)
                    if ev == Event.Message and str(msg) == "ready":
                        break
                    if ev == Event.Return:
                        return [
                            RequestResult(
                                False, 0.0, 0, error="returned before start"
                            )
                            for _ in indices
                        ]
                    if ev == Event.Error:
                        return [
                            RequestResult(False, 0.0, 0, error=str(msg))
                            for _ in indices
                        ]
                start = time.perf_counter()
                await proc.signal("start")
                while True:
                    ev, msg = await recv(proc)
                    if ev == Event.Return:
                        obj = json.loads(msg)
                        if first_output_text[0] is None:
                            first_output_text[0] = obj.get("text", "")
                        req_out = obj.get("request_output_tokens") or []
                        req_prompt = obj.get("request_prompt_tokens") or []
                        elapsed = time.perf_counter() - start
                        if len(req_out) == len(indices) and len(req_prompt) == len(indices):
                            return [
                                RequestResult(True, elapsed, int(out), int(prompt))
                                for out, prompt in zip(req_out, req_prompt)
                            ]
                        total_out = int(_output_token_count(obj))
                        total_prompt = int(obj.get("num_prompt_tokens") or 0)
                        per_out = total_out // max(1, len(indices))
                        per_prompt = total_prompt // max(1, len(indices))
                        return [
                            RequestResult(True, elapsed, per_out, per_prompt)
                            for _ in indices
                        ]
                    if ev == Event.Error:
                        return [
                            RequestResult(False, time.perf_counter() - start, 0, error=str(msg))
                            for _ in indices
                        ]
            except Exception as e:
                return [
                    RequestResult(
                        False,
                        time.perf_counter() - start,
                        0,
                        error=f"{type(e).__name__}: {e}",
                    )
                    for _ in indices
                ]

        pacer = ArrivalPacer(
            arrival_schedule(
                n, args.arrival_rate, args.arrival_process, args.arrival_seed
            )
        )

        async def one(i: int, *, max_tokens: int | None = None) -> RequestResult:
            return await wait_one(await launch_one(i, max_tokens=max_tokens))

        use_single_batch = args.mode == "tput" and (
            args.single_process_batch
            or (
                args.engine == "xla"
                and args.concurrency > 1
                and (
                    args.inferlet_dir is None
                    or "text-completion-bench" in str(args.inferlet_dir)
                )
            )
        )

        async def many(indices, *, max_tokens: int | None = None) -> list[RequestResult]:
            if use_single_batch:
                return await batch(indices, max_tokens=max_tokens)
            if args.concurrency > 0 and not args.defer_start:
                seats = asyncio.Semaphore(args.concurrency)

                async def seated(i: int) -> RequestResult:
                    queued = time.perf_counter()
                    async with seats:
                        waited = time.perf_counter() - queued
                        result = await one(i, max_tokens=max_tokens)
                    if isinstance(result, RequestResult):
                        result.latency_s += waited
                        if result.ttft_s is not None:
                            result.ttft_s += waited
                    return result

                return await asyncio.gather(*(seated(i) for i in indices))
            launched = await asyncio.gather(
                *(launch_one(i, max_tokens=max_tokens) for i in indices)
            )
            if args.defer_start and args.mode == "tput":
                async def await_ready(item):
                    if isinstance(item, RequestResult):
                        return item
                    i, _start, proc, _client_send_s = item
                    try:
                        while True:
                            ev, msg = await recv(proc)
                            if ev == Event.Message and str(msg) == "ready":
                                return i, proc
                            if ev == Event.Return:
                                return RequestResult(False, 0.0, 0, error="returned before start")
                            if ev == Event.Error:
                                return RequestResult(False, 0.0, 0, error=str(msg))
                    except Exception as e:
                        return RequestResult(False, 0.0, 0, error=f"{type(e).__name__}: {e}")

                waited = await asyncio.gather(*(await_ready(item) for item in launched))
                ready = [w for w in waited if not isinstance(w, RequestResult)]
                failed = [w for w in waited if isinstance(w, RequestResult)]
                start = time.perf_counter()
                await asyncio.gather(*(proc.signal("start") for _i, proc in ready))
                deferred = [
                    (
                        i,
                        start,
                        proc,
                        (
                            monotonic_ns()
                            - measured_epoch_monotonic_ns
                        )
                        / 1_000_000_000.0
                        if measured_epoch_monotonic_ns is not None
                        else None,
                    )
                    for i, proc in ready
                ]
                return failed + await asyncio.gather(
                    *(wait_one(item) for item in deferred)
                )
            return await asyncio.gather(*(wait_one(item) for item in launched))

        async def many_paced(indices) -> list[RequestResult]:
            pacer.start()

            async def offer(k: int, i: int) -> RequestResult:
                await pacer.wait(k)
                return await one(i)

            return await asyncio.gather(
                *(offer(k, i) for k, i in enumerate(indices))
            )

        if args.warmup:
            warmup_max_tokens = args.warmup_max_tokens or args.max_tokens

            async def warmup_pass() -> None:
                if args.mode == "tput":
                    if args.engine == "xla" and args.concurrency > 0:
                        m_end = min(len(prompts), args.warmup + n)
                        if use_single_batch:
                            await batch(range(args.warmup, m_end), max_tokens=2)
                            await batch(range(args.warmup, min(len(prompts), args.warmup + args.concurrency)), max_tokens=args.max_tokens)
                        else:
                            for b_c in (1, 2, 4, 8, 16, 24, 32, 48, 64):
                                if b_c <= len(prompts) and b_c <= args.concurrency:
                                    await many(range(b_c), max_tokens=2)
                            await many(range(args.warmup, m_end), max_tokens=args.max_tokens)
                    else:
                        await many(range(args.warmup), max_tokens=warmup_max_tokens)
                else:
                    for i in range(args.warmup):
                        await one(i, max_tokens=warmup_max_tokens)

            await warmup_pass()
            await run_timed_warmup(
                warmup_pass, args.warmup_seconds, label="pie")

        start_idx = args.warmup
        pre_stats: dict[str, Any] = {}
        try:
            ok, body = await client.query("model_status", "")
            if ok:
                pre_stats = json.loads(body)
        except Exception:
            pass
        clocks_at_start = gpu_clock_state()
        print("[pie-bench] measured-start", flush=True)
        profiler_task = None
        if (
            args.cuda_profiler_capture
            and args.cuda_profiler_duration_s > 0
        ):
            async def capture_profiler_window() -> None:
                await asyncio.sleep(args.cuda_profiler_delay_s)
                cuda_profiler_start(True)
                try:
                    await asyncio.sleep(args.cuda_profiler_duration_s)
                finally:
                    cuda_profiler_stop(True)

            profiler_task = asyncio.create_task(capture_profiler_window())
        else:
            cuda_profiler_start(args.cuda_profiler_capture)
        if (
            args.report_timing
            or args.report_arrivals
            or args.report_wall_clock
        ):
            measured_epoch_unix_s = time.time()
            measured_epoch_monotonic_ns = monotonic_ns()
            measured_epoch = time.perf_counter()
            start = measured_epoch
        else:
            start = time.perf_counter()
        cooled = 0.0
        try:
            if args.mode == "latency":
                results = []
                for i in range(n):
                    cooled += await asyncio.to_thread(cool_before_request)
                    results.append(await one(start_idx + i))
            elif pacer.enabled:
                results = await many_paced(range(start_idx, start_idx + n))
            else:
                results = await many(range(start_idx, start_idx + n))
        finally:
            wall = time.perf_counter() - start - cooled
            if profiler_task is None:
                cuda_profiler_stop(args.cuda_profiler_capture)
            else:
                if not profiler_task.done():
                    profiler_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await profiler_task
            clocks_at_end = gpu_clock_state()
            print("[pie-bench] measured-end", flush=True)
        for result in results:
            if result.process_id is not None:
                token_ids = output_token_ids_by_process[result.process_id]
                result.output_token_sha256 = hash_output_tokens(token_ids)
                if args.dump_all_token_ids:
                    result.output_token_ids = token_ids
        seen: dict[str, int] = {}
        for r in results:
            if not r.ok:
                seen[(r.error or "?")[:200]] = seen.get((r.error or "?")[:200], 0) + 1
        for why, n in list(seen.items())[:4]:
            print(f"[pie-bench] {n} failed: {why}", file=sys.stderr, flush=True)
        if args.mode == "tput" and (args.defer_start or use_single_batch):
            measured = [r.latency_s for r in results if r.ok]
            if measured:
                wall = max(measured)

        try:
            ok, body = await client.query("model_status", "")
            if ok:
                model_status_raw = json.loads(body)
                model_status: dict[str, Any] = {}
                for k, v in model_status_raw.items():
                    pre = pre_stats.get(k)
                    if (
                        is_cumulative_status_key(k)
                        and isinstance(v, (int, float))
                        and isinstance(pre, (int, float))
                    ):
                        model_status[k] = v - pre
                    elif (
                        is_cumulative_status_key(k)
                        and isinstance(v, list)
                        and isinstance(pre, list)
                        and len(v) == len(pre)
                    ):
                        model_status[k] = [a - b for a, b in zip(v, pre)]
                    else:
                        model_status[k] = v
                measured_batches = model_status.get("default.total_batches", 0)
                if isinstance(measured_batches, (int, float)):
                    measured_average(
                        model_status,
                        "default.cumulative_batch_latency_us",
                        measured_batches,
                        "default.avg_batch_latency_us",
                    )
                    for sum_key, average_key in (
                        ("default.fire.accumulate.accum_loop_us_sum",
                         "default.fire.accumulate.accum_loop_us"),
                        ("default.fire.pre_dispatch.fire_prepare_us_sum",
                         "default.fire.pre_dispatch.fire_prepare_us"),
                        ("default.fire.execute.total_us_sum",
                         "default.fire.execute.total_us"),
                        ("default.fire.execute.batch_build_us_sum",
                         "default.fire.execute.batch_build_us"),
                        ("default.fire.execute.engine_fire_us_sum",
                         "default.fire.execute.engine_fire_us"),
                        ("default.fire.post_dispatch.context_tick_us_sum",
                         "default.fire.post_dispatch.context_tick_us"),
                        ("default.fire.post_dispatch.stats_update_us_sum",
                         "default.fire.post_dispatch.stats_update_us"),
                        ("default.fire.quorum.inter_batch_bubble_us_sum",
                         "default.fire.quorum.inter_batch_bubble_us"),
                        ("default.fire.quorum.quorum_latency_us_sum",
                         "default.fire.quorum.quorum_latency_us"),
                    ):
                        measured_average(
                            model_status,
                            sum_key,
                            measured_batches,
                            average_key,
                        )
                    pre_batches = pre_stats.get("default.total_batches", 0)
                    inter_fire_samples = (
                        measured_batches
                        if isinstance(pre_batches, (int, float)) and pre_batches > 0
                        else max(measured_batches - 1, 0)
                    )
                    for sum_key, average_key in (
                        ("default.fire.inter_fire_us_sum",
                         "default.fire.inter_fire_us"),
                        ("default.fire.post_dispatch_to_fire_us_sum",
                         "default.fire.post_dispatch_to_fire_us"),
                        ("default.fire.recv_block_wait_us_sum",
                         "default.fire.recv_block_wait_us"),
                    ):
                        measured_average(
                            model_status,
                            sum_key,
                            inter_fire_samples,
                            average_key,
                        )
                wave_fires = model_status.get("default.fire.quorum.wave_fires", 0)
                if isinstance(wave_fires, (int, float)):
                    measured_average(
                        model_status,
                        "default.fire.quorum.wave_active_sum",
                        wave_fires,
                        "default.fire.quorum.avg_active_pipelines_at_fire",
                    )
                    measured_average(
                        model_status,
                        "default.fire.quorum.wave_missing_sum",
                        wave_fires,
                        "default.fire.quorum.avg_missing_at_fire",
                    )
                for key, label in (
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
                    (
                        "default.fire.quorum.avg_active_pipelines_at_fire",
                        "wave avg active pipelines",
                    ),
                    (
                        "default.fire.quorum.avg_missing_at_fire",
                        "wave avg missing pipelines",
                    ),
                    ("default.fire.quorum.wave_fires", "wave fires"),
                    ("default.fire.quorum.seal_events", "seal events"),
                    ("default.fire.quorum.seal_while_executing",
                     "seals while executing"),
                    ("default.fire.quorum.dispatch_blocked_holds",
                     "sealed-queue blocked holds"),
                    ("default.fire.quorum.device_idle_us", "device idle us"),
                    ("default.fire.quorum.device_idle_gaps", "device idle gaps"),
                    ("default.fire.quorum.idle_break_control",
                     "idle breaks (control holds launches)"),
                    ("default.fire.quorum.idle_break_depth",
                     "idle breaks (depth cap)"),
                    ("default.fire.quorum.idle_park_control_us",
                     "idle park us (control holds launches)"),
                    ("default.fire.quorum.idle_park_other_us",
                     "idle park us (other)"),
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
                    ("default.process.avg_admission_wait_us",
                     "process avg admission wait us"),
                    ("default.process.avg_instantiate_us",
                     "process avg instantiate us"),
                    ("default.process.avg_wasm_run_us",
                     "process avg wasm run us"),
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
                ):
                    if key in model_status:
                        engine_config[label] = model_status[key]
                for key, value in model_status.items():
                    if (
                        "wave" in key
                        or "active_pipelines" in key
                        or "missing_at_fire" in key
                        or "straggler" in key
                    ):
                        engine_config[key] = value
        except Exception:
            pass

    if args.dump_first_text and first_output_text[0] is not None:
        import hashlib
        sha = hashlib.sha256(first_output_text[0].encode()).hexdigest()[:16]
        print(f"\nFIRST REQUEST OUTPUT (sha256[:16]={sha}):")
        print(first_output_text[0])
        print(f"END OUTPUT (chars={len(first_output_text[0])})")

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
            **(
                {
                    "client timing epoch unix s": measured_epoch_unix_s,
                    "client timing epoch monotonic ns": (
                        measured_epoch_monotonic_ns
                    ),
                }
                if (
                    args.report_timing
                    or args.report_arrivals
                    or args.report_wall_clock
                )
                else {}
            ),
            "cpu affinity": cpu_affinity,
            "gpu clocks at start": clocks_at_start,
            "gpu clocks at end": clocks_at_end,
            **engine_config,
        },
    )
    return summary, results


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Pie canonical latency/throughput benchmark")
    add_mode_subcommands(p)
    for sp in p._subparsers._group_actions[0].choices.values():
        sp.add_argument(
            "--inferlet-dir",
            default=os.environ.get("PIE_BENCH_INFERLET_DIR"),
            help="Path to a built text-completion-bench inferlet project "
                 "(or set PIE_BENCH_INFERLET_DIR).",
        )
        sp.add_argument("--device", default=PIE_BENCH_DEFAULT_DEVICE)
        sp.add_argument("--engine", default="cuda",
                        choices=["cuda", "metal", "xla", "vllm", "sglang",
                                 "tensorrt_llm", "dummy"])
        sp.add_argument("--default-token-limit", type=int, default=200_000)
        sp.add_argument("--default-endowment-pages", type=int, default=64)
        sp.add_argument("--admission-oversubscription-factor", type=float, default=4.0)
        sp.add_argument("--cpu-mem-budget", type=int, default=0)
        sp.add_argument(
            "--kv-pages", type=int, default=2048,
            help="DEAD for cuda: never reaches engine_options, so it "
                 "silently does nothing. Use --device-kv-budget to cap KV.",
        )
        sp.add_argument("--precision", default=None,
                        help="[model] weight_precision, e.g. bf16+nvfp4a4")
        sp.add_argument("--kv", default=None,
                        help="[model] kv, e.g. e4m3 (DeepSeek-V4's fp8 rows)")
        sp.add_argument(
            "--device-kv-budget",
            default=None,
            help="[model] device_kv_budget: device bytes for the kv pages and "
                 "state slots, with a unit (\"8GiB\"). Omit to fill what "
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
        sp.add_argument(
            "--frame-size", type=int, default=None,
            help="Waves per frame (pie scheduler `frame_size`). Omit for the "
                 "engine default (2).",
        )
        sp.add_argument(
            "--frame-submit-depth", type=int, default=None,
            help="Frames a guest keeps queued in the engine. Omit for the "
                 "engine default (3). This is the guest running ahead of the "
                 "engine; too few collapses the pipeline to lockstep.",
        )
        sp.add_argument(
            "--frame-dispatch-depth", type=int, default=None,
            help="Frames the engine keeps posted to the engine. Omit for the "
                 "engine default (2). The worker's config notes this is a "
                 "two-sided trade-off that a fully batched fleet can lose.",
        )
        sp.add_argument(
            "--submit-deadline", default=None,
            help="How long a wave waits on a straggler lane before sealing "
                 "without it, with unit (e.g. '50ms'). Omit for the engine "
                 "default.",
        )
        sp.add_argument("--max-forward-tokens", type=int,
                        default=PIE_MAX_FORWARD_TOKENS_DEFAULT)
        sp.add_argument("--max-forward-requests", type=int,
                        default=PIE_MAX_FORWARD_REQUESTS_DEFAULT)
        sp.add_argument("--worker-threads", type=int, default=None)
        sp.add_argument("--extra-input", action="append", default=None, metavar="KEY=VALUE",
                        help="Extra inferlet input field (typed like --engine-option); repeatable.")
        sp.add_argument("--device-weight-budget", default=None,
                        help="[model] device_weight_budget, e.g. 20GiB (metal residency)")
        sp.add_argument("--host-weight-budget", default=None,
                        help="[model] host_weight_budget, e.g. 8GiB")
        for flag, dest, helptext in (
            ("--wasm-warm-slots", "wasm_warm_slots",
             "Prepared-but-idle guest slots kept for fast respawn. "
             "Default: the engine's (100)."),
            ("--wasm-warm-memory-mb", "wasm_warm_memory_mb",
             "MiB of a guest's linear memory kept resident across its exit "
             "instead of decommitted. Default: the engine's (0)."),
            ("--frame-size", "frame_size",
             "Waves per frame (k). Default: the engine's."),
            ("--frame-submit-depth", "frame_submit_depth",
             "Frames a guest keeps submitted. Default: the engine's."),
            ("--frame-dispatch-depth", "frame_dispatch_depth",
             "Frames the engine keeps posted to the engine. "
             "Default: the engine's."),
        ):
            if not any(flag in a.option_strings for a in sp._actions):
                sp.add_argument(flag, dest=dest, type=int, default=None,
                                help=helptext)
        if not any(
            "--run-ahead-frames" in a.option_strings for a in sp._actions
        ):
            sp.add_argument(
                "--run-ahead-frames",
                dest="run_ahead_frames",
                type=int,
                default=None,
                help="Override the inferlet's run-ahead window depth, in "
                     "frames (forwarded as the bench input's "
                     "run_ahead_frames; the ring grows to match). "
                     "Default: the inferlet's own sizing.",
            )
        if not any(
            "--host-first-token" in a.option_strings for a in sp._actions
        ):
            sp.add_argument(
                "--host-first-token",
                dest="host_first_token",
                action="store_true",
                help="Hand the prefill's first token to the decode pass "
                     "through the HOST (out on g0, back as the decode's seed) "
                     "instead of across the device-only channel the two "
                     "passes share. Costs one host hop per request and none "
                     "per token. Default: the device handoff, which both "
                     "engines now serve.",
            )
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
        sp.add_argument("--vllm-attention-backend", default=None)
        sp.add_argument("--vllm-max-num-seqs", type=int, default=None)
        sp.add_argument("--vllm-max-num-batched-tokens", type=int, default=None)
        sp.add_argument("--vllm-max-model-len", type=int, default=None)
        sp.add_argument("--vllm-spec-ngram", action=argparse.BooleanOptionalAction, default=False)
        sp.add_argument("--vllm-spec-ngram-num-drafts", type=int, default=4)
        sp.add_argument("--vllm-spec-ngram-min-n", type=int, default=2)
        sp.add_argument("--vllm-spec-ngram-max-n", type=int, default=4)
        sp.add_argument("--trtllm-backend", default=None)
        sp.add_argument("--trtllm-attn-backend", default=None)
        sp.add_argument("--trtllm-lookahead-tokens", type=int, default=None)
        sp.add_argument(
            "--trtllm-execution-mode",
            choices=["generate", "pyexecutor"],
            default=None,
        )
        sp.add_argument("--trtllm-pyexecutor-max-tokens", type=int, default=None)
        sp.add_argument("--trtllm-pyexecutor-lookahead", action="store_true")
        sp.add_argument(
            "--trtllm-pyexecutor-lookahead-min-batch-size",
            type=int,
            default=None,
        )
        sp.add_argument("--trtllm-pyexecutor-direct-token-limit", type=int, default=None)
        sp.add_argument(
            "--trtllm-pyexecutor-speculative-lookahead",
            action="store_true",
        )
        sp.add_argument("--trtllm-max-seq-len", type=int, default=None)
        sp.add_argument("--trtllm-max-batch-size", type=int, default=None)
        sp.add_argument("--trtllm-max-num-tokens", type=int, default=None)
        sp.add_argument(
            "--trtllm-kv-cache-free-gpu-memory-fraction",
            type=float,
            default=None,
        )
        sp.add_argument("--pie-bin", default=str(ROOT / "target" / "release" / "pie"))
        sp.add_argument("--server-startup-timeout", type=float, default=300.0)
        sp.add_argument("--venv", default=None,
                        help="Path to a Python venv for subprocess engines (vllm/sglang/tensorrt_llm/dev)")
    return p


def run_data_parallel(args):
    import subprocess
    import tempfile

    total = args.requests if args.mode == "latency" else args.num_requests
    per = [total // args.dp_size] * args.dp_size
    for i in range(total % args.dp_size):
        per[i] += 1

    rewritten = {"--dp-size", "--json-out", "--requests", "--num-requests",
                 "--device"}
    forwarded, skip_next = [], False
    for token in sys.argv[1:]:
        if skip_next:
            skip_next = False
            continue
        if token in rewritten:
            skip_next = True
            continue
        if any(token.startswith(f"{flag}=") for flag in rewritten):
            continue
        forwarded.append(token)

    procs, outs = [], []
    tmpdir = tempfile.mkdtemp(prefix="pie-dp-")
    for replica, count in enumerate(per):
        if count == 0:
            continue
        devices = ",".join(
            str(replica * args.tp_size + i) for i in range(args.tp_size))
        out = os.path.join(tmpdir, f"replica{replica}.json")
        outs.append(out)
        argv = [sys.executable, os.path.abspath(__file__),
                *forwarded, "--json-out", out]
        argv += (["--requests", str(count)] if args.mode == "latency"
                 else ["--num-requests", str(count)])
        env = {**os.environ, "CUDA_VISIBLE_DEVICES": devices}
        procs.append(subprocess.Popen(argv, env=env))
    failures = [p.wait() for p in procs]
    if any(rc != 0 for rc in failures):
        raise RuntimeError(f"pie data-parallel replica failed: {failures}")

    merged: list = []
    wall = 0.0
    for path in outs:
        with open(path) as fh:
            payload = json.load(fh)
        wall = max(wall, float(payload["summary"]["wall_s"]))
        for record in payload["requests"]:
            merged.append(RequestResult(**record))
    summary = summarize(
        mode=args.mode,
        engine="pie",
        model=args.model,
        results=merged,
        wall_s=wall,
        config={
            "data_parallel_size": args.dp_size,
            "tensor_parallel_size": args.tp_size,
            "dp_replica_requests": per,
            "max_tokens": args.max_tokens,
        },
    )
    return summary, merged


def refuse_if_a_wedged_pie_is_still_dying() -> None:
    if sys.platform != "darwin":
        return
    if os.environ.get("PIE_BENCH_ALLOW_WEDGED") == "1":
        return
    try:
        out = subprocess.run(["ps", "-eo", "pid,stat,comm"],
                             capture_output=True, text=True, timeout=10).stdout
    except Exception:
        return
    wedged = [line.split()[0] for line in out.splitlines()[1:]
              if "(pie)" in line and "E" in line.split()[1]]
    if wedged:
        raise SystemExit(
            f"pie_bench: refusing to start — {len(wedged)} wedged pie "
            f"process(es) still hold GPU memory: {', '.join(wedged)}.\n"
            "They are blocked in the kernel awaiting GPU work and cannot be "
            "killed; their memory is unreclaimable. Retrying will only add "
            "another. Reboot the machine.")


def _typed_pairs(raw: list[str] | None) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for item in raw or []:
        key, sep, value = item.partition("=")
        if not sep:
            raise SystemExit(f"want KEY=VALUE, got {item!r}")
        if value in ("true", "false"):
            out[key] = value == "true"
        else:
            try:
                out[key] = int(value)
            except ValueError:
                try:
                    out[key] = float(value)
                except ValueError:
                    out[key] = value
    return out


def main() -> None:
    args = build_parser().parse_args()
    args.extra_input = _typed_pairs(getattr(args, "extra_input", None))
    refuse_if_a_wedged_pie_is_still_dying()
    if args.dp_size > 1:
        summary, results = run_data_parallel(args)
    else:
        summary, results = asyncio.run(run(args))
    finish(summary, results, args.json_out)


if __name__ == "__main__":
    main()
