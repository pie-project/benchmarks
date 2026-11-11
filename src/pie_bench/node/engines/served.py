from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
import urllib.request
from abc import abstractmethod
from pathlib import Path
from typing import Any

from pie_bench.node.build import bench_dir
from pie_bench.schema import ErrorClass, WorkloadKind, WorkloadSpec

from .base import Engine, EngineLaunchError
from .shape import max_model_len_for, workload_concurrency

SCRIPT = Path(__file__).resolve().parent / "scripts" / "openai_bench.py"


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


class ServedEngine(Engine):
    script = "openai_bench.py"
    health_path = "/v1/models"
    ignore_eos_field: str | None = None
    exact_length: str | None = None
    chat = False
    token_ids = False
    one_request_server = False

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.load_s: float | None = None
        self.drafting = False
        existing = self.env.get("PYTHONPATH") or os.environ.get("PYTHONPATH")
        self.env["PYTHONPATH"] = ":".join([str(bench_dir())] + ([existing] if existing else []))

    @abstractmethod
    def server_cmd(self, port: int, slots: int, context: int) -> list[str]:
        pass

    def speculates(self, workload: WorkloadSpec) -> bool:
        mode = str(self.recipe.get("speculation", "auto"))
        if workload.params.get("speculation") is False:
            return False
        if not self.artifact.draft_model or type(self).draft_args is ServedEngine.draft_args:
            return False
        if workload.params.get("speculation") is True:
            return True
        return mode == "on" or (mode != "off" and workload.kind == WorkloadKind.SINGLE_STREAM)

    def draft_args(self) -> list[str]:
        return []

    def api_model(self) -> str:
        return ""

    def extra_body(self) -> dict[str, Any]:
        return {}

    def script_path(self) -> Path:
        return SCRIPT

    def default_python(self) -> str:
        if os.environ.get("OPENAI_BENCH_PY"):
            return os.environ["OPENAI_BENCH_PY"]
        from pie_bench.node.build import bench_python

        return str(bench_python())

    def engine_args(self, workload: WorkloadSpec) -> list[str]:
        r = self.recipe
        args = ["--url", self.server_url or "http://127.0.0.1:8000", "--engine-name", str(self.name)]
        if self.api_model():
            args += ["--api-model", self.api_model()]
        if self.chat:
            args.append("--chat")
        elif self.token_ids:
            args.append("--token-ids")
        body = {**self.extra_body(), **(r.get("extra_body") or {})}
        if self.ignore_eos_field:
            body[self.ignore_eos_field] = True
        if self.exact_length == "ignore_eos":
            body["ignore_eos"] = True
        elif self.exact_length == "logit_bias" and (bias := self.stop_token_bias()):
            body["logit_bias"] = bias
        if body:
            args += ["--extra-body", json.dumps(body, sort_keys=True)]
        if r.get("flush_cache") is False:
            args.append("--no-flush-cache")
        if r.get("request_timeout"):
            args += ["--request-timeout", str(r["request_timeout"])]
        if workload.params.get("seed") is not None:
            args += ["--seed", str(workload.params["seed"])]
        return args

    def stop_token_bias(self) -> dict[str, float]:
        from .shape import hf_snapshot_dir

        snap = hf_snapshot_dir(self.artifact.base_model, self.artifact.revision)
        path = Path(snap) / "tokenizer.json" if snap else None
        if not path or not path.exists():
            return {}
        added = json.loads(path.read_text()).get("added_tokens") or []
        return {str(t["id"]): -100.0 for t in added if "id" in t}

    def build_argv(self, workload: WorkloadSpec, common_args: list[str], json_out: Path) -> list[str]:
        argv = [a for a in super().build_argv(workload, common_args, json_out) if a != "--ignore-eos"]
        return argv + (["--ignore-eos"] if self.exact_length else ["--no-ignore-eos"])

    def server_env(self) -> dict[str, str]:
        return {}

    def serve(self, workload: WorkloadSpec, log_path: Path, timeout_s: int) -> None:
        if self._server_proc is not None:
            return
        port = int(self.recipe.get("port") or free_port())
        slots, context = workload_concurrency(workload), max_model_len_for(workload)
        self.drafting = self.speculates(workload)
        cmd = self.server_cmd(port, slots, context) + (self.draft_args() if self.drafting else [])
        log_path = Path(log_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        url = f"http://127.0.0.1:{port}"
        t0 = time.monotonic()
        with open(log_path, "w") as log:
            log.write(" ".join(cmd) + "\n")
            log.flush()
            proc = subprocess.Popen([sys.executable, "-m", "pie_bench.node.engines.lifeline", *cmd],
                                    env=self.process_env(self.server_env()), stdin=subprocess.PIPE, stdout=log, stderr=subprocess.STDOUT)
        self._server_proc = proc
        deadline = t0 + min(timeout_s, int(self.recipe.get("startup_timeout") or timeout_s))
        while time.monotonic() < deadline:
            if proc.poll() is not None:
                self._server_proc = None
                tail = log_path.read_text(errors="replace").strip().splitlines()[-5:]
                raise EngineLaunchError(ErrorClass.LOAD_FAIL, f"{self.name} server exited during startup: " + " | ".join(tail)[:500])
            try:
                with urllib.request.urlopen(url + self.health_path, timeout=5) as resp:
                    resp.read()
                self.server_url, self.load_s = url, time.monotonic() - t0
                return
            except OSError:
                time.sleep(0.05)
        self.stop()
        raise EngineLaunchError(ErrorClass.HANG, f"{self.name} server did not answer {self.health_path} in time (see {log_path})")

    def stop(self) -> None:
        super().stop()
        self.server_url = None

    def watch_pids(self) -> list[int]:
        return [self._server_proc.pid] if self._server_proc is not None else []

    def run(self, workload: WorkloadSpec, common_args: list[str], out_dir: Path, timeout_s: int):
        if self._server_proc is not None and self.drafting != self.speculates(workload):
            raise EngineLaunchError(ErrorClass.HARNESS_INVALID, f"{self.name} server {'drafts' if self.drafting else 'does not draft'} but {workload.id} {'does not speculate' if self.drafting else 'speculates'}")
        return super().run(workload, common_args, out_dir, timeout_s)

    def counters_from_summary(self, summary: dict[str, Any]) -> dict[str, float]:
        out = {"server_load_s": float(self.load_s)} if self.load_s is not None else {}
        if self.drafting:
            out["speculative"] = 1.0
        return out
