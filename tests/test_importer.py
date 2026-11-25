from pathlib import Path

from pie_bench.checkpoints import pie_import as im
from pie_bench.schema import ArtifactSpec, QuantScheme, SourceFormat


def _art(fmt=SourceFormat.MLX, sku=None):
    return ArtifactSpec(id="qwen36-mini", base_model="mlx-community/Qwen3.6-35B-A3B-4bit", family="qwen3_6_moe", scheme=QuantScheme.AFFINE_U4_G64, source_format=fmt, pie_sku=sku)


def test_needs_import_only_for_mlx():
    assert im.needs_import(_art())
    assert not im.needs_import(_art(fmt=SourceFormat.HF_SAFETENSORS))


def test_ensure_artifact_runs_import_once(tmp_path, monkeypatch):
    calls = []

    def fake_run(argv, **kw):
        if "--help" in argv:
            return type("R", (), {"returncode": 0, "stderr": "", "stdout": "      --deployment <NAME>"})()
        calls.append(argv)
        out = Path(argv[argv.index("--out") + 1])
        (out / "qwen36.zt").write_bytes(b"zt")
        return type("R", (), {"returncode": 0, "stderr": "", "stdout": ""})()

    monkeypatch.setattr(im.subprocess, "run", fake_run)
    zt = im.ensure_artifact(_art(sku="qwen36-35b-a3b-mini-u4g64-kv-bf16"), tmp_path / "snap", Path("/pie/target/release/pie"), "e06ff359377b", root=tmp_path / "cache", log=lambda *_: None)
    assert zt.name == "qwen36.zt" and zt.parent.name == "qwen36-mini-e06ff359"
    assert calls[0][:3] == ["/pie/target/release/pie", "model", "import"] and "--deployment" in calls[0]
    zt2 = im.ensure_artifact(_art(), tmp_path / "snap", Path("/pie/target/release/pie"), "e06ff359377b", root=tmp_path / "cache", log=lambda *_: None)
    assert zt2 == zt and len(calls) == 1


def test_a_pinned_sku_is_always_imported():
    from pie_bench.checkpoints.pie_import import needs_import
    from pie_bench.schema import ArtifactSpec

    base = {"id": "g", "base_model": "meta-models/Muse-Glimmer-30B", "family": "muse_glimmer", "scheme": "affine_u4_g64"}
    assert needs_import(ArtifactSpec(**base, pie_sku="muse-glimmer-30b-u4g64-kv-bf16"))
    assert not needs_import(ArtifactSpec(**base))


def test_an_older_pie_takes_the_row_as_sku(monkeypatch):
    monkeypatch.setattr(im.subprocess, "run", lambda argv, **kw: type("R", (), {"stdout": "      --sku <NAME>"})())
    assert im.row_flag(Path("pie")) == "--sku"


def test_a_drafter_row_is_imported_by_repository_id_with_its_drafter(tmp_path, monkeypatch):
    calls = []

    def fake_run(argv, **kw):
        if "--help" in argv:
            return type("R", (), {"returncode": 0, "stderr": "", "stdout": "      --deployment <NAME>"})()
        calls.append(argv)
        out = Path(argv[argv.index("--out") + 1])
        (out / "q.zt").write_bytes(b"zt")
        return type("R", (), {"returncode": 0, "stderr": "", "stdout": ""})()

    monkeypatch.setattr(im.subprocess, "run", fake_run)
    art = ArtifactSpec(id="q27", base_model="mlx-community/Qwen3.6-27B-4bit", family="qwen3_6", scheme=QuantScheme.AFFINE_U4_G64,
                       source_format=SourceFormat.MLX, pie_sku="qwen36-27b-dflash-u4g64-kv-bf16", pie_drafter="dflash")
    im.ensure_artifact(art, tmp_path / "snap", Path("/pie"), "e06ff359377b", root=tmp_path / "cache", log=lambda *_: None)
    argv = calls[0]
    assert argv[3] == "mlx-community/Qwen3.6-27B-4bit", "a local path matches no published head"
    assert argv[argv.index("--drafter") + 1] == "dflash"
    assert argv[argv.index("--deployment") + 1] == "qwen36-27b-dflash-u4g64-kv-bf16"


def test_a_failed_import_is_recorded_by_the_line_that_says_why():
    from pie_bench.runner.job import import_reason

    e = RuntimeError("pie model import failed for q (exit 1):\n✗ --deployment r: `r` does not read this checkpoint: no `aux.fc.weight`\n"
                     "This import converts for the deployment named and for no other")
    assert "aux.fc.weight" in import_reason(e)


def test_a_drafter_row_imports_its_plain_deployment_from_the_snapshot(tmp_path, monkeypatch):
    calls = []

    def fake_run(argv, **kw):
        if "--help" in argv:
            return type("R", (), {"returncode": 0, "stderr": "", "stdout": "      --deployment <NAME>"})()
        calls.append(argv)
        out = Path(argv[argv.index("--out") + 1])
        (out / "g.zt").write_bytes(b"zt")
        return type("R", (), {"returncode": 0, "stderr": "", "stdout": ""})()

    monkeypatch.setattr(im.subprocess, "run", fake_run)
    art = ArtifactSpec(id="g26", base_model="mlx-community/gemma-4-26b-a4b-it-4bit", family="gemma4_moe", scheme=QuantScheme.AFFINE_U4_G64,
                       source_format=SourceFormat.MLX, pie_sku="gemma4-26b-a4b-dflash-u4g64-kv-bf16", pie_drafter="dflash")
    assert im.plain_sku(art) == "gemma4-26b-a4b-u4g64-kv-bf16"
    assert im.plain_sku(art.model_copy(update={"pie_sku": "qwen38-27b-dflash2-u4g64-kv-bf16"})) == "qwen38-27b-u4g64-kv-bf16"
    assert im.plain_sku(_art(sku="qwen36-27b-u4g64-kv-bf16")) is None
    root = tmp_path / "cache"
    assert not im.have_artifacts(art, "e06ff359377b", root)
    im.ensure_artifact(art, tmp_path / "snap", Path("/pie"), "e06ff359377b", root=root, log=lambda *_: None)
    assert not im.have_artifacts(art, "e06ff359377b", root), "the raw rows still need the plain import's snapshot"
    zt = im.ensure_artifact(art, tmp_path / "snap", Path("/pie"), "e06ff359377b", root=root, plain=True, log=lambda *_: None)
    argv = calls[1]
    assert argv[3] == str(tmp_path / "snap") and "--drafter" not in argv
    assert argv[argv.index("--deployment") + 1] == "gemma4-26b-a4b-u4g64-kv-bf16"
    assert zt.parent.name == "g26-e06ff359-plain" and im.have_artifacts(art, "e06ff359377b", root)
