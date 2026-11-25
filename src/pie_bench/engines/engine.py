from __future__ import annotations

import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pie_bench.engines.failures import classify_failure
from pie_bench.engines.processes import jit_jobs, resident_kib, stall_dump, wait_with_stall_check
from pie_bench.engines.shapes import workload_mode_args
from pie_bench.installers.bench_env import bench_dir
from pie_bench.metrics.fairness import COLD_SEED, cold_prompts, cold_request_count
from pie_bench.metrics.perf import all_completed, perf_from_common_json
from pie_bench.schema import (
    ArtifactSpec,
    EngineName,
    ErrorClass,
    Mode,
    PerfMetrics,
    PlatformSpec,
    WorkloadSpec,
)

NO_PEER_SITE = Path(__file__).resolve().parent / "site_hooks" / "no_peer_all_reduce"


class EngineLaunchError(RuntimeError):
    def __init__(self, error_class: ErrorClass, message: str):
        super().__init__(message)
        self.error_class = error_class


@dataclass
class BenchResult:
    perf: PerfMetrics
    summary: dict[str, Any]
    requests: list[dict[str, Any]]
    argv: list[str]
    stdout_tail: str = ""
    stderr_tail: str = ""
    duration_s: float = 0.0
    output_token_ids: list[list[int]] = field(default_factory=list)


class Engine(ABC):
    name: EngineName
    script: str
    env_defaults: dict[str, str] = {}

    def __init__(
        self,
        *,
        pie_root: Path,
        artifact: ArtifactSpec,
        platform: PlatformSpec,
        mode: Mode,
        recipe: dict[str, Any],
        python: str | None = None,
        env: dict[str, str] | None = None,
        num_layers: int | None = None,
    ):
        self.pie_root = Path(pie_root)
        self.artifact = artifact
        self.platform = platform
        self.mode = mode
        self.recipe = recipe
        self.python = python or self.default_python()
        self.env = dict(env or {})
        for k, v in {**self.env_defaults, **self.default_env()}.items():
            self.env.setdefault(k, v)
        self.env.setdefault("PIE_ROOT", str(self.pie_root))
        self.num_layers = num_layers
        self.server_url: str | None = None
        self._server_proc: subprocess.Popen | None = None

    def drop_env(self) -> set[str]:
        return set()

    def process_env(self, *extra: dict[str, str]) -> dict[str, str]:
        drop = self.drop_env()
        env = {k: v for k, v in os.environ.items() if k not in drop}
        env.setdefault("MAX_JOBS", jit_jobs())
        for e in (self.env, *extra):
            env.update(e)
        return env

    def default_env(self) -> dict[str, str]:
        return {}

    def nccl_env(self) -> dict[str, str]:
        if (
            int(self.mode.tp) > 1
            and os.environ.get("RUNPOD_POD_ID")
            and str(getattr(self.platform, "interconnect", "pcie")) not in ("nvlink", "xgmi")
        ):
            return {"NCCL_P2P_DISABLE": "1", "NCCL_IB_DISABLE": "1"}
        return {}

    def no_peer_all_reduce(self) -> bool:
        return (
            int(self.mode.tp) > 1
            and self.platform is not None
            and not getattr(self.platform, "peer_access", True)
        )

    def no_peer_env(self) -> dict[str, str]:
        if not self.no_peer_all_reduce():
            return {}
        existing = self.env.get("PYTHONPATH") or os.environ.get("PYTHONPATH")
        return {
            "PYTHONPATH": os.pathsep.join([str(NO_PEER_SITE)] + ([existing] if existing else [])),
            "PIE_BENCH_NO_CUSTOM_AR": "1",
        }

    @abstractmethod
    def default_python(self) -> str: ...

    @abstractmethod
    def model_arg(self) -> str:
        pass

    @abstractmethod
    def engine_args(self, workload: WorkloadSpec) -> list[str]:
        pass

    def version(self) -> str:
        return "unknown"

    def counters_from_summary(self, summary: dict[str, Any]) -> dict[str, float]:
        return {}

    def resident_gib(self) -> float | None:
        roots = self.watch_pids()
        if not roots:
            return None
        kib = resident_kib(roots)
        return round(kib / 2**20, 2) if kib else None

    def serve(self, workload: WorkloadSpec, log_path: Path, timeout_s: int) -> None:
        return None

    def stop(self) -> None:
        if self._server_proc is not None:
            if sys.platform == "win32":
                subprocess.run(
                    ["taskkill", "/T", "/F", "/PID", str(self._server_proc.pid)],
                    capture_output=True,
                    check=False,
                )
            self._server_proc.terminate()
            try:
                self._server_proc.wait(timeout=60)
            except subprocess.TimeoutExpired:
                self._server_proc.kill()
            self._server_proc = None

    def leftover_process_names(self) -> list[str]:
        return []

    def stall_s(self) -> int:
        return int(self.recipe.get("stall_s") or os.environ.get("PIE_BENCH_STALL_S") or 180)

    def watch_pids(self) -> list[int]:
        return []

    def script_path(self) -> Path:
        return bench_dir() / self.script

    def build_argv(
        self, workload: WorkloadSpec, common_args: list[str], json_out: Path
    ) -> list[str]:
        mode_sub, mode_args = workload_mode_args(workload)
        argv = [self.python, str(self.script_path()), mode_sub]
        argv += ["--model", self.model_arg()]
        argv += mode_args
        argv += common_args
        argv += self.engine_args(workload)
        argv += ["--json-out", str(json_out), "--dump-all-token-ids"]
        return argv

    supports_prompts_file: bool = True
    reports_timing: bool = True

    def cold_common_args(
        self, workload: WorkloadSpec, common_args: list[str], out_dir: Path
    ) -> list[str]:
        from pie_bench.workloads import prompt_words_for_tokens

        if not self.supports_prompts_file:
            raise EngineLaunchError(
                ErrorClass.INCOMPATIBLE,
                f"{self.name.value}: cold-cache runs need --prompts-file in the bench script",
            )
        prefill = int(workload.params.get("prefill", 128))
        body = lambda i: prompt_words_for_tokens(prefill, salt=f"{workload.id}|{i}")
        m = re.fullmatch(r"r(\d+)", out_dir.name)
        seed = COLD_SEED if not m or m.group(1) == "0" else f"{COLD_SEED}|round{m.group(1)}"
        if out_dir.name == "profile":
            seed = f"{COLD_SEED}|profile"
        prompts = cold_prompts(
            body, workload_id=workload.id, seed=seed, count=cold_request_count(workload.params)
        )
        path = out_dir / "cold_prompts.json"
        path.write_text(json.dumps(prompts, ensure_ascii=False))
        return [*common_args, "--prompts-file", str(path.resolve())]

    def run(
        self, workload: WorkloadSpec, common_args: list[str], out_dir: Path, timeout_s: int
    ) -> BenchResult:
        out_dir.mkdir(parents=True, exist_ok=True)
        json_out = out_dir / "bench.json"
        cold_sha = None
        if workload.params.get("cold_cache"):
            common_args = self.cold_common_args(workload, common_args, out_dir)
            cold_sha = hashlib.sha256((out_dir / "cold_prompts.json").read_bytes()).hexdigest()
            (out_dir / "cold_prompts.sha256").write_text(cold_sha + "\n")
        argv = self.build_argv(workload, common_args, json_out)
        env = self.process_env()
        if self.server_url:
            env["PIE_BENCH_SERVER_URL"] = self.server_url
        (out_dir / "argv.txt").write_text(shlex.join(argv) + "\n")
        t0 = time.monotonic()
        with open(out_dir / "stdout.txt", "w") as so, open(out_dir / "stderr.txt", "w") as se:
            proc = subprocess.Popen(
                argv, cwd=str(bench_dir()), env=env, stdout=so, stderr=se, text=True
            )
            rc, timed_out, stalled = wait_with_stall_check(
                proc,
                timeout_s,
                self.stall_s(),
                self.watch_pids,
                on_stall=lambda pids: (out_dir / "stall-dump.txt").write_text(stall_dump(pids)),
            )
        dur = time.monotonic() - t0
        stdout = (out_dir / "stdout.txt").read_text(errors="replace")
        stderr = (out_dir / "stderr.txt").read_text(errors="replace")
        if stalled:
            raise EngineLaunchError(
                ErrorClass.HANG,
                f"no CPU work from the bench or its engine for {self.stall_s()}s; stopped",
            )
        if rc == -6 and not timed_out and json_out.exists() and all_completed(json_out):
            rc = 0
        if rc != 0 or not json_out.exists():
            cls, msg = classify_failure(rc, stderr, stdout, timed_out)
            if rc == 0 and not timed_out:
                lines = [
                    ln.strip()
                    for ln in (stderr + "\n" + stdout).splitlines()
                    if ln.strip() and not set(ln.strip()) <= set("─│╭╮╰╯═║╔╗╚╝ ")
                ]
                msg = (
                    "bench exited 0 without writing bench.json; last output: "
                    + " | ".join(lines[-3:])[:400]
                )
                cls = ErrorClass.HARNESS_INVALID
            raise EngineLaunchError(cls, msg)
        data = json.loads(json_out.read_text())
        summary = data.get("summary", {})
        requests = data.get("requests", [])
        failed = [r for r in requests if not r.get("ok")]
        if requests and len(failed) == len(requests):
            err = next(
                (str(r.get("error") or "") for r in failed if r.get("error")), "(no error text)"
            )
            cls = (
                ErrorClass.HARNESS_INVALID
                if re.search(r"temperature must be|Failed to parse JSON input", err)
                else ErrorClass.INCOMPATIBLE
                if re.search(r"forward-hybrid|not valid on|interface", err)
                else ErrorClass.CRASH
            )
            raise EngineLaunchError(cls, f"all {len(requests)} requests failed: {err[:300]}")
        perf = perf_from_common_json(
            summary,
            requests,
            self.num_layers,
            concurrency=int(workload.params.get("concurrency", 1)),
            cold_tags=bool(workload.params.get("cold_cache")),
        )
        if workload.params.get("primary"):
            perf.primary = str(workload.params["primary"])
        perf.counters.update(self.counters_from_summary(summary))
        perf.resident_gib = self.resident_gib()
        if cold_sha is not None:
            perf.counters["cold_prompts_sha256_48"] = float(int(cold_sha[:12], 16))
        ids = [r.get("output_token_ids") or [] for r in requests]
        return BenchResult(
            perf=perf,
            summary=summary,
            requests=requests,
            argv=argv,
            stdout_tail=stdout[-4000:],
            stderr_tail=stderr[-4000:],
            duration_s=dur,
            output_token_ids=ids,
        )
