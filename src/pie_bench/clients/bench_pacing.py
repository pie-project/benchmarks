from __future__ import annotations

import asyncio
import ctypes
import ctypes.util
import os
import random
import sys
import time
from typing import Any

from bench_results import percentile


def arrival_schedule(
    n: int, rate: float, process: str, seed: int
) -> list[float]:
    if rate <= 0:
        return [0.0] * n
    rng = random.Random(seed)
    offsets: list[float] = []
    t = 0.0
    for _ in range(n):
        offsets.append(t)
        t += rng.expovariate(rate) if process == "poisson" else 1.0 / rate
    return offsets


class ArrivalPacer:

    def __init__(self, offsets: list[float]) -> None:
        self._offsets = offsets
        self._t0: float | None = None
        self.lag_s: list[float] = []

    @property
    def enabled(self) -> bool:
        return any(o > 0.0 for o in self._offsets)

    def start(self) -> None:
        self._t0 = time.perf_counter()

    async def wait(self, index: int) -> None:
        if self._t0 is None or index >= len(self._offsets):
            return
        due = self._t0 + self._offsets[index]
        delay = due - time.perf_counter()
        if delay > 0:
            await asyncio.sleep(delay)
        self.lag_s.append(max(0.0, time.perf_counter() - due))

    def stats(self) -> dict[str, Any]:
        if not self.lag_s:
            return {}
        return {
            "arrival_lag_p50_ms": (percentile(self.lag_s, 0.50) or 0.0) * 1e3,
            "arrival_lag_p99_ms": (percentile(self.lag_s, 0.99) or 0.0) * 1e3,
            "arrival_lag_max_ms": max(self.lag_s) * 1e3,
            "arrival_span_s": self._offsets[-1] if self._offsets else 0.0,
        }


def mac_thermal_state() -> str | None:
    if sys.platform != "darwin":
        return None
    try:
        objc = ctypes.cdll.LoadLibrary(ctypes.util.find_library("objc"))
        ctypes.cdll.LoadLibrary("/System/Library/Frameworks/Foundation.framework/Foundation")
        objc.objc_getClass.restype = ctypes.c_void_p
        objc.objc_getClass.argtypes = [ctypes.c_char_p]
        objc.sel_registerName.restype = ctypes.c_void_p
        objc.sel_registerName.argtypes = [ctypes.c_char_p]
        obj = ctypes.CFUNCTYPE(ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p)(("objc_msgSend", objc))
        num = ctypes.CFUNCTYPE(ctypes.c_long, ctypes.c_void_p, ctypes.c_void_p)(("objc_msgSend", objc))
        info = obj(objc.objc_getClass(b"NSProcessInfo"), objc.sel_registerName(b"processInfo"))
        return ("nominal", "fair", "serious", "critical")[num(info, objc.sel_registerName(b"thermalState"))]
    except Exception:
        return None


def cool_before_request(timeout_s: float = 600, poll_s: float = 5) -> float:
    if os.environ.get("PIE_BENCH_SETTLE", "1") == "0":
        return 0.0
    t0 = time.monotonic()
    while mac_thermal_state() not in (None, "nominal") and time.monotonic() - t0 < timeout_s:
        time.sleep(poll_s)
    return time.monotonic() - t0


async def run_timed_warmup(run_once, seconds: float, label: str = "pie") -> int:
    if seconds <= 0:
        return 0
    import time as _time
    start = _time.monotonic()
    passes = 0
    while _time.monotonic() - start < seconds:
        await run_once()
        passes += 1
    print(f"[{label}-bench] warmup: {passes} extra pass(es) over "
          f"{_time.monotonic() - start:.1f}s", flush=True)
    return passes


def run_timed_warmup_sync(run_once, seconds: float, label: str = "vllm") -> int:
    if seconds <= 0:
        return 0
    import time as _time
    start = _time.monotonic()
    passes = 0
    while _time.monotonic() - start < seconds:
        run_once()
        passes += 1
    print(f"[{label}-bench] warmup: {passes} extra pass(es) over "
          f"{_time.monotonic() - start:.1f}s", flush=True)
    return passes
