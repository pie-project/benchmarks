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
    """The profiled round's workload: the benchmark's own shape and requests (at most 8), or 3 waves of its concurrency.
    A single-stream step is the median request's, and 4 requests let two lucky ones set it (pie's A40 Qwen3.5-0.8B
    prefill: 15.1 and 15.2 ms against 17.2 to 17.4 for the rest).

    PIE_BENCH_PROFILE_ROUND=full keeps a whole benchmark round, for a Mac that throttles within one: on the fanless
    m3-16g mlx-lm's 4th pf8-512 wave runs 25 to 55% slower than its first, so a 3-wave round leaves the slow wave out
    and profiles 12 to 14% under the benchmark's own step."""
    import os

    if os.environ.get("PIE_BENCH_PROFILE_ROUND") == "full":
        return workload
    p = dict(workload.params)
    if "num_requests" in p:
        p["num_requests"] = min(int(p["num_requests"]), 3 * int(p.get("concurrency", 1)))
    else:
        p["requests"] = min(int(p.get("requests", 4)), 8)
    return workload.model_copy(update={"params": p})


def tracer_for(backend: str, out: Path):
    """The tracer for a platform's backend, its files under out."""
    import os

    from . import cupti, metal, metal_cb, nsys, rocprof, xla

    # CUPTI's activity records alone by default: nsys also traces every CUDA API call, which cost SGLang's and vLLM's
    # eager prefill 10 to 38% of the profiled round (PIE_BENCH_CUDA_TRACER=nsys still selects it)
    cuda = {"nsys": nsys.Tracer, "cupti": cupti.Tracer}[os.environ.get("PIE_BENCH_CUDA_TRACER", "cupti")]
    tracers = {"metal": metal_cb.Tracer if metal_cb.chosen() else metal.Tracer, "cuda": cuda, "rocm": rocprof.Tracer, "xla": xla.Tracer}
    if backend not in tracers:
        raise SystemExit(f"no device tracer for the {backend} backend")
    return tracers[backend](out)
