from __future__ import annotations

import time
from typing import Any

from bench_results import RequestResult
from bench_tracing import monotonic_ns, seconds_after


class StreamTimer:
    def __init__(self, epoch_ns: int | None) -> None:
        self.epoch_ns = epoch_ns
        self.start = time.perf_counter()
        self.client_send_s = seconds_after(epoch_ns, monotonic_ns())
        self.ttft_s: float | None = None
        self.last_tick: float | None = None
        self.gaps_us: list[int] = []
        self.arrival_s: list[float] = []
        self.arrival_ns: list[int] = []
        self.tokens = 0

    def stamp(self) -> tuple[float, int]:
        return time.perf_counter(), monotonic_ns()

    def saw(self, total: int, stamp: tuple[float, int]) -> None:
        if total <= self.tokens:
            return
        now, now_ns = stamp
        if self.epoch_ns is not None:
            new = total - self.tokens
            self.arrival_s.extend([seconds_after(self.epoch_ns, now_ns)] * new)
            self.arrival_ns.extend([now_ns] * new)
        if self.ttft_s is None:
            self.ttft_s = now - self.start
        else:
            self.gaps_us.append(int((now - self.last_tick) * 1e6))
        self.last_tick = now
        self.tokens = total

    def result(self, prompt_count: int, **extra: Any) -> RequestResult:
        returned = time.perf_counter()
        returned_ns = monotonic_ns()
        return RequestResult(
            True,
            returned - self.start,
            self.tokens,
            prompt_count,
            ttft_s=self.ttft_s,
            intertoken_us=self.gaps_us or None,
            client_send_s=self.client_send_s,
            token_arrival_s=self.arrival_s or None,
            token_arrival_monotonic_ns=self.arrival_ns or None,
            client_return_s=seconds_after(self.epoch_ns, returned_ns),
            **extra,
        )

    def failure(self, prompt_count: int, e: Exception, tokens: int | None = None) -> RequestResult:
        return RequestResult(
            False,
            time.perf_counter() - self.start,
            self.tokens if tokens is None else tokens,
            prompt_count,
            error=f"{type(e).__name__}: {e}",
        )
