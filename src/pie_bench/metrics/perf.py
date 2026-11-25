from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from pie_bench.metrics.fairness import (
    FAIR_DEFINITION_VERSION,
    cache_verdict,
    fair_prefill_tok_s,
    prefill_mismatch,
)
from pie_bench.schema import PerfMetrics


def _all_completed(json_out: Path) -> bool:
    try:
        s = json.loads(json_out.read_text()).get("summary", {})
    except (OSError, ValueError):
        return False
    return (
        bool(s.get("requests")) and s.get("completed") == s.get("requests") and not s.get("failed")
    )


def _pct(values: list[float], q: float) -> float | None:
    if not values:
        return None
    return float(np.percentile(np.asarray(values, dtype=float), q))


COLD_OPENING_TOKENS = 32


def serial_clock(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    timed = [
        r
        for r in rows
        if r.get("client_send_s") is not None and r.get("client_return_s") is not None
    ]
    if len(timed) != len(rows) or len(rows) < 2:
        return rows
    out, prev_return = [], None
    for r in sorted(rows, key=lambda r: r["client_send_s"]):
        start = r["client_send_s"] if prev_return is None else max(r["client_send_s"], prev_return)
        shift = start - r["client_send_s"]
        if shift > 0:
            r = {
                **r,
                "ttft_s": r["ttft_s"] - shift if r.get("ttft_s") is not None else None,
                "latency_s": r["latency_s"] - shift if r.get("latency_s") is not None else None,
            }
        out.append(r)
        prev_return = r["client_return_s"]
    return out


def perf_from_common_json(
    summary: dict[str, Any],
    requests: list[dict[str, Any]],
    num_layers: int | None,
    concurrency: int | None = None,
    *,
    cold_tags: bool = False,
) -> PerfMetrics:
    completed = [r for r in requests if r.get("ok")]
    if concurrency == 1:
        completed = serial_clock(completed)
    out_tok = int(summary.get("output_tokens") or sum(r.get("output_tokens", 0) for r in completed))
    prompt_tok = int(
        summary.get("prompt_tokens") or sum(r.get("prompt_tokens", 0) for r in completed)
    )
    wall = float(summary.get("wall_s") or 0.0)
    output_tok_s = float(summary.get("output_tok_per_s") or (out_tok / wall if wall else 0.0))
    ttft = [r["ttft_s"] * 1000.0 for r in completed if r.get("ttft_s") is not None]
    decode_lane = []
    itl_all: list[float] = []
    for r in completed:
        lat = r.get("latency_s")
        tt = r.get("ttft_s")
        n = r.get("output_tokens") or 0
        if lat and tt is not None and n > 1 and lat > tt:
            decode_lane.append((n - 1) / (lat - tt))
            itl_all.append((lat - tt) * 1000.0 / (n - 1))
    counters = {}
    for k, v in (summary.get("config") or {}).items():
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            counters[str(k)] = float(v)
    concurrency = concurrency or int((summary.get("config") or {}).get("concurrency") or 0) or None
    decode_tok_s = float(np.median(decode_lane)) if decode_lane else None
    config_cached = counters.get("cached_prompt_tokens")
    by_construction = config_cached is None and cold_tags
    if by_construction:
        config_cached = 0.0
        counters["cold_by_construction"] = 1.0
    elif (
        cold_tags
        and config_cached
        and completed
        and config_cached / len(completed) <= COLD_OPENING_TOKENS
    ):
        counters["cold_opening_cached_per_request"] = config_cached / len(completed)
        config_cached = 0.0
    verdict = cache_verdict(completed, config_cached)
    prefill_tok_s = fair_prefill_tok_s(
        completed, concurrency=concurrency, config_cached=config_cached
    )
    counters["fair_def"] = float(FAIR_DEFINITION_VERSION)
    counters["cold_cache_verified"] = 1.0 if verdict == "cold" else 0.0
    if prefill_tok_s is not None:
        counters["prefill_ttft_mismatch"] = (
            1.0
            if prefill_mismatch(prefill_tok_s, _pct(ttft, 50), prompt_tok, len(completed))
            else 0.0
        )
    batched_prefill = (concurrency or 0) > 1 and completed and wall and out_tok <= len(completed)
    if batched_prefill:
        prefill_tok_s = prompt_tok / wall
    primary = (
        "prefill_tok_s"
        if batched_prefill
        else "decode_tok_s"
        if (concurrency in (None, 1)) and decode_tok_s
        else "output_tok_s"
    )
    ms_per_tok_per_layer = None
    if num_layers and decode_tok_s:
        ms_per_tok_per_layer = 1000.0 / decode_tok_s / num_layers
    return PerfMetrics(
        primary=primary,
        decode_tok_s=decode_tok_s,
        prefill_tok_s=prefill_tok_s,
        output_tok_s=output_tok_s or None,
        ttft_ms_p50=_pct(ttft, 50) if ttft else (summary.get("ttft_p50_ms") or None),
        ttft_ms_p99=_pct(ttft, 99) if ttft else (summary.get("ttft_p99_ms") or None),
        itl_ms_p50=_pct(itl_all, 50),
        itl_ms_p99=_pct(itl_all, 99),
        latency_ms_p50=summary.get("latency_p50_ms"),
        latency_ms_p99=summary.get("latency_p99_ms"),
        prompt_tokens=prompt_tok,
        output_tokens=out_tok,
        requests=int(summary.get("requests") or len(requests)),
        failed=int(summary.get("failed") or sum(1 for r in requests if not r.get("ok"))),
        ms_per_token_per_layer=ms_per_tok_per_layer,
        counters=counters,
    )
