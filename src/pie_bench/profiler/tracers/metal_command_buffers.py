from __future__ import annotations

import json
import os
import subprocess
import time
from contextlib import contextmanager
from pathlib import Path

from pie_bench.profiler.tracers.span import span

SRC = Path(__file__).resolve().parent / "metal_command_buffers.m"
GATE_S = 0.1


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
        buffers = json.loads((out / "metal-cb.json").read_text())
        if not buffers:
            raise RuntimeError("no process committed a Metal command buffer in the round (was the engine started with the preload?)")
        return [(s, e) for rows in buffers.values() for s, e in rows]


def chosen() -> bool:
    return os.environ.get("PIE_BENCH_METAL_TRACER", "cb") != "xctrace"
