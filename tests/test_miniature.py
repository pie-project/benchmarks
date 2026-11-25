import json
from pathlib import Path

import pytest

from pie_bench.checkpoints.miniature import (
    SHRINK_SCRIPT,
    ensure_miniature,
    miniature_argv,
    miniature_snapshot_dir,
    num_layers_of,
    pattern_period,
    plan_layers,
    recipe_from_snapshot,
    repo_cache_dirname,
)
from pie_bench.installers.bench_env import bench_dir
from pie_bench.schema import ArtifactKind, ArtifactSpec, MiniatureRecipe, QuantScheme


def _mini(**recipe) -> ArtifactSpec:
    r = {"layers": "0-7", "experts": 32, "period": 4}
    r.update(recipe)
    return ArtifactSpec(
        id="qwen3.6-35b-a3b-mini8", base_model="Qwen/Qwen3.6-35B-A3B", family="qwen3_6_moe",
        scheme=QuantScheme.BF16, kind=ArtifactKind.MINIATURE, miniature=MiniatureRecipe(**r),
    )


def test_pattern_period():
    assert pattern_period(["a"] * 10) == 1
    assert pattern_period(["s", "s", "f"] * 4) == 3
    assert pattern_period(["m", "m", "m", "a", "m", "f"] * 2) == 6
    assert pattern_period(["a", "b", "c"]) == 3
    assert pattern_period([]) == 1


def test_plan_layers_keeps_whole_periods_and_last():
    gemma = ["sliding", "sliding", "full"] * 4
    assert plan_layers(gemma, 2) == "0-5,11"
    assert plan_layers(gemma, 2, always_last=False) == "0-5"
    assert plan_layers(gemma, 4) == "0-11"
    dense = ["attn"] * 36
    assert plan_layers(dense, 6) == "0-5,35"
    nemotron = ["M", "M", "M", "A", "M", "F"] * 8
    assert plan_layers(nemotron, 2) == "0-11,47"
    assert plan_layers(gemma, 10) == "0-11"
    with pytest.raises(ValueError):
        plan_layers([], 1)
    with pytest.raises(ValueError):
        plan_layers(gemma, 0)


def test_recipe_tag():
    assert MiniatureRecipe(layers="0-7", experts=32).tag == "mini-l0-7-e32"
    assert MiniatureRecipe(layers="0-5,39").tag == "mini-l0-5_39"
    assert MiniatureRecipe(layers="0-3", experts=8, repeat=3).tag == "mini-l0-3-e8-r3"
    assert MiniatureRecipe(layers="0-7", experts=32).recipe_hash != MiniatureRecipe(layers="0-7", experts=16).recipe_hash


def test_snapshot_dir_is_an_hf_cache_snapshot(tmp_path):
    art = _mini()
    d = miniature_snapshot_dir(art, tmp_path)
    assert d == tmp_path / "models--Qwen--Qwen3.6-35B-A3B" / "snapshots" / "mini-l0-7-e32"
    assert repo_cache_dirname("openai/gpt-oss-20b") == "models--openai--gpt-oss-20b"
    full = ArtifactSpec(id="q", base_model="Qwen/Qwen3-8B", family="qwen3", scheme=QuantScheme.BF16)
    with pytest.raises(ValueError):
        miniature_snapshot_dir(full, tmp_path)


def test_miniature_argv_matches_script_flags(tmp_path):
    art = _mini(text_only=True)
    argv = miniature_argv(art, Path("/pie"), tmp_path / "out", "/venv/bin/python", cache_dir=tmp_path / "c")
    assert argv[:2] == ["/venv/bin/python", str(bench_dir() / SHRINK_SCRIPT)]
    rest = [x for x in argv[2:] if x != "--text-only"]
    flags = dict(zip(rest[0::2], rest[1::2]))
    assert flags["--repo"] == "Qwen/Qwen3.6-35B-A3B"
    assert flags["--revision"] == "main"
    assert flags["--layers"] == "0-7"
    assert flags["--experts"] == "32"
    assert flags["--repeat"] == "1"
    assert "--text-only" in argv
    assert flags["--cache"] == str(tmp_path / "c")
    argv2 = miniature_argv(_mini(experts=None, text_only=False), Path("/pie"), tmp_path, "py")
    assert argv2[argv2.index("--experts") + 1] == "0"
    assert "--text-only" not in argv2


def test_ensure_miniature_short_circuits_on_existing(tmp_path):
    art = _mini()
    d = miniature_snapshot_dir(art, tmp_path)
    d.mkdir(parents=True)
    (d / "config.json").write_text(json.dumps({"num_hidden_layers": 8}))
    assert ensure_miniature(art, Path("/nonexistent/pie"), tmp_path, "/nonexistent/python") == d


def test_ensure_miniature_runs_script_and_records_recipe(tmp_path, monkeypatch):
    art = _mini()
    pie_root = tmp_path / "pie"
    bench = tmp_path / "bench"
    bench.mkdir()
    monkeypatch.setenv("PIE_BENCH_BENCH_DIR", str(bench))
    (bench / SHRINK_SCRIPT).write_text(
        "import argparse, json, pathlib\n"
        "ap = argparse.ArgumentParser()\n"
        "for f in ('--repo','--revision','--out','--layers','--repeat','--experts','--cache'): ap.add_argument(f)\n"
        "ap.add_argument('--text-only', action='store_true')\n"
        "a = ap.parse_args()\n"
        "p = pathlib.Path(a.out); p.mkdir(parents=True, exist_ok=True)\n"
        "(p / 'config.json').write_text(json.dumps({'num_hidden_layers': 8, 'layers': a.layers, 'experts': a.experts}))\n"
    )
    import sys

    d = ensure_miniature(art, pie_root, tmp_path / "hf", sys.executable)
    assert d == miniature_snapshot_dir(art, tmp_path / "hf")
    cfg = json.loads((d / "config.json").read_text())
    assert cfg["layers"] == "0-7" and cfg["experts"] == "32"
    assert num_layers_of(d) == 8
    assert recipe_from_snapshot(d) == art.miniature


def test_ensure_miniature_failure_raises(tmp_path, monkeypatch):
    art = _mini()
    pie_root = tmp_path / "pie"
    bench = tmp_path / "bench"
    bench.mkdir()
    monkeypatch.setenv("PIE_BENCH_BENCH_DIR", str(bench))
    (bench / SHRINK_SCRIPT).write_text("import sys; sys.stderr.write('boom\\n'); sys.exit(3)\n")
    import sys

    with pytest.raises(RuntimeError, match="boom"):
        ensure_miniature(art, pie_root, tmp_path / "hf", sys.executable)


def test_num_layers_of(tmp_path):
    assert num_layers_of(tmp_path) is None
    (tmp_path / "config.json").write_text(json.dumps({"text_config": {"num_hidden_layers": 42}}))
    assert num_layers_of(tmp_path) == 42
    (tmp_path / "config.json").write_text(json.dumps({"num_hidden_layers": 5}))
    assert num_layers_of(tmp_path) == 5
    (tmp_path / "config.json").write_text("{not json")
    assert num_layers_of(tmp_path) is None


def test_stale_recipe_snapshot_is_rebuilt(tmp_path, monkeypatch):
    import json

    from pie_bench.checkpoints import miniature as mm

    art = _mini(text_only=False)
    out = mm.miniature_snapshot_dir(art, tmp_path)
    out.mkdir(parents=True)
    (out / "config.json").write_text("{}")
    stale = dict(art.miniature.model_dump())
    stale["text_only"] = True
    (out / ".miniature.json").write_text(json.dumps({"recipe": stale}))
    calls = []

    def fake_run(argv, **kw):
        calls.append(argv)
        o = Path(argv[argv.index("--out") + 1])
        o.mkdir(parents=True, exist_ok=True)
        (o / "config.json").write_text("{}")
        return type("R", (), {"returncode": 0, "stderr": "", "stdout": ""})()

    monkeypatch.setattr(mm.subprocess, "run", fake_run)
    got = mm.ensure_miniature(art, tmp_path / "pie", tmp_path, python="py")
    assert calls, "stale snapshot must be rebuilt"
    assert json.loads((got / ".miniature.json").read_text())["recipe"] == mm._stamp(art)


def test_an_mlx_quantized_cut_is_its_own_snapshot():
    bf16 = MiniatureRecipe(layers="0-8", experts=16)
    mlx4 = MiniatureRecipe(layers="0-8", experts=16, mlx_quantize="affine_u4_g64")
    assert mlx4.tag == "mini-l0-8-e16-mlx-affine_u4_g64" and bf16.tag == "mini-l0-8-e16"
    assert mlx4.recipe_hash != bf16.recipe_hash
    assert bf16.recipe_hash == MiniatureRecipe(layers="0-8", experts=16, mlx_quantize=None).recipe_hash


def test_mlx_convert_argv_names_the_scheme():
    from pie_bench.checkpoints.mlx_quantize import convert_argv

    argv = convert_argv("py", Path("cut"), Path("cut-mlx"), "affine_u4_g64")
    assert argv[:4] == ["py", "-m", "mlx_lm", "convert"]
    assert argv[argv.index("--q-bits") + 1] == "4" and argv[argv.index("--q-group-size") + 1] == "64"
    assert argv[argv.index("--q-mode") + 1] == "affine" and argv[argv.index("--dtype") + 1] == "bfloat16"
    with pytest.raises(ValueError, match="no mlx_lm.convert flags"):
        convert_argv("py", Path("cut"), Path("cut-mlx"), "nvfp4")


def test_ensure_miniature_quantizes_the_cut_with_mlx(tmp_path, monkeypatch):
    import sys

    art = _mini(mlx_quantize="affine_u4_g64")
    pie_root = tmp_path / "pie"
    bench = tmp_path / "bench"
    bench.mkdir()
    monkeypatch.setenv("PIE_BENCH_BENCH_DIR", str(bench))
    (bench / SHRINK_SCRIPT).write_text(
        "import argparse, json, pathlib\n"
        "ap = argparse.ArgumentParser()\n"
        "for f in ('--repo','--revision','--out','--layers','--repeat','--experts','--cache'): ap.add_argument(f)\n"
        "a = ap.parse_args()\n"
        "p = pathlib.Path(a.out); p.mkdir(parents=True, exist_ok=True)\n"
        "(p / 'config.json').write_text(json.dumps({'num_hidden_layers': 8}))\n"
    )
    fake = tmp_path / "fake"
    (fake / "mlx_lm").mkdir(parents=True)
    (fake / "mlx_lm" / "__init__.py").write_text("")
    (fake / "mlx_lm" / "__main__.py").write_text(
        "import json, pathlib, sys\n"
        "a = sys.argv[1:]\n"
        "assert a[0] == 'convert'\n"
        "src, dst = pathlib.Path(a[a.index('--hf-path') + 1]), pathlib.Path(a[a.index('--mlx-path') + 1])\n"
        "assert not dst.exists()\n"
        "dst.mkdir()\n"
        "cfg = json.loads((src / 'config.json').read_text())\n"
        "cfg['quantization'] = {'group_size': int(a[a.index('--q-group-size') + 1]), 'bits': int(a[a.index('--q-bits') + 1])}\n"
        "(dst / 'config.json').write_text(json.dumps(cfg))\n"
    )
    monkeypatch.setenv("PYTHONPATH", str(fake))
    monkeypatch.setenv("MLX_PY", sys.executable)
    d = ensure_miniature(art, pie_root, tmp_path / "hf", sys.executable)
    assert d.name.endswith("-mlx-affine_u4_g64")
    assert json.loads((d / "config.json").read_text())["quantization"] == {"group_size": 64, "bits": 4}
    assert recipe_from_snapshot(d) == art.miniature
    assert not list(d.parent.glob("*-mlx"))


def test_a_muse_spark_cut_is_quantized_in_place_under_the_release_names(tmp_path, monkeypatch):
    import re
    import subprocess

    from pie_bench.checkpoints import mlx_quantize as mq

    rules = mq.IN_PLACE["muse_spark"]
    quantized = lambda k: any(re.search(p, k) for p in rules["quantize"])
    for k in ("model.language_model.embed_tokens.weight", "model.language_model.layers.1.self_attn.gate_proj.weight",
              "model.language_model.layers.0.mlp.pre_expert_proj.weight", "model.language_model.layers.1.mlp.experts.down_proj.weight"):
        assert quantized(k), k
    for k in ("lm_head.weight", "model.language_model.layers.0.mlp.gate.weight", "model.language_model.layers.0.input_layernorm.weight",
              "model.language_model.layers.0.post_attention_residual_gate.gate", "model.language_model.layers.0.mlp.experts.post_expert_norm.weight"):
        assert not quantized(k), k
    (split_re, how), = rules["split"].items()
    assert [re.sub(split_re, leg, "model.language_model.layers.3.mlp.experts.gate_up_proj") for leg in how["legs"]] == [
        "model.language_model.layers.3.mlp.experts.gate_proj.weight", "model.language_model.layers.3.mlp.experts.up_proj.weight"]
    assert any(re.search(p, "model.vision_tower.layers.0.attn.q_proj.weight") for p in rules["drop"])

    seen = []

    def run(argv, **_):
        seen.append(argv)
        dst = Path(argv[argv.index("--mlx-path") + 1]) if "--mlx-path" in argv else Path(argv[3])
        dst.mkdir()
        (dst / "config.json").write_text("{}")
        if "--mlx-path" not in argv:
            assert json.loads(Path(argv[4]).read_text())["bits"] == 4
        return subprocess.CompletedProcess(argv, 0, "", "")

    monkeypatch.setattr(mq.subprocess, "run", run)
    for family in ("muse_spark", "nemotron_h"):
        cut = tmp_path / family
        cut.mkdir()
        mq.mlx_quantize(cut, "affine_u4_g64", family=family)
        assert (cut / "config.json").exists() and not cut.with_name(cut.name + "-mlx").exists()
    assert seen[0][1].endswith("mlx_quantize_in_place.py") and seen[1][1:4] == ["-m", "mlx_lm", "convert"]
