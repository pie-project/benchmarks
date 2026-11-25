from __future__ import annotations

import asyncio
import contextlib
import ctypes
import ctypes.util
import os
import signal
import time
from pathlib import Path

CUDART_FALLBACKS = (
    "libcudart.so",
    "libcudart.so.13",
    "/usr/local/cuda/lib64/libcudart.so",
    "/usr/local/cuda-13.0/lib64/libcudart.so",
)

XLA_TRACE_STEPS = {
    "start": ("started", "SIGUSR1", 120),
    "stop": ("done", "SIGUSR2", 900),
}


def monotonic_ns() -> int:
    if hasattr(time, "clock_gettime_ns"):
        return time.clock_gettime_ns(time.CLOCK_MONOTONIC)
    return time.monotonic_ns()


def seconds_after(epoch_ns: int | None, ns: int) -> float | None:
    if epoch_ns is None:
        return None
    return (ns - epoch_ns) / 1_000_000_000.0


def end_trace() -> None:
    folder = os.environ.get("PIE_CUPTI_DIR")
    switch = Path(folder) / "on" if folder else None
    if switch is None or not switch.exists():
        return
    try:
        round_id = switch.read_text().strip()
        switch.unlink()
    except OSError:
        return
    started = list(Path(folder).glob(f"*-{round_id}.bin"))
    deadline = time.time() + 30
    while time.time() < deadline and not all(b.with_suffix(".done").exists() for b in started):
        time.sleep(0.05)


def _cudart_candidates() -> list[str]:
    candidates = []
    if override := os.environ.get("CUDART_LIBRARY"):
        candidates.append(override)
    for env_name in ("CUDA_HOME", "CUDA_PATH"):
        if cuda_root := os.environ.get(env_name):
            candidates.append(str(Path(cuda_root) / "lib64" / "libcudart.so"))
            candidates.append(
                str(Path(cuda_root) / "targets" / "x86_64-linux" / "lib" / "libcudart.so")
            )
    if found := ctypes.util.find_library("cudart"):
        candidates.append(found)
    candidates.extend(CUDART_FALLBACKS)
    return candidates


def _load_cudart():
    last_error: Exception | None = None
    for candidate in _cudart_candidates():
        try:
            return ctypes.CDLL(candidate)
        except OSError as exc:
            last_error = exc
    raise RuntimeError(f"could not load CUDA runtime: {last_error}")


def cuda_profiler_start(enabled: bool) -> None:
    if not enabled:
        return
    rc = int(_load_cudart().cudaProfilerStart())
    if rc != 0:
        raise RuntimeError(f"cudaProfilerStart failed with CUDA error {rc}")


def cuda_profiler_stop(enabled: bool) -> None:
    if not enabled:
        return
    rc = int(_load_cudart().cudaProfilerStop())
    if rc != 0:
        raise RuntimeError(f"cudaProfilerStop failed with CUDA error {rc}")


async def _capture_profiler_window(delay_s: float, duration_s: float) -> None:
    await asyncio.sleep(delay_s)
    cuda_profiler_start(True)
    try:
        await asyncio.sleep(duration_s)
    finally:
        cuda_profiler_stop(True)


def start_measured_profiler(args) -> asyncio.Task | None:
    if args.cuda_profiler_capture and args.cuda_profiler_duration_s > 0:
        return asyncio.create_task(
            _capture_profiler_window(args.cuda_profiler_delay_s, args.cuda_profiler_duration_s)
        )
    cuda_profiler_start(args.cuda_profiler_capture)
    return None


async def stop_measured_profiler(args, window: asyncio.Task | None) -> None:
    if window is None:
        cuda_profiler_stop(args.cuda_profiler_capture)
        return
    if not window.done():
        window.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await window


def _signal_traced_processes(folder: Path, marker: str, sig: int) -> list[str]:
    names = []
    for pid_file in folder.glob("*.pid"):
        pid = int(pid_file.stem.removeprefix("pie-"))
        try:
            os.kill(pid, 0)
        except OSError:
            continue
        names.append(pid_file.stem)
        if pid_file.stem.startswith("pie-"):
            (pid_file.parent / f"{pid_file.stem}.{marker}").unlink(missing_ok=True)
            os.kill(pid, sig)
    return names


def _write_trace_command(folder: Path, seq: str, action: str) -> None:
    tmp = folder / f".command-{os.getpid()}"
    tmp.write_text(f"{seq} {action}")
    tmp.replace(folder / "command")


def _await_trace_marker(
    folder: Path, name: str, marker: str, seq: str, deadline: float, timeout_s: int
) -> None:
    path, jax = folder / f"{name}.{marker}", not name.startswith("pie-")
    while True:
        words = (path.read_text() if path.exists() else "").split()
        if words and (not jax or words[0] == seq):
            break
        if time.monotonic() > deadline:
            raise RuntimeError(f"{name}: no trace {marker} marker after {timeout_s} s")
        time.sleep(0.05)
    if words[jax:][:1] == ["error"]:
        raise RuntimeError(f"{name}: trace {marker}: {' '.join(words)}")


def xla_trace(action: str, folder: str | None = None) -> None:
    folder = folder or os.environ.get("PIE_BENCH_JAX_TRACE_DIR")
    if not folder or not (Path(folder) / "recording").exists():
        return
    trace_dir = Path(folder)
    marker, sig_name, timeout_s = XLA_TRACE_STEPS[action]
    seq = str(time.time_ns())
    names = _signal_traced_processes(trace_dir, marker, getattr(signal, sig_name))
    _write_trace_command(trace_dir, seq, action)
    deadline = time.monotonic() + timeout_s
    for name in names:
        _await_trace_marker(trace_dir, name, marker, seq, deadline, timeout_s)
