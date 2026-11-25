from pathlib import Path

import pytest

from pie_bench.paths import MATRIX
from pie_bench.plan.jobs import cell_minutes, make_jobs, process_key, shard_groups
from pie_bench.plan.matrix import Matrix
from pie_bench.results.store import open_store
from pie_bench.schema import Tier

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def matrix():
    return Matrix.load(MATRIX)


def test_shards_respect_budget_and_keep_groups_whole(matrix):
    cells = [c for c in matrix.runnable(Tier.NIGHTLY, matrix.expand(platforms=["l40s-x1"])) if c.platform.id == "l40s-x1"]
    shards = shard_groups(cells, matrix.job_budget_minutes)
    assert sum(len(s) for s in shards) == len(cells)
    for sh in shards:
        assert sum(cell_minutes(c) for c in sh) <= matrix.job_budget_minutes
    placement = {}
    for i, sh in enumerate(shards):
        for c in sh:
            placement.setdefault(process_key(c), set()).add(i)
    groups = {}
    for c in cells:
        groups.setdefault(process_key(c), []).append(c)
    for k, idxs in placement.items():
        if len(idxs) > 1:
            assert sum(cell_minutes(c) for c in groups[k]) > matrix.job_budget_minutes, f"group {k} split without need"


def test_jobs_carry_time_policy(matrix, tmp_path):
    jobs = make_jobs(matrix, Tier.NIGHTLY, pie_commit="abc", store=open_store(tmp_path), platforms=["l40s-x1"])
    assert len(jobs) > 1
    ids = [j.job_id for j in jobs]
    assert len(ids) == len(set(ids))
    for j in jobs:
        assert j.budget_s == j.kill_s
        assert j.kill_s == int(matrix.job_budget_minutes * matrix.kill_factor * 60)
        assert j.per_cell_timeout_s <= j.kill_s
        assert j.est_minutes <= matrix.job_budget_minutes


@pytest.mark.slow
def test_every_tier_within_job_caps(matrix):
    cells = matrix.expand()
    for t in Tier:
        assert matrix.check_budget(t, cells, enforced_only=True) == [], matrix.check_budget(t, cells, enforced_only=True)


@pytest.mark.slow
def test_multi_gpu_platforms_only_run_tp_gt1(matrix):
    for c in matrix.expand():
        if c.platform.count >= 2 and c.mode.tp == 1:
            assert c.tiers == [], f"{c.platform.id} tp1 must not be scheduled"



def test_targeted_mac_shards_keep_groups_whole(matrix):
    cells = [c for c in matrix.runnable(Tier.TARGETED, matrix.expand(platforms=["m4-pro-48g"])) if c.platform.id == "m4-pro-48g"]
    budget = 10.0
    shards = shard_groups(cells, budget)
    assert len(shards) > 1
    assert sum(len(s) for s in shards) == len(cells)
    placement = {}
    for i, sh in enumerate(shards):
        for c in sh:
            placement.setdefault(process_key(c), set()).add(i)
    groups = {}
    for c in cells:
        groups.setdefault(process_key(c), []).append(c)
    for k, idxs in placement.items():
        if len(idxs) > 1:
            assert sum(cell_minutes(c) for c in groups[k]) > budget, f"group {k} split without need"


def test_targeted_mac_jobs_build_metal_and_pin_splash(matrix, tmp_path):
    jobs = make_jobs(matrix, Tier.TARGETED, pie_commit="abc", store=open_store(tmp_path), platforms=["m4-pro-48g"])
    assert jobs
    assert any(str(c.engine) == "splash" for j in jobs for c in j.cells)
    for j in jobs:
        assert j.per_cell_timeout_s <= j.kill_s
        assert j.pie_build_features == ["metal"]
        if any(str(c.engine) == "splash" for c in j.cells):
            assert j.baseline_versions.get("splash") == matrix.engines["splash"].pin


def _jobs_cli(tmp_path, monkeypatch, *platforms):
    import json

    from click.testing import CliRunner

    from pie_bench import cli
    from pie_bench.plan import jobs as J

    def denied(*a, **k):
        raise RuntimeError("HTTP 403")

    monkeypatch.setattr(J.subprocess, "run", denied)
    args = ["--matrix", str(MATRIX), "--store", str(tmp_path / "store"), "jobs", "--tier", "targeted", "--pie-commit", "c" * 40,
            "--out", str(tmp_path / "jobs"), "--skip-unavailable"] + [x for p in platforms for x in ("--platform", p)]
    res = CliRunner().invoke(cli.main, args)
    assert res.exit_code == 0, res.output
    return {j["platform"] for j in json.loads((tmp_path / "jobs" / "gh-matrix.json").read_text())["include"]}


