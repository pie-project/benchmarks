"""Unit: a benchmark's measured windows and the work in them, turned into wall, forward and idle ms per benchmark unit.

Times are Unix nanoseconds. The windows come from the bench client's own clock (its JSON with --report-timing); the
device intervals from a tracer. Forward is the device's busy time inside the windows, idle is the rest of the wall.
"""

from __future__ import annotations

import bisect
import statistics
from dataclasses import dataclass

SETUPS = ("decode", "prefill", "spec", "batching", "pbatch")


@dataclass
class Measured:
    """The windows a benchmark measured and how many of its units of work they hold."""

    unit: str
    windows: list[tuple[int, int]]
    units: float
    # each window's own units where the benchmark's number is the median of its requests' rates (decode, spec, prefill)
    each: list[float] | None = None


def union(intervals) -> list[tuple[int, int]]:
    """The intervals merged: sorted, none overlapping, covering the same time."""
    out: list[list[int]] = []
    for start, end in sorted(intervals):
        if end <= start:
            continue
        if out and start <= out[-1][1]:
            out[-1][1] = max(out[-1][1], end)
        else:
            out.append([start, end])
    return [(s, e) for s, e in out]


def covered(merged: list[tuple[int, int]], window: tuple[int, int]) -> int:
    """How much of the window the merged intervals (union's output) cover."""
    lo, hi = window
    ends = [e for _, e in merged]
    total = 0
    for start, end in merged[bisect.bisect_right(ends, lo):]:
        if start >= hi:
            break
        total += min(end, hi) - max(start, lo)
    return total


def measured(bench: dict, setup: str, concurrency: int, prompt: int) -> Measured:
    """The measured windows of a bench client's run, in the unit of a setup: an output token (decode, spec), a prompt
    of `prompt` tokens (prefill), a batched step of `concurrency` requests (batching) or a wave of `concurrency` such
    prompts (pbatch). Units count tokens, so two engines that ran different shapes still share one unit."""
    epoch = (bench.get("summary", {}).get("config") or {}).get("client timing epoch unix s")
    if epoch is None:
        raise ValueError("the bench client ran without --report-timing, so its requests have no clock")
    reqs = [r for r in bench.get("requests", []) if r.get("ok") and r.get("client_send_s") is not None and r.get("ttft_s") is not None]
    if not reqs:
        raise ValueError("no timed request in the bench client's run")
    base = round(epoch * 1e9)
    ns = lambda s: base + round(s * 1e9)
    sent = lambda r: r["client_send_s"]
    if setup in ("decode", "spec"):
        reqs = [r for r in reqs if r["output_tokens"] > 1]
        return Measured("ms per output token", [(ns(sent(r) + r["ttft_s"]), ns(sent(r) + r["latency_s"])) for r in reqs],
                        sum(r["output_tokens"] - 1 for r in reqs), [r["output_tokens"] - 1 for r in reqs])
    if setup == "prefill":
        return Measured(f"ms per {prompt}-token prompt", [(ns(sent(r)), ns(sent(r) + r["ttft_s"])) for r in reqs],
                        sum(r["prompt_tokens"] for r in reqs) / prompt, [r["prompt_tokens"] / prompt for r in reqs])
    window = [(ns(min(sent(r) for r in reqs)), ns(max(sent(r) + r["latency_s"] for r in reqs)))]
    if setup == "batching":
        return Measured(f"ms per batched decode step ({concurrency} requests)", window, sum(r["output_tokens"] for r in reqs) / concurrency)
    if setup == "pbatch":
        return Measured(f"ms per wave of {concurrency} {prompt}-token prompts", window, sum(r["prompt_tokens"] for r in reqs) / (concurrency * prompt))
    raise ValueError(f"unknown setup {setup!r}")


def split(m: Measured, intervals) -> dict:
    """Wall and forward ms per unit (idle is the difference); every window must hold device work."""
    merged = union(intervals)
    busy = [covered(merged, w) for w in m.windows]
    if not all(busy):
        raise ValueError(f"the trace shows no device work in {busy.count(0)} of {len(busy)} measured windows")
    if m.each:
        # the benchmark's rate is the median of its requests' own rates (node/fair.py, engines/base.py), so the profiled
        # step is taken the same way: one slow request moves neither
        rate = lambda ns: statistics.median(u / t for u, t in zip(m.each, ns))
        return {"unit": m.unit, "wall_ms": 1 / rate([e - s for s, e in m.windows]) / 1e6, "forward_ms": 1 / rate(busy) / 1e6}
    wall = sum(e - s for s, e in m.windows)
    return {"unit": m.unit, "wall_ms": wall / m.units / 1e6, "forward_ms": sum(busy) / m.units / 1e6}
