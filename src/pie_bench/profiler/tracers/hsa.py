"""Rocprof: an AMD GPU's kernel intervals, from the GPU's own dispatch timestamps, in the profiled round only.

rocprofv3 traced every dispatch of the run from launch, through intercept queues, and made each dispatch create and
wait on a signal of its own: that cost the launch-bound engines 4% to 246% of their step, and SGLang's HIP graph replay
crashed in them on ROCm 7.2.0. Instead every engine process loads hsa_trace.cpp (ROCr's HSA_TOOLS_LIB), which leaves
the engine's queues as they are and, outside the round, only checks a flag on each signal store. While the round's
marker file exists, each kernel a doorbell publishes gets a pooled completion signal, the queues write its start and
end timestamps, and a thread of the tool's own writes them as Unix ns. Copies (SDMA, and ROCr's own blit queues) are
not in it; a prefill's are a few microseconds.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import time
from contextlib import contextmanager
from pathlib import Path

from pie_bench.profiler.tracers.span import span

SHIM = Path(__file__).resolve().parent / "hsa_trace.cpp"


def rocm_root() -> Path:
    """The ROCm tree with HSA's headers: ROCM_PATH, /opt/rocm, or the one hipcc sits in (AMD's vLLM image ships ROCm as
    pip packages)."""
    hipcc = shutil.which("hipcc")
    for root in (os.environ.get("ROCM_PATH"), "/opt/rocm", hipcc and str(Path(hipcc).resolve().parents[1])):
        if root and (Path(root) / "include" / "hsa" / "hsa_api_trace.h").exists():
            return Path(root)
    raise SystemExit("no ROCm tree with HSA's headers (set ROCM_PATH)")


class Tracer:
    name = "hsa"
    prefix: list[str] = []

    def __init__(self, out: Path):
        self.dir = out / "hsa"
        self.dir.mkdir(parents=True, exist_ok=True)
        so = out / "hsa_trace.so"
        subprocess.run(["g++", "-O2", "-std=c++17", "-shared", "-fPIC", "-DAMD_INTERNAL_BUILD", f"-I{rocm_root() / 'include' / 'hsa'}",
                        "-o", str(so), str(SHIM), "-lpthread"], check=True)
        # ROCr skips HSA_TOOLS_LIB in processes where rocprofiler-register took the API table (any torch process)
        # unless v1 tools are allowed
        self.env = {"HSA_TOOLS_LIB": str(so), "HSA_TOOLS_ROCPROFILER_V1_TOOLS": "1", "PIE_BENCH_HSA_TRACE_DIR": str(self.dir)}

    @contextmanager
    def recording(self, out: Path):
        """Records the engine processes' kernels while the block runs; their files move to out/hsa."""
        out.mkdir(parents=True, exist_ok=True)
        since = time.time()
        marker = self.dir / "recording"
        marker.touch()
        time.sleep(0.05)  # each process looks for the marker every millisecond
        try:
            with span(out):
                yield
        finally:
            marker.unlink(missing_ok=True)
            made = lambda: [p for p in self.dir.glob("kernels-*.csv") if p.stat().st_mtime >= since]
            # each process writes its .done once the round's dispatches have completed; one that ended in the round
            # (an offline engine inside its bench client) has flushed its file to its last millisecond
            alive = lambda p: Path(f"/proc/{p.name.split('-')[1]}").exists()
            deadline = time.time() + 30
            while time.time() < deadline and not all(p.with_suffix(".done").exists() or not alive(p) for p in made()):
                time.sleep(0.1)
            (out / "hsa").mkdir(exist_ok=True)
            for p in made():
                shutil.move(str(p), str(out / "hsa" / p.name))
                p.with_suffix(".done").unlink(missing_ok=True)
                for extra in (p.with_suffix(".skipped"), p.with_suffix(".unfinished")):
                    if extra.exists():
                        shutil.move(str(extra), str(out / "hsa" / extra.name))

    def intervals(self, out: Path) -> list[tuple[int, int]]:
        """Every kernel the round's processes ran, in Unix ns."""
        found = []
        for path in sorted((out / "hsa").glob("kernels-*.csv")):
            found += [tuple(map(int, line.split(","))) for line in path.read_text().splitlines() if line.count(",") == 1]
        if not found:
            raise RuntimeError("no kernel was recorded in the round")
        # a kernel that came with a completion signal of its own keeps it and is not timed; one that had not completed
        # 5 s after the round has no end
        count = lambda kind: sum(int(p.read_text()) for p in (out / "hsa").glob(f"kernels-*.{kind}"))
        if count("skipped") > 0.01 * len(found):
            raise RuntimeError(f"{count('skipped')} of {len(found) + count('skipped')} kernels carried their own completion signal and were not timed")
        if count("unfinished") > 0.01 * len(found):
            raise RuntimeError(f"{count('unfinished')} kernels of the round had not completed 5 s after it")
        return found
