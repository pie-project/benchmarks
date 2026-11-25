"""Profiler: an engine's forward pass, timed end to end from the device's own trace.

A profiled cell runs its standard benchmark rounds and then one short round under the platform's tracer, in the same
engine session, and reports per benchmark unit the wall time, the time the device was busy (the forward pass: the
union of every device work interval) and the rest (idle). No kernel names.
"""

from __future__ import annotations

import json
import time
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def span(out: Path):
    """Writes when a recording started and stopped (span.json), for the measured windows to be checked against."""
    start = time.time_ns()
    try:
        yield
    finally:
        (out / "span.json").write_text(json.dumps({"start_ns": start, "stop_ns": time.time_ns()}))


def short(workload):
    """The profiled round's workload: the benchmark's own shape with 4 requests, or 3 waves of its concurrency."""
    p = dict(workload.params)
    if "num_requests" in p:
        p["num_requests"] = min(int(p["num_requests"]), 3 * int(p.get("concurrency", 1)))
    else:
        p["requests"] = min(int(p.get("requests", 4)), 4)
    return workload.model_copy(update={"params": p})


def tracer_for(backend: str, out: Path):
    """The tracer for a platform's backend, its files under out."""
    from . import metal, metal_cb, nsys, rocprof, xla

    tracers = {"metal": metal_cb.Tracer if metal_cb.chosen() else metal.Tracer, "cuda": nsys.Tracer, "rocm": rocprof.Tracer, "xla": xla.Tracer}
    if backend not in tracers:
        raise SystemExit(f"no device tracer for the {backend} backend")
    return tracers[backend](out)
