"""Fair prefill and TTFT for every engine: one definition, cold caches only.

Definitions (version ``FAIR_DEFINITION_VERSION``, stored as the ``fair_def``
counter on every row):

* TTFT (client): seconds from the client sending the request to the client
  receiving the first generated token. Measured by ``bench/common.py``
  for every engine; pie's stamp is its ``t0`` message, sent when the first
  sampled token reaches guest code.
* Prefill time: the single-stream TTFT, i.e. the same client stamp. Under
  concurrency the TTFT contains queueing, so no prefill rate is reported.
* ``prefill_tok_s`` per request = ``prompt_tokens / ttft_s``, where
  ``prompt_tokens`` is the count the engine actually processed. The row value is
  the median over measured requests.
* Only a row whose requests all report zero cached prompt tokens is cold; a
  row with any cached token, or without the cache count, gets no prefill value.
* Consistency: ``prefill_tok_s * ttft_p50_s`` must be within 15% of the median
  prompt length, otherwise the row is flagged.

Cold prompts: every request starts with its own 16-hex tag derived from
``(seed, workload id, index)``, so no two requests share a leading token and
no prefix cache can hit. Since version 2 each request also has its own body: with
one body for all, greedy decoding wrote one answer in every lane, so a MoE batch
routed every request to the same experts and read a fraction of their weights
(TensorRT-LLM Qwen3.6-35B-A3B c256 on an RTX PRO 6000 ran above the card's
bandwidth bound). The same list is written for every engine.
"""

from __future__ import annotations

import hashlib
import statistics
from collections.abc import Callable, Iterable, Mapping, Sequence
from typing import Any

FAIR_DEFINITION_VERSION = 2
#: seed of every cold prompt list; changing it changes every cold prompt
COLD_SEED = "pie-fair-v1"
PREFILL_TOLERANCE = 0.15
TAG_HEX_CHARS = 16
#: spare prompts beyond the measured requests (warmup and retries)
COLD_SLACK = 8


def cold_tag(seed: str, workload_id: str, index: int) -> str:
    """Deterministic, unique-per-index 16-hex tag (same for every engine)."""
    digest = hashlib.sha256(f"{seed}|{workload_id}|{index}".encode()).hexdigest()
    return digest[:TAG_HEX_CHARS]


def cold_prompts(body: str | Callable[[int], str], *, workload_id: str, seed: str, count: int) -> list[str]:
    """``count`` prompts that differ from their first character on.

    The tag leads the prompt, so no two prompts share a prefix longer than the
    tokenizer's common opening (and a BOS token at most). ``body`` is one text for
    every request, or a function of the request's index giving each its own.
    """
    if count < 1:
        raise ValueError("count must be at least 1")
    text = body if callable(body) else (lambda i: body)
    return [f"[{cold_tag(seed, workload_id, i)}] {text(i)}" for i in range(count)]


def cold_request_count(params: Mapping[str, Any]) -> int:
    """How many cold prompts a workload needs: its measured requests plus slack."""
    measured = int(params.get("num_requests") or params.get("requests") or 1)
    return measured + COLD_SLACK


def shared_prefix_len(a: str, b: str) -> int:
    n = min(len(a), len(b))
    i = 0
    while i < n and a[i] == b[i]:
        i += 1
    return i


def max_pairwise_prefix(prompts: Sequence[str]) -> int:
    """Longest common prefix (characters) over all pairs; 0 when fully distinct."""
    best = 0
    for i in range(len(prompts)):
        for j in range(i + 1, len(prompts)):
            best = max(best, shared_prefix_len(prompts[i], prompts[j]))
    return best


def prefill_tok_s_one(prompt_tokens: int | None, ttft_s: float | None) -> float | None:
    """Prefill rate of one request: prompt tokens over client TTFT in seconds."""
    if not prompt_tokens or ttft_s is None or ttft_s <= 0:
        return None
    return float(prompt_tokens) / float(ttft_s)


def cache_verdict(requests: Iterable[Mapping[str, Any]], config_cached: float | None = None) -> str:
    """``"cold"``, ``"warm"`` or ``"unverified"``.

    ``config_cached`` is the summary-level cached prompt count, used when the
    engine reports it only in aggregate (openai-compatible servers).
    """
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
    """Row value of ``prefill_tok_s``: median per-request rate, cold single-stream only."""
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
    """``prefill_tok_s * ttft_s / per_request_prompt``; 1.0 means the three agree.

    ``prompt_tokens_total`` is the sum over the measured requests (the row's
    ``prompt_tokens``), so the per-request prompt is the total over ``requests``.
    """
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
    """True when prefill x TTFT differs from the per-request prompt length by more than 15%."""
    ratio = prefill_consistency(prefill_tok_s, ttft_ms_p50, prompt_tokens_total, requests)
    return ratio is not None and abs(ratio - 1.0) > PREFILL_TOLERANCE
