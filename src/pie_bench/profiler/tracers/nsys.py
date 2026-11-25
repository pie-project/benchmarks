from __future__ import annotations

import sqlite3
import subprocess
import time
from contextlib import contextmanager
from pathlib import Path

from pie_bench.profiler.tracers.span import span

SESSION = "pie-bench-profile"
FLUSH_MS = 500
TABLES = (
    "CUPTI_ACTIVITY_KIND_KERNEL",
    "CUPTI_ACTIVITY_KIND_MEMCPY",
    "CUPTI_ACTIVITY_KIND_MEMSET",
    "CUPTI_ACTIVITY_KIND_GRAPH_TRACE",
)


class Tracer:
    name = "nsys"
    prefix = [
        "nsys",
        "launch",
        "--trace=cuda",
        "--cuda-graph-trace=graph",
        "--cuda-event-trace=false",
        "--trace-fork-before-exec=true",
        f"--cuda-flush-interval={FLUSH_MS}",
        f"--session-new={SESSION}",
    ]
    start_args = ["--sample=none", "--cpuctxsw=none"]
    env: dict[str, str] = {"VLLM_WORKER_MULTIPROC_METHOD": "spawn"}

    def __init__(self, out: Path):
        self.out = out

    @contextmanager
    def recording(self, out: Path):
        out.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            [
                "nsys",
                "start",
                f"--session={SESSION}",
                *self.start_args,
                "--output",
                str(out / "nsys"),
                "--force-overwrite=true",
            ],
            check=True,
        )
        time.sleep(3 * FLUSH_MS / 1000)
        try:
            with span(out):
                yield
        finally:
            time.sleep(3 * FLUSH_MS / 1000)
            subprocess.run(["nsys", "stop", f"--session={SESSION}"], check=True)
            subprocess.run(
                [
                    "nsys",
                    "export",
                    "--type=sqlite",
                    "--force-overwrite=true",
                    "--output",
                    str(out / "nsys.sqlite"),
                    str(out / "nsys.nsys-rep"),
                ],
                check=True,
            )

    def intervals(self, out: Path) -> list[tuple[int, int]]:
        with sqlite3.connect(out / "nsys.sqlite") as db:
            t0 = db.execute("SELECT utcEpochNs FROM TARGET_INFO_SESSION_START_TIME").fetchone()[0]
            tables = {
                name
                for (name,) in db.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
            }
            return [
                (t0 + s, t0 + e)
                for t in TABLES
                if t in tables
                for s, e in db.execute(f"SELECT start, end FROM {t}")
            ]
