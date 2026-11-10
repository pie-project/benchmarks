"""Execute a JobSpec on this machine.

Order of operations, per job:

1. preflight: hardware fingerprint, machine state (thermal/power on macOS,
   GPU drain on Linux), the pie build for the pinned commit.
2. group cells into processes: one model per process; within a process the
   workloads/programs are interleaved (ABBA when repeating), and every cell
   in the group shares the same loaded weights.
3. per cell: run once; consult history (adaptive repetition); confirm if
   outside the band; compute CoV; NOISY if the spread is above policy.
4. accuracy gate (T0) for FULL artifacts whose program has a token-parity
   gate and for which a reference exists; miniature cells are
   SKIPPED_MINIATURE by construction.
5. write ``records.jsonl`` incrementally so a killed job still leaves what
   it finished.

Every failure is classified into ``ErrorClass``; a hang is a timeout.
"""

from __future__ import annotations

import os
import random
import re
import signal
import subprocess
import threading
import time
import traceback
import uuid
from datetime import datetime, timezone
from pathlib import Path

from pie_evals.node.build import bench_dir
from pie_evals.schema import (
    AccuracyMetrics,
    AccuracyStatus,
    ArtifactKind,
    Backend,
    Cell,
    CellStatus,
    ErrorClass,
    JobSpec,
    PerfMetrics,
    Record,
    Tier,
)

from . import preflight as pf
from . import profile
from . import provenance as prov
from .engines import EngineLaunchError, get_engine
from .engines.base import workload_mode_args
from .engines.recipes import load_recipe
from .engines.shape import (
    context_tokens_for,
    max_model_len_for,
    serve_envelope,
    workload_concurrency,
)
from .metrics.stats import cov, decide_repetition, median
from .validate import expected_requests, round_problem
from .workloads import common_args_for

# the long-context shapes (lc-8k, lc-32k) size the server's arena and KV rows; when
# that envelope does not fit the card the short shapes still can (gemma-4-26b on a 4090)
SHORT_CONTEXT_TOKENS = 8192
MEMORY_BOUND_MARKS = ("device memory exhausted", "weight residency", "does not hold this deployment", "bytes of elastic device memory")


HEAVY_FRACTION = 0.35  # weights past this share of the card: the 32k envelope leaves the pool a seat or two


def split_heavy_processes(groups: dict[tuple, list]) -> dict[tuple, list]:
    """One boot per model serves every cell at the envelope of the longest shape.
    On a card the weights nearly fill, that envelope starves the concurrency
    cells: Qwen3.6-27B (14 GiB) on the RTX 5090 booted for lc-32k got a pool of
    "1 sequences at the declared context", c64 ran serially (p50 latency 152 s)
    and every request timed out (nightly 36081616837 s13). A heavy model boots
    twice instead: the shapes under ``SHORT_CONTEXT_TOKENS`` on their own
    envelope, then the long ones. Light models keep the single boot."""
    out: dict[tuple, list] = {}
    for key, cells in groups.items():
        first = cells[0]
        per_gpu = float(first.platform.memory_gib or 0) * max(1, int(first.mode.tp))
        heavy = per_gpu > 0 and float(first.artifact.expected_gib or 0) / per_gpu > HEAVY_FRACTION
        short = [c for c in cells if context_tokens_for(c.workload) <= SHORT_CONTEXT_TOKENS]
        if not heavy or not short or len(short) == len(cells):
            out[key] = cells
            continue
        engine, artifact, mode = key
        out[(engine, artifact, f"{mode}-short")] = short
        out[(engine, artifact, f"{mode}-long")] = [c for c in cells if c not in short]
    return out


def split_draft_processes(groups: dict[tuple, list]) -> dict[tuple, list]:
    """A served baseline whose artifact names a ``draft_model`` drafts on the rows pie
    speculates (single stream) and decodes plain on the rest. Its server is booted once
    per process with or without the draft, so the single-stream cells get a process of
    their own: drafting must not reach a throughput row, nor a plain server a drafting row."""
    from .engines.served import ServedEngine

    out: dict[tuple, list] = {}
    for key, cells in groups.items():
        engine, artifact, mode = key
        cls = get_engine(cells[0].engine, str(cells[0].platform.backend))
        drafts = cells[0].artifact.draft_model and issubclass(cls, ServedEngine) and cls.draft_args is not ServedEngine.draft_args
        spec = [c for c in cells if c.workload.kind.value == "single_stream"] if drafts else []
        if not spec or len(spec) == len(cells):
            out[key] = cells
            continue
        out[key] = [c for c in cells if c not in spec]
        out[(engine, artifact, f"{mode}-draft")] = spec
    return out


def split_startups(groups: dict[tuple, list]) -> dict[tuple, list]:
    """pie's CUDA server boots once per process, for the widest of its cells, while vLLM and SGLang
    start each cell at its own concurrency: MiniMax-M3.1-Flash mini60's c64 ran on a 1024-lane pie
    server beside c1024 on an H100 and lost to vLLM's 64-sequence one. Each pie process is split by
    its cells' own concurrency and context, so every cell runs on a server started for its shape.
    A served engine with ``one_request_server`` set (llama.cpp, vllm-metal) gives its one-request cells a
    server of one slot, as vLLM and SGLang run them at max_num_seqs=1: llama-server booted for 32 slots
    stops skipping Gemma 4's KV-shared layers on a prompt and prefilled E2B/E4B about 2.75x slower."""
    out: dict[tuple, list] = {}
    for key, cells in groups.items():
        engine, artifact, mode = key
        one = [c for c in cells if workload_concurrency(c.workload) == 1]
        if getattr(get_engine(cells[0].engine, str(cells[0].platform.backend)), "one_request_server", False) and 0 < len(one) < len(cells):
            out[(engine, artifact, f"{mode}@c1")] = one  # first: a control A/A runs before the rows it vouches for
            out[key] = [c for c in cells if c not in one]
            continue
        if str(engine) != "pie" or cells[0].platform.backend not in (Backend.CUDA, Backend.ROCM):
            out[key] = cells
            continue
        shapes: dict[tuple[int, int], list] = {}
        for c in cells:
            shapes.setdefault((workload_concurrency(c.workload), max_model_len_for(c.workload)), []).append(c)
        if len(shapes) == 1:
            out[key] = cells
            continue
        for (conc, ctx), sub in sorted(shapes.items()):
            out[(engine, artifact, f"{mode}@c{conc}x{ctx}")] = sub
    return out


def recipe_for_cell(recipe: dict, recipe_name: str, cell: Cell) -> dict:
    """The process's recipe resolved for ``cell``'s own shape. Until nightly
    36099862659 the recipe was resolved once, for the process's first cell:
    SGLang then captured graphs to that cell's concurrency (32) and ran every
    wider shape eager, and vLLM's prefix cache followed the first shape. The
    keys the boot added (snapshot_dir, pin, program_path) are kept."""
    fresh = load_recipe(str(cell.engine), recipe_name, cell.platform, cell.workload, family=cell.artifact.family, artifact=cell.artifact.id)
    for k, v in recipe.items():
        if isinstance(fresh.get(k), str) and fresh[k].startswith("$serve_"):
            fresh[k] = v
        fresh.setdefault(k, v)
    return fresh


def cell_priority(cell) -> tuple[int, float]:
    """Order of the cells one engine process serves: the control A/A first (if the
    harness cannot agree with itself nothing else is read), then the cheap shapes
    before the heavy ones. A 27B on the H100 spent 15 and 19 min on c256 and
    kv-oversub (estimated 3 each) and the soft budget then dropped its
    single-stream and long-context cells, the numbers a row is read for (nightly
    36081635037 s20). The sort is stable, so the interleave shuffle survives
    within one estimate tier."""
    return (0 if cell.workload.kind.value == "control_aa" else 1, float(cell.workload.est_minutes))



def import_reason(e: Exception) -> str:
    """The line of a failed `pie model import` that says why: pie marks it `✗`, and the
    line after it is a generic hint that alone names no cause."""
    lines = [ln.strip() for ln in str(e).strip().splitlines() if ln.strip()]
    marked = [ln for ln in lines if ln.startswith("✗")]
    return marked[-1] if marked else (lines[-1] if lines else "")

class NodeRunner:
    def __init__(self, job: JobSpec, *, pie_root: Path, out_dir: Path, hf_cache: Path | None = None, runner_name: str | None = None, build: bool = True, download: bool = False):
        self.job = job
        # a pod without the shared volume never saw `prepare`: it must fetch for itself
        self.download = download or not os.environ.get("PIE_EVALS_VOLUME", "") and bool(os.environ.get("RUNPOD_POD_ID"))
        self.pie_root = Path(pie_root).resolve()
        # absolute: cell output paths are handed to bench subprocesses that run
        # with their own cwd (bench/), and a relative --out made them
        # write bench.json somewhere the runner never looked
        self.out = Path(out_dir).resolve()
        self.out.mkdir(parents=True, exist_ok=True)
        self.hf_cache = Path(hf_cache or os.environ.get("HF_HUB_CACHE") or Path.home() / ".cache/huggingface/hub")
        self.runner_name = runner_name or os.environ.get("RUNNER_NAME") or os.uname().nodename
        self.run_id = f"{job.job_id}-{uuid.uuid4().hex[:6]}"
        self.records_path = self.out / "records.jsonl"
        self.build = build
        self.platform = job.cells[0].platform if job.cells else None
        self._log = open(self.out / "runner.log", "a")
        (self.out / "run_id.txt").write_text(self.run_id + "\n")
        self.t_start = time.monotonic()
        self._killed = threading.Event()
        self._done: set[str] = set()
        self._t0_pending: dict[str, tuple] = {}
        self._last_state: dict = {}
        self._start_watchdog()

    # ------------------------------------------------------------------ time policy
    def elapsed_s(self) -> float:
        return time.monotonic() - self.t_start

    def over_budget(self) -> bool:
        """Soft budget: no new cell starts after ``job.budget_s``."""
        return self.elapsed_s() >= self.job.budget_s

    def remaining_to_kill_s(self) -> float:
        return max(1.0, self.job.kill_s - self.elapsed_s())

    def cell_timeout_s(self, cell: Cell) -> int:
        """A round may take at most ten times the workload's estimate (floor
        ten minutes), under the job-wide cap and the kill deadline. Nightly
        35959142812 lost a whole 60-minute shard to one hung 30-second cell
        (pie #649): the flat 5400 s cap let it run to the client's timeout."""
        # an XLA round includes the compile: vLLM's TPU build spent the whole 600 s on gemma-4-12B (b5 39575054600)
        floor = 1800.0 if self.platform is not None and str(getattr(self.platform.backend, "value", self.platform.backend)) == "xla" else 600.0
        # a baseline boots its server inside the cell: a checkpoint of hundreds of GiB loads, compiles and captures
        # for longer than ten minutes (vLLM on MiMo-V2.6-Flash, 166 GiB on two H200s: still loading at 600 s)
        gib = float(getattr(getattr(cell, "artifact", None), "expected_gib", None) or 0)
        # SGLang on a B200 autotunes its MXFP8 GEMMs and captures 74 prefill shapes before it serves:
        # MiniMax-M3.1-Flash's miniature took past ten minutes to boot
        if str(getattr(cell, "engine", "")) in ("sglang", "vllm", "trtllm"):
            floor = max(floor, 1200.0)
        # pie on a TPU boots its server inside the cell (pie_bench) and compiles its batch shapes there first: the
        # ladder's wait (recipes/pie.yaml server_startup_timeout, 2400 s) and the round after it
        if floor >= 1800.0 and str(getattr(cell, "engine", "")) == "pie":
            floor = max(floor, 3600.0)
        if gib >= 100:
            floor = max(floor, 600.0 + gib * 6.0)
        scaled = max(floor, float(cell.workload.est_minutes) * 60.0 * 10.0, float(cell.workload.params.get("round_timeout_s") or 0))
        cap = max(self.job.per_cell_timeout_s, int(cell.workload.params.get("round_timeout_s") or 0))
        return int(min(cap, scaled, self.remaining_to_kill_s()))

    def _start_watchdog(self) -> None:
        """Hard deadline: at ``job.kill_s`` (= budget × kill_factor) kill every
        child in our process group and exit. The workflow's timeout-minutes
        and the pod's self-destruct are the two outer layers of the same
        limit; this is the one that leaves a record behind."""

        def _fire() -> None:
            self._killed.set()
            try:
                self.log(f"WATCHDOG: hard deadline {self.job.kill_s}s reached; killing children and exiting")
                self._emit_unreached("hard deadline reached (job.kill_s); force-killed")
                self._log.flush()
            finally:
                # kill children (not ourselves first): every subprocess we spawned shares our pgid
                try:
                    os.killpg(os.getpgrp(), signal.SIGTERM)
                    time.sleep(3)
                    os.killpg(os.getpgrp(), signal.SIGKILL)
                except OSError:
                    pass
                os._exit(124)

        t = threading.Timer(self.job.kill_s, _fire)
        t.daemon = True
        t.start()
        self._watchdog = t

    def _emit_unreached(self, reason: str) -> None:
        """Record every cell that has not been reached as NOT_RUN with the
        reason. Called once by the runner when the soft budget stops it, or by
        the watchdog. Idempotent per cell via ``_done``."""
        for c in self.job.cells:
            if c.cell_id in self._done:
                continue
            self._done.add(c.cell_id)
            self.emit(self._not_run(c, reason))

    # ------------------------------------------------------------------ logging
    def log(self, msg: str) -> None:
        line = f"[{datetime.now(timezone.utc).isoformat(timespec='seconds')}] {msg}"
        print(line, flush=True)
        self._log.write(line + "\n")
        self._log.flush()

    def emit(self, rec: Record) -> None:
        with open(self.records_path, "a") as f:
            f.write(rec.model_dump_json() + "\n")

    # ------------------------------------------------------------------ setup
    def ensure_pie(self) -> None:
        """Pin the checkout to the job's commit and put the build artifacts in
        place: cache hit → restore; miss → build here (pod-local cargo target)
        and cache. The tier workflow runs a build job before the fan-out so
        bench pods normally hit the cache."""
        if not self.job.pie_commit:
            return
        from . import build as pb

        mirror = Path(os.environ["PIE_MIRROR"]) if os.environ.get("PIE_MIRROR") else None
        if not self.build:
            # --no-build: use the tree as it is; only pin it if it is a real checkout
            if (self.pie_root / ".git").exists():
                pb.ensure_checkout(self.pie_root, self.job.pie_commit, mirror=mirror)
            else:
                self.log(f"--no-build and {self.pie_root} is not a git checkout; using it as-is")
            return
        pb.ensure_checkout(self.pie_root, self.job.pie_commit, mirror=mirror)
        pb.ensure(self.pie_root, self.job.pie_commit, self.job.pie_build_features,
                  target_dir=Path(os.environ["CARGO_TARGET_DIR"]) if os.environ.get("CARGO_TARGET_DIR") else None,
                  python=os.environ.get("PIE_PY", "python3"), log=self.log)
        self.log(f"pie interpreter for the bench: {os.environ.get('PIE_PY', 'python3')}")

    def snapshot_dir(self, cell: Cell) -> Path:
        from .importer import have_artifacts, needs_import
        from .snapshots import ensure_snapshot, snapshot_dir_if_present

        try:
            py = os.environ.get("PIE_PY")
            if not py:
                from .build import bench_python

                py = str(bench_python(log=self.log))
            # a download mid-shard can outgrow what the job-start reclaim left (l40s nightly 36329832366: ENOSPC)
            from .reclaim import LOW_WATER_GIB, reclaim

            importing = str(cell.engine) == "pie" and self.job.pie_commit and needs_import(cell.artifact)
            # a pie import (also every tp>1 one, run()) writes its artifact beside the checkpoint (pro6000-x4 weekly 39867658406: MiMo ENOSPC mid-import)
            stamps = str(cell.engine) == "pie" and self.job.pie_commit and (importing or int(cell.mode.tp) > 1 or cell.platform.backend == Backend.XLA)
            reclaim(getattr(self, "_ahead", None) or self.job, self.hf_cache, low_water_gib=max(LOW_WATER_GIB, float(cell.artifact.expected_gib or 0) * (2.2 if stamps and not have_artifacts(cell.artifact, self.job.pie_commit) else 1.2) + 10), log=self.log)
            if importing and have_artifacts(cell.artifact, self.job.pie_commit):
                snap = snapshot_dir_if_present(cell.artifact, self.hf_cache, weights=False)
                if snap:
                    return snap
            pending = getattr(self, "_prefetch", {}).get(cell.artifact.id)
            if pending is not None:
                pending.result()
            return ensure_snapshot(cell.artifact, self.hf_cache, pie_root=self.pie_root, python=py, download=self.download, log=self.log)
        except EngineLaunchError:
            raise
        except Exception as e:  # download / shrink failure: the model, not the harness
            from huggingface_hub.errors import LocalEntryNotFoundError

            # the hub unreachable from this pod, or a full disk, says nothing of the model: a re-dispatch measures it
            unreachable = isinstance(e, (LocalEntryNotFoundError, ConnectionError, TimeoutError)) or type(e).__module__.split(".")[0] in ("requests", "httpx", "urllib3") or (isinstance(e, OSError) and e.errno == 28) or "hf_xet" in str(e)
            raise EngineLaunchError(ErrorClass.HARNESS_INVALID if unreachable else ErrorClass.LOAD_FAIL, f"checkpoint unavailable for {cell.artifact.id}: {str(e).strip().splitlines()[-1][:300] if str(e).strip() else e!r}") from e

    def _start_prefetch(self, artifacts) -> None:
        if not self.download:
            return
        from concurrent.futures import ThreadPoolExecutor

        from .importer import have_artifacts, needs_import
        from .snapshots import ensure_snapshot

        pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="prefetch")
        self._prefetch = {}
        for art in {a.id: a for a in artifacts}.values():
            if art.kind == ArtifactKind.MINIATURE:
                continue
            if self.job.pie_commit and needs_import(art) and have_artifacts(art, self.job.pie_commit):
                continue
            def fetch(a=art):
                ensure_snapshot(a, self.hf_cache, download=True, log=lambda m: self.log(f"prefetch: {m}"))
            self._prefetch[art.id] = pool.submit(fetch)
        pool.shutdown(wait=False)

    # ------------------------------------------------------------------ run
    def run(self) -> list[Record]:
        job = self.job
        try:
            os.setpgrp()  # our own process group, so the watchdog's killpg reaches only our children
        except OSError:
            pass
        self.log(f"job {job.job_id} tier={job.tier} platform={job.platform_id} cells={len(job.cells)} run_id={self.run_id}")
        broken = pf.cuda_init() if self.platform is not None and not pf._is_mac(str(self.platform.os)) else None
        if broken:
            self.log(f"GPU preflight failed: {broken}; this pod cannot reach the driver, so no cell is attempted")
            for c in job.cells:
                self.emit(self._failed(c, ErrorClass.HARNESS_INVALID, f"GPU preflight: {broken}", None))
            return []
        if self.platform is not None and str(self.platform.backend) == "cuda" and os.geteuid() == 0:
            from .baselines import ensure_cuda_devkit

            ensure_cuda_devkit(log=self.log)  # nvcc + headers + libcudadevrt.a for pie's NVRTC and the baselines' JITs
        try:
            self.ensure_pie()
        except Exception as e:  # a build failure fails every pie cell identically
            self.log(f"pie build failed: {e}")
            for c in job.cells:
                if str(c.engine) == "pie":
                    self.emit(self._failed(c, ErrorClass.LOAD_FAIL, f"pie build failed: {e}", None))
            job = job.model_copy(update={"cells": [c for c in job.cells if str(c.engine) != "pie"]})
        pre = pf.Preflight()
        self._pre = pre
        machine_before = pre.before_job(self.platform.os if self.platform else None)
        self._last_state = machine_before  # failure records carry the state the card was in
        if machine_before.get("gpu_drain_error"):
            # a card that already holds someone else's memory (nightly 35963868578: 5.7 GiB,
            # no process) invalidates every number and refuses the big loads; give the shard back
            self.log(f"GPU not clean at job start: {machine_before['gpu_drain_error']}; no cell is attempted on this pod")
            for c in job.cells:
                self.emit(self._failed(c, ErrorClass.HARNESS_INVALID, f"GPU not clean at job start: {machine_before['gpu_drain_error']}", None))
            return []
        try:
            from .reclaim import reclaim

            reclaim(job, self.hf_cache, log=self.log)  # a pod that hosts a whole queue fills its disk otherwise
        except Exception as e:  # noqa: BLE001 — room-making must never fail the shard
            self.log(f"disk reclaim skipped: {str(e)[:120]}")
        fingerprint = prov.hardware_fingerprint()
        records: list[Record] = []
        groups = split_startups(split_draft_processes(split_heavy_processes(job.cells_by_process())))
        control_failed: set[tuple] = set()  # a process split by shape keeps its control A/A's verdict
        # pie is what we measure: its processes go first, so a job that runs long never drops pie for a competitor
        groups = dict(sorted(groups.items(), key=lambda kv: str(kv[0][0]) != "pie"))
        from .reclaim import cache_root, free_gib

        models = {}
        for cells in groups.values():
            models.setdefault(cells[0].artifact.base_model, float(cells[0].artifact.expected_gib or 0))
        tight = free_gib(cache_root() or self.hf_cache) < sum(models.values()) * 2.5 + 20
        if tight:
            # every checkpoint plus its import outgrows the disk (a 100 GB TPU VM, b5 39547584473: ENOSPC): one
            # model at a time, pie first within it, and what is done is dropped before the next downloads
            order = list(models)
            groups = dict(sorted(groups.items(), key=lambda kv: order.index(kv[1][0].artifact.base_model)))
            self.log(f"{len(groups)} engine processes to run, one model at a time (the disk holds fewer than all {len(models)})")
        else:
            self.log(f"{len(groups)} engine processes to run")
            self._start_prefetch([cells[0].artifact for cells in groups.values()])
        keys = list(groups)
        for gi, (gkey, cells) in enumerate(groups.items()):
            if tight:
                self._ahead = job.model_copy(update={"cells": [c for k in keys[gi:] for c in groups[k]]})
            engine_name, artifact_key, mode_key = gkey
            if self.over_budget():
                self.log(f"soft budget {job.budget_s}s exhausted after {self.elapsed_s():.0f}s; not starting {engine_name} {artifact_key}")
                continue
            self.log(f"--- process {engine_name} {artifact_key} {mode_key} ({len(cells)} cells) t+{self.elapsed_s():.0f}s")
            engine = None
            snapshot = None
            try:
                snapshot = self.snapshot_dir(cells[0])
            except EngineLaunchError as e:
                for c in cells:
                    self.emit(self._failed(c, e.error_class, str(e), fingerprint))
                continue
            except Exception as e:  # nothing about one model may take the job down
                self.log(f"process setup crashed: {e}\n{traceback.format_exc()}")
                for c in cells:
                    self.emit(self._failed(c, ErrorClass.HARNESS_INVALID, f"process setup: {e}", fingerprint))
                continue
            from .miniature import num_layers_of

            num_layers = num_layers_of(snapshot)
            first = cells[0]
            model_path = snapshot
            if str(first.engine) == "pie" and self.job.pie_commit:
                from .importer import ensure_artifact, needs_import

                # tp>1: the ranks band a stamped artifact at load (pie #633); the XLA engine boots from an imported .xla.zt
                if needs_import(first.artifact) or int(first.mode.tp) > 1 or first.platform.backend == Backend.XLA:
                    try:
                        if first.artifact.family == "deepseek_v41" and first.artifact.kind != ArtifactKind.MINIATURE and not (Path(snapshot) / "engram_token_map.safetensors").exists():
                            # pie reads Engram's tokenizer-compressed id map from beside the weights, which the release does not
                            # ship ("this checkpoint carries no `engram.token_map`", h200-x4 weekly 40014471810)
                            self.log(f"engram: writing the token map beside {snapshot}")
                            subprocess.run([os.environ.get("PIE_PY", "python3"), str(bench_dir() / "engram_token_map.py"), str(snapshot)], check=True, timeout=1800)
                        model_path = ensure_artifact(first.artifact, snapshot, self.pie_root / "target/release/pie", self.job.pie_commit, log=self.log)
                    except Exception as e:
                        for c in cells:
                            self.emit(self._failed(c, ErrorClass.LOAD_FAIL, f"artifact import: {import_reason(e)[:900]}", fingerprint))
                        continue
            recipe_name = "competitive" if str(first.engine) != "pie" else "default"
            try:
                pre.between_engines(self.platform.os if self.platform else None, [])
                cls = get_engine(first.engine, str(first.platform.backend))
                recipe = load_recipe(str(first.engine), recipe_name, first.platform, first.workload, family=first.artifact.family, artifact=first.artifact.id)
                recipe["program_path"] = first.program.path
                recipe["snapshot_dir"] = str(model_path)
                if str(first.engine) in self.job.baseline_versions:
                    from .baselines import SPECS, ensure_baseline

                    # a recipe may pin one model to another build of the engine (sglang.yaml: MiniMax-M3 on sglang-jax main)
                    recipe["pin"] = recipe.get("pin") or self.job.baseline_versions[str(first.engine)]
                    if str(first.engine) in SPECS and not os.environ.get({"vllm": "VLLM_PY", "sglang": "SGLANG_PY", "trtllm": "TRTLLM_PY"}.get(str(first.engine), "")):
                        ensure_baseline(str(first.engine), recipe["pin"], backend=str(first.platform.backend), log=self.log)
                engine = cls(pie_root=self.pie_root, artifact=first.artifact, platform=first.platform, mode=first.mode, recipe=recipe, num_layers=num_layers)
                self._plain_deployment(engine, cells, snapshot, model_path, recipe)
                engine_version = engine.version()
                # one boot per model: the bench then attaches to this server for every
                # cell and round instead of reloading the weights each time (gemma-4 E4B
                # spent ~7 min per round loading; the measurement itself takes seconds)
                serve_log = self.out / "serve" / f"{re.sub(r'[^A-Za-z0-9._-]', '_', artifact_key)}-{mode_key}.log"

                try:
                    engine, model_path = self._boot(engine, serve_envelope([c.workload for c in cells]), serve_log, cls=cls, first=first, recipe=recipe, num_layers=num_layers, snapshot=snapshot, model_path=model_path)
                except EngineLaunchError as e:
                    # a cell's own shape can fail where the process's wider one booted: Qwen3.5-9B's pf8-512 on an
                    # RTX 4090 backed an 8-lane pool the card could not hold, and the Nemotron-3 Ultra mini's c16 boot
                    # there reserved no elastic memory for its first fire; such a cell runs at the process's envelope
                    wide = [c.workload for k, cs in groups.items() if k[:2] == (engine_name, artifact_key) and k[2].split("@")[0] == mode_key.split("@")[0] for c in cs]
                    if "@" in mode_key and any(m in str(e) for m in MEMORY_BOUND_MARKS) and len(wide) > len(cells):
                        self.log("engine boot at the cells' own shape failed for memory; retrying at the process's envelope")
                        try:
                            engine.stop()
                        except Exception:
                            pass
                        engine = cls(pie_root=self.pie_root, artifact=first.artifact, platform=first.platform, mode=first.mode, recipe=recipe, num_layers=num_layers)
                        engine, model_path = self._boot(engine, serve_envelope(wide), serve_log, cls=cls, first=first, recipe=recipe, num_layers=num_layers, snapshot=snapshot, model_path=model_path)
                    else:
                        # a 32k envelope does not fit a 24 GB card beside a 16 GiB model
                        # (nightly 35985312978): give the long shapes up, keep the short ones
                        short = [c for c in cells if context_tokens_for(c.workload) <= SHORT_CONTEXT_TOKENS]
                        if not any(m in str(e) for m in MEMORY_BOUND_MARKS) or not short or len(short) == len(cells):
                            raise
                        self.log(f"engine boot at the full envelope failed for memory; retrying with the shapes under {SHORT_CONTEXT_TOKENS} tokens ({len(short)} of {len(cells)} cells)")
                        for c in cells:
                            if c not in short:
                                self.emit(self._failed(c, e.error_class, f"does not fit beside the short shapes: {e}", fingerprint))
                        try:
                            engine.stop()
                        except Exception:
                            pass
                        engine = cls(pie_root=self.pie_root, artifact=first.artifact, platform=first.platform, mode=first.mode, recipe=recipe, num_layers=num_layers)
                        cells = short
                        engine, model_path = self._boot(engine, serve_envelope([c.workload for c in cells]), serve_log, cls=cls, first=first, recipe=recipe, num_layers=num_layers, snapshot=snapshot, model_path=model_path)
                if getattr(engine, "server_url", None):
                    self.log(f"serving {artifact_key} at {engine.server_url}")
            except EngineLaunchError as e:
                self.log(f"engine boot failed: {e.error_class} {e}")
                for c in cells:
                    self.emit(self._failed(c, e.error_class, str(e), fingerprint))
                if engine:
                    engine.stop()
                continue
            except Exception as e:
                self.log(f"engine setup failed: {e}\n{traceback.format_exc()}")
                for c in cells:
                    self.emit(self._failed(c, ErrorClass.LOAD_FAIL, f"engine setup: {e}", fingerprint))
                continue
            order = list(cells)
            if job.repetition.interleave:
                random.Random(self.run_id).shuffle(order)
            order.sort(key=cell_priority)
            control_ok = (engine_name, artifact_key, mode_key.split("@")[0]) not in control_failed
            model_state = pre.before_model(self.platform) if hasattr(pre, "before_model") else machine_before
            self._last_state = model_state
            for cell in order:
                if cell.cell_id in self._done:
                    continue
                if self.over_budget():
                    self.log(f"soft budget exhausted at t+{self.elapsed_s():.0f}s; remaining cells of this process not started")
                    break
                if not control_ok and job.control_required and not job.control_marks_noisy:
                    rec = self._invalid(cell, "control A/A failed on this process; numbers not read", fingerprint)
                    records.append(rec)
                    self.emit(rec)
                    continue
                if hasattr(engine, "program_path"):
                    engine.program_path = cell.program.path  # the cell's own inferlet, not the process's first
                recipe = recipe_for_cell(engine.recipe, recipe_name, cell)
                engine.recipe = recipe
                state = machine_before
                # every cell starts on a cooled Mac, reruns too: a hot chip from the cell before throttles the next
                # (0.5.3-b2 prefill rerun: the M5 Max 64GB came out lower with the cool-down skipped)
                if hasattr(pre, "settle") and os.environ.get("PIE_EVALS_SETTLE", "1") != "0":
                    settled = pre.settle(self.platform.os if self.platform else None)
                    if settled:
                        self.log(f"{cell.workload.id}: settled {settled['settle_s']}s, thermal {settled['thermal_state_before_settle']} -> {settled['thermal_state']}")
                        state = {**machine_before, **settled}
                # one workload per GPU: a cell starts only on an idle GPU, else it is not measured
                if hasattr(pre, "before_cell"):
                    idle = pre.before_cell(self.platform.os if self.platform else None)
                    if idle.get("gpu_busy_error"):
                        rec = self._invalid(cell, idle["gpu_busy_error"], fingerprint)
                        records.append(rec)
                        self._done.add(cell.cell_id)
                        self.emit(rec)
                        continue
                    if idle:
                        self.log(f"{cell.workload.id}: GPU idle after {idle['gpu_idle_wait_s']}s (was {idle['gpu_util_before_cell']}%)")
                        state = {**state, **idle}
                rec = self._run_cell(cell, engine, snapshot, engine_version, recipe, recipe_name, fingerprint, state)
                if not control_ok and rec.status == CellStatus.PASS:
                    # a noisy machine still yields numbers: the row keeps them, marked noisy, as a competitor's noisy row is
                    rec = rec.model_copy(update={"status": CellStatus.NOISY, "invalid_reason": "control A/A failed on this process"})
                if cell.workload.kind.value == "control_aa" and rec.status == CellStatus.NOISY:
                    # a spread a hair past the bound on a freshly booted process withholds every
                    # number of the process (gemma-4-E4B tp2: 5.6 % against 5 %); one more look
                    # before condemning it — a process that really drifts fails twice
                    self.log(f"control A/A noisy ({rec.invalid_reason}); running the control once more")
                    again = self._run_cell(cell, engine, snapshot, engine_version, recipe, recipe_name, fingerprint, machine_before)
                    if again.status == CellStatus.PASS:
                        rec = again
                if cell.workload.kind.value == "control_aa" and rec.status != CellStatus.PASS:
                    control_ok = False
                    control_failed.add((engine_name, artifact_key, mode_key.split("@")[0]))
                    self.log("control A/A failed; remaining cells in this process are " + ("NOISY" if job.control_marks_noisy else "HARNESS_INVALID"))
                records.append(rec)
                self._done.add(cell.cell_id)
                self.emit(rec)
            try:
                if engine:
                    engine.stop()
                    pre.between_engines(self.platform.os if self.platform else None, engine.leftover_process_names())
            except Exception as e:
                self.log(f"teardown: {e}")
            self._judge_t0(records)
            invalid = pre.after_model(self.platform.os if self.platform else None, model_state)
            if invalid:
                self.log(f"model run invalidated: {invalid}")
                for r in [r for r in records if r.cell.artifact.artifact_key == artifact_key and r.status == CellStatus.PASS]:
                    r.status = CellStatus.NOISY
                    r.invalid_reason = "; ".join(invalid)
                    self.emit(r)
                # a GPU that was not ours to begin with (5.7 GB held by a foreign process on a
                # fresh 5090 pod, nightly 35942190398) fails the engine at boot: that is the
                # pod's fault, not the engine's, so the crash is recorded as harness-invalid
                for r in [r for r in records if r.cell.artifact.artifact_key == artifact_key and r.status == CellStatus.FAIL]:
                    r.error_class = ErrorClass.HARNESS_INVALID
                    r.invalid_reason = "; ".join(invalid)
                    self.emit(r)
        self._emit_unreached(f"job budget ({job.budget_s}s) exhausted before this cell was reached" if self.over_budget() else "not reached (earlier failure)")
        self._watchdog.cancel()
        self.log(f"done in {self.elapsed_s():.0f}s (budget {job.budget_s}s, kill {job.kill_s}s)")
        self._log.close()
        return records

    def _plain_deployment(self, engine, cells, snapshot: Path, model_path: Path, recipe: dict) -> None:
        """A drafter row's process serves the rows that do not speculate from the plain
        deployment (importer.plain_sku): the drafter one taps the trunk and fills the head's
        kv on every prompt row, which the engines without a drafter never pay. A failed
        import leaves those rows on the drafter deployment, as before."""
        from .importer import ensure_artifact, plain_sku

        first = cells[0]
        if str(first.engine) != "pie" or not self.job.pie_commit or model_path == snapshot or not plain_sku(first.artifact):
            return
        if not hasattr(engine, "speculates") or all(engine.speculates(c.workload) for c in cells):
            return
        try:
            recipe["plain_snapshot_dir"] = str(ensure_artifact(first.artifact, snapshot, self.pie_root / "target/release/pie", self.job.pie_commit, plain=True, log=self.log))
        except Exception as e:
            self.log(f"plain deployment import failed; rows that do not speculate serve the drafter deployment: {import_reason(e)[:600]}")

    def _boot(self, engine, shape, serve_log: Path, *, cls, first: Cell, recipe: dict, num_layers, snapshot: Path, model_path: Path):
        """Serve ``shape``; a pie checkpoint it refuses to read directly is
        imported as an artifact once and served from there. Returns the
        (possibly rebuilt) engine and the path it serves."""
        try:
            engine.serve(shape, serve_log, int(min(self.job.load_timeout_s, self.remaining_to_kill_s())))
        except EngineLaunchError as e:
            from .importer import RELAYOUT_MARK, ensure_artifact

            if RELAYOUT_MARK not in str(e) or str(first.engine) != "pie" or not self.job.pie_commit or model_path != snapshot:
                raise
            self.log("pie refuses to serve this checkpoint directly; importing it as an artifact and retrying")
            model_path = ensure_artifact(first.artifact, snapshot, self.pie_root / "target/release/pie", self.job.pie_commit, log=self.log)
            recipe["snapshot_dir"] = str(model_path)
            engine = cls(pie_root=self.pie_root, artifact=first.artifact, platform=first.platform, mode=first.mode, recipe=recipe, num_layers=num_layers)
            engine.serve(shape, serve_log, int(min(self.job.load_timeout_s, self.remaining_to_kill_s())))
        sample = profile.start(engine.watch_pids(), self.out / "profile" / f"{first.engine}-{first.artifact.id}.txt")
        if sample is not None:
            self.log(f"sampling {first.engine} {first.artifact.id} (PIE_EVALS_SAMPLE_SECS)")
        return engine, model_path

    # ------------------------------------------------------------------ one cell
    def _noise_bound(self, cell: Cell) -> float:
        policy = self.job.repetition
        tight = policy.cov_noisy_threshold if int(cell.mode.tp) <= 1 else policy.cov_noisy_threshold_concurrent
        return tight if cell.workload.kind.value in ("single_stream", "control_aa", "long_context") else policy.cov_noisy_threshold_concurrent

    def _round(self, cell: Cell, engine, common: list[str], out_dir: Path, first: bool):
        """One measured round. Every round after the first starts on a cooled Mac too: with exact output lengths a
        round is long enough to heat the chip, and the rounds of one cell fell 20-40 % from first to last
        (0.5.3-b3, M5 Max 64GB, Qwen3.8-27B single stream 68.9 -> 41.6 tok/s); the cell's cool-down alone did not hold."""
        pre = getattr(self, "_pre", None)
        if not first and pre is not None and hasattr(pre, "settle") and os.environ.get("PIE_EVALS_SETTLE", "1") != "0":
            settled = pre.settle(self.platform.os if self.platform else None)
            if settled:
                self.log(f"{cell.workload.id}: cooled {settled['settle_s']}s before the next round ({settled['thermal_state_before_settle']} -> {settled['thermal_state']})")
        return engine.run(cell.workload, common, out_dir, self.cell_timeout_s(cell))

    def _run_cell(self, cell: Cell, engine, snapshot: Path, engine_version: str, recipe: dict, recipe_name: str, fingerprint: dict, machine_state: dict) -> Record:
        t0 = time.monotonic()
        cell = cell.model_copy(update={"engine_version": engine_version})
        cell_out = self.out / "cells" / cell.cell_id
        common = common_args_for(cell.workload, warmup=int(cell.workload.params.get("warmup", 2 if self.job.tier in (Tier.SMOKE, Tier.TARGETED) else 3))) + list(cell.program.bench_args)
        policy = self.job.repetition
        # a concurrent shape's round is minutes long (kv-oversub, mixed, c256: 2/3 of a nightly's cell time):
        # two rounds that agree within its bound are the record; a third comes only through confirmation
        need = min(policy.min_rounds, 2) if cell.workload.kind.value not in ("single_stream", "control_aa", "long_context") else policy.min_rounds
        if cell.workload.kind.value == "single_stream" and policy.single_stream_rounds:
            need = max(need, policy.single_stream_rounds)
        rounds: list[float] = []
        results = []
        try:
            for i in range(need):
                res = self._round(cell, engine, common, cell_out / f"r{i}", first=i == 0)
                results.append(res)
                rounds.append(self._primary(res.perf))
            hist = self.job.history.get(cell.cell_id, [])
            if need == 1:
                d = decide_repetition(rounds[0], hist, sigma=policy.history_sigma, confirm_rounds=policy.confirm_rounds)
                self.log(f"{cell.workload.id}/{cell.program.id}: {rounds[0]:.4g} — {d.reason}")
                for _ in range(d.more_rounds):
                    if len(rounds) >= policy.max_rounds:
                        break
                    res = self._round(cell, engine, common, cell_out / f"r{len(rounds)}", first=False)
                    results.append(res)
                    rounds.append(self._primary(res.perf))
            elif cov(rounds) > self._noise_bound(cell):
                # the policy's confirmation rounds: a first round still warming (a fresh pod's
                # autotune, H100 nightly 36212062773: 6344/6981/6903) settles in the next ones
                for _ in range(min(policy.confirm_rounds, policy.max_rounds - len(rounds))):
                    res = self._round(cell, engine, common, cell_out / f"r{len(rounds)}", first=False)
                    results.append(res)
                    rounds.append(self._primary(res.perf))
        except EngineLaunchError as e:
            self.log(f"{cell.workload.id}/{cell.program.id}: {e.error_class} {e}")
            return self._failed(cell, e.error_class, str(e), fingerprint, duration=time.monotonic() - t0)
        except Exception as e:
            self.log(f"{cell.workload.id}/{cell.program.id}: harness exception {e}\n{traceback.format_exc()}")
            return self._failed(cell, ErrorClass.HARNESS_INVALID, f"harness: {e}", fingerprint, duration=time.monotonic() - t0)
        # median of the steady rounds (the last min_rounds) is the record; every round travels with it
        steady = list(range(len(rounds)))[-need:] if need > 1 else list(range(len(rounds)))
        if len(rounds) >= 5:
            # a baseline restarts for every round and each boot settles at its own speed: one slow boot among
            # the last three marked a cell noisy while four of five agreed (b200-x1 vLLM raw 447/429/422/422/360)
            mid = median(rounds)
            far = max(range(len(rounds)), key=lambda i: abs(rounds[i] - mid))
            steady = [i for i in range(len(rounds)) if i != far]
        med_idx = sorted(steady, key=lambda i: rounds[i])[len(steady) // 2]
        perf: PerfMetrics = results[med_idx].perf
        perf.rounds = rounds
        perf.cov = cov([rounds[i] for i in steady])
        # a served engine loads the model when its server starts; otherwise the first round's extra time over the median
        served = (perf.counters or {}).get("server_load_s")
        warm = results[0].duration_s - results[med_idx].duration_s if len(results) > 1 else None
        perf.load_s = served if served is not None else (warm if warm is not None and warm > 0 else None)
        status = CellStatus.PASS
        invalid = None
        # a tensor-parallel process adds collective latency to every step, so its
        # single-stream rounds spread like a concurrent shape's (gemma-4-E4B tp2 on
        # L40S x2: A/A spread 2.1 % against the 2 % bound, every cell withheld)
        tight = policy.cov_noisy_threshold if int(cell.mode.tp) <= 1 else policy.cov_noisy_threshold_concurrent
        thr = self._noise_bound(cell)
        # every round must have finished the requests asked for, on the same prompts; else the median is not this workload
        problem = round_problem(expected_requests(workload_mode_args(cell.workload)[1]), [r.perf for r in results])
        if problem:
            status, invalid = CellStatus.FAIL, problem
        elif len(rounds) >= 2 and perf.cov > thr:
            status, invalid = CellStatus.NOISY, f"cov {perf.cov:.3%} > {thr:.1%}"
        if cell.workload.kind.value == "control_aa" and len(rounds) >= 2:
            spread = abs(rounds[0] - rounds[-1]) / median(rounds)
            if spread > tight:
                status, invalid = CellStatus.NOISY, f"control A/A spread {spread:.3%} > {tight:.1%}"
        accuracy = self._accuracy(cell, engine, snapshot)
        if accuracy.status == AccuracyStatus.FAIL and status == CellStatus.PASS:
            status = CellStatus.FAIL
        provenance = prov.build_provenance(self.pie_root, snapshot, engine_version, recipe, recipe_name, self.runner_name)
        provenance.hardware_fingerprint = fingerprint
        provenance.machine_state = machine_state
        provenance.pie_commit = self.job.pie_commit or provenance.pie_commit
        provenance.pie_build_features = self.job.pie_build_features
        return Record(
            run_id=self.run_id, job_id=self.job.job_id, tier=self.job.tier, cell_id=cell.cell_id, cell_key=cell.cell_key, cell=cell,
            status=status, error_class=ErrorClass.GATE_FAIL if accuracy.status == AccuracyStatus.FAIL else None,
            error_message=None, invalid_reason=invalid, perf=perf, accuracy=accuracy, provenance=provenance,
            duration_s=time.monotonic() - t0,
        )

    @staticmethod
    def _primary(perf: PerfMetrics) -> float:
        v = getattr(perf, perf.primary, None)
        if v is None:
            raise EngineLaunchError(ErrorClass.HARNESS_INVALID, f"no {perf.primary} in bench output")
        return float(v)

    def _accuracy(self, cell: Cell, engine, snapshot: Path) -> AccuracyMetrics:
        """T0 token parity, once per engine process: it is a property of the
        loaded model, not of the workload, so it rides on the ``ss-128-64``
        cell of each process and every other cell of that process is NOT_RUN.
        The engine answers the T0 prompts here; the reference judges them in
        ``_judge_t0`` once the engine is down, so the cell stays NOT_RUN until
        then."""
        from .accuracy.gate import T0Outputs, skip_reason, t0_engine_outputs

        skip = skip_reason(cell)
        if skip is not None:
            return AccuracyMetrics(status=skip)
        if cell.program.accuracy_gate != "token_parity" or cell.workload.id != "ss-128-64":
            return AccuracyMetrics(status=AccuracyStatus.NOT_RUN)
        try:
            from .snapshots import with_tokenizer

            snapshot = with_tokenizer(cell.artifact, snapshot, self.hf_cache, log=self.log)
            outputs = t0_engine_outputs(engine, snapshot, pie_root=self.pie_root,
                                        out_dir=self.out / "cells" / cell.cell_id / "t0", timeout_s=self.job.per_cell_timeout_s)
        except Exception as e:  # a missing reference is not a pie failure
            self.log(f"accuracy gate skipped: {e}")
            return AccuracyMetrics(status=AccuracyStatus.SKIPPED_NO_REFERENCE, detail={"error": str(e)[:300]})
        if not isinstance(outputs, T0Outputs):
            return outputs
        self._t0_pending[cell.cell_id] = (outputs, snapshot)
        return AccuracyMetrics(status=AccuracyStatus.NOT_RUN)

    def _judge_t0(self, records: list[Record]) -> None:
        """Judge the T0 answers this process's engine gave, now that it is down."""
        from .accuracy.gate import t0_judge

        cache = Path(os.environ.get("PIE_EVALS_CACHE", Path.home() / ".cache/pie-evals")) / "refcache"
        pending, self._t0_pending = self._t0_pending, {}
        for rec in [r for r in records if r.cell_id in pending]:
            outputs, snapshot = pending[rec.cell_id]
            try:
                accuracy = t0_judge(outputs, rec.cell, snapshot, self.platform.os, cache_dir=cache)
            except Exception as e:  # a missing reference is not a pie failure
                self.log(f"accuracy gate skipped: {e}")
                accuracy = AccuracyMetrics(status=AccuracyStatus.SKIPPED_NO_REFERENCE, detail={"error": str(e)[:300]})
            rec.accuracy = accuracy
            if accuracy.status == AccuracyStatus.FAIL and rec.status == CellStatus.PASS:
                rec.status = CellStatus.FAIL
                rec.error_class = ErrorClass.GATE_FAIL
            self.emit(rec)

    def _not_run(self, cell: Cell, reason: str) -> Record:
        p = prov.Provenance(runner=self.runner_name, pie_commit=self.job.pie_commit)
        return Record(run_id=self.run_id, job_id=self.job.job_id, tier=self.job.tier, cell_id=cell.cell_id, cell_key=cell.cell_key, cell=cell,
                      status=CellStatus.NOT_RUN, invalid_reason=reason, provenance=p)

    def _failed(self, cell: Cell, cls: ErrorClass, msg: str, fingerprint: dict | None, duration: float | None = None) -> Record:
        self._done.add(cell.cell_id)
        p = prov.Provenance(hardware_fingerprint=fingerprint or {}, runner=self.runner_name, pie_commit=self.job.pie_commit, harness_commit=prov.harness_commit(Path(__file__).resolve().parents[3]))
        p.machine_state = self._last_state  # a boot refusal on a card someone else holds 5 GiB of (nightly 35963868578) reads differently
        return Record(run_id=self.run_id, job_id=self.job.job_id, tier=self.job.tier, cell_id=cell.cell_id, cell_key=cell.cell_key, cell=cell,
                      status=CellStatus.FAIL, error_class=cls, error_message=msg[:1000], provenance=p, duration_s=duration)

    def _invalid(self, cell: Cell, reason: str, fingerprint: dict | None) -> Record:
        r = self._failed(cell, ErrorClass.HARNESS_INVALID, reason, fingerprint)
        r.status = CellStatus.NOISY
        r.invalid_reason = reason
        return r
