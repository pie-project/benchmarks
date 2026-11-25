from __future__ import annotations

import hashlib
import statistics
from collections.abc import Callable, Iterable, Mapping, Sequence
from typing import Any

FAIR_DEFINITION_VERSION = 2
COLD_SEED = "pie-fair-v1"
PREFILL_TOLERANCE = 0.15
TAG_HEX_CHARS = 16
COLD_SLACK = 8


def cold_tag(seed: str, workload_id: str, index: int) -> str:
    digest = hashlib.sha256(f"{seed}|{workload_id}|{index}".encode()).hexdigest()
    return digest[:TAG_HEX_CHARS]


def cold_prompts(body: str | Callable[[int], str], *, workload_id: str, seed: str, count: int) -> list[str]:
    if count < 1:
        raise ValueError("count must be at least 1")
    text = body if callable(body) else (lambda i: body)
    return [f"[{cold_tag(seed, workload_id, i)}] {text(i)}" for i in range(count)]


def cold_request_count(params: Mapping[str, Any]) -> int:
    measured = int(params.get("num_requests") or params.get("requests") or 1)
    return measured + COLD_SLACK


def shared_prefix_len(a: str, b: str) -> int:
    n = min(len(a), len(b))
    i = 0
    while i < n and a[i] == b[i]:
        i += 1
    return i


def max_pairwise_prefix(prompts: Sequence[str]) -> int:
    best = 0
    for i in range(len(prompts)):
        for j in range(i + 1, len(prompts)):
            best = max(best, shared_prefix_len(prompts[i], prompts[j]))
    return best


def prefill_tok_s_one(prompt_tokens: int | None, ttft_s: float | None) -> float | None:
    if not prompt_tokens or ttft_s is None or ttft_s <= 0:
        return None
    return float(prompt_tokens) / float(ttft_s)


def cache_verdict(requests: Iterable[Mapping[str, Any]], config_cached: float | None = None) -> str:
    reqs = list(requests)
    per_request = [r.get("cached_prompt_tokens") for r in reqs if r.get("ok", True)]
    if per_request and all(v is not None for v in per_request):
        return "warm" if any(float(v) > 0 for v in per_request) else "cold"
    if config_cached is not None:
        return "warm" if float(config_cached) > 0 else "cold"
    return "unverified"


def fair_prefill_tok_s(
    requests: Sequence[Mapping[str, Any]],
    *,
    concurrency: int | None,
    config_cached: float | None = None,
) -> float | None:
    if concurrency not in (None, 1):
        return None
    if cache_verdict(requests, config_cached) != "cold":
        return None
    rates = [
        prefill_tok_s_one(r.get("prompt_tokens"), r.get("ttft_s"))
        for r in requests
        if r.get("ok", True)
    ]
    rates = [x for x in rates if x is not None]
    if not rates:
        return None
    return float(statistics.median(rates))


def prefill_consistency(
    prefill_tok_s: float | None,
    ttft_ms_p50: float | None,
    prompt_tokens_total: float | None,
    requests: float | None,
) -> float | None:
    if not prefill_tok_s or not ttft_ms_p50 or not prompt_tokens_total or not requests:
        return None
    per_request = float(prompt_tokens_total) / float(requests)
    return prefill_tok_s * (ttft_ms_p50 / 1000.0) / per_request


def prefill_mismatch(
    prefill_tok_s: float | None,
    ttft_ms_p50: float | None,
    prompt_tokens_total: float | None,
    requests: float | None,
) -> bool:
    ratio = prefill_consistency(prefill_tok_s, ttft_ms_p50, prompt_tokens_total, requests)
    return ratio is not None and abs(ratio - 1.0) > PREFILL_TOLERANCE
