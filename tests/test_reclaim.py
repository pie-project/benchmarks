from pathlib import Path

from pie_bench.paths import MATRIX
from pie_bench.plan.jobs import make_jobs
from pie_bench.plan.matrix import Matrix
from pie_bench.runner import disk_space as reclaim
from pie_bench.schema import Tier

ROOT = Path(__file__).resolve().parents[1]


def test_reclaim_keeps_this_jobs_imports_and_builds(tmp_path: Path, monkeypatch):
    m = Matrix.load(MATRIX)
    job = make_jobs(m, Tier.NIGHTLY, pie_commit="c" * 40, platforms=["l40s-x1"], engines=["pie"], cells=[c for c in m.expand(artifacts=["qwen3.5-0.8b-bf16"])])[0]
    root = tmp_path / "cache"
    for d in ("artifacts/qwen3.5-0.8b-bf16-cccccccc", "artifacts/qwen3.5-0.8b-bf16-01234567", "artifacts/gemma-4-e4b-bf16-cccccccc", "artifacts/.tmp-x", "builds/cccccccccccc-cuda", "builds/012345678901-cuda", "shrink"):
        (root / d).mkdir(parents=True)
        (root / d / "f").write_bytes(b"x" * 10)
    monkeypatch.setenv("PIE_BENCH_CACHE", str(root))
    monkeypatch.setattr(reclaim, "free_gib", lambda p: 500.0)
    assert reclaim.reclaim(job, tmp_path / "hf", log=lambda *_: None) == 0.0
    assert (root / "artifacts/gemma-4-e4b-bf16-cccccccc").exists()
    monkeypatch.setattr(reclaim, "free_gib", lambda p: 10.0)
    monkeypatch.setattr(reclaim, "_drop_hf_repos", lambda *a, **k: None)
    reclaim.reclaim(job, tmp_path / "hf", log=lambda *_: None)
    assert (root / "artifacts/qwen3.5-0.8b-bf16-cccccccc").exists()
    assert (root / "builds/cccccccccccc-cuda").exists()
    for gone in ("artifacts/qwen3.5-0.8b-bf16-01234567", "artifacts/gemma-4-e4b-bf16-cccccccc", "artifacts/.tmp-x", "builds/012345678901-cuda", "shrink"):
        assert not (root / gone).exists(), gone


def test_reclaim_on_a_mac_drops_hf_repos_only_when_asked(tmp_path: Path, monkeypatch):
    m = Matrix.load(MATRIX)
    job = make_jobs(m, Tier.TARGETED, pie_commit="c" * 40, platforms=["m4-pro-48g"], engines=["pie"], cells=[c for c in m.expand(artifacts=["gemma-4-26b-a4b-mlx4"])])[0]
    root = tmp_path / "cache"
    for d in ("artifacts/gemma-4-26b-a4b-mlx4-cccccccc", "artifacts/gemma-4-26b-a4b-mlx4-cccccccc-plain", "artifacts/gemma-4-26b-a4b-mlx4-01234567-plain", "artifacts/gemma-4-26b-a4b-mlx4-01234567", "builds/cccccccccccc-metal", "builds/012345678901-metal"):
        (root / d).mkdir(parents=True)
        (root / d / "f").write_bytes(b"x" * 10)
    monkeypatch.setenv("PIE_BENCH_CACHE", str(root))
    monkeypatch.setattr(reclaim.sys, "platform", "darwin")
    monkeypatch.delenv("PIE_BENCH_RECLAIM_HF", raising=False)
    dropped = []
    monkeypatch.setattr(reclaim, "_drop_hf_repos", lambda *a, **k: dropped.append(a))
    monkeypatch.setattr(reclaim, "free_gib", lambda p: 10.0)
    reclaim.reclaim(job, tmp_path / "hf", log=lambda *_: None)
    assert (root / "artifacts/gemma-4-26b-a4b-mlx4-cccccccc").exists()
    assert (root / "artifacts/gemma-4-26b-a4b-mlx4-cccccccc-plain").exists(), "the raw rows' plain deployment is this job's too"
    assert (root / "builds/cccccccccccc-metal").exists()
    for gone in ("artifacts/gemma-4-26b-a4b-mlx4-01234567", "artifacts/gemma-4-26b-a4b-mlx4-01234567-plain", "builds/012345678901-metal"):
        assert not (root / gone).exists(), gone
    assert dropped == []
    monkeypatch.setenv("PIE_BENCH_RECLAIM_HF", "1")
    reclaim.reclaim(job, tmp_path / "hf", log=lambda *_: None)
    assert dropped and dropped[0][1] == {c.artifact.base_model for c in job.cells}
