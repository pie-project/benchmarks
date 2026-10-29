from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from pie_evals.results import report as rp


class FakeStore:
    def __init__(self, latest, hist=None):
        self._latest, self._hist = latest, hist or {}

    def latest_by_cell(self, tier=None):
        return self._latest

    def history(self, tier=None, *, limit=20, engine=None, since=None):
        return self._hist


def row(engine, out, artifact="a", started=0, **kw):
    return {"engine": engine, "platform": "m5-max-64g", "artifact": artifact, "workload": "ss-512-256", "status": "pass",
            "output_tokens": out, "requests": 8, "failed": 0, "started_at": datetime(2026, 10, 16, tzinfo=timezone.utc) + timedelta(minutes=started), **kw}


MATRIX = SimpleNamespace(artifacts={"a": SimpleNamespace(base_model="mlx-community/Qwen3.8-27B-4bit"),
                                    "b": SimpleNamespace(base_model="unsloth/Qwen3.8-27B-GGUF")}, workloads={})


def test_an_engine_that_decodes_much_less_than_pie_is_named():
    store = FakeStore({"1": row("pie", 2048), "2": row("splash", 1400, artifact="a"), "3": row("llamacpp", 2000, artifact="b")})
    found = rp.output_length_mismatches(MATRIX, store)
    assert [r["engine"] for r in found] == ["splash"] and round(found[0]["gap_rel"], 2) == -0.32


def test_one_model_across_its_builds_is_one_group():
    assert rp.model_of(MATRIX, "a") == rp.model_of(MATRIX, "b") == "qwen3.8-27b"


def test_a_drop_past_two_spreads_of_the_week_is_a_regression():
    latest = {"c": {**row("pie", 2048), "cell_key": "k", "primary_metric": "decode_tok_s", "primary_value": 40.0, "mode": "tp1",
                    "program": "p", "pie_commit": "abc", "engine_version": "", "family": "f"}}
    week = {"c": [50.0, 50.2, 49.9, 50.1]}
    found = rp.regressions(SimpleNamespace(workloads={}), FakeStore(latest, week), None)
    assert found and found[0]["kind"] == "regression" and round(found[0]["vs_peak_rel"], 2) == -0.2


def test_engines_prefilling_different_prompts_are_named():
    cold = SimpleNamespace(artifacts=MATRIX.artifacts, workloads={"c128": SimpleNamespace(params={"cold_cache": True})})
    def prow(engine, pt, artifact="a"):
        return row(engine, 2048, artifact=artifact, workload="c128", prompt_tokens=pt)
    store = FakeStore({"1": prow("pie", 180 * 8), "2": prow("vllm", 148 * 8), "3": prow("sglang", 148 * 8)})
    found = rp.prompt_length_mismatches(cold, store)
    assert len(found) == 1 and found[0]["per_request"] == {"pie": 180, "vllm": 148, "sglang": 148}
    assert not rp.prompt_length_mismatches(cold, FakeStore({"1": prow("pie", 148 * 8), "2": prow("vllm", 149 * 8)}))
