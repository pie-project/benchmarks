from __future__ import annotations

import collections
import os
import queue
import re
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any

from pie_bench.node.build import bench_dir
from pie_bench.schema import Backend, EngineName, ErrorClass, WorkloadKind, WorkloadSpec

from .base import Engine, EngineLaunchError, classify_failure, register
from .shape import CHAT_TEMPLATE_MARGIN_TOKENS, context_tokens_for, max_model_len_for

_NCCL_SONAMES = ("libnccl.so", "libnccl.so.13", "libnccl.so.12", "libnccl.so.11", "libnccl.so.10", "libnccl.so.9", "libnccl.so.1")


def nccl_shim_dir(root: Path | None = None) -> Path | None:
    if sys.platform != "linux":
        return None
    try:
        out = subprocess.run(["ldconfig", "-p"], capture_output=True, text=True, timeout=30, check=False).stdout
    except OSError:
        return None
    found: dict[str, str] = {}
    for line in out.splitlines():
        if "libnccl" not in line or "=>" not in line:
            continue
        name, _, path = line.strip().partition(" => ")
        found[name.split(" ")[0]] = path.strip()
    if any(n in found for n in _NCCL_SONAMES) or "libnccl.so.2" not in found:
        return None
    from pie_bench.node.baselines import cache_root

    d = cache_root(root) / "lib"
    d.mkdir(parents=True, exist_ok=True)
    link = d / "libnccl.so"
    target = Path(found["libnccl.so.2"])
    if not link.is_symlink() or link.resolve() != target.resolve():
        if link.exists() or link.is_symlink():
            link.unlink()
        link.symlink_to(target)
    return d


_BACKEND_TO_ENGINE: dict[Backend, str] = {
    Backend.CUDA: "cuda_native",
    Backend.ROCM: "cuda_native",
    Backend.METAL: "metal",
    Backend.VULKAN: "vulkan",
    Backend.WGPU: "wgpu",
    Backend.XLA: "metal",
}

XLA_SHIM = Path(__file__).resolve().parent / "scripts" / "pie_xla.py"

SMALL_MAC_GIB = 16
SMALL_MAC_FORWARD_TOKENS = 2048

_DIRECT_FLAGS: tuple[tuple[str, str], ...] = (
    ("total_pages", "--total-pages"),
    ("device_kv_budget", "--device-kv-budget"),
    ("swap_pool_size", "--swap-pool-size"),
    ("frame_size", "--frame-size"),
    ("frame_submit_depth", "--frame-submit-depth"),
    ("frame_dispatch_depth", "--frame-dispatch-depth"),
    ("submit_deadline", "--submit-deadline"),
    ("run_ahead_frames", "--run-ahead-frames"),
    ("max_forward_tokens", "--max-forward-tokens"),
    ("max_forward_requests", "--max-forward-requests"),
    ("worker_threads", "--worker-threads"),
    ("wasm_warm_slots", "--wasm-warm-slots"),
    ("wasm_warm_memory_mb", "--wasm-warm-memory-mb"),
    ("default_token_limit", "--default-token-limit"),
    ("default_endowment_pages", "--default-endowment-pages"),
    ("admission_oversubscription_factor", "--admission-oversubscription-factor"),
    ("device_weight_budget", "--device-weight-budget"),
    ("host_weight_budget", "--host-weight-budget"),
    ("pie_bin", "--pie-bin"),
    ("server_startup_timeout", "--server-startup-timeout"),
    ("cpu_mem_budget", "--cpu-mem-budget"),
    ("cpu_affinity", "--cpu-affinity"),
    ("request_timeout", "--request-timeout"),
    ("wasm_delay_us", "--wasm-delay-us"),
    ("venv", "--venv"),
)

_BOOL_OPTIONAL_FLAGS: tuple[tuple[str, str], ...] = (
    ("pretokenized_prompts", "--pretokenized-prompts"),
    ("single_process_batch", "--single-process-batch"),
    ("defer_start", "--defer-start"),
    ("system_speculation", "--system-speculation"),
)

_STORE_TRUE_FLAGS: tuple[tuple[str, str], ...] = (
    ("host_first_token", "--host-first-token"),
    ("report_arrivals", "--report-arrivals"),
    ("report_wall_clock", "--report-wall-clock"),
)


METAL_TOTAL_PAGES = 1024
METAL_PAGE_SIZE = 32


def metal_total_pages(pinned: Any, max_model_len: int) -> int | None:
    floor = -(-max_model_len // METAL_PAGE_SIZE)
    base = int(pinned) if pinned is not None else METAL_TOTAL_PAGES
    if base >= floor:
        return pinned
    return floor


def _scalar(v: Any) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    return str(v)


def _num(cfg: dict[str, Any], *keys: str) -> float | None:
    for k in keys:
        v = cfg.get(k)
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            return float(v)
    return None


@register
class PieEngine(Engine):
    name = EngineName.PIE
    script = "bench_pie.py"

    DEFAULT_PROGRAM_PATH = "examples/text-completion-bench"

    def __init__(self, *args: Any, program_path: str | None = None, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._program_path = ""
        self.program_path = program_path or self.recipe.get("program_path") or self.DEFAULT_PROGRAM_PATH
        sdk_paths = [
            str(self.pie_root / "python" / "client" / "src"),
            str(self.pie_root / "python" / "server" / "python"),
            str(self.pie_root / "packages" / "python" / "client" / "src"),
            str(self.pie_root / "packages" / "python" / "server" / "python"),
        ]
        existing = self.env.get("PYTHONPATH") or os.environ.get("PYTHONPATH")
        self.env["PYTHONPATH"] = ":".join(sdk_paths + ([existing] if existing else []))
        for k, v in self.nccl_env().items():
            self.env.setdefault(k, v)
        shim = nccl_shim_dir()
        if shim:
            ld = self.env.get("LD_LIBRARY_PATH") or os.environ.get("LD_LIBRARY_PATH")
            self.env["LD_LIBRARY_PATH"] = ":".join([str(shim)] + ([ld] if ld else []))
        self._server_log = None
        if self.platform is not None and self.platform.backend == Backend.XLA:
            self.env["PIE_XLA_REAL_PIE"] = str(self.pie_root / "target" / "release" / "pie")
            try:
                XLA_SHIM.chmod(0o755)
            except OSError:
                pass

    @property
    def program_path(self) -> str:
        return self._program_path

    @program_path.setter
    def program_path(self, value: str) -> None:
        self._program_path = str(value)
        self.env["PIE_BENCH_INFERLET_DIR"] = str(self.inferlet_dir)

    @property
    def inferlet_dir(self) -> Path:
        p = Path(self._program_path)
        return p if p.is_absolute() else self.pie_root / p

    def default_python(self) -> str:
        return os.environ.get("PIE_PY") or sys.executable

    def model_arg(self) -> str:
        return str(self.recipe.get("snapshot_dir") or self.artifact.base_model)

    def build_argv(self, workload: WorkloadSpec, common_args: list[str], json_out: Path) -> list[str]:
        argv = super().build_argv(workload, common_args, json_out)
        plain = self.recipe.get("plain_snapshot_dir")
        if plain and self.pie_engine_name() != "cuda_native" and not self.speculates(workload):
            argv[argv.index("--model") + 1] = str(plain)
        return argv

    def pie_engine_name(self) -> str:
        return _BACKEND_TO_ENGINE[self.platform.backend]

    def _pie_has(self, text: str) -> bool:
        try:
            return text in (self.pie_root / "crates/worker/src/config/backend.rs").read_text()
        except OSError:
            return False

    def _bench_has(self, flag: str) -> bool:
        try:
            return flag in self.script_path().read_text()
        except OSError:
            return False

    def speculates(self, workload: WorkloadSpec) -> bool:
        mode = str(self.recipe.get("speculation", "auto"))
        if workload.params.get("speculation") is False:
            return False
        if not (self.artifact.pie_sku and "dflash" in self.artifact.pie_sku):
            return False
        if workload.params.get("speculation") is True:
            return True
        return mode == "on" or (mode != "off" and workload.kind == WorkloadKind.SINGLE_STREAM)

    def engine_args(self, workload: WorkloadSpec) -> list[str]:
        r = self.recipe
        engine = self.pie_engine_name()
        spec = self.speculates(workload)
        inferlet = self.pie_root / "examples/dflash-speculative-bench" if spec else self.inferlet_dir
        self.env["PIE_BENCH_INFERLET_DIR"] = str(inferlet)
        cli = "cuda" if engine == "cuda_native" and '"cuda_native"' not in self.script_path().read_text() else engine
        args: list[str] = ["--engine", cli, "--inferlet-dir", str(inferlet)]
        if not spec:
            args += ["--no-system-speculation"]
        elif "dflash2" in (self.artifact.pie_sku or ""):
            args += ["--extra-input", "block=8", "--extra-input", "no_mask=true"]
            if self.artifact.family.endswith("_moe"):
                args += ["--extra-input", "verify_budget=true"]
            else:
                args += ["--extra-input", "verify_rows=8", "--extra-input", "priced=false"]

        if self.platform.backend in (Backend.CUDA, Backend.ROCM):
            tp = max(1, int(self.mode.tp))
            args += ["--device", ",".join(f"cuda:{i}" for i in range(tp)), "--tp-size", str(tp)]
        elif self.platform.backend == Backend.XLA:
            args += ["--device", str(r.get("device") or "tpu:0")]
            if not r.get("pie_bin"):
                args += ["--pie-bin", str(XLA_SHIM)]
        elif r.get("device"):
            args += ["--device", str(r["device"])]

        args += ["--max-model-len", str(max_model_len_for(workload))]
        if self.platform.backend == Backend.XLA and self._pie_has("pub seat_tokens"):
            args += ["--engine-option", f"seat_tokens={context_tokens_for(workload) + CHAT_TEMPLATE_MARGIN_TOKENS}"]

        bytes_pool = self._bench_has("--device-kv-budget")
        gmu = r.get("gpu_mem_util", 0.90)
        if gmu is not None and (engine == "cuda_native" or bytes_pool):
            args += ["--gpu-mem-util", str(gmu)]

        if r.get("report_timing", True):
            args += ["--report-timing"]
        if self._bench_has("--no-prefix-cache"):
            args += ["--no-prefix-cache"]

        for knob, flag in _DIRECT_FLAGS:
            v = r.get(knob)
            if knob == "total_pages" and bytes_pool:
                v = None
            elif knob == "total_pages" and self.platform.backend == Backend.METAL:
                v = metal_total_pages(v, max_model_len_for(workload))
            elif knob == "max_forward_tokens" and v is None and self.platform.backend == Backend.METAL and 0 < float(self.platform.memory_gib or 0) <= SMALL_MAC_GIB:
                v = SMALL_MAC_FORWARD_TOKENS
            elif knob == "max_forward_tokens" and v is None and self.platform.backend == Backend.CUDA and self.artifact.family == "nemotron_h" and 0 < float(self.platform.memory_gib or 0) <= 32:
                v = 2048
            elif v == "$serve_concurrency":
                from pie_bench.node.engines.shape import workload_concurrency

                v = workload_concurrency(workload)
            elif knob == "max_forward_requests" and v is not None and self.platform.backend == Backend.CUDA:
                from pie_bench.node.engines.shape import workload_concurrency

                v = min(int(v), workload_concurrency(workload))
            if v is not None:
                args += [flag, str(v)]
        for knob, flag in _BOOL_OPTIONAL_FLAGS:
            v = r.get(knob)
            if v is True:
                args.append(flag)
            elif v is False:
                args.append("--no-" + flag[2:])
        for knob, flag in _STORE_TRUE_FLAGS:
            if r.get(knob):
                args.append(flag)

        for k, v in (r.get("engine_option") or {}).items():
            if v == "$pie_sku":
                if not self.artifact.pie_sku:
                    continue
                v = self.artifact.pie_sku
            args += ["--engine-option", f"{k}={_scalar(v)}"]
        for k, v in (r.get("extra_input") or {}).items():
            args += ["--extra-input", f"{k}={_scalar(v)}"]
        cap = r.get("admission_cap")
        if cap:
            from pie_bench.node.engines.shape import workload_concurrency

            if (workload_concurrency(workload) or 1) > int(cap):
                self.env["PIE_BENCH_ADMISSION_CAP"] = str(int(cap))
            else:
                self.env.pop("PIE_BENCH_ADMISSION_CAP", None)
        return args

    def version(self) -> str:
        try:
            out = subprocess.run(
                ["git", "-C", str(self.pie_root), "rev-parse", "--short", "HEAD"],
                capture_output=True, text=True, timeout=10, check=True,
            ).stdout.strip()
            return out or "unknown"
        except Exception:
            return "unknown"

    def counters_from_summary(self, summary: dict[str, Any]) -> dict[str, float]:
        cfg = summary.get("config") or {}
        wall_s = summary.get("wall_s")
        out: dict[str, float] = {}

        load = _num(cfg, "server load s")
        if load is not None:
            out["server_load_s"] = load

        batches = _num(cfg, "total batches", "default.total_batches")
        if batches is not None:
            out["batches"] = batches

        idle_us = _num(cfg, "device idle us", "default.fire.quorum.device_idle_us")
        if idle_us is not None:
            out["device_idle_us"] = idle_us
            if isinstance(wall_s, (int, float)) and wall_s > 0:
                out["device_idle_pct"] = 100.0 * idle_us / (float(wall_s) * 1e6)

        cum_batch_us = _num(cfg, "cumulative_batch_latency_us", "default.cumulative_batch_latency_us")
        avg_batch_us = _num(cfg, "avg batch latency us", "default.avg_batch_latency_us")
        if avg_batch_us is None and cum_batch_us is not None and batches:
            avg_batch_us = cum_batch_us / batches
        if avg_batch_us is not None:
            out["batch_latency_us"] = avg_batch_us
        engine_fire_us = _num(cfg, "fire.execute.engine_fire_us", "default.fire.execute.engine_fire_us")
        if engine_fire_us is None:
            fire_sum = _num(cfg, "default.fire.execute.engine_fire_us_sum")
            if fire_sum is not None and batches:
                engine_fire_us = fire_sum / batches
        if engine_fire_us is not None:
            out["engine_fire_us_per_step"] = engine_fire_us
            if avg_batch_us is not None:
                out["host_us_per_step"] = max(0.0, avg_batch_us - engine_fire_us)

        ta_sum = _num(cfg, "turnaround sum us", "default.fire.quorum.turnaround_sum_us")
        ta_n = _num(cfg, "turnaround n", "default.fire.quorum.turnaround_n")
        if ta_sum is not None and ta_n:
            out["guest_turnaround_us"] = ta_sum / ta_n
        ta_max = _num(cfg, "turnaround max us", "default.fire.quorum.turnaround_max_us")
        if ta_max is not None:
            out["guest_turnaround_max_us"] = ta_max

        for label, key in (
            ("wave_fires", "wave fires"),
            ("wave_avg_active_pipelines", "wave avg active pipelines"),
            ("wave_avg_missing_pipelines", "wave avg missing pipelines"),
            ("max_forward_requests_observed", "max forward requests"),
            ("process_avg_admission_wait_us", "process avg admission wait us"),
            ("process_avg_instantiate_us", "process avg instantiate us"),
        ):
            v = _num(cfg, key)
            if v is not None:
                out[label] = v
        return out

    def leftover_process_names(self) -> list[str]:
        return ["pie"]

    def serve(self, workload: WorkloadSpec, log_path: Path, timeout_s: int) -> None:
        if self.pie_engine_name() != "cuda_native":
            self.env["PIE_BENCH_SERVER_LOG"] = str(log_path)
            return
        if self._server_proc is not None:
            return
        from pie_bench.node.workloads import common_args_for

        log_path = Path(log_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        json_out = log_path.with_suffix(".serve.json")
        argv = self.build_argv(workload, common_args_for(workload), json_out)
        env = {**os.environ, **self.env, "PIE_BENCH_SERVE_ONLY": "1"}
        env.pop("PIE_BENCH_SERVER_URL", None)
        log = log_path.open("w", encoding="utf-8")
        proc = subprocess.Popen(
            argv, cwd=str(bench_dir()), env=env,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1,
        )
        lines: queue.Queue[str | None] = queue.Queue()
        announced = threading.Event()

        def pump() -> None:
            assert proc.stdout is not None
            for line in proc.stdout:
                log.write(line)
                log.flush()
                if not announced.is_set():
                    lines.put(line)
            lines.put(None)

        threading.Thread(target=pump, name="pie-serve-log", daemon=True).start()
        tail: collections.deque[str] = collections.deque(maxlen=200)
        deadline = time.monotonic() + timeout_s
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                self._kill(proc, log)
                raise EngineLaunchError(ErrorClass.HANG, f"pie serve did not announce PIE_BENCH_SERVER_URL within {timeout_s}s")
            try:
                line = lines.get(timeout=min(remaining, 1.0))
            except queue.Empty:
                continue
            if line is None:
                rc = proc.wait()
                log.close()
                cls, msg = classify_failure(rc, "", "".join(tail), False)
                raise EngineLaunchError(cls, f"pie serve exited before ready: {msg}")
            tail.append(line)
            m = re.search(r"PIE_BENCH_SERVER_URL=(\S+)", line)
            if m:
                announced.set()
                self.server_url = m.group(1)
                self._server_proc = proc
                self._server_log = log
                return

    def watch_pids(self) -> list[int]:
        return [self._server_proc.pid] if self._server_proc is not None and self._server_proc.poll() is None else []

    @staticmethod
    def _kill(proc: subprocess.Popen, log: Any) -> None:
        proc.terminate()
        try:
            proc.wait(timeout=30)
        except subprocess.TimeoutExpired:
            proc.kill()
        try:
            log.close()
        except Exception:
            pass

    def stop(self) -> None:
        super().stop()
        self.server_url = None
        if self._server_log is not None:
            try:
                self._server_log.close()
            finally:
                self._server_log = None
