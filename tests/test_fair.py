"""Fair prefill/TTFT formulas and the cold-cache prompt generator."""

from __future__ import annotations

import json
import types

import pytest

from pie_evals.node import fair
from pie_evals.node.engines.base import Engine, EngineLaunchError, perf_from_common_json
from pie_evals.node.workloads.synthetic import prompt_words_for_tokens
from pie_evals.schema import ErrorClass, WorkloadSpec


def req(prompt_tokens: int, ttft_s: float, cached: int | None = 0, ok: bool = True, output_tokens: int = 200, latency_s: float = 1.3) -> dict:
    r = {"ok": ok, "prompt_tokens": prompt_tokens, "ttft_s": ttft_s, "output_tokens": output_tokens, "latency_s": latency_s, "intertoken_us": []}
    if cached is not None:
        r["cached_prompt_tokens"] = cached
    return r


# ---- prefill formula -------------------------------------------------------

def test_prefill_one_is_prompt_over_ttft():
    assert fair.prefill_tok_s_one(3234, 0.25) == pytest.approx(12936.0)


@pytest.mark.parametrize("prompt,ttft", [(None, 0.1), (0, 0.1), (100, None), (100, 0.0), (100, -1.0)])
def test_prefill_one_none_when_undefined(prompt, ttft):
    assert fair.prefill_tok_s_one(prompt, ttft) is None


def test_fair_prefill_is_median_of_cold_single_stream_rates():
    rows = [req(1000, 0.5), req(1000, 0.25), req(1000, 0.2)]  # 2000, 4000, 5000 tok/s
    assert fair.fair_prefill_tok_s(rows, concurrency=1) == pytest.approx(4000.0)


def test_fair_prefill_ignores_failed_requests():
    rows = [req(1000, 0.5), req(1000, 0.25), {"ok": False, "prompt_tokens": 1000, "ttft_s": 0.001}]
    assert fair.fair_prefill_tok_s(rows, concurrency=1) == pytest.approx(3000.0)


def test_fair_prefill_none_under_concurrency():
    rows = [req(616, 0.088), req(616, 0.176)]
    assert fair.fair_prefill_tok_s(rows, concurrency=4) is None


def test_fair_prefill_none_when_warm():
    rows = [req(3234, 0.04, cached=3000), req(3234, 0.25, cached=0)]
    assert fair.cache_verdict(rows) == "warm"
    assert fair.fair_prefill_tok_s(rows, concurrency=1) is None


def test_fair_prefill_none_when_cache_unverified():
    rows = [req(3234, 0.25, cached=None)]
    assert fair.cache_verdict(rows) == "unverified"
    assert fair.fair_prefill_tok_s(rows, concurrency=1) is None


def test_cache_verdict_uses_summary_count_when_requests_lack_it():
    rows = [req(512, 0.1, cached=None)]
    assert fair.cache_verdict(rows, config_cached=0.0) == "cold"
    assert fair.cache_verdict(rows, config_cached=64.0) == "warm"


def test_cache_verdict_cold_when_all_zero():
    assert fair.cache_verdict([req(512, 0.1, cached=0), req(512, 0.1, cached=0)]) == "cold"


# ---- consistency check -----------------------------------------------------

def test_consistent_row_is_not_flagged():
    # 539 tokens per request at 41 ms TTFT is 13,100 tok/s; the row agrees with itself
    assert fair.prefill_mismatch(13100.0, 41.0, 3234, 6) is False


def test_stored_pie_row_agrees_when_prompt_is_per_request():
    # m5-max-128g qwen3.6 ob-512-200: the row's prompt_tokens (3234) is the total over 6 requests
    ratio = fair.prefill_consistency(13096.43, 41.156, 3234, 6)
    assert ratio == pytest.approx(1.0, abs=1e-3)
    assert fair.prefill_mismatch(13096.43, 41.156, 3234, 6) is False


def test_total_prompt_read_as_per_request_is_flagged():
    # the same row compared against the total instead of the per-request prompt is off by the request count
    assert fair.prefill_mismatch(13096.43, 41.156, 3234, 1) is True


def test_tolerance_boundary():
    assert fair.prefill_mismatch(1.15 * 1000, 1000.0, 1000, 1) is False  # ratio 1.15 exactly
    assert fair.prefill_mismatch(1.16 * 1000, 1000.0, 1000, 1) is True


def test_consistency_none_without_inputs():
    assert fair.prefill_mismatch(None, 41.0, 3234, 6) is False
    assert fair.prefill_consistency(100.0, None, 3234, 6) is None
    assert fair.prefill_consistency(100.0, 41.0, 3234, None) is None


# ---- cold prompts ----------------------------------------------------------

def test_cold_tag_is_deterministic_and_unique_per_index():
    tags = [fair.cold_tag(fair.COLD_SEED, "cold-ss-512-200", i) for i in range(200)]
    assert len(set(tags)) == 200
    assert all(len(t) == fair.TAG_HEX_CHARS for t in tags)
    assert tags == [fair.cold_tag(fair.COLD_SEED, "cold-ss-512-200", i) for i in range(200)]


def test_cold_tag_depends_on_workload_and_seed():
    assert fair.cold_tag("a", "w", 0) != fair.cold_tag("b", "w", 0)
    assert fair.cold_tag("a", "w", 0) != fair.cold_tag("a", "x", 0)


def test_cold_prompts_share_no_prefix():
    body = prompt_words_for_tokens(128, salt="cold-ss-128-64")
    prompts = fair.cold_prompts(body, workload_id="cold-ss-128-64", seed=fair.COLD_SEED, count=12)
    assert len(prompts) == 12
    assert len(set(prompts)) == 12
    # the first character of the tag differs for some pairs, so the common prefix is at most "[" plus one hex digit
    assert fair.max_pairwise_prefix(prompts) < len("[") + fair.TAG_HEX_CHARS
    assert all(p.endswith(body) for p in prompts)


def test_cold_prompts_identical_for_every_caller():
    body = "x y z"
    a = fair.cold_prompts(body, workload_id="w", seed="s", count=5)
    b = fair.cold_prompts(body, workload_id="w", seed="s", count=5)
    assert a == b


def test_cold_prompts_rejects_empty_count():
    with pytest.raises(ValueError):
        fair.cold_prompts("x", workload_id="w", seed="s", count=0)


def test_cold_request_count_covers_measured_plus_slack():
    assert fair.cold_request_count({"requests": 6, "warmup": 1}) == 6 + fair.COLD_SLACK
    assert fair.cold_request_count({"num_requests": 32}) == 32 + fair.COLD_SLACK
    assert fair.cold_request_count({}) == 1 + fair.COLD_SLACK


def test_max_pairwise_prefix():
    assert fair.max_pairwise_prefix(["abc", "abd", "xyz"]) == 2
    assert fair.max_pairwise_prefix(["abc"]) == 0


# ---- perf_from_common_json wiring -----------------------------------------

def _summary(**config):
    return {"output_tokens": 400, "prompt_tokens": 2 * 3234, "wall_s": 2.0, "config": config}


def test_perf_prefill_uses_fair_definition_for_cold_single_stream():
    requests = [req(3234, 0.25), req(3234, 0.5)]  # 12936, 6468 tok/s -> median 9702
    perf = perf_from_common_json(_summary(concurrency=1), requests, None, concurrency=1)
    assert perf.prefill_tok_s == pytest.approx((12936.0 + 6468.0) / 2)
    assert perf.counters["fair_def"] == float(fair.FAIR_DEFINITION_VERSION)
    assert perf.counters["cold_cache_verified"] == 1.0


def test_perf_prefill_none_for_warm_or_unverified_rows():
    warm = perf_from_common_json(_summary(), [req(3234, 0.04, cached=3000)], None, concurrency=1)
    assert warm.prefill_tok_s is None
    assert warm.counters["cold_cache_verified"] == 0.0
    unverified = perf_from_common_json(_summary(), [req(3234, 0.25, cached=None)], None, concurrency=1)
    assert unverified.prefill_tok_s is None


def test_perf_prefill_none_under_concurrency():
    perf = perf_from_common_json(_summary(concurrency=4), [req(616, 0.088, cached=0)], None, concurrency=4)
    assert perf.prefill_tok_s is None


def test_perf_prefill_uses_summary_cache_count_for_openai_servers():
    perf = perf_from_common_json(_summary(concurrency=1, cached_prompt_tokens=0.0), [req(512, 0.2, cached=None)], None, concurrency=1)
    assert perf.prefill_tok_s == pytest.approx(512 / 0.2)
    assert perf.counters["cached_prompt_tokens"] == 0.0


# ---- cold argv --------------------------------------------------------------

class _Fake(Engine):  # minimal stand-in: only the attributes cold_common_args reads
    def __init__(self):  # noqa: D401 - skip the real constructor
        self.name = types.SimpleNamespace(value="fake")
        self.supports_prompts_file = True

    def default_python(self):
        return "python"

    def model_arg(self):
        return "m"

    def engine_args(self, workload):
        return []


def _workload(params: dict) -> WorkloadSpec:
    return WorkloadSpec(id="cold-ss-128-64", kind="single_stream", params=params, tiers=["targeted"], est_minutes=1)


def test_cold_common_args_writes_one_prompt_per_request(tmp_path):
    w = _workload({"prefill": 128, "decode": 64, "requests": 6, "warmup": 1, "cold_cache": True})
    args = _Fake().cold_common_args(w, ["--max-tokens", "64"], tmp_path)
    assert args[:2] == ["--max-tokens", "64"]
    assert args[2] == "--prompts-file"
    prompts = json.loads((tmp_path / "cold_prompts.json").read_text())
    assert len(prompts) == fair.cold_request_count(w.params)
    assert len(set(prompts)) == len(prompts)


def test_cold_common_args_refuses_adapter_without_prompts_file(tmp_path):
    eng = _Fake()
    eng.supports_prompts_file = False
    w = _workload({"prefill": 128, "requests": 6, "cold_cache": True})
    with pytest.raises(EngineLaunchError) as exc:
        eng.cold_common_args(w, [], tmp_path)
    assert exc.value.error_class == ErrorClass.INCOMPATIBLE


def test_cold_prompt_file_hash_is_recorded_and_decodable(tmp_path, monkeypatch):
    import hashlib

    w = _workload({"prefill": 128, "decode": 64, "requests": 6, "warmup": 1, "cold_cache": True})
    eng = _Fake()
    eng.cold_common_args(w, [], tmp_path)
    digest = hashlib.sha256((tmp_path / "cold_prompts.json").read_bytes()).hexdigest()
    value = float(int(digest[:12], 16))
    assert int(value) == int(digest[:12], 16)
    assert format(int(value), "012x") == digest[:12]


def test_cold_tagged_run_without_a_cache_count_is_cold_by_construction():
    from pie_evals.node.engines.base import perf_from_common_json
    reqs = [{"ok": True, "latency_s": 1.0, "ttft_s": 0.2, "output_tokens": 64, "prompt_tokens": 512, "intertoken_us": []}] * 4
    summary = {"config": {"concurrency": 1}}
    cold = perf_from_common_json(summary, reqs, None, concurrency=1, cold_tags=True)
    assert cold.prefill_tok_s is not None
    assert cold.counters["cold_cache_verified"] == 1.0 and cold.counters["cold_by_construction"] == 1.0
    plain = perf_from_common_json(summary, reqs, None, concurrency=1)
    assert plain.prefill_tok_s is None and plain.counters["cold_cache_verified"] == 0.0


def test_a_cold_tagged_run_with_a_cached_opening_is_cold():
    from pie_evals.node.engines.base import perf_from_common_json
    reqs = [{"ok": True, "latency_s": 1.0, "ttft_s": 0.2, "output_tokens": 64, "prompt_tokens": 555, "intertoken_us": []}] * 8
    opening = perf_from_common_json({"config": {"concurrency": 1, "cached_prompt_tokens": 120}}, reqs, None, concurrency=1, cold_tags=True)
    assert opening.prefill_tok_s is not None and opening.counters["cold_opening_cached_per_request"] == 15
    warm = perf_from_common_json({"config": {"concurrency": 1, "cached_prompt_tokens": 4000}}, reqs, None, concurrency=1, cold_tags=True)
    assert warm.prefill_tok_s is None


def test_each_cold_prompt_has_its_own_body():
    from pie_evals.node.workloads.synthetic import prompt_words_for_tokens

    prompts = fair.cold_prompts(lambda i: prompt_words_for_tokens(128, salt=f"c256|{i}"), workload_id="c256", seed=fair.COLD_SEED, count=8)
    bodies = [p.split("] ", 1)[1] for p in prompts]
    assert len(set(bodies)) == 8  # one answer per lane: a MoE batch routes its requests apart
    assert {len(b.split()) for b in bodies} == {len(prompt_words_for_tokens(128, salt="c256|0").split())}  # same length every request
    assert fair.cold_prompts("one body", workload_id="w", seed="s", count=2)[1].endswith("] one body")  # a plain body still works


def test_time_per_output_token_does_not_read_a_batched_stream_as_zero():
    # 65 tokens over 0.8 s after the first, handed over 4 at a time: most gaps are 0 us
    chunked = {"ok": True, "latency_s": 1.0, "ttft_s": 0.2, "output_tokens": 65, "prompt_tokens": 512, "intertoken_us": ([50000] + [0] * 3) * 16}
    perf = perf_from_common_json({"config": {"concurrency": 1}}, [chunked] * 3, None, concurrency=1)
    assert perf.itl_ms_p50 == pytest.approx(12.5) and perf.itl_ms_p99 == pytest.approx(12.5)
