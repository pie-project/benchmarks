from __future__ import annotations


def short(workload):
    """The profiled round's workload: the benchmark's own shape and requests (at most 8), or 3 waves of its concurrency.
    A single-stream step is the median request's, and 4 requests let two lucky ones set it (pie's A40 Qwen3.5-0.8B
    prefill: 15.1 and 15.2 ms against 17.2 to 17.4 for the rest).

    PIE_BENCH_PROFILE_ROUND=full keeps a whole benchmark round, for a Mac that throttles within one: on the fanless
    m3-16g mlx-lm's 4th pf8-512 wave runs 25 to 55% slower than its first, so a 3-wave round leaves the slow wave out
    and profiles 12 to 14% under the benchmark's own step."""
    import os

    if os.environ.get("PIE_BENCH_PROFILE_ROUND") == "full":
        return workload
    p = dict(workload.params)
    if "num_requests" in p:
        p["num_requests"] = min(int(p["num_requests"]), 3 * int(p.get("concurrency", 1)))
    else:
        p["requests"] = min(int(p.get("requests", 4)), 8)
    return workload.model_copy(update={"params": p})
