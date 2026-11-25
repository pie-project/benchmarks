from pathlib import Path

from pie_bench.checkpoints.snapshots import snapshot_dir_if_present
from pie_bench.schema.cell import ArtifactSpec


def _art(**over) -> ArtifactSpec:
    base = dict(id="qwen3.6-35b-a3b-mlx4", base_model="mlx-community/Qwen3.6-35B-A3B-4bit", family="qwen3_6", scheme="affine_u4_g64", source_format="mlx")
    base.update(over)
    return ArtifactSpec(**base)


def test_a_full_row_never_picks_the_miniature_built_beside_it(tmp_path: Path):
    snaps = tmp_path / "models--mlx-community--Qwen3.6-35B-A3B-4bit" / "snapshots"
    rev = "38740b847e4cb78f352aba30aa41c76e08e6eb46"
    for d in (rev, "mini-l0-4-e16"):
        (snaps / d).mkdir(parents=True)
        (snaps / d / "config.json").write_text("{}")
        (snaps / d / "model.safetensors").write_bytes(b"x")
    assert snapshot_dir_if_present(_art(), tmp_path) == snaps / rev
    assert snapshot_dir_if_present(_art(revision=rev), tmp_path) == snaps / rev
    (snaps / rev / "config.json").unlink()
    assert snapshot_dir_if_present(_art(), tmp_path) is None


def test_a_pinned_revision_wins_over_the_newest_snapshot(tmp_path: Path):
    snaps = tmp_path / "models--mlx-community--Qwen3.6-35B-A3B-4bit" / "snapshots"
    old, new = "38740b847e4cb78f352aba30aa41c76e08e6eb46", "f000000000000000000000000000000000000000"
    for d in (old, new):
        (snaps / d).mkdir(parents=True)
        (snaps / d / "config.json").write_text("{}")
        (snaps / d / "model.safetensors").write_bytes(b"x")
    assert snapshot_dir_if_present(_art(), tmp_path) == snaps / new
    assert snapshot_dir_if_present(_art(revision=old), tmp_path) == snaps / old


def test_a_snapshot_whose_weights_are_gone_is_not_present(tmp_path: Path):
    snaps = tmp_path / "models--mlx-community--Qwen3.6-35B-A3B-4bit" / "snapshots"
    rev = "38740b847e4cb78f352aba30aa41c76e08e6eb46"
    (snaps / rev).mkdir(parents=True)
    (snaps / rev / "config.json").write_text("{}")
    (snaps / rev / "model.safetensors").symlink_to(tmp_path / "blobs" / "gone")
    assert snapshot_dir_if_present(_art(), tmp_path) is None
    assert snapshot_dir_if_present(_art(revision=rev), tmp_path) is None
    (tmp_path / "blobs").mkdir()
    (tmp_path / "blobs" / "gone").write_bytes(b"x")
    assert snapshot_dir_if_present(_art(), tmp_path) == snaps / rev


def test_the_revision_main_resolved_to_wins_over_hex_order(tmp_path: Path):
    repo = tmp_path / "models--mlx-community--Qwen3.6-35B-A3B-4bit"
    old, new = "f000000000000000000000000000000000000000", "38740b847e4cb78f352aba30aa41c76e08e6eb46"
    for d in (old, new):
        (repo / "snapshots" / d).mkdir(parents=True)
        (repo / "snapshots" / d / "config.json").write_text("{}")
    (repo / "refs").mkdir()
    (repo / "refs" / "main").write_text(new)
    assert snapshot_dir_if_present(_art(), tmp_path, weights=False) == repo / "snapshots" / new
    assert snapshot_dir_if_present(_art(), tmp_path) is None
