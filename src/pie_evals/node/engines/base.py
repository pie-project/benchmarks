"""Engine adapter contract.

All adapters drive the bench scripts under the pinned pie checkout's
``scripts/bench/`` (``pie_bench.py``, ``vllm_bench.py``, ``sglang_bench.py``,
``llamacpp_bench.py``, ``mlx_bench.py``), or this repo's ``openai_bench.py``
for the OpenAI-compatible servers. Those scripts share ``scripts/bench/common.py`` — one
client, one prompt construction, one JSON envelope — which is what makes a
cross-engine number a comparison at all.
The adapter's job is therefore: build the argv for a (artifact, mode,
workload, recipe), run it under a timeout, classify failure, and lift the
JSON into ``PerfMetrics``.

An adapter that needs to hold an engine process across workloads (one model
per process, workloads interleaved inside it) uses the ``serve``/``attach``
pair; the bench scripts support that through ``PIE_BENCH_SERVE_ONLY`` /
``PIE_BENCH_SERVER_URL`` for pie and the HTTP server for llama.cpp, mlx-lm
and Splash.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from pie_evals.node.fair import (
    COLD_SEED,
    FAIR_DEFINITION_VERSION,
    cache_verdict,
    cold_prompts,
    cold_request_count,
    fair_prefill_tok_s,
    prefill_mismatch,
)
from pie_evals.schema import (
    ArtifactSpec,
    EngineName,
    ErrorClass,
    Mode,
    PerfMetrics,
    PlatformSpec,
    WorkloadSpec,
)

#: holds the sitecustomize that turns vLLM's and SGLang's custom all-reduce off (Engine.no_peer_env)
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


# Patterns that classify a failed run. Order matters: the first match wins.
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
    # A Python traceback is described by its exception (the last
    # "SomeError: ..." line and the lines its message runs on to), never by a
    # code line that happens to contain a keyword ("resolved_model =
    # resolve_local_model(args.model)" is not a message). pie_bench's startup
    # failure puts the server's own refusal on those following lines.
    if "Traceback (most recent call last)" in text:
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        at = next((i for i in reversed(range(len(lines))) if re.match(r"^[A-Za-z_][A-Za-z0-9_.]*(Error|Exception|Exit|Interrupt)\b", lines[i])), len(lines) - 1)
        exc = " | ".join(lines[at:]) or "Traceback"
        # the exception line, then the end of what follows: the server's
        # refusal comes last, after its startup logs
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
    """Whether a bench.json holds every request it was asked for, none failed."""
    try:
        s = json.loads(json_out.read_text()).get("summary", {})
    except (OSError, ValueError):
        return False
    return bool(s.get("requests")) and s.get("completed") == s.get("requests") and not s.get("failed")


def _pct(values: list[float], q: float) -> float | None:
    if not values:
        return None
    return float(np.percentile(np.asarray(values, dtype=float), q))


#: cached tokens per request a cold-tagged run may show from the prompt's shared opening
COLD_OPENING_TOKENS = 32


def serial_clock(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """One request at a time: a request's clock starts when the engine could take it.

    vLLM's streaming client hands every request to the engine at t=0 and the engine seats
    one, so each TTFT counted the requests queued before it (0.5.3-b5, L4: 0.11 s, 10 s,
    20 s, ...). A request starts at its send or at the previous request's last token,
    whichever is later; a client that already sends one at a time is left as it was."""
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
    """Lift ``scripts/bench/common.py``'s BenchSummary + RequestResult rows."""
    completed = [r for r in requests if r.get("ok")]
    if concurrency == 1:
        completed = serial_clock(completed)
    out_tok = int(summary.get("output_tokens") or sum(r.get("output_tokens", 0) for r in completed))
    prompt_tok = int(summary.get("prompt_tokens") or sum(r.get("prompt_tokens", 0) for r in completed))
    wall = float(summary.get("wall_s") or 0.0)
    output_tok_s = float(summary.get("output_tok_per_s") or (out_tok / wall if wall else 0.0))
    ttft = [r["ttft_s"] * 1000.0 for r in completed if r.get("ttft_s") is not None]
    # decode tok/s for a lane = output tokens / (latency - ttft)
    decode_lane = []
    itl_all: list[float] = []
    for r in completed:
        lat = r.get("latency_s")
        tt = r.get("ttft_s")
        n = r.get("output_tokens") or 0
        if lat and tt is not None and n > 1 and lat > tt:
            decode_lane.append((n - 1) / (lat - tt))
        it = r.get("intertoken_us") or []
        if isinstance(it, list):
            itl_all.extend(float(x) / 1000.0 for x in it)
    counters = {}
    for k, v in (summary.get("config") or {}).items():
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            counters[str(k)] = float(v)
    # derived counters (device_idle_pct, host_us_per_step, ...) are filled by the pie adapter
    concurrency = concurrency or int((summary.get("config") or {}).get("concurrency") or 0) or None
    decode_tok_s = float(np.median(decode_lane)) if decode_lane else None
    # prefill: one definition for every engine (see pie_evals.node.fair)
    config_cached = counters.get("cached_prompt_tokens")
    # a cold-cache workload tags every prompt's start, so no prefix can hit: an engine that
    # does not report its cache count is taken as cold by construction, and the row says so
    by_construction = config_cached is None and cold_tags
    if by_construction:
        config_cached = 0.0
        counters["cold_by_construction"] = 1.0
    # on tagged prompts only the opening before the tag can hit (~15 of 555 tokens);
    # that is not a warm cache, so the row is cold and says how much the opening was
    elif cold_tags and config_cached and completed and config_cached / len(completed) <= COLD_OPENING_TOKENS:
        counters["cold_opening_cached_per_request"] = config_cached / len(completed)
        config_cached = 0.0
    verdict = cache_verdict(completed, config_cached)
    prefill_tok_s = fair_prefill_tok_s(completed, concurrency=concurrency, config_cached=config_cached)
    counters["fair_def"] = float(FAIR_DEFINITION_VERSION)
    counters["cold_cache_verified"] = 1.0 if verdict == "cold" else 0.0
    if prefill_tok_s is not None:
        counters["prefill_ttft_mismatch"] = 1.0 if prefill_mismatch(prefill_tok_s, _pct(ttft, 50), prompt_tok, len(completed)) else 0.0
    # batched prefill (many prompts at once, one token each): the batch's prompt tokens over the wall
    batched_prefill = (concurrency or 0) > 1 and completed and wall and out_tok <= len(completed)
    if batched_prefill:
        prefill_tok_s = prompt_tok / wall
    # single-stream: the lane's decode rate is the aggregate; concurrency: aggregate output tok/s is the headline
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
        itl_ms_p50=_pct(itl_all, 50) if itl_all else (summary.get("intertoken_p50_ms") or None),
        itl_ms_p99=_pct(itl_all, 99) if itl_all else (summary.get("intertoken_p99_ms") or None),
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
    """One adapter per engine. Instances are per (artifact, mode, platform)."""

    name: EngineName
    #: bench script under the pie checkout, e.g. "scripts/bench/pie_bench.py"
    script: str
    #: environment the engine's processes get unless the caller set the key
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
        self.recipe = recipe  # engine knobs for this (engine, platform, artifact) — see recipes/
        self.python = python or self.default_python()
        self.env = dict(env or {})
        for k, v in {**self.env_defaults, **self.default_env()}.items():
            self.env.setdefault(k, v)
        self.num_layers = num_layers
        self.server_url: str | None = None
        self._server_proc: subprocess.Popen | None = None

    def drop_env(self) -> set[str]:
        """Variables of the node's own environment the engine process must not inherit."""
        return set()

    def process_env(self, *extra: dict[str, str]) -> dict[str, str]:
        drop = self.drop_env()
        env = {k: v for k, v in os.environ.items() if k not in drop}
        env.setdefault("MAX_JOBS", jit_jobs())
        for e in (self.env, *extra):
            env.update(e)
        return env

    def default_env(self) -> dict[str, str]:
        """Runtime-computed environment defaults (paths under the cache root);
        static ones go in ``env_defaults``. The caller's env wins over both."""
        return {}

    def nccl_env(self) -> dict[str, str]:
        """NCCL settings for a tensor-parallel baseline on a RunPod pod: the
        container advertises GPU peer access it cannot deliver, and NCCL's init
        then waits forever — vLLM 0.30 tp2 on the L40S x2 pod printed "vLLM is
        using nccl==2.29.7" and nothing more for 30 minutes (nightly
        36081628995 s05); SGLang tp2 hung the same way (s10). Peer-to-peer and
        InfiniBand off makes NCCL fall back to host-staged copies, which is
        what the pod's PCIe topology delivers anyway. pie falls back to NCCL when its own peer
        collectives cannot run, so it takes the same settings.
        An NVLink pod (A100 SXM, H100 SXM) or an Infinity Fabric one (MI300X, MI350X OAM) keeps peer access: turning it off there
        would slow vLLM and SGLang below what the hardware gives them."""
        if int(self.mode.tp) > 1 and os.environ.get("RUNPOD_POD_ID") and str(getattr(self.platform, "interconnect", "pcie")) not in ("nvlink", "xgmi"):
            return {"NCCL_P2P_DISABLE": "1", "NCCL_IB_DISABLE": "1"}
        return {}

    def no_peer_all_reduce(self) -> bool:
        """True for a tp>1 run on a platform whose GPU peer access is advertised but broken
        (``peer_access: false``): an engine's custom all-reduce reads the peer's memory directly
        and there hangs or faults, so it is turned off and NCCL carries the all-reduce, the path
        pie takes on the same pod when its own peer collectives cannot run."""
        return int(self.mode.tp) > 1 and self.platform is not None and not getattr(self.platform, "peer_access", True)

    def no_peer_env(self) -> dict[str, str]:
        """The env that turns vLLM's and SGLang's custom all-reduce off from outside their bench
        scripts: ``scripts/no_peer_site/sitecustomize.py`` goes first on PYTHONPATH (every spawned
        worker inherits it) and makes the engine's P2P check answer "no", exactly the
        ``disable_custom_all_reduce=True`` outcome. Empty unless ``no_peer_all_reduce()``."""
        if not self.no_peer_all_reduce():
            return {}
        existing = self.env.get("PYTHONPATH") or os.environ.get("PYTHONPATH")
        return {"PYTHONPATH": ":".join([str(NO_PEER_SITE)] + ([existing] if existing else [])), "PIE_EVALS_NO_CUSTOM_AR": "1"}

    # ---- to implement per engine ---------------------------------------------
    @abstractmethod
    def default_python(self) -> str: ...

    @abstractmethod
    def model_arg(self) -> str:
        """What ``--model`` receives for this engine (HF id, GGUF path, snapshot dir...)."""

    @abstractmethod
    def engine_args(self, workload: WorkloadSpec) -> list[str]:
        """Engine-specific flags: device/tp, memory, graphs, competitive recipe knobs."""

    def version(self) -> str:
        return "unknown"

    def counters_from_summary(self, summary: dict[str, Any]) -> dict[str, float]:
        return {}

    def resident_gib(self) -> float | None:
        """Resident memory of the engine's processes and their children, in GiB."""
        roots = set(self.watch_pids())
        if not roots:
            return None
        try:
            out = subprocess.run(["ps", "-A", "-o", "pid=,ppid=,rss="], capture_output=True, text=True, timeout=10).stdout
        except Exception:  # noqa: BLE001
            return None
        rows = [tuple(int(x) for x in line.split()) for line in out.splitlines() if len(line.split()) == 3]
        tree, grew = set(roots), True
        while grew:
            more = {pid for pid, ppid, _ in rows if ppid in tree and pid not in tree}
            tree |= more
            grew = bool(more)
        kib = sum(rss for pid, _, rss in rows if pid in tree)
        return round(kib / 2**20, 2) if kib else None

    # ---- optional long-lived server (one model per process) ------------------
    def serve(self, workload: WorkloadSpec, log_path: Path, timeout_s: int) -> None:
        """Default: no persistent server; each ``run`` boots the engine."""
        return None

    def stop(self) -> None:
        if self._server_proc is not None:
            self._server_proc.terminate()
            try:
                self._server_proc.wait(timeout=60)
            except subprocess.TimeoutExpired:
                self._server_proc.kill()
            self._server_proc = None

    def leftover_process_names(self) -> list[str]:
        """Process names that may outlive the parent and hold the GPU (vLLM's EngineCore)."""
        return []

    def stall_s(self) -> int:
        return int(self.recipe.get("stall_s") or os.environ.get("PIE_EVALS_STALL_S") or 180)

    def watch_pids(self) -> list[int]:
        return []

    # ---- the run -------------------------------------------------------------
    def script_path(self) -> Path:
        """The bench script this adapter runs (a path under the pie checkout by default)."""
        return self.pie_root / self.script

    def build_argv(self, workload: WorkloadSpec, common_args: list[str], json_out: Path) -> list[str]:
        mode_sub, mode_args = workload_mode_args(workload)
        argv = [self.python, str(self.script_path()), mode_sub]
        argv += ["--model", self.model_arg()]
        argv += mode_args
        argv += common_args
        argv += self.engine_args(workload)
        argv += ["--json-out", str(json_out), "--dump-all-token-ids"]
        return argv

    #: True when the bench script reads ``--prompts-file`` (scripts/bench/common.py's
    #: ``make_prompts``). Cold-cache workloads need it; an adapter without it refuses them.
    supports_prompts_file: bool = True

    def cold_common_args(self, workload: WorkloadSpec, common_args: list[str], out_dir: Path) -> list[str]:
        """Swap the shape's prompts for the cold prompt list, one per request, same for every engine.

        Each round gets its own list: an engine that keeps its server between rounds (pie, the
        Mac servers) would otherwise see round 1's prompts again in rounds 2 and 3 and serve them
        from its prefix cache (0.5.3-b5: pie gpt-oss-120b on a PRO 6000, TTFT 64 ms cold, 16 ms
        in the later rounds, so the median row was a cached one)."""
        from pie_evals.node.workloads.synthetic import prompt_words_for_tokens

        if not self.supports_prompts_file:
            raise EngineLaunchError(ErrorClass.INCOMPATIBLE, f"{self.name.value}: cold-cache runs need --prompts-file in the bench script")
        body = prompt_words_for_tokens(int(workload.params.get("prefill", 128)), salt=workload.id)
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
            proc = subprocess.Popen(argv, cwd=str(self.pie_root / "scripts/bench"), env=env, stdout=so, stderr=se, text=True)
            rc, timed_out, stalled = wait_with_stall_check(
                proc, timeout_s, self.stall_s(), self.watch_pids,
                on_stall=lambda pids: (out_dir / "stall-dump.txt").write_text(stall_dump(pids)),
            )
        dur = time.monotonic() - t0
        stdout = (out_dir / "stdout.txt").read_text(errors="replace")
        stderr = (out_dir / "stderr.txt").read_text(errors="replace")
        if stalled:
            raise EngineLaunchError(ErrorClass.HANG, f"no CPU work from the bench or its engine for {self.stall_s()}s; stopped")
        # SGLang 0.5.22 on ROCm aborts in its own teardown after the bench wrote every request (gemma-4-E4B raw on
        # mi300x-x1: 6/6 completed, then SIGABRT); a whole result is the measurement, the exit after it is not
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
            # first 48 bits of the cold prompt file's sha256; exact in a float. decode: format(int(v), "012x")
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


def process_table() -> dict[int, tuple[int, float]]:
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
    """What a stalled process tree is doing when the watchdog gives up on it:
    the GPUs' utilization (busy with no CPU work points at a device-side wait,
    e.g. ranks blocked in a collective; idle points at a host-side deadlock)
    and every thread's stack — gdb's when it is installed and may attach,
    otherwise the kernel's view from /proc."""
    out = []
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
    """Parallel compiles for an engine's JIT build (FlashInfer's ninja reads MAX_JOBS): what the container's CPU quota
    and memory hold, not the host's core count. Unset, ninja ran 82 nvcc at once on an RTX 4090 pod of 8.5 CPUs and
    87 GiB (about 1.6 GiB each) building SGLang's Nemotron-H CUTLASS MoE, and the container was OOM-killed."""
    jobs = os.cpu_count() or 8
    for path, per in (("/sys/fs/cgroup/cpu.max", None), ("/sys/fs/cgroup/memory.max", 4 << 30)):
        try:
            limit = open(path).read().split()
            if limit and limit[0] != "max":
                jobs = min(jobs, max(1, int(limit[0]) // int(limit[1]) if per is None else int(limit[0]) // per))
        except (OSError, ValueError, IndexError):
            pass
    return str(jobs)


def wait_with_stall_check(proc: subprocess.Popen, timeout_s: float, stall_s: float, extra_pids=lambda: [], poll_s: float = 5.0, on_stall=None) -> tuple[int, bool, bool]:
    start = last_work = time.monotonic()
    last_cpu = None
    while True:
        try:
            return proc.wait(timeout=poll_s), False, False
        except subprocess.TimeoutExpired:
            pass
        now = time.monotonic()
        table = process_table()
        # per process: a tree's summed CPU drops when a busy child exits (an inductor compile pool), and the
        # nvcc/ptxas of a JIT build that follows stayed under the old peak for minutes (SGLang Marlin on sm_86)
        cpu = {p: table[p][1] for p in tree_pids([proc.pid, *extra_pids()], table)}
        if last_cpu is None or any(c > last_cpu.get(p, 0.0) + 0.05 for p, c in cpu.items()):
            last_work = now
        last_cpu = cpu
        timed_out, stalled = now - start > timeout_s, now - last_work > stall_s
        if stalled and not timed_out and on_stall is not None:
            try:
                on_stall(sorted(tree_pids([proc.pid, *extra_pids()], table)))
            except Exception:  # a dump must never turn a recorded hang into a harness crash
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
    """Map a WorkloadSpec onto common.py's ``latency`` / ``tput`` subcommands."""
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
    _REGISTRY[str(cls.name)] = cls
    return cls


def get_engine(name: str | EngineName) -> type[Engine]:
    # import side effects register the adapters
    from . import llamacpp, mlxlm, pie, sglang, splash, trtllm, vllm  # noqa: F401

    return _REGISTRY[str(name)]
