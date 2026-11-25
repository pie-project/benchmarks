"""Metal command buffers: the GPU's work intervals on Apple silicon, as Metal itself times them inside each engine process.

metal_cb.m, preloaded into the processes the job starts (DYLD_INSERT_LIBRARIES), wraps -commit of the device's command
buffers and, while the round's gate file exists, appends each buffer's GPUStartTime..GPUEndTime in Unix ns to
<dir>/<pid>.txt. There is no kernel tracing, so a host-bound engine runs at its own speed: xctrace's kernel event
tracing costs mlx-lm's 512-token prefill 8 to 15% on an M5 Max. A buffer's interval spans its encoders back to back.

On an M5 Max (gemma-4-e2b, 512-token prefill) the profiled walls came within 0.8% of the same session's benchmark for
pie and mlx-lm (xctrace: +2% and +13%), and the forward passes within 0.6% of xctrace's GPU intervals (22.42 vs 22.49 ms,
24.65 vs 24.50 ms). The default on Apple silicon; PIE_BENCH_METAL_TRACER=xctrace records with Instruments instead, for
an engine started through a system shell, which drops DYLD_INSERT_LIBRARIES.
"""

from __future__ import annotations

import json
import os
import subprocess
import time
from contextlib import contextmanager
from pathlib import Path

from pie_bench.profiler.tracers.span import span

SRC = Path(__file__).resolve().parent / "metal_command_buffers.m"
GATE_S = 0.1  # the processes' watchers look for the gate every 10 ms


class Tracer:
    name = "metal-cb"
    prefix: list[str] = []

    def __init__(self, out: Path):
        self.dir = out / "metal-cb"
        self.dir.mkdir(parents=True, exist_ok=True)
        lib = out / "metal_cb.dylib"
        subprocess.run(["cc", "-O2", "-dynamiclib", "-fno-objc-arc", "-framework", "Metal", "-framework", "Foundation", "-o", str(lib), str(SRC)], check=True)
        self.env = {"DYLD_INSERT_LIBRARIES": str(lib), "PIE_BENCH_METAL_CB_DIR": str(self.dir)}

    @contextmanager
    def recording(self, out: Path):
        """Opens the gate while the block runs; the buffers the job's processes completed in it go to out/metal-cb.json."""
        out.mkdir(parents=True, exist_ok=True)
        gate = self.dir / "recording"
        seen = {p: p.stat().st_size for p in self.dir.glob("*.txt")}
        gate.touch()
        time.sleep(GATE_S)
        try:
            with span(out):
                yield
        finally:
            time.sleep(GATE_S)
            gate.unlink(missing_ok=True)
            time.sleep(GATE_S)
            buffers = {}
            for p in self.dir.glob("*.txt"):
                with open(p) as f:
                    f.seek(seen.get(p, 0))
                    rows = [tuple(int(x) for x in line.split()) for line in f.read().splitlines() if line.count(" ") == 1]
                if rows:
                    buffers[p.stem] = rows
            (out / "metal-cb.json").write_text(json.dumps(buffers))

    def intervals(self, out: Path) -> list[tuple[int, int]]:
        """The GPU intervals of the command buffers the round's processes completed, in Unix ns."""
        buffers = json.loads((out / "metal-cb.json").read_text())
        if not buffers:
            raise RuntimeError("no process committed a Metal command buffer in the round (was the engine started with the preload?)")
        return [(s, e) for rows in buffers.values() for s, e in rows]


def chosen() -> bool:
    """Whether this job times the GPU from the command buffers (the default) instead of xctrace (PIE_BENCH_METAL_TRACER=xctrace)."""
    return os.environ.get("PIE_BENCH_METAL_TRACER", "cb") != "xctrace"
