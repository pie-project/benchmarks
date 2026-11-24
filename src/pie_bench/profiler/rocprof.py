"""Rocprof: an AMD GPU's kernel and copy intervals, from a rocprofv3 trace.

The profiler runs under rocprofv3, which traces every process below it and writes each one's CSV files when it exits.
Their timestamps are CLOCK_BOOTTIME ns; each round notes that clock against Unix time to move them.
"""

from __future__ import annotations

import csv
import json
import time
from contextlib import contextmanager
from pathlib import Path

from . import span

FILES = ("*kernel_trace.csv", "*memory_copy_trace.csv")


class Tracer:
    name = "rocprof"
    # rocprofv3's tool brings up HSA in every process it is preloaded into, so a model worker forked from the engine's
    # first process (vLLM's EngineCore) hangs on its first GPU signal: vLLM starts it with spawn instead.
    # Each traced dispatch's completion is waited on by one of rocprofiler's async handler threads (4 by default); pie
    # keeps hundreds of dispatches in flight across streams that wait on each other, so a small pool deadlocks it
    env: dict[str, str] = {"VLLM_WORKER_MULTIPROC_METHOD": "spawn", "ROCPROFILER_ASYNC_SIGNAL_HANDLER_THREADS": "4096"}

    def __init__(self, out: Path):
        self.root = out / "rocprof"
        self.prefix = ["rocprofv3", "--kernel-trace", "--memory-copy-trace", "--output-format", "csv", "--output-directory", str(self.root), "--"]

    @contextmanager
    def recording(self, out: Path):
        """Notes the boot clock against Unix time; rocprofv3 traces the whole run."""
        out.mkdir(parents=True, exist_ok=True)
        (out / "clock.json").write_text(json.dumps({"unix_minus_boot_ns": time.time_ns() - time.clock_gettime_ns(time.CLOCK_BOOTTIME)}))
        with span(out):
            yield

    def intervals(self, out: Path) -> list[tuple[int, int]]:
        """Every kernel and copy of every traced process, in Unix ns."""
        shift = json.loads((out / "clock.json").read_text())["unix_minus_boot_ns"]
        found = []
        for pattern in FILES:
            for path in self.root.rglob(pattern):
                with open(path, newline="") as f:
                    found += [(int(r["Start_Timestamp"]) + shift, int(r["End_Timestamp"]) + shift) for r in csv.DictReader(f)]
        return found
