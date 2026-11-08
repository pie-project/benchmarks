import json
import subprocess
import sys
from pathlib import Path

import pytest

from pie_evals.node.snapshots import gguf_shards
from pie_evals.plan.matrix import Matrix, cannot_load
from pie_evals.plan.suites import all_models, load_config, suite_models, suites
from pie_evals.schema import Tier

ROOT = Path(__file__).resolve().parents[1]

TIER1 = {"qwen3.8-flash-next", "qwen3.8-27b", "qwen3.6-27b", "qwen3.6-35b-a3b", "qwen3.5-4b", "gemma-4-26b-a4b", "gemma-4-31b", "muse-glimmer-30b"}
# Nemotron-3-Ultra and Muse Spark: their 4-bit cuts against mlx-lm (and vLLM-Metal), no llama.cpp copy of the cut
FULL = TIER1 | {"gemma-4-12b", "gemma-4-e2b", "gemma-4-e4b", "gpt-oss-20b", "qwen3.5-9b", "nvidia-nemotron-3-ultra-550b-a55b", "muse-spark-open-816b-a42b"}


@pytest.fixture(scope="module")
def matrix():
    return Matrix.load(ROOT / "matrix")


@pytest.fixture(scope="module")
def config():
    return load_config(ROOT / "config.json")


@pytest.fixture(scope="module")
def webdb():
    sys.path.insert(0, str(ROOT / "tools"))
    import webdb

    return webdb


def test_both_suites_name_only_competitor_arms_of_the_matrix(matrix, config):
    for name, arms in suites(config).items():
        assert arms, name
        assert len(arms) == len(set(arms)), name
        for aid in arms:
            a = matrix.artifacts[aid]
            assert a.baseline_of in matrix.artifacts and a.baseline_label, (name, aid)
            assert cannot_load(matrix, aid.rsplit("-", 1)[1], a) is None, (name, aid)  # an arm in a suite can be run


def test_the_full_suite_holds_the_targeted_one(config):
    assert set(suite_models(config, "targeted")) <= set(suite_models(config, "full"))
    assert set(all_models(config)) == set(suite_models(config, "full"))


def test_suites_cover_their_models(config, webdb):
    a2m, _ = webdb.artifact_to_model()
    ids = webdb.suite_model_ids(config, a2m)
    assert set(ids["targeted"]) == TIER1 and set(ids["full"]) == FULL


def test_targeted_is_the_default_and_models_still_reads_as_targeted():
    assert suite_models({"suites": {"targeted": ["a"], "full": ["a", "b"]}}) == ["a"]
    old = {"models": ["x-llamacpp"]}
    assert suite_models(old) == ["x-llamacpp"] and suite_models(old, "full") == []
    with pytest.raises(ValueError):
        suite_models(old, "nightly")


def test_every_tier1_model_has_pie_llamacpp_and_mlxlm_arms(matrix, config, webdb):
    a2m, _ = webdb.artifact_to_model()
    # pie's targeted rows come from suites.yaml's include, whatever the artifact's own tiers say
    pie_targeted = {str(c.artifact.id) for c in matrix.cells_for(Tier.TARGETED, matrix.expand(platforms=[p for p, s in matrix.platforms.items() if s.os == "macos"])) if str(c.engine) == "pie"}
    arms = {}
    for a in matrix.artifacts.values():
        if a.baseline_of and a2m[a.id] in TIER1 and "targeted" in a.tiers and not (a.platforms and all(p.startswith("web-") for p in a.platforms)):
            arms.setdefault(a2m[a.id], set()).add(a.baseline_label)
            pie = matrix.artifacts[a.baseline_of]
            assert pie.id in pie_targeted and pie.source_format != "gguf", a.id
            if a2m[a.id] not in {"qwen3.8-27b", "qwen3.6-27b", "qwen3.6-35b-a3b", "gemma-4-26b-a4b", "muse-glimmer-30b"}:
                assert pie.pie_sku and not pie.pie_drafter and "dflash" not in pie.pie_sku, pie.id  # the plain row
    assert set(arms) == TIER1
    for model, labels in arms.items():
        assert {"llama.cpp", "mlx-lm"} <= labels, model
        assert ("Splash" in labels) == (model in {"qwen3.8-27b", "qwen3.6-27b", "qwen3.6-35b-a3b", "qwen3.8-flash-next"}), model


def test_unsupported_models_say_why(matrix):
    for aid in ("gemma-4-12b-mlx4", "gemma-4-e2b-mlx4", "gemma-4-e4b-mlx4"):
        assert cannot_load(matrix, "pie", matrix.artifacts[aid]) is None, aid  # pie runs Gemma 4 E2B, E4B and 12B at 4-bit (#604)
        assert cannot_load(matrix, "mlxlm", matrix.artifacts[aid.replace("-mlx4", "-mlxlm")]) is None
    # mlx-vlm serves Qwen3.8-Flash-Next's MLX arm (support.yaml), and mlx-lm 0.32 loads Muse Glimmer (#1302)
    assert cannot_load(matrix, "mlxlm", matrix.artifacts["qwen3.8-flash-next-mlxlm"]) is None
    assert cannot_load(matrix, "mlxlm", matrix.artifacts["muse-glimmer-30b-mlxlm"]) is None
    assert cannot_load(matrix, "pie", matrix.artifacts["qwen3.5-4b-mlx4"]) is None


def test_a_split_gguf_is_every_shard():
    assert gguf_shards("Qwen3.5-4B-Q4_K_M.gguf") == ["Qwen3.5-4B-Q4_K_M.gguf"]
    assert gguf_shards("UD-Q4_K_XL/M-UD-Q4_K_XL-00001-of-00003.gguf") == [
        "UD-Q4_K_XL/M-UD-Q4_K_XL-00001-of-00003.gguf", "UD-Q4_K_XL/M-UD-Q4_K_XL-00002-of-00003.gguf", "UD-Q4_K_XL/M-UD-Q4_K_XL-00003-of-00003.gguf"]


def test_the_cli_prints_a_suite(tmp_path):
    (tmp_path / "config.json").write_text(json.dumps({"suites": {"targeted": ["a-llamacpp"], "full": ["a-llamacpp", "b-mlxlm"]}}))
    base = [sys.executable, "-m", "pie_evals.cli", "--matrix", str(ROOT / "matrix"), "--store", str(tmp_path / "store"), "suite"]
    run = lambda *a: subprocess.run(base + list(a), cwd=tmp_path, capture_output=True, text=True)  # noqa: E731
    assert run().stdout.strip() == "a-llamacpp"
    assert run("full").stdout.strip() == "a-llamacpp,b-mlxlm"
    assert run("nightly").returncode != 0


def test_the_site_lists_every_model_of_every_suite(config, webdb):
    a2m, models = webdb.artifact_to_model()
    ids = webdb.suite_model_ids(config, a2m)
    catalog = {m["id"] for m in models if m["id"] in {i for v in ids.values() for i in v}}
    assert catalog == FULL
    arms = webdb.quality_arms(config)
    assert ("pie", "qwen3.8-flash-next-mlx4") in arms and ("llamacpp", "gpt-oss-20b-llamacpp") in arms


def test_a_gap_takes_the_newest_run_not_the_newest_tags(webdb):
    # "old" was imported into again after "dev" ran, so it sorts first; its pie row is still the older run
    key = ("h200-x1", "pie", "mimo", "raw")
    tagged = {"top": {}, "old": {key: {"at": "2026-10-27 01:12", "v": 1}}, "dev": {key: {"at": "2026-11-03 00:18", "v": 2}}}
    snaps = webdb.stack(["top", "old", "dev"], tagged, [key], lambda item, k, src: {"v": item["v"]}, lambda item: item["at"])
    assert snaps["top"] == [{"v": 2, "stale": {"tag": "dev", "measured": "2026-11-03 00:18"}}]
    assert snaps["old"][0]["v"] == 1 and snaps["old"][0]["stale"] is None  # a tag's own run is always its own
    assert snaps["dev"][0]["v"] == 2 and snaps["dev"][0]["stale"] is None


def test_the_benchmarks_catalog_lists_every_scored_task_and_the_parity_check(webdb):
    rows = {r["id"]: r for r in webdb.quality_tasks()}
    assert {"gsm8k", "ifeval", "mmlu", "arc", "math500", "parity"} <= set(rows)
    assert rows["parity"]["task"] == "parity" and rows["parity"]["scoring"] == "mean KL, top-1 agreement"
