"""pie adapter: drives ``bench/pie_bench.py``.

Everything emitted here is a flag ``pie_bench.py`` (or ``bench/common.py``)
parses; knobs the script has no flag for are noted with ``TODO(pie/benches)``
rather than invented. The bench inferlet (``text-completion-bench`` by
default) is pointed at through ``PIE_BENCH_INFERLET_DIR`` and ``--inferlet-dir``.
"""

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

from pie_evals.node.build import bench_dir
from pie_evals.schema import Backend, EngineName, ErrorClass, WorkloadKind, WorkloadSpec

from .base import Engine, EngineLaunchError, classify_failure, register
from .shape import max_model_len_for

#: the sonames pie's loader (cudarc) tries for NCCL: the unversioned dev link
#: and the CUDA-major-numbered ones — never the ``.so.2`` that ``libnccl2``
#: alone installs (nightly 35921789513 lost every tp2 cell on a100-x2 to it).
_NCCL_SONAMES = ("libnccl.so", "libnccl.so.13", "libnccl.so.12", "libnccl.so.11", "libnccl.so.10", "libnccl.so.9", "libnccl.so.1")


def nccl_shim_dir(root: Path | None = None) -> Path | None:
    """A directory holding ``libnccl.so`` -> the installed ``libnccl.so.2``
    when the loader would otherwise find no NCCL; None when NCCL already
    resolves under a name pie tries (or is absent altogether, in which case
    tp>1 cells fail with the real message)."""
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
    from pie_evals.node.baselines import cache_root

    d = cache_root(root) / "lib"
    d.mkdir(parents=True, exist_ok=True)
    link = d / "libnccl.so"
    target = Path(found["libnccl.so.2"])
    if not link.is_symlink() or link.resolve() != target.resolve():
        if link.exists() or link.is_symlink():
            link.unlink()
        link.symlink_to(target)
    return d


#: platform backend -> pie_bench ``--engine``. ``vulkan``/``wgpu`` are the
#: names pie's driver layer uses; pie_bench's argparse ``choices`` currently
#: stops at cuda_native/metal (its own comment: "no build of pie hosts them"),
#: so those two are refused by the script until it grows the choice.
#: TODO(pie/benches): add vulkan / wgpu to pie_bench.py's --engine choices.
_BACKEND_TO_ENGINE: dict[Backend, str] = {
    Backend.CUDA: "cuda_native",
    # the ROCm build is the same engine over HIP (pie's `rocm` feature): same config, `cuda:N` devices
    Backend.ROCM: "cuda_native",
    Backend.METAL: "metal",
    Backend.VULKAN: "vulkan",
    Backend.WGPU: "wgpu",
    # pie_bench.py has no --engine xla; its metal arm boots `pie serve` as a
    # subprocess, and XLA_SHIM (its --pie-bin) turns that config into the XLA engine's
    Backend.XLA: "metal",
}

#: the ``pie`` stand-in for the XLA engine (see scripts/pie_xla.py)
XLA_SHIM = Path(__file__).resolve().parent / "scripts" / "pie_xla.py"

#: a Mac this small gets a smaller forward budget than pie_bench's 10240 (still a whole raw prompt per forward)
SMALL_MAC_GIB = 16
SMALL_MAC_FORWARD_TOKENS = 2048

#: recipe knob -> flag, value passed through as ``str(value)``.
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
    # NOTE: ``--kv-pages`` exists but pie_bench documents it as DEAD for
    # cuda_native (never reaches engine_options); ``total_pages`` is the cap.
)

#: recipe knob -> BooleanOptionalAction flag (True -> --x, False -> --no-x).
_BOOL_OPTIONAL_FLAGS: tuple[tuple[str, str], ...] = (
    ("pretokenized_prompts", "--pretokenized-prompts"),
    ("single_process_batch", "--single-process-batch"),
    ("defer_start", "--defer-start"),
    ("system_speculation", "--system-speculation"),
)

#: recipe knob -> store_true flag.
_STORE_TRUE_FLAGS: tuple[tuple[str, str], ...] = (
    ("host_first_token", "--host-first-token"),
    ("report_arrivals", "--report-arrivals"),
    ("report_wall_clock", "--report-wall-clock"),
)


#: the Metal engine's own ``total_pages`` and ``kv_page_size`` defaults
#: (pie ``MetalEngineOptions``).
METAL_TOTAL_PAGES = 1024
METAL_PAGE_SIZE = 32


def metal_total_pages(pinned: Any, max_model_len: int) -> int | None:
    """``--total-pages`` for a Metal boot: the recipe's cap, raised to hold one
    request at ``max_model_len``. The engine's pool is fixed at boot (1024
    pages, 32k tokens, unless pinned), so lc-32k's 32k prompt + decode was refused
    on every Mac ("allocation of 1027 units can never fit (pool total 1024)")."""
    floor = -(-max_model_len // METAL_PAGE_SIZE)
    base = int(pinned) if pinned is not None else METAL_TOTAL_PAGES
    if base >= floor:
        return pinned
    return floor


def _scalar(v: Any) -> str:
    """Format a value the way pie_bench's ``--engine-option`` parser reads it back."""
    if isinstance(v, bool):
        return "true" if v else "false"
    return str(v)


def _num(cfg: dict[str, Any], *keys: str) -> float | None:
    """First numeric value among ``keys`` in ``cfg`` (labelled or raw status key)."""
    for k in keys:
        v = cfg.get(k)
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            return float(v)
    return None


@register
class PieEngine(Engine):
    name = EngineName.PIE
    script = "pie_bench.py"

    #: path under the pie tree of the bench inferlet project (a built
    #: ``Pie.toml`` + ``target/wasm32-wasip{2,3}/release/*.wasm``).
    DEFAULT_PROGRAM_PATH = "examples/text-completion-bench"

    def __init__(self, *args: Any, program_path: str | None = None, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._program_path = ""
        self.program_path = program_path or self.recipe.get("program_path") or self.DEFAULT_PROGRAM_PATH
        sdk_paths = [
            str(self.pie_root / "python" / "client" / "src"),
            str(self.pie_root / "python" / "server" / "python"),
            # pie moved python/ under packages/ (pie #838)
            str(self.pie_root / "packages" / "python" / "client" / "src"),
            str(self.pie_root / "packages" / "python" / "server" / "python"),
        ]
        existing = self.env.get("PYTHONPATH") or os.environ.get("PYTHONPATH")
        self.env["PYTHONPATH"] = ":".join(sdk_paths + ([existing] if existing else []))
        # where its own peer collectives fail ("peer collectives are off, NCCL carries them"), pie's
        # tensor-parallel ranks talk through NCCL, which hangs on a RunPod PCIe pod as the baselines'
        # did: the L40S x2 sat 20 min at boot on Qwen3.6-27B and gpt-oss-120b (0.5.3-b5)
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

    # ---- program (inferlet) ------------------------------------------------
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

    # ---- contract ----------------------------------------------------------
    def default_python(self) -> str:
        return os.environ.get("PIE_PY") or sys.executable

    def model_arg(self) -> str:
        # pie_bench resolves an HF id through common.resolve_local_model (HF
        # cache, then ~/.pie/programs); a local path is taken as-is.
        # The runner resolves the checkpoint (a miniature lives under a snapshot
        # dir with no refs/main, so an HF id would not find it) and passes the
        # path through the recipe; a bare HF id is the fallback.
        return str(self.recipe.get("snapshot_dir") or self.artifact.base_model)

    def build_argv(self, workload: WorkloadSpec, common_args: list[str], json_out: Path) -> list[str]:
        argv = super().build_argv(workload, common_args, json_out)
        # a row that does not speculate serves the drafter row's target without its head
        # (importer.plain_sku): the drafter deployment taps the trunk and fills the head's kv on
        # every prompt row, a cost no engine without a drafter pays. A CLI engine boots per run,
        # so the model can follow the row; cuda_native serves one boot for every row (serve()).
        plain = self.recipe.get("plain_snapshot_dir")
        if plain and self.pie_engine_name() != "cuda_native" and not self.speculates(workload):
            argv[argv.index("--model") + 1] = str(plain)
        return argv

    def pie_engine_name(self) -> str:
        return _BACKEND_TO_ENGINE[self.platform.backend]

    def _bench_has(self, flag: str) -> bool:
        try:
            return flag in self.script_path().read_text()
        except OSError:
            return False

    def speculates(self, workload: WorkloadSpec) -> bool:
        """Draft-and-verify decode for this row. ``speculation`` in the recipe forces
        it on or off; ``auto`` (the default) speculates single-stream rows only, since
        drafting costs throughput under concurrency. Needs the artifact's drafter row."""
        mode = str(self.recipe.get("speculation", "auto"))
        # a raw shape decodes plain on every engine, whatever the recipe says
        if workload.params.get("speculation") is False:
            return False
        if not (self.artifact.pie_sku and "dflash" in self.artifact.pie_sku):
            return False
        # a speculative shape drafts on every engine that can, whatever the recipe says
        if workload.params.get("speculation") is True:
            return True
        return mode == "on" or (mode != "off" and workload.kind == WorkloadKind.SINGLE_STREAM)

    def engine_args(self, workload: WorkloadSpec) -> list[str]:
        r = self.recipe
        engine = self.pie_engine_name()
        spec = self.speculates(workload)
        inferlet = self.pie_root / "examples/dflash-speculative-bench" if spec else self.inferlet_dir
        self.env["PIE_BENCH_INFERLET_DIR"] = str(inferlet)
        # pie #1099 renamed pie_bench's cuda_native engine to cuda: a newer checkout takes the new name
        cli = "cuda" if engine == "cuda_native" and '"cuda_native"' not in self.script_path().read_text() else engine
        args: list[str] = ["--engine", cli, "--inferlet-dir", str(inferlet)]
        # every engine writes exactly the shape's length: pie through ignore-EOS (the common flag), llama.cpp and
        # Splash through ignore_eos, mlx-lm by blocking its stop tokens; so every decode number covers the same work
        if not spec:
            args += ["--no-system-speculation"]
        elif "dflash2" in (self.artifact.pie_sku or ""):
            # the bench defaults to the v1 head (16-row block, masked last layer); DFlash2 is
            # trained at 8 rows and all-causal, and drafts out of distribution at any other shape.
            args += ["--extra-input", "block=8", "--extra-input", "no_mask=true"]
            if self.artifact.family.endswith("_moe"):
                # a MoE target's verify rows each route their own experts, so, as Splash's verify budget
                # does for MoE targets, each round verifies the rows its draft's confidence pays for
                args += ["--extra-input", "verify_budget=true"]
            else:
                # a dense target's rows share one read of the weights: Splash verifies all 8 rows every
                # round, and pie does the same rather than pricing shorter rounds
                args += ["--extra-input", "verify_rows=8", "--extra-input", "priced=false"]

        if self.platform.backend in (Backend.CUDA, Backend.ROCM):
            tp = max(1, int(self.mode.tp))
            # One device per TP rank. pie_bench's --device is ONE flag holding
            # a comma-separated list (build_config splits on ","); repeating
            # the flag would keep only the last value.
            args += ["--device", ",".join(f"cuda:{i}" for i in range(tp)), "--tp-size", str(tp)]
        elif self.platform.backend == Backend.XLA:
            args += ["--device", str(r.get("device") or "tpu:0")]
            if not r.get("pie_bin"):
                args += ["--pie-bin", str(XLA_SHIM)]
        elif r.get("device"):
            args += ["--device", str(r["device"])]

        args += ["--max-model-len", str(max_model_len_for(workload))]

        # A pie that sizes its pool in bytes (`[model] device_kv_budget`, pie
        # #929) has no page-count key, and its `device_memory_share` holds on
        # every engine; an older one took --total-pages, and a fraction only
        # on cuda_native.
        bytes_pool = self._bench_has("--device-kv-budget")
        gmu = r.get("gpu_mem_util", 0.90)
        if gmu is not None and (engine == "cuda_native" or bytes_pool):
            args += ["--gpu-mem-util", str(gmu)]

        if r.get("report_timing", True):
            args += ["--report-timing"]
        # prefill is measured cold for every engine: a bench that can map in prompt
        # pages an earlier request published runs with that cache off (pie #855 added it)
        if self._bench_has("--no-prefix-cache"):
            args += ["--no-prefix-cache"]

        for knob, flag in _DIRECT_FLAGS:
            v = r.get(knob)
            if knob == "total_pages" and bytes_pool:
                v = None
            elif knob == "total_pages" and self.platform.backend == Backend.METAL:
                v = metal_total_pages(v, max_model_len_for(workload))
            elif knob == "max_forward_tokens" and v is None and self.platform.backend == Backend.METAL and 0 < float(self.platform.memory_gib or 0) <= SMALL_MAC_GIB:
                # pie_bench writes 10240, and the scratch those axes reserve is wired: Qwen3.5-9B's took
                # 5.2 GB on the 16 GB M3 and left no byte for the kv pool (0.5.3-b5, every rerun doesnt_fit)
                v = SMALL_MAC_FORWARD_TOKENS
            elif knob == "max_forward_tokens" and v is None and self.platform.backend == Backend.CUDA and self.artifact.family == "nemotron_h" and 0 < float(self.platform.memory_gib or 0) <= 32:
                # pie_bench's 10240 leaves the Nemotron-3-Super mini 905 MiB for the cache on a 32 GB RTX 5090 (50
                # sequences seat): 2048-token fires lift c256 3.63k -> 3.84k tok/s, pf16-512 15.8k (16.2k before)
                v = 2048
            elif v == "$serve_concurrency":
                from pie_evals.node.engines.shape import workload_concurrency

                v = workload_concurrency(workload)
            elif knob == "max_forward_requests" and v is not None and self.platform.backend == Backend.CUDA:
                # a card's cap holds a wide shape's lanes down; a narrower shape still boots at its own,
                # as vLLM's max_num_seqs is each cell's (Qwen3.8-27B's 384 on b200-x1 booted pf32-512 at 384)
                from pie_evals.node.engines.shape import workload_concurrency

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

        # TODO(pie/benches): the worker takes the quantization SKU as
        # `[model] sku`, but pie_bench.py builds ModelConfig without it and has
        # no --sku flag, so `artifact.pie_sku` cannot be passed today. The
        # recipe's `engine_option` may carry `"$pie_sku"` as a value, which is
        # substituted here - it only helps once the worker accepts such a key
        # under [model.engine.options] (unknown keys refuse to boot).
        for k, v in (r.get("engine_option") or {}).items():
            if v == "$pie_sku":
                if not self.artifact.pie_sku:
                    continue
                v = self.artifact.pie_sku
            args += ["--engine-option", f"{k}={_scalar(v)}"]
        for k, v in (r.get("extra_input") or {}).items():
            args += ["--extra-input", f"{k}={_scalar(v)}"]
        # the processes the engine seats at once where its kv pool holds fewer lanes than the shape offers: the
        # client still holds the shape's requests open, the rest queue for a seat (pie_bench's admission override)
        cap = r.get("admission_cap")
        if cap:
            from pie_evals.node.engines.shape import workload_concurrency

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
        """Engine-internal counters from ``model_status`` as pie_bench labels
        them in ``summary.config`` (raw ``default.*`` keys are accepted too)."""
        cfg = summary.get("config") or {}
        wall_s = summary.get("wall_s")
        out: dict[str, float] = {}

        # launch to the ready banner, as a served engine's load is timed (pie_bench, pie#989);
        # without it the runner's first-round surplus stands in, which on a CLI engine that
        # boots per round is not the load at all
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
                # what a step costs beyond the device: batch build, dispatch,
                # post-dispatch bookkeeping. Only meaningful on profile builds
                # where engine_fire_us is non-zero.
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

    # ---- persistent server (PIE_BENCH_SERVE_ONLY) -------------------------
    def serve(self, workload: WorkloadSpec, log_path: Path, timeout_s: int) -> None:
        """Boot one pie server with this cell's config and keep it for every
        workload that follows (``run`` then connects through
        ``PIE_BENCH_SERVER_URL``).

        pie_bench honours ``PIE_BENCH_SERVE_ONLY`` only on its embedded-python
        path (``cuda_native``); the CLI engines (metal, vulkan) boot ``pie
        serve`` per run, so this is a no-op for them. The serving invocation's
        admission cap comes from ``workload``: pass the widest shape of the
        batch.
        """
        if self.pie_engine_name() != "cuda_native":
            # the CLI engines' bench boots `pie serve` itself and copies its output here
            self.env["PIE_BENCH_SERVER_LOG"] = str(log_path)
            return
        if self._server_proc is not None:
            return
        from pie_evals.node.workloads import common_args_for

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
        # served mode runs the engine in its own process; the bench is only a client
        # that idles on its socket while the engine works, so the stall watchdog must
        # count the server's CPU too (a slow cell was otherwise stopped as a hang)
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
