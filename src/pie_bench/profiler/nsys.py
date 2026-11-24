"""Nsys: an NVIDIA GPU's kernel, copy and memset intervals, from an Nsight Systems trace.

The profiler runs under `nsys launch`, so every engine process below it is traced; each measured round is one
`nsys start`/`nsys stop` collection, exported to SQLite. Its timestamps count from the session start, which the
export gives in Unix ns.
"""

from __future__ import annotations

import sqlite3
import subprocess
from contextlib import contextmanager
from pathlib import Path

from . import span

SESSION = "pie-bench-profile"
TABLES = ("CUPTI_ACTIVITY_KIND_KERNEL", "CUPTI_ACTIVITY_KIND_MEMCPY", "CUPTI_ACTIVITY_KIND_MEMSET")


class Tracer:
    name = "nsys"
    prefix = ["nsys", "launch", "--trace=cuda", "--cuda-graph-trace=node", f"--session-new={SESSION}"]
    env: dict[str, str] = {}

    def __init__(self, out: Path):
        self.out = out

    @contextmanager
    def recording(self, out: Path):
        """One collection of the launched session while the block runs, saved as nsys.sqlite."""
        out.mkdir(parents=True, exist_ok=True)
        subprocess.run(["nsys", "start", f"--session={SESSION}", "--output", str(out / "nsys"), "--force-overwrite=true"], check=True)
        try:
            with span(out):
                yield
        finally:
            subprocess.run(["nsys", "stop", f"--session={SESSION}"], check=True)
            subprocess.run(["nsys", "export", "--type=sqlite", "--force-overwrite=true", "--output", str(out / "nsys.sqlite"),
                            str(out / "nsys.nsys-rep")], check=True)

    def intervals(self, out: Path) -> list[tuple[int, int]]:
        """Every kernel, copy and memset the session recorded, in Unix ns."""
        with sqlite3.connect(out / "nsys.sqlite") as db:
            t0 = db.execute("SELECT utcEpochNs FROM TARGET_INFO_SESSION_START_TIME").fetchone()[0]
            tables = {name for (name,) in db.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
            return [(t0 + s, t0 + e) for t in TABLES if t in tables for s, e in db.execute(f"SELECT start, end FROM {t}")]
