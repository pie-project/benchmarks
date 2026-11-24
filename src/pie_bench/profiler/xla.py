"""Xla: a TPU's op intervals, from a JAX profiler trace of the engine process.

Every process that imports jax arms a trace (jax_site/sitecustomize.py, first on PYTHONPATH): SIGUSR1 starts
jax.profiler tracing with a Perfetto export, SIGUSR2 stops it. The intervals are the ops on the TPU devices' "XLA Ops"
lines; their timestamps are Unix microseconds.
"""

from __future__ import annotations

import gzip
import json
import os
import signal
import time
from contextlib import contextmanager
from pathlib import Path

from . import span

SITE = Path(__file__).resolve().parent / "jax_site"


class Tracer:
    name = "xla"
    prefix: list[str] = []

    def __init__(self, out: Path):
        self.dir = out / "xla"
        self.env = {"PIE_BENCH_JAX_TRACE_DIR": str(self.dir),
                    "PYTHONPATH": os.pathsep.join([str(SITE), *filter(None, [os.environ.get("PYTHONPATH")])])}

    def _armed(self) -> list[int]:
        pids = [int(p.stem) for p in self.dir.glob("*.pid")]
        return [p for p in pids if _alive(p)]

    @contextmanager
    def recording(self, out: Path):
        """Traces every armed engine process while the block runs; their traces land under xla/<pid>."""
        out.mkdir(parents=True, exist_ok=True)
        pids = self._armed()
        if not pids:
            raise RuntimeError("no engine process imported jax with the profiler armed")
        for pid in pids:
            os.kill(pid, signal.SIGUSR1)
        try:
            with span(out):
                yield
        finally:
            for pid in pids:
                os.kill(pid, signal.SIGUSR2)
            time.sleep(10)
            (out / "pids.json").write_text(json.dumps(pids))

    def intervals(self, out: Path) -> list[tuple[int, int]]:
        """The TPU ops of the traced processes, in Unix ns."""
        found = []
        for pid in json.loads((out / "pids.json").read_text()):
            for path in (self.dir / str(pid)).rglob("perfetto_trace.json.gz"):
                found += device_ops(json.loads(gzip.decompress(path.read_bytes())))
        return found


def device_ops(trace: dict) -> list[tuple[int, int]]:
    """(start, end) Unix ns of every complete event on a TPU device's XLA Ops line of a Chrome trace."""
    events = trace.get("traceEvents", [])
    devices = {e["pid"] for e in events if e.get("ph") == "M" and e.get("name") == "process_name" and "TPU" in str(e.get("args", {}).get("name"))}
    lines = {(e["pid"], e.get("tid")) for e in events if e.get("ph") == "M" and e.get("name") == "thread_name"
             and e.get("pid") in devices and e.get("args", {}).get("name") == "XLA Ops"}
    ns = lambda us: int(us) * 1000 + round((us - int(us)) * 1000)
    return [(ns(e["ts"]), ns(e["ts"]) + round(e["dur"] * 1000)) for e in events if e.get("ph") == "X" and (e.get("pid"), e.get("tid")) in lines]


def _alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False
