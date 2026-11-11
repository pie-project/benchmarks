from pathlib import Path

from pie_bench.schema.cell import ArtifactSpec


def _art() -> ArtifactSpec:
    return ArtifactSpec(id="qwen3.6-35b-a3b-mlx4", base_model="mlx-community/Qwen3.6-35B-A3B-4bit", family="qwen3_6", scheme="affine_u4_g64", source_format="mlx")


def test_t0_fetches_the_tokenizer_files_of_the_revision_it_reads(tmp_path: Path, monkeypatch):
    import huggingface_hub

    from pie_bench.node.snapshots import TOKENIZER_PATTERNS, with_tokenizer

    snap = tmp_path / "models--mlx-community--Qwen3.6-35B-A3B-4bit" / "snapshots" / "38740b847e4cb78f352aba30aa41c76e08e6eb46"
    calls = []
    monkeypatch.setattr(huggingface_hub, "snapshot_download", lambda repo, **kw: calls.append((repo, kw)))
    assert with_tokenizer(_art(), snap, tmp_path, log=lambda _: None) == snap
    assert calls[0][0] == "mlx-community/Qwen3.6-35B-A3B-4bit"
    assert calls[0][1]["revision"] == snap.name and calls[0][1]["allow_patterns"] == TOKENIZER_PATTERNS

    def offline(repo, **kw):
        raise OSError("offline")

    monkeypatch.setattr(huggingface_hub, "snapshot_download", offline)
    said = []
    assert with_tokenizer(_art(), snap, tmp_path, log=said.append) == snap
    assert "not fetched" in said[0]
