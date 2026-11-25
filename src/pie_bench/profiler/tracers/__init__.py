from __future__ import annotations

from pathlib import Path


def tracer_for(backend: str, out: Path):
    import os

    from pie_bench.profiler.tracers import cupti, hsa, metal_command_buffers, nsys, xctrace, xla

    cuda = {"nsys": nsys.Tracer, "cupti": cupti.Tracer}[os.environ.get("PIE_BENCH_CUDA_TRACER", "cupti")]
    tracers = {"metal": metal_command_buffers.Tracer if metal_command_buffers.chosen() else xctrace.Tracer, "cuda": cuda, "rocm": hsa.Tracer, "xla": xla.Tracer}
    if backend not in tracers:
        raise SystemExit(f"no device tracer for the {backend} backend")
    return tracers[backend](out)
