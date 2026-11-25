from __future__ import annotations


def short(workload):
    import os

    if os.environ.get("PIE_BENCH_PROFILE_ROUND") == "full":
        return workload
    p = dict(workload.params)
    if "num_requests" in p:
        p["num_requests"] = min(int(p["num_requests"]), 3 * int(p.get("concurrency", 1)))
    else:
        p["requests"] = min(int(p.get("requests", 4)), 8)
    return workload.model_copy(update={"params": p})
