from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from pie_bench.paths import MATRIX
from pie_bench.plan.jobs import make_jobs
from pie_bench.plan.matrix import Matrix
from pie_bench.results.store import Store
from pie_bench.schema import CellStatus, PerfMetrics, Provenance, Record, Tier

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def matrix():
    return Matrix.load(MATRIX)


@pytest.fixture(scope="module")
def cells(matrix):
    return matrix.expand(platforms=["l40s-x1", "m4-pro-48g"])


def _rec(cell, value, when, status=CellStatus.PASS, engine_version="abc123", run="r"):
    prov = Provenance(harness_commit="h", pie_commit="abc123", engine_version=engine_version, checkpoint_revision="rev", hardware_fingerprint={"gpu": "x"})
    return Record(run_id=run, job_id="j", tier=Tier.SMOKE, cell_id=cell.cell_id, cell_key=cell.cell_key, cell=cell.model_copy(update={"engine_version": engine_version}),
                  status=status, perf=PerfMetrics(primary="decode_tok_s", decode_tok_s=value, rounds=[value], cov=0.002, prompt_tokens=100, output_tokens=64),
                  provenance=prov, started_at=when, duration_s=30.0)


def test_store_roundtrip_and_history(tmp_path, matrix, cells):
    cells = matrix.runnable(Tier.SMOKE, cells)
    cell = next(c for c in cells if c.workload.id == "ss-128-64" and c.artifact.id == "qwen3.5-0.8b-bf16" and c.platform.id == "l40s-x1" and c.program.id == "text-completion-bench")
    st = Store(tmp_path / "store")
    t0 = datetime(2026, 9, 1, tzinfo=timezone.utc)
    for i, v in enumerate([430, 432, 431, 433]):
        st.write_run([_rec(cell, v, t0 + timedelta(days=i), run=f"r{i}")], tier=Tier.SMOKE, run_id=f"r{i}", when=t0 + timedelta(days=i))
    hist = st.history()
    assert hist[cell.cell_id] == [430, 432, 431, 433]
    assert st.latest_by_cell()[cell.cell_id]["primary_value"] == 433


def test_store_refuses_missing_provenance(tmp_path, matrix, cells):
    cell = matrix.runnable(Tier.SMOKE, cells)[0]
    r = _rec(cell, 1.0, datetime.now(timezone.utc))
    r.provenance.checkpoint_revision = None
    with pytest.raises(ValueError):
        Store(tmp_path).write_run([r], tier=Tier.SMOKE, run_id="x")


def test_jobs_group_one_model_per_process(matrix, tmp_path):
    jobs = make_jobs(matrix, Tier.SMOKE, pie_commit="abc123", store=Store(tmp_path), platforms=["l40s-x1"])
    assert 1 <= len(jobs) <= matrix.suites["smoke"].max_jobs_per_platform
    for j in jobs:
        assert j.platform_id == "l40s-x1" and j.pie_build_features == ["cuda"]
        groups = j.cells_by_process()
        assert all(len({c.artifact.artifact_key for c in g}) == 1 for g in groups.values())
        assert j.model_dump_json()


def _pair(matrix, workload="ob-512-200"):
    cells = matrix.runnable(Tier.TARGETED, matrix.expand(platforms=["m4-pro-48g"], artifacts=["gemma-4-26b-a4b-mlx4", "gemma-4-26b-a4b-llamacpp"]))

    def pick(aid):
        return next(c for c in cells if c.workload.id == workload and c.artifact.id == aid and c.platform.id == "m4-pro-48g")

    return pick("gemma-4-26b-a4b-mlx4"), pick("gemma-4-26b-a4b-llamacpp")


def test_targeted_mac_jobs_keep_one_engine_per_process(matrix, tmp_path):
    jobs = make_jobs(matrix, Tier.TARGETED, pie_commit="abc123", store=Store(tmp_path), platforms=["m4-pro-48g"])
    suite = matrix.suites["targeted"]
    assert jobs and (not suite.enforce_budget or len(jobs) <= suite.max_jobs_per_platform)
    for j in jobs:
        assert j.platform_id == "m4-pro-48g" and j.pie_build_features == ["metal"]
        groups = j.cells_by_process()
        assert all(len({c.artifact.artifact_key for c in g}) == 1 for g in groups.values())
        assert all(len({str(c.engine) for c in g}) == 1 for g in groups.values())
