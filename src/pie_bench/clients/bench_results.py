from __future__ import annotations

import argparse
import json
import math
import statistics
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass
class RequestResult:
    ok: bool
    latency_s: float
    output_tokens: int
    prompt_tokens: int | None = None
    error: str | None = None
    ttft_s: float | None = None
    intertoken_us: list[int] | None = None
    client_send_s: float | None = None
    token_arrival_s: list[float] | None = None
    token_arrival_monotonic_ns: list[int] | None = None
    client_return_s: float | None = None
    process_id: str | None = None
    prologue_us: list[int] | None = None
    speculation: dict[str, Any] | None = None
    output_token_sha256: str | None = None
    output_token_ids: list[int] | None = None
    output_text: str | None = None


@dataclass
class BenchSummary:
    mode: str
    engine: str
    model: str
    requests: int
    completed: int
    failed: int
    wall_s: float
    output_tokens: int
    prompt_tokens: int | None
    req_per_s: float
    output_tok_per_s: float
    latency_mean_ms: float | None
    latency_p50_ms: float | None
    latency_p95_ms: float | None
    latency_p99_ms: float | None
    config: dict[str, Any]
    ttft_mean_ms: float | None = None
    ttft_p50_ms: float | None = None
    ttft_p95_ms: float | None = None
    ttft_p99_ms: float | None = None
    intertoken_p50_ms: float | None = None
    intertoken_p99_ms: float | None = None
    intertoken_max_ms: float | None = None


def percentile(xs: list[float], q: float) -> float | None:
    if not xs:
        return None
    s = sorted(xs)
    k = (len(s) - 1) * q
    lo = math.floor(k)
    hi = math.ceil(k)
    if lo == hi:
        return s[int(k)]
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


def summarize(
    *,
    mode: str,
    engine: str,
    model: str,
    results: list[RequestResult],
    wall_s: float,
    config: dict[str, Any],
) -> BenchSummary:
    ok = [r for r in results if r.ok]
    lats = [r.latency_s for r in ok if r.latency_s > 0.0]
    output_tokens = sum(r.output_tokens for r in ok)
    prompt_known = [r.prompt_tokens for r in ok if r.prompt_tokens is not None]
    prompt_tokens = sum(prompt_known) if len(prompt_known) == len(ok) else None
    ttfts = [r.ttft_s for r in ok if getattr(r, "ttft_s", None) is not None]
    gaps_ms = [
        g / 1000.0
        for r in ok
        for g in (getattr(r, "intertoken_us", None) or [])
    ]
    return BenchSummary(
        mode=mode,
        engine=engine,
        model=model,
        requests=len(results),
        completed=len(ok),
        failed=len(results) - len(ok),
        wall_s=wall_s,
        output_tokens=output_tokens,
        prompt_tokens=prompt_tokens,
        req_per_s=(len(ok) / wall_s) if wall_s > 0 else 0.0,
        output_tok_per_s=(output_tokens / wall_s) if wall_s > 0 else 0.0,
        latency_mean_ms=(statistics.fmean(lats) * 1000.0) if lats else None,
        latency_p50_ms=(percentile(lats, 0.50) * 1000.0) if lats else None,
        latency_p95_ms=(percentile(lats, 0.95) * 1000.0) if lats else None,
        latency_p99_ms=(percentile(lats, 0.99) * 1000.0) if lats else None,
        config=config,
        ttft_mean_ms=(statistics.fmean(ttfts) * 1000.0) if ttfts else None,
        ttft_p50_ms=(percentile(ttfts, 0.50) * 1000.0) if ttfts else None,
        ttft_p95_ms=(percentile(ttfts, 0.95) * 1000.0) if ttfts else None,
        ttft_p99_ms=(percentile(ttfts, 0.99) * 1000.0) if ttfts else None,
        intertoken_p50_ms=percentile(gaps_ms, 0.50) if gaps_ms else None,
        intertoken_p99_ms=percentile(gaps_ms, 0.99) if gaps_ms else None,
        intertoken_max_ms=max(gaps_ms) if gaps_ms else None,
    )


def print_summary(s: BenchSummary) -> None:
    print()
    print("-" * 52)
    print(f"mode:              {s.mode}")
    print(f"engine:            {s.engine}")
    print(f"model:             {s.model}")
    print(f"completed:         {s.completed}/{s.requests}  failed={s.failed}")
    print(f"wall:              {s.wall_s:.3f} s")
    print(f"requests/sec:      {s.req_per_s:.2f}")
    print(f"output tokens:     {s.output_tokens}")
    if s.prompt_tokens is not None:
        print(f"prompt tokens:     {s.prompt_tokens}")
    print(f"output tok/sec:    {s.output_tok_per_s:.2f}")
    if s.latency_mean_ms is not None:
        print(f"lat mean/p50:      {s.latency_mean_ms:.1f} / {s.latency_p50_ms:.1f} ms")
        print(f"lat p95/p99:       {s.latency_p95_ms:.1f} / {s.latency_p99_ms:.1f} ms")
    if s.ttft_mean_ms is not None:
        print(f"ttft mean/p50:     {s.ttft_mean_ms:.1f} / {s.ttft_p50_ms:.1f} ms")
        print(f"ttft p95/p99:      {s.ttft_p95_ms:.1f} / {s.ttft_p99_ms:.1f} ms")
    if s.intertoken_p50_ms is not None:
        print(
            f"intertoken p50/p99/max: {s.intertoken_p50_ms:.2f} / "
            f"{s.intertoken_p99_ms:.2f} / {s.intertoken_max_ms:.2f} ms"
        )
    spec_keys = (
        "spec attempted",
        "spec hits",
        "spec misses",
        "spec rule skipped",
        "spec budget skipped",
        "spec dropped orphan",
        "spec need pages",
        "spec chain now",
        "spec chain peak",
        "spec longest chain",
        "total batches",
        "cumulative batch latency us",
        "avg batch latency us",
        "last batch latency us",
        "system spec draft tokens proposed",
        "system spec draft tokens accepted",
        "system spec draft tokens proposed per pos",
        "system spec draft tokens accepted per pos",
        "bypass hits",
        "chain submits",
        "chain drops",
        "total requests",
        "max forward requests",
        "batch size hist",
        "runtime launch ack mean ms",
        "runtime launch ack p50 ms",
        "runtime launch ack p95 ms",
        "runtime launch ack max ms",
        "runtime launch ack before start ms",
        "runtime first launch ack ms",
        "runtime all launch ack ms",
        "runtime ready before start ms",
        "runtime all ready ms",
        "runtime first return ms",
        "runtime last return ms",
        "runtime engine cumulative ms",
        "runtime wall minus engine ms",
        "runtime non-engine after launch ms",
        "vllm spec drafts",
        "vllm spec draft tokens",
        "vllm spec accepted tokens",
        "vllm spec accepted per position",
        "vllm spec acceptance rate",
        "vllm spec mean acceptance length",
    )
    if any(k in s.config for k in spec_keys):
        for k in spec_keys:
            if k in s.config:
                print(f"{k+':':<18} {s.config[k]}")
        hits = s.config.get("spec hits", 0)
        misses = s.config.get("spec misses", 0)
        attempted = s.config.get("spec attempted", 0)
        depth_cap = s.config.get("max chain depth")
        total_calls = hits + misses + attempted
        if total_calls > 0:
            print(f"{'spec hit rate:':<18} {hits / total_calls:.1%}")
        if depth_cap and attempted > 0:
            theoretical = attempted * depth_cap
            print(f"{'spec chain yield:':<18} {hits / theoretical:.1%}")
    print("-" * 52)


def write_json(path: str | None, summary: BenchSummary, results: list[RequestResult]) -> None:
    if not path:
        return
    out = {"summary": asdict(summary), "requests": [asdict(r) for r in results]}
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(out, indent=2))


def hash_output_tokens(token_ids: list[int]) -> str:
    import hashlib

    digest = hashlib.sha256()
    for token in token_ids:
        digest.update(int(token).to_bytes(4, "little", signed=False))
    return digest.hexdigest()


def print_first_output(args: argparse.Namespace, text: str | None) -> None:
    if not getattr(args, "dump_first_text", False) or text is None:
        return
    import hashlib

    sha = hashlib.sha256(text.encode()).hexdigest()[:16]
    print(f"\nFIRST REQUEST OUTPUT (sha256[:16]={sha}):")
    print(text)
    print(f"END OUTPUT (chars={len(text)})")


def finish(summary: BenchSummary, results: list[RequestResult], json_out: str | None) -> None:
    print_summary(summary)
    write_json(json_out, summary, results)
    if summary.failed:
        print(f"{summary.failed} request(s) failed; inspect JSON output for details.")
