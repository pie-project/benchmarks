from __future__ import annotations

import hashlib
import importlib
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from pie_bench.node.build import bench_dir
from pie_bench.node.fair import (
    COLD_SEED,
    FAIR_DEFINITION_VERSION,
    cache_verdict,
    cold_prompts,
    cold_request_count,
    fair_prefill_tok_s,
    prefill_mismatch,
)
from pie_bench.schema import (
    ArtifactSpec,
    EngineName,
    ErrorClass,
    Mode,
    PerfMetrics,
    PlatformSpec,
    WorkloadSpec,
)

NO_PEER_SITE = Path(__file__).resolve().parent / "scripts" / "no_peer_site"


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


_ERROR_PATTERNS: list[tuple[ErrorClass, re.Pattern[str]]] = [
    (ErrorClass.OOM, re.compile(r"out of memory|CUDA_ERROR_OUT_OF_MEMORY|OutOfMemoryError|cudaErrorMemoryAllocation|kIOGPUCommandBufferCallbackErrorOutOfMemory|MTLResourceOptions.*failed|insufficient memory", re.I)),
    (ErrorClass.DOESNT_FIT, re.compile(r"does not fit|refus\w+ .*fit|exceeds .*working set|recommendedMaxWorkingSetSize|host fit check", re.I)),
    (ErrorClass.LOAD_FAIL, re.compile(r"failed to load|load plan|missing quant metadata|unknown variant|No such file|safetensors|model import|failed to import|not found in cache|resolve_local_model|matches no SKU|no SKU this build|missing .*\.wasm|in /root/\.pie/models|not in HF cache|pull model manifest|model .* not found", re.I)),
    (ErrorClass.CRASH, re.compile(r"Traceback|panicked at|Segmentation fault|SIGSEGV|SIGABRT|invalid resource handle|invalid argument|NCCL error|cudaGraphInstantiate", re.I)),
]


def classify_failure(returncode: int, stderr: str, stdout: str, timed_out: bool) -> tuple[ErrorClass, str]:
    if timed_out:
        return ErrorClass.HANG, "timed out (hang is only ever observed via timeout)"
    text = stderr + "\n" + stdout
    if "Traceback (most recent call last)" in text:
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        at = next((i for i in reversed(range(len(lines))) if re.match(r"^[A-Za-z_][A-Za-z0-9_.]*(Error|Exception|Exit|Interrupt)\b", lines[i])), len(lines) - 1)
        exc = " | ".join(lines[at:]) or "Traceback"
        told = exc if len(exc) <= 1000 else lines[at][:300] + " | ... " + exc[-690:]
        for cls, pat in _ERROR_PATTERNS[:3]:
            if pat.search(exc):
                return cls, told
        return ErrorClass.CRASH, told
    for cls, pat in _ERROR_PATTERNS:
        m = pat.search(text)
        if m:
            line = next((ln for ln in text.splitlines() if m.group(0) in ln), m.group(0))
            return cls, line.strip()[:400]
    if returncode < 0:
        return ErrorClass.CRASH, f"killed by signal {-returncode}"
    return ErrorClass.CRASH, f"exit {returncode}: " + (stderr.strip().splitlines() or ["(no stderr)"])[-1][:400]


def _all_completed(json_out: Path) -> bool:
    try:
        s = json.loads(json_out.read_text()).get("summary", {})
    except (OSError, ValueError):
        return False
    return bool(s.get("requests")) and s.get("completed") == s.get("requests") and not s.get("failed")


def _pct(values: list[float], q: float) -> float | None:
    if not values:
        return None
    return float(np.percentile(np.asarray(values, dtype=float), q))


COLD_OPENING_TOKENS = 32


def serial_clock(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    timed = [r for r in rows if r.get("client_send_s") is not None and r.get("client_return_s") is not None]
    if len(timed) != len(rows) or len(rows) < 2:
        return rows
    out, prev_return = [], None
    for r in sorted(rows, key=lambda r: r["client_send_s"]):
        start = r["client_send_s"] if prev_return is None else max(r["client_send_s"], prev_return)
        shift = start - r["client_send_s"]
        if shift > 0:
            r = {**r, "ttft_s": r["ttft_s"] - shift if r.get("ttft_s") is not None else None,
                 "latency_s": r["latency_s"] - shift if r.get("latency_s") is not None else None}
        out.append(r)
        prev_return = r["client_return_s"]
    return out


def perf_from_common_json(summary: dict[str, Any], requests: list[dict[str, Any]], num_layers: int | None, concurrency: int | None = None, *, cold_tags: bool = False) -> PerfMetrics:
    completed = [r for r in requests if r.get("ok")]
    if concurrency == 1:
        completed = serial_clock(completed)
    out_tok = int(summary.get("output_tokens") or sum(r.get("output_tokens", 0) for r in completed))
    prompt_tok = int(summary.get("prompt_tokens") or sum(r.get("prompt_tokens", 0) for r in completed))
    wall = float(summary.get("wall_s") or 0.0)
    output_tok_s = float(summary.get("output_tok_per_s") or (out_tok / wall if wall else 0.0))
    ttft = [r["ttft_s"] * 1000.0 for r in completed if r.get("ttft_s") is not None]
    decode_lane = []
    itl_all: list[float] = []
    for r in completed:
        lat = r.get("latency_s")
        tt = r.get("ttft_s")
        n = r.get("output_tokens") or 0
        if lat and tt is not None and n > 1 and lat > tt:
            decode_lane.append((n - 1) / (lat - tt))
            itl_all.append((lat - tt) * 1000.0 / (n - 1))
    counters = {}
    for k, v in (summary.get("config") or {}).items():
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            counters[str(k)] = float(v)
    concurrency = concurrency or int((summary.get("config") or {}).get("concurrency") or 0) or None
    decode_tok_s = float(np.median(decode_lane)) if decode_lane else None
    config_cached = counters.get("cached_prompt_tokens")
    by_construction = config_cached is None and cold_tags
    if by_construction:
        config_cached = 0.0
        counters["cold_by_construction"] = 1.0
    elif cold_tags and config_cached and completed and config_cached / len(completed) <= COLD_OPENING_TOKENS:
        counters["cold_opening_cached_per_request"] = config_cached / len(completed)
        config_cached = 0.0
    verdict = cache_verdict(completed, config_cached)
    prefill_tok_s = fair_prefill_tok_s(completed, concurrency=concurrency, config_cached=config_cached)
    counters["fair_def"] = float(FAIR_DEFINITION_VERSION)
    counters["cold_cache_verified"] = 1.0 if verdict == "cold" else 0.0
    if prefill_tok_s is not None:
        counters["prefill_ttft_mismatch"] = 1.0 if prefill_mismatch(prefill_tok_s, _pct(ttft, 50), prompt_tok, len(completed)) else 0.0
    batched_prefill = (concurrency or 0) > 1 and completed and wall and out_tok <= len(completed)
    if batched_prefill:
        prefill_tok_s = prompt_tok / wall
    primary = "prefill_tok_s" if batched_prefill else "decode_tok_s" if (concurrency in (None, 1)) and decode_tok_s else "output_tok_s"
    ms_per_tok_per_layer = None
    if num_layers and decode_tok_s:
        ms_per_tok_per_layer = 1000.0 / decode_tok_s / num_layers
    return PerfMetrics(
        primary=primary,
        decode_tok_s=decode_tok_s,
        prefill_tok_s=prefill_tok_s,
        output_tok_s=output_tok_s or None,
        ttft_ms_p50=_pct(ttft, 50) if ttft else (summary.get("ttft_p50_ms") or None),
        ttft_ms_p99=_pct(ttft, 99) if ttft else (summary.get("ttft_p99_ms") or None),
        itl_ms_p50=_pct(itl_all, 50),
        itl_ms_p99=_pct(itl_all, 99),
        latency_ms_p50=summary.get("latency_p50_ms"),
        latency_ms_p99=summary.get("latency_p99_ms"),
        prompt_tokens=prompt_tok,
        output_tokens=out_tok,
        requests=int(summary.get("requests") or len(requests)),
        failed=int(summary.get("failed") or sum(1 for r in requests if not r.get("ok"))),
        ms_per_token_per_layer=ms_per_tok_per_layer,
        counters=counters,
    )


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
        if int(self.mode.tp) > 1 and os.environ.get("RUNPOD_POD_ID") and str(getattr(self.platform, "interconnect", "pcie")) not in ("nvlink", "xgmi"):
            return {"NCCL_P2P_DISABLE": "1", "NCCL_IB_DISABLE": "1"}
        return {}

    def no_peer_all_reduce(self) -> bool:
        return int(self.mode.tp) > 1 and self.platform is not None and not getattr(self.platform, "peer_access", True)

    def no_peer_env(self) -> dict[str, str]:
        if not self.no_peer_all_reduce():
            return {}
        existing = self.env.get("PYTHONPATH") or os.environ.get("PYTHONPATH")
        return {"PYTHONPATH": os.pathsep.join([str(NO_PEER_SITE)] + ([existing] if existing else [])), "PIE_BENCH_NO_CUSTOM_AR": "1"}

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
        roots = set(self.watch_pids())
        if not roots:
            return None
        if sys.platform == "win32":
            rows = [(pid, ppid, rss) for pid, ppid, _, rss in win_processes()]
        else:
            try:
                out = subprocess.run(["ps", "-A", "-o", "pid=,ppid=,rss="], capture_output=True, text=True, timeout=10).stdout
            except Exception:
                return None
            rows = [tuple(int(x) for x in line.split()) for line in out.splitlines() if len(line.split()) == 3]
        tree, grew = set(roots), True
        while grew:
            more = {pid for pid, ppid, _ in rows if ppid in tree and pid not in tree}
            tree |= more
            grew = bool(more)
        kib = sum(rss for pid, _, rss in rows if pid in tree)
        return round(kib / 2**20, 2) if kib else None

    def serve(self, workload: WorkloadSpec, log_path: Path, timeout_s: int) -> None:
        return None

    def stop(self) -> None:
        if self._server_proc is not None:
            if sys.platform == "win32":
                subprocess.run(["taskkill", "/T", "/F", "/PID", str(self._server_proc.pid)], capture_output=True, check=False)
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

    def build_argv(self, workload: WorkloadSpec, common_args: list[str], json_out: Path) -> list[str]:
        mode_sub, mode_args = workload_mode_args(workload)
        argv = [self.python, str(self.script_path()), mode_sub]
        argv += ["--model", self.model_arg()]
        argv += mode_args
        argv += common_args
        argv += self.engine_args(workload)
        argv += ["--json-out", str(json_out), "--dump-all-token-ids"]
        return argv

    supports_prompts_file: bool = True
    reports_timing: bool = True  # the bench client takes --report-timing, so a profiler can line its requests up with a trace

    def cold_common_args(self, workload: WorkloadSpec, common_args: list[str], out_dir: Path) -> list[str]:
        from pie_bench.node.workloads.synthetic import prompt_words_for_tokens

        if not self.supports_prompts_file:
            raise EngineLaunchError(ErrorClass.INCOMPATIBLE, f"{self.name.value}: cold-cache runs need --prompts-file in the bench script")
        prefill = int(workload.params.get("prefill", 128))
        body = lambda i: prompt_words_for_tokens(prefill, salt=f"{workload.id}|{i}")
        m = re.fullmatch(r"r(\d+)", out_dir.name)
        seed = COLD_SEED if not m or m.group(1) == "0" else f"{COLD_SEED}|round{m.group(1)}"
        prompts = cold_prompts(body, workload_id=workload.id, seed=seed, count=cold_request_count(workload.params))
        path = out_dir / "cold_prompts.json"
        path.write_text(json.dumps(prompts, ensure_ascii=False))
        return [*common_args, "--prompts-file", str(path.resolve())]

    def run(self, workload: WorkloadSpec, common_args: list[str], out_dir: Path, timeout_s: int) -> BenchResult:
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
            proc = subprocess.Popen(argv, cwd=str(bench_dir()), env=env, stdout=so, stderr=se, text=True)
            rc, timed_out, stalled = wait_with_stall_check(
                proc, timeout_s, self.stall_s(), self.watch_pids,
                on_stall=lambda pids: (out_dir / "stall-dump.txt").write_text(stall_dump(pids)),
            )
        dur = time.monotonic() - t0
        stdout = (out_dir / "stdout.txt").read_text(errors="replace")
        stderr = (out_dir / "stderr.txt").read_text(errors="replace")
        if stalled:
            raise EngineLaunchError(ErrorClass.HANG, f"no CPU work from the bench or its engine for {self.stall_s()}s; stopped")
        if rc == -6 and not timed_out and json_out.exists() and _all_completed(json_out):
            rc = 0
        if rc != 0 or not json_out.exists():
            cls, msg = classify_failure(rc, stderr, stdout, timed_out)
            if rc == 0 and not timed_out:
                lines = [ln.strip() for ln in (stderr + "\n" + stdout).splitlines() if ln.strip() and not set(ln.strip()) <= set("─│╭╮╰╯═║╔╗╚╝ ")]
                msg = "bench exited 0 without writing bench.json; last output: " + " | ".join(lines[-3:])[:400]
                cls = ErrorClass.HARNESS_INVALID
            raise EngineLaunchError(cls, msg)
        data = json.loads(json_out.read_text())
        summary = data.get("summary", {})
        requests = data.get("requests", [])
        failed = [r for r in requests if not r.get("ok")]
        if requests and len(failed) == len(requests):
            err = next((str(r.get("error") or "") for r in failed if r.get("error")), "(no error text)")
            cls = ErrorClass.HARNESS_INVALID if re.search(r"temperature must be|Failed to parse JSON input", err) else ErrorClass.INCOMPATIBLE if re.search(r"forward-hybrid|not valid on|interface", err) else ErrorClass.CRASH
            raise EngineLaunchError(cls, f"all {len(requests)} requests failed: {err[:300]}")
        perf = perf_from_common_json(summary, requests, self.num_layers, concurrency=int(workload.params.get("concurrency", 1)), cold_tags=bool(workload.params.get("cold_cache")))
        if workload.params.get("primary"):
            perf.primary = str(workload.params["primary"])
        perf.counters.update(self.counters_from_summary(summary))
        perf.resident_gib = self.resident_gib()
        if cold_sha is not None:
            perf.counters["cold_prompts_sha256_48"] = float(int(cold_sha[:12], 16))
        ids = [r.get("output_token_ids") or [] for r in requests]
        return BenchResult(
            perf=perf, summary=summary, requests=requests, argv=argv,
            stdout_tail=stdout[-4000:], stderr_tail=stderr[-4000:], duration_s=dur, output_token_ids=ids,
        )


def _cpu_seconds(text: str) -> float:
    days, _, rest = text.strip().rpartition("-")
    parts = [float(x) for x in rest.split(":")]
    secs = 0.0
    for x in parts:
        secs = secs * 60 + x
    return secs + (float(days) * 86400 if days else 0.0)


def win_processes() -> list[tuple[int, int, float, int]]:
    import psutil

    rows = []
    for p in psutil.process_iter(["pid", "ppid", "cpu_times", "memory_info"]):
        ct, mi = p.info.get("cpu_times"), p.info.get("memory_info")
        rows.append((p.info["pid"], p.info.get("ppid") or 0, (ct.user + ct.system) if ct else 0.0, (mi.rss // 1024) if mi else 0))
    return rows


def process_table() -> dict[int, tuple[int, float]]:
    if sys.platform == "win32":
        return {pid: (ppid, cpu) for pid, ppid, cpu, _ in win_processes()}
    out = subprocess.run(["ps", "-axo", "pid=,ppid=,time="], capture_output=True, text=True, check=False).stdout
    table = {}
    for line in out.splitlines():
        parts = line.split()
        if len(parts) == 3 and parts[0].isdigit() and parts[1].isdigit():
            try:
                table[int(parts[0])] = (int(parts[1]), _cpu_seconds(parts[2]))
            except ValueError:
                continue
    return table


def tree_pids(roots: list[int], table: dict[int, tuple[int, float]]) -> set[int]:
    pids = {r for r in roots if r in table}
    grew = True
    while grew:
        more = {p for p, (pp, _) in table.items() if pp in pids and p not in pids}
        pids |= more
        grew = bool(more)
    return pids


def stall_dump(pids: list[int]) -> str:
    out = []
    if shutil.which("nvidia-smi"):
        smi = subprocess.run(["nvidia-smi", "--query-gpu=index,utilization.gpu,memory.used", "--format=csv,noheader"],
                             capture_output=True, text=True, check=False, timeout=30)
        out.append("== nvidia-smi (index, util, mem)\n" + (smi.stdout or smi.stderr))
    gdb = shutil.which("gdb")
    for pid in pids:
        try:
            cmd = Path(f"/proc/{pid}/cmdline").read_bytes().replace(b"\0", b" ").decode(errors="replace")[:300]
        except OSError:
            continue
        out.append(f"== pid {pid}: {cmd}")
        if gdb:
            bt = subprocess.run([gdb, "-p", str(pid), "-batch", "-nx", "-ex", "set pagination off", "-ex", "thread apply all bt 30"],
                                capture_output=True, text=True, check=False, timeout=120)
            if bt.returncode == 0 and "Thread" in bt.stdout:
                out.append(bt.stdout)
                continue
            out.append(f"(gdb could not attach: {bt.stderr.strip()[-200:]})")
        for task in sorted(Path(f"/proc/{pid}/task").glob("*")):
            def read(name: str, task: Path = task) -> str:
                try:
                    return (task / name).read_text(errors="replace").strip()
                except OSError:
                    return "?"
            out.append(f"-- tid {task.name} {read('comm')} wchan={read('wchan')}\n{read('stack')}")
    return "\n".join(out)


def jit_jobs() -> str:
    jobs = os.cpu_count() or 8
    for path, per in (("/sys/fs/cgroup/cpu.max", None), ("/sys/fs/cgroup/memory.max", 4 << 30)):
        try:
            limit = open(path).read().split()
            if limit and limit[0] != "max":
                jobs = min(jobs, max(1, int(limit[0]) // int(limit[1]) if per is None else int(limit[0]) // per))
        except (OSError, ValueError, IndexError):
            pass
    return str(jobs)


def mac_gpu_busy() -> bool:
    if sys.platform != "darwin":
        return False
    from pie_bench.node.preflight import mac_gpu_utilization

    return (mac_gpu_utilization() or 0) > 5


def wait_with_stall_check(proc: subprocess.Popen, timeout_s: float, stall_s: float, extra_pids=lambda: [], poll_s: float = 5.0, on_stall=None, device_busy=mac_gpu_busy) -> tuple[int, bool, bool]:
    start = last_work = time.monotonic()
    last_cpu = None
    while True:
        try:
            return proc.wait(timeout=poll_s), False, False
        except subprocess.TimeoutExpired:
            pass
        now = time.monotonic()
        table = process_table()
        cpu = {p: table[p][1] for p in tree_pids([proc.pid, *extra_pids()], table)}
        if last_cpu is None or any(c > last_cpu.get(p, 0.0) + 0.05 for p, c in cpu.items()) or device_busy():
            last_work = now
        last_cpu = cpu
        timed_out, stalled = now - start > timeout_s, now - last_work > stall_s
        if stalled and not timed_out and on_stall is not None:
            try:
                on_stall(sorted(tree_pids([proc.pid, *extra_pids()], table)))
            except Exception:
                pass
        if timed_out or stalled:
            for p in tree_pids([proc.pid], table) - {proc.pid}:
                try:
                    os.kill(p, 9)
                except OSError:
                    pass
            proc.kill()
            proc.wait()
            return -1, timed_out, stalled and not timed_out


def workload_mode_args(workload: WorkloadSpec) -> tuple[str, list[str]]:
    p = workload.params
    kind = str(workload.kind)
    if kind in ("single_stream", "control_aa"):
        return "latency", ["--requests", str(p.get("requests", 8))]
    if kind == "long_context":
        conc = int(p.get("concurrency", 1))
        if conc <= 1:
            return "latency", ["--requests", str(p.get("requests", 4))]
        return "tput", ["--num-requests", str(p.get("num_requests", conc * 2)), "--concurrency", str(conc)]
    if kind in ("concurrency", "prefix_shared", "mixed_length", "replay"):
        conc = int(p.get("concurrency", 8))
        n = int(p.get("num_requests", p.get("variants", conc * 4)))
        return "tput", ["--num-requests", str(n), "--concurrency", str(conc)]
    raise ValueError(f"unknown workload kind {kind}")


_REGISTRY: dict[str, type[Engine]] = {}


def register(cls: type[Engine]) -> type[Engine]:
    backend = getattr(cls, "only_backend", None)
    _REGISTRY[f"{cls.name}@{backend}" if backend else str(cls.name)] = cls
    return cls


ADAPTERS = ("atom", "browser", "llamacpp", "mlxlm", "ollama", "pie", "sglang", "splash", "trtllm", "vllm", "vllm_metal")


def get_engine(name: str | EngineName, backend: str | None = None) -> type[Engine]:
    for module in ADAPTERS:
        importlib.import_module(f"{__package__}.{module}")
    return _REGISTRY.get(f"{name}@{backend}") or _REGISTRY[str(name)]
