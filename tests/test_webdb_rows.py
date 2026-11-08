import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import webdb  # noqa: E402


def test_a_row_carries_the_prompt_its_engine_prefilled_per_request():
    # raw-512-256 on Qwen: 6 measured requests of ~554 tokens (the 512-token shape, chat template and cold tag)
    assert webdb.prompt_per_request({"prompt_tokens": 3324, "requests": 6, "failed": 0}) == 554.0
    # failed requests carry no prompt tokens: the count is over the completed ones
    assert webdb.prompt_per_request({"prompt_tokens": 2770, "requests": 6, "failed": 1}) == 554.0
    # no count, or nothing completed: no figure, and the site falls back to the shape's nominal prompt
    assert webdb.prompt_per_request({"prompt_tokens": None, "requests": 6, "failed": 0}) is None
    assert webdb.prompt_per_request({"prompt_tokens": 100, "requests": 2, "failed": 2}) is None
    assert webdb.prompt_per_request({}) is None


def test_a_prefill_only_rerun_brings_its_prompt_count_with_its_prefill():
    t0, t1 = datetime(2026, 10, 1, tzinfo=timezone.utc), datetime(2026, 10, 2, tzinfo=timezone.utc)
    base = {"platform": "pro6000-x1", "engine": "pie", "artifact": "qwen3.6-35b-a3b-bf16", "workload": "raw-512-256", "scheme": "bf16"}
    old = {**base, "started_at": t0, "decode_tok_s": 185.0, "prefill_tok_s": 9000.0, "ttft_ms_p50": 61.5, "ttft_ms_p99": 62.0,
           "prompt_tokens": 3300, "requests": 6, "failed": 0}
    new = {**base, "started_at": t1, "decode_tok_s": 150.0, "prefill_tok_s": 12823.7, "ttft_ms_p50": 43.2, "ttft_ms_p99": 44.4,
           "prompt_tokens": 2770, "requests": 5, "failed": 0}
    key = ("pro6000-x1", "pie", "qwen3.6-35b-a3b", "raw")
    picked = {key: ((t1,), new)}
    webdb.keep_decode([old, new], picked, {"qwen3.6-35b-a3b-bf16": "qwen3.6-35b-a3b"}, "pie", t1)
    row = picked[key][1]
    assert row["decode_tok_s"] == 185.0 and row["prefill_tok_s"] == 12823.7
    assert webdb.prompt_per_request(row) == 554.0


def test_every_install_size_names_its_engine_bytes_and_how_it_was_counted():
    rows = webdb.install_sizes()
    engines = {e["id"] for e in webdb.load("engines")["engines"]}
    assert {r["platform"] for r in rows} <= {"mac", "nvidia", "web", "amd", "tpu", "android"}
    # one figure per engine and platform, each with what it counts and where it came from
    assert len({(r["platform"], r["engine"]) for r in rows}) == len(rows)
    for r in rows:
        assert r["engine"] in engines
        assert isinstance(r["bytes"], int) and r["bytes"] > 0
        assert r["version"] and r["method"] and r["source"] and r["measured"]
        # the parts name pieces of the figure, never more than all of it
        assert sum(n for _, n in r["parts"]) <= r["bytes"]


def test_a_diagnostic_tag_never_reaches_the_site():
    # profilers and timing A/Bs slow their own tok/s on purpose: their tags are neither releases nor fills
    assert webdb.is_diag_tag("tpu-diag-c256prof")
    assert webdb.is_diag_tag("tpu-diag-window-fix")
    assert not webdb.is_diag_tag("tpu-v6e-green")
    assert not webdb.is_diag_tag("a40-rerun")
    assert not webdb.is_diag_tag("0.5.3-b5")
