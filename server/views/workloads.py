from __future__ import annotations

from server.views.matrix_files import load

THROUGHPUT = ["c32", "c64", "c256", "c8", "c4", "c16", "c128", "c512", "c1024"]
RAW = ["raw-512-256"]
SPEC = ["spec-512-256"]
PREFILL_BATCH = ["pf256-512", "pf4-512", "pf8-512", "pf16-512", "pf32-512", "pf64-512", "pf128-512", "pf512-512", "pf1024-512"]
CATEGORIES = (("throughput", THROUGHPUT, "Batching"), ("raw", RAW, "Raw"), ("spec", SPEC, "Speculative"), ("prefill_batch", PREFILL_BATCH, "Batched Prefill"))


WL_PRIORITY = {wl: (cat, i) for cat, ids, _ in CATEGORIES for i, wl in enumerate(ids)}


METRICS = ["decode_tok_s", "prefill_tok_s", "output_tok_s", "ttft_ms_p50", "ttft_ms_p99",
           "itl_ms_p50", "itl_ms_p99", "latency_ms_p50", "latency_ms_p99", "resident_gib", "load_s"]


def workloads() -> list[dict]:
    params = {w["id"]: w.get("params", {}) for w in load("workloads")["workloads"]}
    out = []
    for cat, ids, label in CATEGORIES:
        src = next((i for i in ids if i in params), None)
        p = params.get(src, {})
        shapes = {i: {"concurrency": params[i].get("concurrency") or 1, "prompt_tokens": params[i].get("prefill"),
                      "output_tokens": params[i].get("decode")} for i in ids if i in params}
        out.append({"id": cat, "label": label, "concurrency": p.get("concurrency") or (32 if cat == "throughput" else 1),
                    "prompt_tokens": p.get("prefill"), "output_tokens": p.get("decode"), "benchmark": ", ".join(ids),
                    "shapes": shapes})
    return out
