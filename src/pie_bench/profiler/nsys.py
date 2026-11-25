"""Nsys: an NVIDIA GPU's kernel, copy and memset intervals, from an Nsight Systems trace.

The profiler runs under `nsys launch`, so every engine process below it is traced; each measured round is one
`nsys start`/`nsys stop` collection, exported to SQLite. Its timestamps count from the session start, which the
export gives in Unix ns.
"""

from __future__ import annotations

import sqlite3
import subprocess
import time
from contextlib import contextmanager
from pathlib import Path

from . import span

SESSION = "pie-bench-profile"
FLUSH_MS = 500
# a CUDA graph launch is one interval of its own (whole-graph trace): its kernels are not listed one by one
TABLES = ("CUPTI_ACTIVITY_KIND_KERNEL", "CUPTI_ACTIVITY_KIND_MEMCPY", "CUPTI_ACTIVITY_KIND_MEMSET", "CUPTI_ACTIVITY_KIND_GRAPH_TRACE")


class Tracer:
    name = "nsys"
    # engines that fork their model worker without exec (vLLM's EngineCore) are traced too. A CUDA buffer is saved every
    # FLUSH_MS: with the default (saved when full), a server process idle after the round lost its last part-filled
    # buffer at `nsys stop` (SGLang on an A40: the last 620 ms of the round)
    # each CUDA graph launch traced whole, not node by node: node tracing slowed graph-replaying engines' profiled decode
    # (TRT-LLM on an H200: +19% node by node, +1.4% whole). No device-side CUDA event trace (on by default since driver
    # 12.8, it can add false dependencies across streams)
    prefix = ["nsys", "launch", "--trace=cuda", "--cuda-graph-trace=graph", "--cuda-event-trace=false", "--trace-fork-before-exec=true",
              f"--cuda-flush-interval={FLUSH_MS}", f"--session-new={SESSION}"]
    # no CPU IP sampling or context switch trace (on by default for a launched app): only device work is read
    start_args = ["--sample=none", "--cpuctxsw=none"]
    # vLLM's EngineCore forked from its first process kept losing the round's last kernels at stop (1.3 s of a Raw 512
    # round on an A40) even with the flush interval: started with spawn, it is a traced process of its own
    env: dict[str, str] = {"VLLM_WORKER_MULTIPROC_METHOD": "spawn"}

    def __init__(self, out: Path):
        self.out = out

    @contextmanager
    def recording(self, out: Path):
        """One collection of the launched session while the block runs, saved as nsys.sqlite."""
        out.mkdir(parents=True, exist_ok=True)
        subprocess.run(["nsys", "start", f"--session={SESSION}", *self.start_args, "--output", str(out / "nsys"), "--force-overwrite=true"], check=True)
        # every traced process collecting before the round's first request (SGLang's scheduler on an RTX 5090 had
        # no device work in its first measured window without it)
        time.sleep(3 * FLUSH_MS / 1000)
        try:
            with span(out):
                yield
        finally:
            time.sleep(3 * FLUSH_MS / 1000)  # the round's last buffers saved before the collection ends
            subprocess.run(["nsys", "stop", f"--session={SESSION}"], check=True)
            subprocess.run(["nsys", "export", "--type=sqlite", "--force-overwrite=true", "--output", str(out / "nsys.sqlite"),
                            str(out / "nsys.nsys-rep")], check=True)

    def intervals(self, out: Path) -> list[tuple[int, int]]:
        """Every kernel, copy, memset and graph launch the session recorded, in Unix ns."""
        with sqlite3.connect(out / "nsys.sqlite") as db:
            t0 = db.execute("SELECT utcEpochNs FROM TARGET_INFO_SESSION_START_TIME").fetchone()[0]
            tables = {name for (name,) in db.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
            return [(t0 + s, t0 + e) for t in TABLES if t in tables for s, e in db.execute(f"SELECT start, end FROM {t}")]
