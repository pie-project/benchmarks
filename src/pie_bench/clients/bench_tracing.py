from __future__ import annotations

import ctypes
import ctypes.util
import os
import time
from pathlib import Path


def end_trace() -> None:
    """Ends a CUPTI-profiled round (profiler/cupti.py) while an in-process engine still runs: at shutdown SGLang kills
    its scheduler process, and with it the device records CUPTI has not handed over yet."""
    d = os.environ.get("PIE_CUPTI_DIR")
    on = Path(d) / "on" if d else None
    if on is None or not on.exists():
        return
    try:
        n = on.read_text().strip()
        on.unlink()
    except OSError:
        return
    started = list(Path(d).glob(f"*-{n}.bin"))
    deadline = time.time() + 30
    while time.time() < deadline and not all(b.with_suffix(".done").exists() for b in started):
        time.sleep(0.05)


def _load_cudart():
    candidates = []
    if override := os.environ.get("CUDART_LIBRARY"):
        candidates.append(override)
    for env_name in ("CUDA_HOME", "CUDA_PATH"):
        if cuda_root := os.environ.get(env_name):
            candidates.extend(
                (
                    str(Path(cuda_root) / "lib64" / "libcudart.so"),
                    str(
                        Path(cuda_root)
                        / "targets"
                        / "x86_64-linux"
                        / "lib"
                        / "libcudart.so"
                    ),
                )
            )
    found = ctypes.util.find_library("cudart")
    if found:
        candidates.append(found)
    candidates.extend(
        [
            "libcudart.so",
            "libcudart.so.13",
            "/usr/local/cuda/lib64/libcudart.so",
            "/usr/local/cuda-13.0/lib64/libcudart.so",
        ]
    )
    last_error: Exception | None = None
    for candidate in candidates:
        try:
            return ctypes.CDLL(candidate)
        except OSError as exc:
            last_error = exc
    raise RuntimeError(f"could not load CUDA runtime: {last_error}")


def cuda_profiler_start(enabled: bool) -> None:
    if not enabled:
        return
    cudart = _load_cudart()
    rc = int(cudart.cudaProfilerStart())
    if rc != 0:
        raise RuntimeError(f"cudaProfilerStart failed with CUDA error {rc}")


def cuda_profiler_stop(enabled: bool) -> None:
    if not enabled:
        return
    cudart = _load_cudart()
    rc = int(cudart.cudaProfilerStop())
    if rc != 0:
        raise RuntimeError(f"cudaProfilerStop failed with CUDA error {rc}")


def xla_trace(action: str, folder: str | None = None) -> None:
    """Under the profiler (PIE_BENCH_JAX_TRACE_DIR), starts or stops the device trace of every engine process armed
    there and alive, and waits until each has started or written it. pie's server (pie-<pid>.pid, profiler/
    xla_trace.c) takes SIGUSR1 and SIGUSR2; processes that imported jax (<pid>.pid, profiler/jax_site) watch the
    folder's `command` file from a thread of their own, as a signal reaches Python only in a main thread that may be
    blocked. An engine that runs inside its bench client (pie's server, vLLM's engine core) is traced this way around
    the measured requests only; the profiler does the same around the whole round for a server already up."""
    import signal

    folder = folder or os.environ.get("PIE_BENCH_JAX_TRACE_DIR")
    if not folder or not (Path(folder) / "recording").exists():  # a benchmark round beside the profiled one runs untraced
        return
    # a trace starts in a second or two; writing one can take minutes
    marker, sig, timeout_s = {"start": ("started", signal.SIGUSR1, 120), "stop": ("done", signal.SIGUSR2, 900)}[action]
    seq = str(time.time_ns())
    names = []
    for p in Path(folder).glob("*.pid"):
        pid = int(p.stem.removeprefix("pie-"))
        try:
            os.kill(pid, 0)
        except OSError:
            continue
        names.append(p.stem)
        if p.stem.startswith("pie-"):
            (p.parent / f"{p.stem}.{marker}").unlink(missing_ok=True)
            os.kill(pid, sig)
    tmp = Path(folder) / f".command-{os.getpid()}"
    tmp.write_text(f"{seq} {action}")
    tmp.replace(Path(folder) / "command")
    deadline = time.monotonic() + timeout_s
    for name in names:
        path, jax = Path(folder) / f"{name}.{marker}", not name.startswith("pie-")
        while True:
            words = (path.read_text() if path.exists() else "").split()
            if words and (not jax or words[0] == seq):
                break
            if time.monotonic() > deadline:
                raise RuntimeError(f"{name}: no trace {marker} marker after {timeout_s} s")
            time.sleep(0.05)
        if words[jax:][:1] == ["error"]:
            raise RuntimeError(f"{name}: trace {marker}: {' '.join(words)}")
