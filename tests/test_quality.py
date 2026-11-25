import json

from pie_bench.quality.tasks import Item, score_gsm8k, wilson
from pie_bench.results.store import Store


def test_gsm8k_reads_the_marked_answer_first():
    item = Item("q", "p", "42")
    assert score_gsm8k(item, "6 * 7 = 42\n#### 42") == 1.0
    assert score_gsm8k(item, "#### 1,042") == 0.0
    assert score_gsm8k(item, "so the answer is 42.") == 1.0
    assert score_gsm8k(item, "no idea") == 0.0


def test_wilson_interval_brackets_the_rate():
    lo, hi = wilson(70, 100)
    assert lo < 0.7 < hi and round(lo, 2) == 0.60 and round(hi, 2) == 0.78
    assert wilson(0, 0) == (0.0, 0.0)


def test_store_reads_quality_summaries(tmp_path):
    q = tmp_path / "quality"
    q.mkdir()
    (q / "gemma-4-26b-a4b-llamacpp-gsm8k.json").write_text(json.dumps({"artifact": "gemma-4-26b-a4b-llamacpp", "task": "gsm8k", "score": 0.9, "ci95": [0.8, 0.95], "n": 100, "samples": [1]}))
    assert Store(tmp_path).quality() == [{"artifact": "gemma-4-26b-a4b-llamacpp", "task": "gsm8k", "score": 0.9, "ci95": [0.8, 0.95], "n": 100}]


def test_scores_grade_the_answer_not_the_thinking():
    from pie_bench.quality.tasks import answer_part

    assert answer_part("<|channel>thought\nlet me think 41<channel|>#### 42") == "#### 42"
    assert answer_part("<think>41</think>\n#### 42") == "#### 42"
    assert answer_part("<|channel>thought\nnever closed") == ""
    assert score_gsm8k(Item("q", "p", "42"), "<|channel>thought\n#### 41<channel|>#### 42") == 1.0


def test_glimmer_answers_are_the_user_message():
    from pie_bench.quality.tasks import answer_part

    out = " to=self<|message|>We need to capitalize.<|eom|><|start|>assistant to=user<|message|>HELLO THERE<|eot|>"
    assert answer_part(out) == "HELLO THERE"
    assert answer_part(" to=self<|message|>still thinking when the budget ran out") == ""


def test_choice_tasks_read_the_marked_letter():
    from pie_bench.quality.tasks import score_choice

    item = Item("q", "p", "C")
    assert score_choice(item, "It is the third.\nAnswer: C") == 1.0
    assert score_choice(item, "Answer: **C**") == 1.0
    assert score_choice(item, "the answer is (C)") == 1.0
    assert score_choice(item, "C") == 1.0
    assert score_choice(item, "Answer: B") == 0.0
    assert score_choice(item, "A looks right, then B, so\nAnswer: C") == 1.0
    assert score_choice(item, "no idea") == 0.0
    assert score_choice(item, "<think>Answer: B</think>Answer: C") == 1.0


def test_math_tasks_compare_the_boxed_answer():
    from pie_bench.quality.tasks import score_math

    item = Item("q", "p", "\\frac{1}{2}")
    assert score_math(item, "so \\boxed{\\dfrac{1}{2}}") == 1.0
    assert score_math(item, "so \\boxed{ \\frac{1}{2} }.") == 1.0
    assert score_math(item, "\\boxed{\\frac{1}{3}}") == 0.0
    assert score_math(item, "the answer is 1/2") == 0.0
    assert score_math(Item("q", "p", "\\left( 3, \\frac{\\pi}{2} \\right)"), "\\boxed{(3, \\frac{\\pi}{2})}") == 1.0
    assert score_math(Item("q", "p", "10"), "\\boxed{\\text{10}}") == 1.0
    assert score_math(Item("q", "p", "5"), "first \\boxed{4} then \\boxed{5}") == 1.0
    assert score_math(Item("q", "p", "{1}"), "\\boxed{{1}}") == 1.0


def test_every_task_has_a_loader_scorer_and_budget():
    from pie_bench.quality.tasks import TASKS

    assert set(TASKS) == {"gsm8k", "ifeval", "mmlu", "arc", "math500"}
    for load, score, budget in TASKS.values():
        assert callable(load) and callable(score) and budget > 0


def test_a_task_that_cannot_load_is_skipped_not_fatal(monkeypatch):
    from pie_bench.quality import run, tasks

    class GatedRepoError(Exception):
        pass

    def gated(n):
        raise GatedRepoError("401 Client Error. Cannot access gated repo")

    monkeypatch.setitem(tasks.TASKS, "mmlu", (gated, tasks.score_choice, 1024))
    lines = []
    assert run.load_items("mmlu", 100, lines.append) is None
    assert "skipped" in lines[0] and "HF_TOKEN" in lines[0]
    monkeypatch.setitem(tasks.TASKS, "mmlu", (lambda n: ["item"], tasks.score_choice, 1024))
    assert run.load_items("mmlu", 100, lines.append) == ["item"]


def _arm(artifact, engine, score, n=100, samples=None, scheme="affine_u4_g64", checkpoint="mlx-community/x-4bit"):
    lo, hi = wilson(round(score * n), n)
    return {"artifact": artifact, "model": "x-mlx4", "task": "gsm8k", "engine": engine, "label": engine, "scheme": scheme,
            "checkpoint": checkpoint, "score": score, "ci95": [lo, hi], "n": n, "samples": samples or []}


def test_engine_comes_from_the_artifact_format():
    from types import SimpleNamespace as A

    from pie_bench.quality.engines import engine_for, strip_bos

    assert engine_for(A(source_format="gguf", baseline_label="llama.cpp")) == "llamacpp"
    assert engine_for(A(source_format="splash", baseline_label="Splash")) == "splash"
    assert engine_for(A(source_format="mlx", baseline_label="mlx-lm")) == "mlxlm"
    assert engine_for(A(source_format="mlx", baseline_label=None)) == "pie"
    assert strip_bos("<bos>hi", "<bos>") == "hi" and strip_bos("hi", None) == "hi"


def test_parity_flags_a_score_gap_beyond_the_combined_intervals():
    from pie_bench.quality.parity import rows

    same = [_arm("x-mlx4", "pie", 0.80), _arm("x-mlxlm", "mlxlm", 0.82)]
    cell = rows(same)[0]["arms"][1]
    assert cell["score_flag"] == "ok" and rows(same)[0]["flag"] == "ok"
    far = [_arm("x-mlx4", "pie", 0.80), _arm("x-mlxlm", "mlxlm", 0.99)]
    assert rows(far)[0]["arms"][1]["score_flag"] == "mismatch" and rows(far)[0]["flag"] == "mismatch"
    ahead = [_arm("x-mlx4", "pie", 0.99), _arm("x-mlxlm", "mlxlm", 0.80)]
    assert rows(ahead)[0]["arms"][1]["score_flag"] == "ok" and rows(ahead)[0]["flag"] == "ok"


def test_parity_measures_answer_drift_only_on_the_same_weights():
    from pie_bench.quality.parity import rows

    a = [{"id": str(i), "text": "#### 1"} for i in range(10)]
    b = [{"id": str(i), "text": "#### 2" if i < 3 else "#### 1"} for i in range(10)]
    same = rows([_arm("x-mlx4", "pie", 0.8, samples=a), _arm("x-mlxlm", "mlxlm", 0.8, samples=b)])[0]
    assert same["arms"][1]["agree"] == 0.7 and same["arms"][1]["agree_flag"] == "measured" and same["flag"] == "ok"
    splash = rows([_arm("x-mlx4", "pie", 0.8, samples=a), _arm("x-splash", "splash", 0.8, samples=b)])[0]
    assert splash["arms"][1]["agree_flag"] == "n/a"


def test_parity_leaves_out_an_arm_on_other_weights():
    from pie_bench.quality.parity import rows

    gguf = rows([_arm("x-mlx4", "pie", 0.3), _arm("x-llamacpp", "llamacpp", 0.6, scheme="gguf_q4_k_m", checkpoint="org/x-GGUF")])[0]
    assert [c["engine"] for c in gguf["arms"]] == ["pie"] and gguf["flag"] == "ok"


def test_parity_compares_on_the_machine_pie_ran_on():
    from pie_bench.quality.parity import rows

    h100 = {**_arm("x-mlx4", "pie", 0.8), "platform": "h100-sxm-x1"}
    vllm = {**_arm("x-mlx4@vllm", "vllm", 0.8), "model": "x-mlx4@vllm", "platform": "b200-x1"}
    out = rows([h100, vllm, _arm("x-mlx4", "pie", 0.8) | {"artifact": "x-mac"}])
    assert [(r["platform"], [c["engine"] for c in r["arms"]]) for r in out] == [(None, ["pie"]), ("b200-x1", ["vllm"]), ("h100-sxm-x1", ["pie"])]


def test_parity_compares_a_vllm_arm_with_the_pie_arm_on_its_weights():
    from pie_bench.quality.parity import rows

    a = [{"id": str(i), "text": "#### 1"} for i in range(10)]
    vllm = {**_arm("x-bf16@vllm", "vllm", 0.8, samples=a, scheme="bf16", checkpoint="org/x"), "model": "x-mlx4@vllm", "label": None}
    out = rows([_arm("x-mlx4", "pie", 0.5), _arm("x-bf16", "pie", 0.8, samples=a, scheme="bf16", checkpoint="org/x"), vllm])
    assert len(out) == 1 and [c["engine"] for c in out[0]["arms"]] == ["pie", "pie", "vllm"]
    cell = out[0]["arms"][2]
    assert cell["label"] == "vLLM" and cell["vs"] == "x-bf16" and cell["score_flag"] == "ok" and cell["agree"] == 1.0


def test_a_quality_write_keeps_a_stored_score(tmp_path):
    base = {"artifact": "x-mlx4", "task": "gsm8k", "model": "x-mlx4", "engine": "pie", "n": 100, "ci95": [0.7, 0.9], "date": "2026-10-08T00:00:00Z"}
    store = Store(tmp_path)
    store.write_quality({**base, "score": None, "n": 0}, tag="0.5.2", tag_kind="release")
    store.write_quality({**base, "score": 0.8}, tag="0.5.2", tag_kind="release")
    assert store.quality(samples=True)[0]["score"] == 0.8
    store.write_quality({**base, "score": 0.5}, tag="0.5.2", tag_kind="release")
    assert store.quality(samples=True)[0]["score"] == 0.8
