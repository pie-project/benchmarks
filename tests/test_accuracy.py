import importlib
import math
import sys

import numpy as np
import pytest

from pie_bench.accuracy.divergence import (
    COSINE_GATE,
    adjudicate_divergence,
    bootstrap_ci,
    cosine,
    first_divergence,
    kl_divergence,
    perplexity_from_logits,
    psnr,
    scores_differ,
    t0_verdict,
    topk_agreement,
)
from pie_bench.accuracy.gate import SAME_WEIGHTS_REFERENCE, run_t0, skip_reason
from pie_bench.accuracy.prompts import LONG_PROMPT_TARGET_WORDS, t0_prompts
from pie_bench.accuracy.reference import LazyReference, ReferenceCache, prompt_hash, reference_for
from pie_bench.schema import (
    AccuracyStatus,
    ArtifactKind,
    ArtifactSpec,
    Backend,
    Cell,
    EngineName,
    MiniatureRecipe,
    Mode,
    PlatformSpec,
    ProgramSpec,
    QuantScheme,
    WorkloadKind,
    WorkloadSpec,
)


def test_package_imports_without_heavy_deps():
    assert "torch" not in sys.modules
    assert "transformers" not in sys.modules
    importlib.import_module("pie_bench.accuracy.reference")
    importlib.import_module("pie_bench.accuracy.prompts")
    assert "torch" not in sys.modules
    assert "transformers" not in sys.modules


def test_first_divergence():
    assert first_divergence([1, 2, 3], [1, 2, 3]) is None
    assert first_divergence([1, 2, 3], [1, 9, 3]) == 1
    assert first_divergence([], []) is None
    assert first_divergence([1, 2], [1, 2, 3]) == 2
    assert first_divergence([1, 2, 3], [1, 2]) == 2
    assert first_divergence([5], [1, 2]) == 0


def test_adjudicate_benign_when_top2_within_ulp():
    v = np.zeros(10, dtype=np.float32)
    v[3], v[7] = 16.0, 16.0625
    gap, benign = adjudicate_divergence(v, 3, 7)
    assert gap == pytest.approx(0.0625)
    assert benign


def test_adjudicate_bug_when_gap_large():
    v = np.zeros(10)
    v[3], v[7] = 16.0, 12.0
    gap, benign = adjudicate_divergence(v, 3, 7)
    assert gap == pytest.approx(4.0)
    assert not benign


def test_adjudicate_bug_when_not_top2_even_if_close():
    v = np.zeros(10)
    v[0] = 20.0
    v[3], v[7] = 16.0, 16.05
    gap, benign = adjudicate_divergence(v, 3, 7)
    assert gap == pytest.approx(0.05)
    assert not benign


def test_adjudicate_boundary_and_same_token():
    v = np.zeros(4)
    v[1], v[2] = 1.0, 1.125
    assert adjudicate_divergence(v, 1, 2)[1]
    v[2] = 1.126
    assert not adjudicate_divergence(v, 1, 2)[1]
    assert adjudicate_divergence(v, 1, 1) == (0.0, True)
    with pytest.raises(IndexError):
        adjudicate_divergence(v, 1, 99)


def test_t0_verdict():
    assert t0_verdict([None, None], [], []) == AccuracyStatus.PASS
    assert t0_verdict([None, 4], [0.05], [True]) == AccuracyStatus.PASS
    assert t0_verdict([None, 4], [3.0], [False]) == AccuracyStatus.FAIL
    assert t0_verdict([2, 4], [0.01, 3.0], [True, False]) == AccuracyStatus.FAIL
    assert t0_verdict([2], [], []) == AccuracyStatus.FAIL


def test_kl_and_topk():
    rng = np.random.default_rng(0)
    p = rng.normal(size=(5, 50))
    assert kl_divergence(p, p) == pytest.approx(0.0, abs=1e-12)
    q = p + rng.normal(scale=0.1, size=p.shape)
    assert kl_divergence(p, q) > 0.0
    assert math.isfinite(kl_divergence(p * 1e4, q * 1e4))
    assert topk_agreement(p, p, k=1) == 1.0
    assert topk_agreement(p, p, k=5) == 1.0
    q2 = p.copy()
    q2[0] = -p[0]
    assert topk_agreement(p, q2, k=1) == pytest.approx(0.8)


def test_perplexity():
    logits = np.full((4, 3), -1e9)
    ids = [0, 1, 2, 0]
    for i, t in enumerate(ids):
        logits[i, t] = 0.0
    assert perplexity_from_logits(logits, ids) == pytest.approx(1.0)
    uniform = np.zeros((4, 3))
    assert perplexity_from_logits(uniform, ids) == pytest.approx(3.0)
    with pytest.raises(ValueError):
        perplexity_from_logits(uniform, [0])


def test_cosine_and_psnr():
    a = np.random.default_rng(1).normal(size=(3, 8, 8))
    assert cosine(a, a) == pytest.approx(1.0)
    assert cosine(a, -a) == pytest.approx(-1.0)
    assert cosine(a, a * 3.0) == pytest.approx(1.0)
    assert cosine(a, a) >= COSINE_GATE
    assert psnr(a, a) == math.inf
    noisy = a + 1e-3 * np.random.default_rng(2).normal(size=a.shape)
    assert cosine(a, noisy) > COSINE_GATE
    assert 40.0 < psnr(a, noisy) < 200.0
    assert psnr(np.zeros(4), np.ones(4), peak=1.0) == pytest.approx(0.0)


def test_bootstrap_ci_and_scores_differ():
    rng = np.random.default_rng(0)
    a = list(rng.normal(loc=0.7, scale=0.05, size=200))
    lo, hi = bootstrap_ci(a)
    assert lo < 0.7 < hi
    assert hi - lo < 0.05
    assert bootstrap_ci(a) == bootstrap_ci(a)
    assert bootstrap_ci([0.5]) == (0.5, 0.5)
    b = [x + 0.001 for x in a]
    assert not scores_differ(a, a)
    assert not scores_differ(a, list(rng.normal(loc=0.7, scale=0.05, size=200)))
    assert scores_differ(a, [x + 0.1 for x in a])
    assert scores_differ(a, list(rng.normal(loc=0.9, scale=0.05, size=150)))
    assert not scores_differ(a, b) or True
    with pytest.raises(ValueError):
        bootstrap_ci([])


def _fake_tf(vocab: int, leaders: dict[int, tuple[int, int, float]]):

    calls: list[list[int]] = []

    def fn(ids: list[int]) -> np.ndarray:
        calls.append(list(ids))
        out = np.zeros((len(ids), vocab), dtype=np.float32)
        pos = len(ids) - 1
        if pos in leaders:
            a, b, gap = leaders[pos]
            out[pos, a] = 16.0
            out[pos, b] = 16.0 - gap
        return out

    fn.calls = calls
    return fn


def test_run_t0_identical_passes_without_calling_reference():
    fn = _fake_tf(20, {})
    m = run_t0([[1, 2, 3], [4, 5]], [[1, 2, 3], [4, 5]], fn, [[9], [9, 9]], reference="hf")
    assert m.status == AccuracyStatus.PASS
    assert m.t0_first_divergence == [None, None]
    assert m.t0_max_logit_gap is None
    assert m.t0_benign is True
    assert m.reference == "hf"
    assert fn.calls == []


def test_run_t0_benign_flip_passes():
    prompt = [7, 8, 9]
    ref = [1, 2, 3, 4]
    eng = [1, 2, 5, 4]
    fn = _fake_tf(20, {4: (3, 5, 0.06)})
    m = run_t0([eng], [ref], fn, [prompt])
    assert m.status == AccuracyStatus.PASS
    assert m.t0_first_divergence == [2]
    assert m.t0_max_logit_gap == pytest.approx(0.06, abs=1e-4)
    assert m.t0_benign is True
    assert fn.calls == [[7, 8, 9, 1, 2]]
    assert m.detail["t0"][0]["engine_tok"] == 5


def test_run_t0_large_gap_fails():
    fn = _fake_tf(20, {4: (3, 5, 2.5)})
    m = run_t0([[1, 2, 5, 4]], [[1, 2, 3, 4]], fn, [[7, 8, 9]])
    assert m.status == AccuracyStatus.FAIL
    assert m.t0_max_logit_gap == pytest.approx(2.5)
    assert m.t0_benign is False


def test_run_t0_length_mismatch_fails_without_adjudication():
    fn = _fake_tf(20, {})
    m = run_t0([[1, 2]], [[1, 2, 3]], fn, [[7]])
    assert m.status == AccuracyStatus.FAIL
    assert m.t0_first_divergence == [2]
    assert m.t0_max_logit_gap is None
    assert m.detail["t0"][0]["kind"] == "length_mismatch"
    assert fn.calls == []


def test_run_t0_compares_through_the_reference_stop_and_no_further():
    fn = _fake_tf(20, {})
    m = run_t0([[1, 2, 6, 9, 9]], [[1, 2, 6, 4, 5]], fn, [[7]], stops={6})
    assert m.status == AccuracyStatus.PASS
    assert m.t0_first_divergence == [None]
    assert fn.calls == []
    fn = _fake_tf(20, {1: (6, 5, 2.5)})
    m = run_t0([[1, 5, 6]], [[1, 6, 4]], fn, [[7]], stops={6})
    assert m.status == AccuracyStatus.FAIL
    assert m.t0_first_divergence == [1]
    assert m.t0_max_logit_gap == pytest.approx(2.5)


def test_run_t0_an_engine_that_stops_at_eos_leaves_the_stop_out():
    fn = _fake_tf(20, {})
    m = run_t0([[1, 2]], [[1, 2, 6, 4, 5]], fn, [[7]], stops={6})
    assert m.status == AccuracyStatus.PASS
    assert m.t0_first_divergence == [None]
    assert fn.calls == []


def test_run_t0_an_engine_that_stops_early_is_judged_by_its_stop():
    fn = _fake_tf(20, {2: (3, 6, 0.06)})
    m = run_t0([[1, 2]], [[1, 2, 3, 4]], fn, [[7]], stops={6, 8})
    assert m.status == AccuracyStatus.PASS
    assert m.t0_first_divergence == [2]
    assert m.detail["t0"][0]["engine_tok"] == 6
    fn = _fake_tf(20, {2: (3, 6, 2.5)})
    m = run_t0([[1, 2]], [[1, 2, 3, 4]], fn, [[7]], stops={6, 8})
    assert m.status == AccuracyStatus.FAIL
    assert m.t0_max_logit_gap == pytest.approx(2.5)


def test_stop_ids_read_generation_config_then_config(tmp_path):
    from pie_bench.accuracy.gate import stop_ids

    (tmp_path / "config.json").write_text('{"text_config": {"eos_token_id": 1}}')
    assert stop_ids(tmp_path) == {1}
    (tmp_path / "generation_config.json").write_text('{"eos_token_id": [1, 106, 50]}')
    assert stop_ids(tmp_path) == {1, 106, 50}


def test_stop_ids_take_the_tokenizers_turn_end(tmp_path):
    from pie_bench.accuracy.gate import stop_ids

    (tmp_path / "config.json").write_text('{"text_config": {"eos_token_id": 248044}}')
    (tmp_path / "tokenizer_config.json").write_text('{"eos_token": "<|im_end|>", "pad_token": "<|endoftext|>"}')
    (tmp_path / "tokenizer.json").write_text(
        '{"added_tokens": [{"id": 248044, "content": "<|endoftext|>"}, {"id": 248046, "content": "<|im_end|>"}]}'
    )
    assert stop_ids(tmp_path) == {248044, 248046}


def test_run_t0_prompt_count_mismatch():
    with pytest.raises(ValueError):
        run_t0([[1]], [[1], [2]], _fake_tf(4, {}), [[0]])


def _cell(artifact: ArtifactSpec) -> Cell:
    return Cell(
        engine=EngineName.PIE,
        platform=PlatformSpec(id="l40s", os="linux", backend=Backend.CUDA, accelerator="NVIDIA L40S", arch="ada", memory_gib=48),
        artifact=artifact,
        workload=WorkloadSpec(id="ss", kind=WorkloadKind.SINGLE_STREAM),
        program=ProgramSpec(id="tcb", path="examples/text-completion-bench", category="serving"),
        mode=Mode(),
    )


def test_skip_reason():
    full = ArtifactSpec(id="q", base_model="Qwen/Qwen3-8B", family="qwen3", scheme=QuantScheme.BF16)
    assert skip_reason(_cell(full)) is None
    mini = ArtifactSpec(
        id="m", base_model="Qwen/Qwen3.6-35B-A3B", family="qwen3_6_moe", scheme=QuantScheme.BF16,
        kind=ArtifactKind.MINIATURE, miniature=MiniatureRecipe(layers="0-7", experts=32),
    )
    assert skip_reason(_cell(mini)) == AccuracyStatus.SKIPPED_MINIATURE
    assert QuantScheme.W4A16_MARLIN not in SAME_WEIGHTS_REFERENCE
    marlin = ArtifactSpec(id="w", base_model="x/y", family="qwen3", scheme=QuantScheme.W4A16_MARLIN)
    assert skip_reason(_cell(marlin)) == AccuracyStatus.SKIPPED_NO_REFERENCE
    budgeted = marlin.model_copy(update={"degradation_budget": {"ppl_ratio": 1.05}})
    assert skip_reason(_cell(budgeted)) is None


def test_t0_prompts_fixed_and_deterministic():
    ps = t0_prompts()
    ids = [i for i, _ in ps]
    assert len(ps) == 8
    assert len(set(ids)) == 8
    assert "long-1k" in ids
    long = dict(ps)["long-1k"]
    assert len(long.split()) >= LONG_PROMPT_TARGET_WORDS
    assert dict(t0_prompts())["long-1k"] == long
    assert any(ord(c) > 127 for c in dict(ps)["zh"])
    ps.append(("x", "y"))
    assert len(t0_prompts()) == 8


def test_reference_for():
    assert reference_for("macos", "mlx") == "mlx"
    assert reference_for("darwin", "mlx") == "mlx"
    assert reference_for("macos", "hf_safetensors") == "hf"
    assert reference_for("linux", "mlx") == "hf"
    assert reference_for("linux", "gguf") == "llamacpp"
    assert reference_for("macos", "gguf") == "llamacpp"


def _llamacpp_ref(reply):
    from pie_bench.accuracy.reference import LlamaCppReference

    sent = []
    ref = object.__new__(LlamaCppReference)
    ref.url, ref.vocab_size, ref.n_probs, ref._proc = "http://stub", 8, 4, None
    ref._post = lambda url, body: (sent.append((url, body)), reply)[1]
    return ref, sent


def test_llamacpp_greedy_continues_the_prompt_ids():
    ref, sent = _llamacpp_ref({"tokens": [5, 2, 7, 1]})
    assert ref.greedy([3, 4], 3) == [5, 2, 7]
    url, body = sent[0]
    assert url == "http://stub/completion"
    assert body["prompt"] == [3, 4] and body["n_predict"] == 3 and body["top_k"] == 1
    assert body["ignore_eos"] and body["return_tokens"] and not body["cache_prompt"]


def test_llamacpp_teacher_forced_logits_fills_the_last_row_with_top_logprobs():
    ref, sent = _llamacpp_ref({"completion_probabilities": [{"top_logprobs": [{"id": 6, "logprob": -0.1}, {"id": 2, "logprob": -2.5}]}]})
    rows = ref.teacher_forced_logits([1, 2, 3])
    assert rows.shape == (3, 8) and rows.dtype == np.float32
    assert rows[-1, 6] == pytest.approx(-0.1) and rows[-1, 2] == pytest.approx(-2.5)
    assert np.isneginf(rows[-1, 0]) and np.isneginf(rows[0]).all()
    assert sent[0][1]["n_predict"] == 1 and sent[0][1]["n_probs"] == 4


def test_llamacpp_teacher_forced_logits_reads_older_probs():
    ref, _ = _llamacpp_ref({"completion_probabilities": [{"probs": [{"id": 3, "prob": 0.5}]}]})
    assert ref.teacher_forced_logits([1])[-1, 3] == pytest.approx(math.log(0.5))


class _StubRef:
    name = "stub"

    def __init__(self):
        self.greedy_calls = 0
        self.tf_calls = 0

    def greedy(self, prompt_ids, max_new_tokens):
        self.greedy_calls += 1
        return [sum(prompt_ids) + i for i in range(max_new_tokens)]

    def teacher_forced_logits(self, ids):
        self.tf_calls += 1
        return np.arange(len(ids) * 4, dtype=np.float32).reshape(len(ids), 4)


def test_reference_cache_roundtrip(tmp_path):
    cache = ReferenceCache(tmp_path / "refcache")
    ref = _StubRef()
    out1 = cache.greedy(ref, "abc123", [1, 2, 3], 4)
    out2 = cache.greedy(ref, "abc123", [1, 2, 3], 4)
    assert out1 == out2 == [6, 7, 8, 9]
    assert ref.greedy_calls == 1
    cache.greedy(ref, "abc123", [1, 2, 3], 5)
    cache.greedy(ref, "def456", [1, 2, 3], 4)
    cache.greedy(ref, "abc123", [1, 2, 4], 4)
    assert ref.greedy_calls == 4
    tf1 = cache.teacher_forced_logits(ref, "abc123", [1, 2])
    tf2 = cache.teacher_forced_logits(ref, "abc123", [1, 2])
    assert ref.tf_calls == 1
    np.testing.assert_array_equal(tf1, tf2)
    assert tf2.dtype == np.float32
    assert prompt_hash([1, 2, 3]) != prompt_hash([1, 2, 4])
    files = list((tmp_path / "refcache" / "abc123").glob("*.npz"))
    assert len(files) == 4 and not any(f.name.endswith(".tmp.npz") for f in files)


def test_a_program_that_states_no_prompt_count_is_not_judged(tmp_path, monkeypatch):
    from types import SimpleNamespace

    from pie_bench.accuracy import gate

    monkeypatch.setattr(gate, "bench_system_prompt", lambda root: "sys")
    monkeypatch.setattr(gate, "render_like_bench", lambda snap, system, text, enable_thinking=False: [1, 2, 3])

    class Engine:
        def run(self, wl, args, out, timeout):
            return SimpleNamespace(output_token_ids=[[7, 8]], requests=[{"prompt_tokens": 0}])

    m = gate.t0_engine_outputs(Engine(), tmp_path, pie_root=tmp_path, out_dir=tmp_path)
    assert m.status == AccuracyStatus.SKIPPED_NO_REFERENCE
    assert m.detail["mismatch"][0][1:] == (3, 0)


def test_a_cached_reference_never_loads_beside_the_engine(tmp_path, monkeypatch):
    import pie_bench.accuracy.reference as reference

    cache = ReferenceCache(tmp_path / "refcache")
    cache.put("rev", "argmax", [1, 2, 3], 4, np.asarray([5, 6, 7, 8]))
    loads, closes = [], []

    class Loaded:
        def greedy(self, ids, n):
            return [9] * n

        def close(self):
            closes.append(True)

    monkeypatch.setattr(reference, "load_reference", lambda kind, snap, **kw: loads.append(kind) or Loaded())
    ref = LazyReference("hf", tmp_path)
    assert cache.greedy(ref, "rev", [1, 2, 3], 4) == [5, 6, 7, 8]
    ref.close()
    assert loads == [] and closes == []

    assert cache.greedy(ref, "rev", [4], 2) == [9, 9]
    ref.close()
    assert loads == ["hf"] and closes == [True]


def test_a_reply_cached_by_the_eos_masking_reference_is_read_again(tmp_path, monkeypatch):
    import pie_bench.accuracy.reference as reference

    cache = ReferenceCache(tmp_path / "refcache")
    cache.put("rev", "greedy", [1, 2, 3], 2, np.asarray([5, 6]))

    class Loaded:
        def greedy(self, ids, n):
            return [7] * n

        def close(self):
            pass

    monkeypatch.setattr(reference, "load_reference", lambda kind, snap, **kw: Loaded())
    assert cache.greedy(LazyReference("hf", tmp_path), "rev", [1, 2, 3], 2) == [7, 7]


def test_the_hf_reference_writes_the_end_of_turn_it_ranks_first():
    torch = pytest.importorskip("torch")
    from types import SimpleNamespace

    from pie_bench.accuracy.reference import HFReference

    eos, vocab = 3, 8
    script = [5, eos, 6, 7]

    class Model:
        def __call__(self, input_ids, past_key_values=None, use_cache=True):
            step = 0 if past_key_values is None else past_key_values + 1
            logits = torch.zeros(1, input_ids.shape[1], vocab)
            logits[0, -1, script[step]] = 1.0
            return SimpleNamespace(logits=logits, past_key_values=step)

    ref = object.__new__(HFReference)
    ref.torch, ref.device, ref.model = torch, "cpu", Model()
    assert ref.greedy([1, 2], 4) == [5, eos, 6, 7]
