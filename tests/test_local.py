from pie_bench.paths import CONFIG, MATRIX
from pie_bench.plan.local import arms
from pie_bench.plan.matrix import Matrix
from pie_bench.plan.suites import load_config, suite_models


def test_a_named_model_on_a_mac_measures_only_its_suite_arms_and_their_pie_checkpoint():
    m = Matrix.load(MATRIX)
    ids = arms(m, ["qwen3.5-4b"], "targeted")
    assert ids == sorted(ids)
    assert all(m.artifacts[a].baseline_of or any(m.artifacts[b].baseline_of == a for b in ids) for a in ids)
    assert not any(m.artifacts[a].source_format.value == "hf_safetensors" and not m.artifacts[a].baseline_of
                   and not any(m.artifacts[b].baseline_of == a for b in ids) for a in ids)


def test_the_release_suite_is_the_default():
    m = Matrix.load(MATRIX)
    assert set(arms(m, None, "targeted")) >= set(suite_models(load_config(CONFIG), "targeted"))
