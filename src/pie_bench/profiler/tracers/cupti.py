"""Cupti: an NVIDIA GPU's kernel, copy and memset intervals from CUPTI's activity API alone, without nsys.

nsys traces every CUDA API call as well, and on engines that launch kernels one by one from Python (SGLang's and vLLM's
eager prefill) that cost lands in the measured round: an RTX 4090's SGLang Qwen3.5-0.8B prefill took 29 to 34% longer
under nsys. This tracer is a CUDA injection library (cupti_trace.c, built here against the CUPTI of an engine's own
wheel) that every engine process loads at CUDA init and that records nothing until the profiled round: then only the
device's activity records, as a binary of (start, end) pairs per process, with a clock pair to put them in Unix ns.
"""

from __future__ import annotations

import glob
import os
import shutil
import subprocess
import sys
import time
from contextlib import contextmanager
from pathlib import Path

from pie_bench.profiler.tracers.span import span

SHIM = Path(__file__).resolve().parent / "cupti_trace.c"
ARM_S = 120  # how long a process may take to start recording: CUPTI's first enable in a process with many modules loaded
# (vLLM's EngineCore) takes seconds, and a round started before it lost its first windows


def _cupti() -> tuple[Path, Path]:
    """The include and lib folders of a CUDA 13 CUPTI: the toolkit's, or an nvidia-cuda-cupti wheel's."""
    # the toolkit's CUPTI: extras/CUPTI, or the targets/ layout of the cuda-cupti-dev package
    roots = [Path("/usr/local/cuda/extras/CUPTI"), Path("/usr/local/cuda/targets/x86_64-linux"), Path("/usr/local/cuda/targets/sbsa-linux")]
    roots += [Path(p).parent.parent for p in glob.glob(str(Path.home() / ".cache/pie-bench/venv-*/lib/python3*/site-packages/nvidia/cu13/lib/libcupti.so*"))]
    roots += [Path(p).parent.parent for p in glob.glob(str(Path(sys.prefix) / "lib/python3*/site-packages/nvidia/cu13/lib/libcupti.so*"))]
    for r in roots:
        for lib in ("lib64", "lib"):
            if (r / "include" / "cupti_activity.h").exists() and list((r / lib).glob("libcupti.so*")):
                return r / "include", r / lib
    raise RuntimeError("no CUPTI headers and library: install nvidia-cuda-cupti (CUDA 13) or the toolkit's CUPTI")


class Tracer:
    name = "cupti"
    prefix: list[str] = []  # nothing launches the run: each engine process loads the library itself

    def __init__(self, out: Path):
        self.out = out
        self.dir = Path(os.environ.get("PIE_CUPTI_DIR") or f"/tmp/pie-cupti-{os.getpid()}")
        self.round = 0
        self.env: dict[str, str] = {}
        so = Path.home() / ".cache/pie-bench/cupti" / "libpiecupti.so"
        if not so.exists() or so.stat().st_mtime < SHIM.stat().st_mtime:
            inc, lib = _cupti()
            so.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run(["cc", "-O2", "-shared", "-fPIC", "-o", str(so), str(SHIM), f"-I{inc}", f"-L{lib}", "-l:" + sorted(p.name for p in lib.glob("libcupti.so*"))[0],
                            f"-Wl,-rpath,{lib}", "-lpthread"], check=True)
        shutil.rmtree(self.dir, ignore_errors=True)
        self.dir.mkdir(parents=True)
        self.env = {"CUDA_INJECTION64_PATH": str(so), "PIE_CUPTI_DIR": str(self.dir)}

    @contextmanager
    def recording(self, out: Path):
        """The activity records of every engine process while the block runs, moved to out/cupti/."""
        out.mkdir(parents=True, exist_ok=True)
        self.round += 1
        n = self.round
        (self.dir / "on.tmp").write_text(f"{n}\n")
        os.replace(self.dir / "on.tmp", self.dir / "on")  # whole: a process that reads it half-written records round 0
        deadline = time.time() + ARM_S
        while time.time() < deadline and not all((self.dir / f"{pid}-{n}.armed").exists() for pid in self._alive()):
            time.sleep(0.05)
        time.sleep(0.2)
        try:
            with span(out):
                yield
        finally:
            started = [p for p in self.dir.glob(f"*-{n}.bin")]
            (self.dir / "on").unlink(missing_ok=True)
            deadline = time.time() + 30
            while time.time() < deadline and not all((self.dir / p.name.replace(".bin", ".done")).exists() for p in started):
                time.sleep(0.05)
            dest = out / "cupti"
            dest.mkdir(exist_ok=True)
            for p in self.dir.glob(f"*-{n}.*"):
                shutil.move(str(p), dest / p.name)

    def _alive(self) -> list[int]:
        """The processes that loaded the library and still run."""
        pids = []
        for p in self.dir.glob("*.alive"):
            try:
                os.kill(int(p.stem), 0)
                pids.append(int(p.stem))
            except (OSError, ValueError):
                p.unlink(missing_ok=True)
        return pids

    def intervals(self, out: Path) -> list[tuple[int, int]]:
        """Every kernel, copy and memset the engine processes recorded, in Unix ns."""
        import array

        found: list[tuple[int, int]] = []
        for b in (out / "cupti").glob("*.bin"):
            cupti_ns, unix_ns = (int(x) for x in b.with_suffix(".clock").read_text().split())
            shift = unix_ns - cupti_ns
            a = array.array("Q")
            a.frombytes(b.read_bytes())
            found += [(a[i] + shift, a[i + 1] + shift) for i in range(0, len(a) - 1, 2)]
        if not found:
            raise RuntimeError("CUPTI recorded no device work (is the library loaded? CUDA_INJECTION64_PATH)")
        return found
