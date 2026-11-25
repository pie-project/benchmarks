from __future__ import annotations

import os
import platform
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

from pie_bench.engines import get_engine
from pie_bench.engines.engine import EngineLaunchError
from pie_bench.engines.recipes import load_recipe
from pie_bench.engines.shapes import context_tokens_for, serve_envelope, workload_mode_args
from pie_bench.installers.bench_env import bench_dir
from pie_bench.metrics.stats import cov, decide_repetition, median
from pie_bench.paths import PACKAGE
from pie_bench.runner import process_sampler as profile
from pie_bench.runner.grouping import (
    MEMORY_BOUND_MARKS,
    SHORT_CONTEXT_TOKENS,
    cell_priority,
    split_draft_processes,
    split_heavy_processes,
    split_startups,
)
from pie_bench.runner.round_checks import expected_requests, round_problem
from pie_bench.schema import (
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
from pie_bench.workloads import common_args_for

from . import preflight as pf
from . import provenance as prov


def recipe_for_cell(recipe: dict, recipe_name: str, cell: Cell) -> dict:
    fresh = load_recipe(str(cell.engine), recipe_name, cell.platform, cell.workload, family=cell.artifact.family, artifact=cell.artifact.id)
    for k, v in recipe.items():
        if isinstance(fresh.get(k), str) and fresh[k].startswith("$serve_"):
            fresh[k] = v
        fresh.setdefault(k, v)
    return fresh


def import_reason(e: Exception) -> str:
    lines = [ln.strip() for ln in str(e).strip().splitlines() if ln.strip()]
    marked = [ln for ln in lines if ln.startswith("✗")]
    return marked[-1] if marked else (lines[-1] if lines else "")


class JobRunner:
    def __init__(self, job: JobSpec, *, pie_root: Path, out_dir: Path, hf_cache: Path | None = None, runner_name: str | None = None, build: bool = True, download: bool = False, tracer=None):
        self.job = job
        self.tracer = tracer
        self.download = download or not os.environ.get("PIE_BENCH_VOLUME", "") and bool(os.environ.get("RUNPOD_POD_ID"))
        self.pie_root = Path(pie_root).resolve()
        self.out = Path(out_dir).resolve()
        self.out.mkdir(parents=True, exist_ok=True)
        self.hf_cache = Path(hf_cache or os.environ.get("HF_HUB_CACHE") or Path.home() / ".cache/huggingface/hub")
        self.runner_name = runner_name or os.environ.get("RUNNER_NAME") or platform.node()
        self.run_id = f"{job.job_id}-{uuid.uuid4().hex[:6]}"
        self.records_path = self.out / "records.jsonl"
        self.build = build
        self.platform = job.cells[0].platform if job.cells else None
        self._log = open(self.out / "run.log", "a")
        (self.out / "run_id.txt").write_text(self.run_id + "\n")
        self.t_start = time.monotonic()
        self._killed = threading.Event()
        self._done: set[str] = set()
        self._t0_pending: dict[str, tuple] = {}
        self._last_state: dict = {}
        self._start_watchdog()

    def elapsed_s(self) -> float:
        return time.monotonic() - self.t_start

    def over_budget(self) -> bool:
        return self.elapsed_s() >= self.job.budget_s

    def remaining_to_kill_s(self) -> float:
        return max(1.0, self.job.kill_s - self.elapsed_s())

    def cell_timeout_s(self, cell: Cell) -> int:
        floor = 1800.0 if self.platform is not None and str(getattr(self.platform.backend, "value", self.platform.backend)) == "xla" else 600.0
        gib = float(getattr(getattr(cell, "artifact", None), "expected_gib", None) or 0)
        if str(getattr(cell, "engine", "")) in ("sglang", "vllm", "trtllm"):
            floor = max(floor, 1200.0)
        if floor >= 1800.0 and str(getattr(cell, "engine", "")) == "pie":
            floor = max(floor, 3600.0)
        if gib >= 100:
            floor = max(floor, 600.0 + gib * 6.0)
        scaled = max(floor, float(cell.workload.est_minutes) * 60.0 * 10.0, float(cell.workload.params.get("round_timeout_s") or 0))
        cap = max(self.job.per_cell_timeout_s, int(cell.workload.params.get("round_timeout_s") or 0))
        return int(min(cap, scaled, self.remaining_to_kill_s()))

    def _start_watchdog(self) -> None:

        def _fire() -> None:
            self._killed.set()
            try:
                self.log(f"WATCHDOG: hard deadline {self.job.kill_s}s reached; killing children and exiting")
                self._emit_unreached("hard deadline reached (job.kill_s); force-killed")
                self._log.flush()
            finally:
                try:
                    os.killpg(os.getpgrp(), signal.SIGTERM)
                    time.sleep(3)
                    os.killpg(os.getpgrp(), signal.SIGKILL)
                except (OSError, AttributeError):
                    pass
                os._exit(124)

        t = threading.Timer(self.job.kill_s, _fire)
        t.daemon = True
        t.start()
        self._watchdog = t

    def _emit_unreached(self, reason: str) -> None:
        for c in self.job.cells:
            if c.cell_id in self._done:
                continue
            self._done.add(c.cell_id)
            self.emit(self._not_run(c, reason))

    def log(self, msg: str) -> None:
        line = f"[{datetime.now(timezone.utc).isoformat(timespec='seconds')}] {msg}"
        print(line, flush=True)
        self._log.write(line + "\n")
        self._log.flush()

    def emit(self, rec: Record) -> None:
        with open(self.records_path, "a") as f:
            f.write(rec.model_dump_json() + "\n")

    def ensure_pie(self) -> None:
        if not self.job.pie_commit:
            return
        from pie_bench.installers import pie as pb

        mirror = Path(os.environ["PIE_MIRROR"]) if os.environ.get("PIE_MIRROR") else None
        if not self.build:
            if (self.pie_root / ".git").exists():
                pb.ensure_checkout(self.pie_root, self.job.pie_commit, mirror=mirror)
            else:
                self.log(f"--no-build and {self.pie_root} is not a git checkout; using it as-is")
            return
        pb.ensure_checkout(self.pie_root, self.job.pie_commit, mirror=mirror)
        pb.ensure(self.pie_root, self.job.pie_commit, self.job.pie_build_features,
                  target_dir=Path(os.environ["CARGO_TARGET_DIR"]) if os.environ.get("CARGO_TARGET_DIR") else None, log=self.log)
        self.log(f"pie interpreter for the bench: {os.environ.get('PIE_PY', 'python3')}")

    def snapshot_dir(self, cell: Cell) -> Path:
        from pie_bench.checkpoints.pie_import import have_artifacts, needs_import
        from pie_bench.checkpoints.snapshots import ensure_snapshot, snapshot_dir_if_present

        try:
            py = os.environ.get("PIE_PY")
            if not py:
                from pie_bench.installers.bench_env import bench_python

                py = str(bench_python(log=self.log))
            from pie_bench.runner.disk_space import LOW_WATER_GIB, reclaim

            importing = str(cell.engine) == "pie" and self.job.pie_commit and needs_import(cell.artifact)
            stamps = str(cell.engine) == "pie" and self.job.pie_commit and (importing or int(cell.mode.tp) > 1 or cell.platform.backend == Backend.XLA)
            reclaim(getattr(self, "_ahead", None) or self.job, self.hf_cache, low_water_gib=max(LOW_WATER_GIB, float(cell.artifact.expected_gib or 0) * (2.2 if stamps and not have_artifacts(cell.artifact, self.job.pie_commit) else 1.2) + 10), log=self.log)
            if importing and have_artifacts(cell.artifact, self.job.pie_commit):
                snap = snapshot_dir_if_present(cell.artifact, self.hf_cache, weights=False)
                if snap:
                    return snap
            pending = getattr(self, "_prefetch", {}).get(cell.artifact.id)
            if pending is not None:
                pending.result()
            return ensure_snapshot(cell.artifact, self.hf_cache, python=py, download=self.download, log=self.log)
        except EngineLaunchError:
            raise
        except Exception as e:
            from huggingface_hub.errors import LocalEntryNotFoundError

            unreachable = isinstance(e, (LocalEntryNotFoundError, ConnectionError, TimeoutError)) or type(e).__module__.split(".")[0] in ("requests", "httpx", "urllib3") or (isinstance(e, OSError) and e.errno == 28) or "hf_xet" in str(e)
            raise EngineLaunchError(ErrorClass.HARNESS_INVALID if unreachable else ErrorClass.LOAD_FAIL, f"checkpoint unavailable for {cell.artifact.id}: {str(e).strip().splitlines()[-1][:300] if str(e).strip() else e!r}") from e

    def _start_prefetch(self, artifacts) -> None:
        if not self.download:
            return
        from concurrent.futures import ThreadPoolExecutor

        from pie_bench.checkpoints.pie_import import have_artifacts, needs_import
        from pie_bench.checkpoints.snapshots import ensure_snapshot

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

    def run(self) -> list[Record]:
        job = self.job
        try:
            os.setpgrp()
        except (OSError, AttributeError):
            pass
        self.log(f"job {job.job_id} tier={job.tier} platform={job.platform_id} cells={len(job.cells)} run_id={self.run_id}")
        broken = pf.cuda_init() if self.platform is not None and not pf._is_mac(str(self.platform.os)) else None
        if broken:
            self.log(f"GPU preflight failed: {broken}; this pod cannot reach the driver, so no cell is attempted")
            for c in job.cells:
                self.emit(self._failed(c, ErrorClass.HARNESS_INVALID, f"GPU preflight: {broken}", None))
            return []
        if self.platform is not None and str(self.platform.backend) == "cuda" and hasattr(os, "geteuid") and os.geteuid() == 0:
            from pie_bench.installers.cuda_toolkit import ensure_cuda_devkit

            ensure_cuda_devkit(log=self.log)
        try:
            self.ensure_pie()
        except Exception as e:
            self.log(f"pie build failed: {e}")
            for c in job.cells:
                if str(c.engine) == "pie":
                    self.emit(self._failed(c, ErrorClass.LOAD_FAIL, f"pie build failed: {e}", None))
            job = job.model_copy(update={"cells": [c for c in job.cells if str(c.engine) != "pie"]})
        pre = pf.Preflight()
        self._pre = pre
        machine_before = pre.before_job(self.platform.os if self.platform else None)
        self._last_state = machine_before
        if machine_before.get("gpu_drain_error"):
            self.log(f"GPU not clean at job start: {machine_before['gpu_drain_error']}; no cell is attempted on this pod")
            for c in job.cells:
                self.emit(self._failed(c, ErrorClass.HARNESS_INVALID, f"GPU not clean at job start: {machine_before['gpu_drain_error']}", None))
            return []
        try:
            from pie_bench.runner.disk_space import reclaim

            reclaim(job, self.hf_cache, log=self.log)
        except Exception as e:
            self.log(f"disk reclaim skipped: {str(e)[:120]}")
        fingerprint = prov.hardware_fingerprint()
        records: list[Record] = []
        groups = split_startups(split_draft_processes(split_heavy_processes(job.cells_by_process())))
        control_failed: set[tuple] = set()
        groups = dict(sorted(groups.items(), key=lambda kv: str(kv[0][0]) != "pie"))
        from pie_bench.runner.disk_space import cache_root, free_gib

        models = {}
        for cells in groups.values():
            models.setdefault(cells[0].artifact.base_model, float(cells[0].artifact.expected_gib or 0))
        tight = free_gib(cache_root() or self.hf_cache) < sum(models.values()) * 2.5 + 20
        if tight:
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
            except Exception as e:
                self.log(f"process setup crashed: {e}\n{traceback.format_exc()}")
                for c in cells:
                    self.emit(self._failed(c, ErrorClass.HARNESS_INVALID, f"process setup: {e}", fingerprint))
                continue
            from pie_bench.checkpoints.miniature import num_layers_of

            num_layers = num_layers_of(snapshot)
            first = cells[0]
            model_path = snapshot
            if str(first.engine) == "pie" and self.job.pie_commit:
                from pie_bench.checkpoints.pie_import import ensure_artifact, needs_import

                if needs_import(first.artifact) or int(first.mode.tp) > 1 or first.platform.backend == Backend.XLA:
                    try:
                        if first.artifact.family == "deepseek_v41" and first.artifact.kind != ArtifactKind.MINIATURE and not (Path(snapshot) / "engram_token_map.safetensors").exists():
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
                    from pie_bench.installers.baselines import SPECS, ensure_baseline

                    recipe["pin"] = recipe.get("pin") or self.job.baseline_versions[str(first.engine)]
                    if str(first.engine) in SPECS and not os.environ.get({"vllm": "VLLM_PY", "sglang": "SGLANG_PY", "trtllm": "TRTLLM_PY"}.get(str(first.engine), "")):
                        ensure_baseline(str(first.engine), recipe["pin"], backend=str(first.platform.backend), log=self.log)
                engine = cls(pie_root=self.pie_root, artifact=first.artifact, platform=first.platform, mode=first.mode, recipe=recipe, num_layers=num_layers)
                self._plain_deployment(engine, cells, snapshot, model_path, recipe)
                engine_version = engine.version()
                serve_log = self.out / "serve" / f"{re.sub(r'[^A-Za-z0-9._-]', '_', artifact_key)}-{mode_key}.log"

                try:
                    engine, model_path = self._boot(engine, serve_envelope([c.workload for c in cells]), serve_log, cls=cls, first=first, recipe=recipe, num_layers=num_layers, snapshot=snapshot, model_path=model_path)
                except EngineLaunchError as e:
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
            model_state = machine_before
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
                    engine.program_path = cell.program.path
                recipe = recipe_for_cell(engine.recipe, recipe_name, cell)
                engine.recipe = recipe
                state = machine_before
                if os.environ.get("PIE_BENCH_SETTLE", "1") != "0":
                    settled = pre.settle(self.platform.os if self.platform else None)
                    if settled:
                        self.log(f"{cell.workload.id}: settled {settled['settle_s']}s, thermal {settled['thermal_state_before_settle']} -> {settled['thermal_state']}")
                        state = {**machine_before, **settled}
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
                    rec = rec.model_copy(update={"status": CellStatus.NOISY, "invalid_reason": "control A/A failed on this process"})
                if cell.workload.kind.value == "control_aa" and rec.status == CellStatus.NOISY:
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
        from pie_bench.checkpoints.pie_import import ensure_artifact, plain_sku

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
        try:
            engine.serve(shape, serve_log, int(min(self.job.load_timeout_s, self.remaining_to_kill_s())))
        except EngineLaunchError as e:
            from pie_bench.checkpoints.pie_import import RELAYOUT_MARK, ensure_artifact

            if RELAYOUT_MARK not in str(e) or str(first.engine) != "pie" or not self.job.pie_commit or model_path != snapshot:
                raise
            self.log("pie refuses to serve this checkpoint directly; importing it as an artifact and retrying")
            model_path = ensure_artifact(first.artifact, snapshot, self.pie_root / "target/release/pie", self.job.pie_commit, log=self.log)
            recipe["snapshot_dir"] = str(model_path)
            engine = cls(pie_root=self.pie_root, artifact=first.artifact, platform=first.platform, mode=first.mode, recipe=recipe, num_layers=num_layers)
            engine.serve(shape, serve_log, int(min(self.job.load_timeout_s, self.remaining_to_kill_s())))
        sample = profile.start(engine.watch_pids(), self.out / "profile" / f"{first.engine}-{first.artifact.id}.txt")
        if sample is not None:
            self.log(f"sampling {first.engine} {first.artifact.id} (PIE_BENCH_SAMPLE_SECS)")
        return engine, model_path

    def _noise_bound(self, cell: Cell) -> float:
        policy = self.job.repetition
        tight = policy.cov_noisy_threshold if int(cell.mode.tp) <= 1 else policy.cov_noisy_threshold_concurrent
        return tight if cell.workload.kind.value in ("single_stream", "control_aa", "long_context") else policy.cov_noisy_threshold_concurrent

    def _round(self, cell: Cell, engine, common: list[str], out_dir: Path, first: bool, traced: bool = False):
        if not first and os.environ.get("PIE_BENCH_SETTLE", "1") != "0":
            settled = self._pre.settle(self.platform.os if self.platform else None)
            if settled:
                self.log(f"{cell.workload.id}: cooled {settled['settle_s']}s before the next round ({settled['thermal_state_before_settle']} -> {settled['thermal_state']})")
        if not traced:
            return engine.run(cell.workload, common, out_dir, self.cell_timeout_s(cell))
        with self.tracer.recording(out_dir):
            return engine.run(cell.workload, [*common, "--report-timing"] if engine.reports_timing else common, out_dir, self.cell_timeout_s(cell))

    def _run_cell(self, cell: Cell, engine, snapshot: Path, engine_version: str, recipe: dict, recipe_name: str, fingerprint: dict, machine_state: dict) -> Record:
        t0 = time.monotonic()
        cell = cell.model_copy(update={"engine_version": engine_version})
        cell_out = self.out / "cells" / cell.cell_id
        common = common_args_for(cell.workload, warmup=int(cell.workload.params.get("warmup", 2 if self.job.tier in (Tier.SMOKE, Tier.TARGETED) else 3))) + list(cell.program.bench_args)
        policy = self.job.repetition
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
        if self.tracer is not None and cell.workload.kind.value != "control_aa":
            from pie_bench.profiler.profiled_round import short

            try:
                self._round(cell.model_copy(update={"workload": short(cell.workload)}), engine, common, cell_out / "profile", first=False, traced=True)
            except Exception as e:
                self.log(f"{cell.workload.id}/{cell.program.id}: profiled round failed: {e}")
        steady = list(range(len(rounds)))[-need:] if need > 1 else list(range(len(rounds)))
        if len(rounds) >= 5:
            mid = median(rounds)
            far = max(range(len(rounds)), key=lambda i: abs(rounds[i] - mid))
            steady = [i for i in range(len(rounds)) if i != far]
        med_idx = sorted(steady, key=lambda i: rounds[i])[len(steady) // 2]
        perf: PerfMetrics = results[med_idx].perf
        perf.rounds = rounds
        perf.cov = cov([rounds[i] for i in steady])
        served = (perf.counters or {}).get("server_load_s")
        warm = results[0].duration_s - results[med_idx].duration_s if len(results) > 1 else None
        perf.load_s = served if served is not None else (warm if warm is not None and warm > 0 else None)
        status = CellStatus.PASS
        invalid = None
        tight = policy.cov_noisy_threshold if int(cell.mode.tp) <= 1 else policy.cov_noisy_threshold_concurrent
        thr = self._noise_bound(cell)
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
        from pie_bench.accuracy.gate import T0Outputs, skip_reason, t0_engine_outputs

        skip = skip_reason(cell)
        if skip is not None:
            return AccuracyMetrics(status=skip)
        if cell.program.accuracy_gate != "token_parity" or cell.workload.id != "ss-128-64":
            return AccuracyMetrics(status=AccuracyStatus.NOT_RUN)
        try:
            from pie_bench.checkpoints.snapshots import with_tokenizer

            snapshot = with_tokenizer(cell.artifact, snapshot, self.hf_cache, log=self.log)
            outputs = t0_engine_outputs(engine, snapshot, out_dir=self.out / "cells" / cell.cell_id / "t0", timeout_s=self.job.per_cell_timeout_s)
        except Exception as e:
            self.log(f"accuracy gate skipped: {e}")
            return AccuracyMetrics(status=AccuracyStatus.SKIPPED_NO_REFERENCE, detail={"error": str(e)[:300]})
        if not isinstance(outputs, T0Outputs):
            return outputs
        self._t0_pending[cell.cell_id] = (outputs, snapshot)
        return AccuracyMetrics(status=AccuracyStatus.NOT_RUN)

    def _judge_t0(self, records: list[Record]) -> None:
        from pie_bench.accuracy.gate import t0_judge

        cache = Path(os.environ.get("PIE_BENCH_CACHE", Path.home() / ".cache/pie-bench")) / "refcache"
        pending, self._t0_pending = self._t0_pending, {}
        for rec in [r for r in records if r.cell_id in pending]:
            outputs, snapshot = pending[rec.cell_id]
            try:
                accuracy = t0_judge(outputs, rec.cell, snapshot, self.platform.os, cache_dir=cache)
            except Exception as e:
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
        p = prov.Provenance(hardware_fingerprint=fingerprint or {}, runner=self.runner_name, pie_commit=self.job.pie_commit, harness_commit=prov.harness_commit(PACKAGE))
        p.machine_state = self._last_state
        return Record(run_id=self.run_id, job_id=self.job.job_id, tier=self.job.tier, cell_id=cell.cell_id, cell_key=cell.cell_key, cell=cell,
                      status=CellStatus.FAIL, error_class=cls, error_message=msg[:1000], provenance=p, duration_s=duration)

    def _invalid(self, cell: Cell, reason: str, fingerprint: dict | None) -> Record:
        r = self._failed(cell, ErrorClass.HARNESS_INVALID, reason, fingerprint)
        r.status = CellStatus.NOISY
        r.invalid_reason = reason
        return r
