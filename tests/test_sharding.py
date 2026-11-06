from pathlib import Path

import pytest

from pie_evals.plan.jobs import cell_minutes, make_jobs, process_key, shard_groups
from pie_evals.plan.matrix import Matrix
from pie_evals.results.store import Store
from pie_evals.schema import Tier

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def matrix():
    return Matrix.load(ROOT / "matrix")


def test_shards_respect_budget_and_keep_groups_whole(matrix):
    cells = [c for c in matrix.runnable(Tier.NIGHTLY) if c.platform.id == "l40s-x1"]
    shards = shard_groups(cells, matrix.job_budget_minutes)
    assert sum(len(s) for s in shards) == len(cells)
    for sh in shards:
        assert sum(cell_minutes(c) for c in sh) <= matrix.job_budget_minutes
    # a process group is either entirely inside one shard, or (only if it was itself over budget) split
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
    jobs = make_jobs(matrix, Tier.NIGHTLY, pie_commit="abc", store=Store(tmp_path), platforms=["l40s-x1"])
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
        assert matrix.check_budget(t, cells) == [], matrix.check_budget(t, cells)


@pytest.mark.slow
def test_multi_gpu_platforms_only_run_tp_gt1(matrix):
    for c in matrix.expand():
        if c.platform.count >= 2 and c.mode.tp == 1:
            assert c.tiers == [], f"{c.platform.id} tp1 must not be scheduled"


def test_available_platforms_keeps_runpod_and_online_resident(matrix, monkeypatch):
    import json

    from pie_evals.plan import jobs as J

    runners = {"runners": [{"status": "online", "labels": [{"name": "self-hosted"}, {"name": "macos"}, {"name": "m1-max-32g"}]},
                           {"status": "offline", "labels": [{"name": "m4-pro-48g"}]}]}
    monkeypatch.setattr(J.subprocess, "run", lambda *a, **k: type("R", (), {"stdout": json.dumps(runners)})())
    ok, skipped = J.available_platforms(matrix, "o/r")
    assert "l40s-x1" in ok and "m1-max-32g" in ok
    assert "m4-pro-48g" in skipped and "m2-max" in skipped


def test_targeted_mac_shards_keep_groups_whole(matrix):
    cells = [c for c in matrix.runnable(Tier.TARGETED) if c.platform.id == "m4-pro-48g"]
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
    jobs = make_jobs(matrix, Tier.TARGETED, pie_commit="abc", store=Store(tmp_path), platforms=["m4-pro-48g"])
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

    from pie_evals import cli
    from pie_evals.plan import jobs as J

    def denied(*a, **k):
        raise RuntimeError("HTTP 403")

    monkeypatch.setattr(J.subprocess, "run", denied)
    args = ["--matrix", str(ROOT / "matrix"), "--store", str(tmp_path / "store"), "jobs", "--tier", "targeted", "--pie-commit", "c" * 40,
            "--out", str(tmp_path / "jobs"), "--skip-unavailable"] + [x for p in platforms for x in ("--platform", p)]
    res = CliRunner().invoke(cli.main, args)
    assert res.exit_code == 0, res.output
    return {j["platform"] for j in json.loads((tmp_path / "jobs" / "gh-matrix.json").read_text())["include"]}


def test_unknown_runners_schedule_only_the_macs_asked_for(tmp_path, monkeypatch):
    assert _jobs_cli(tmp_path, monkeypatch, "m5-max-128g") == {"m5-max-128g"}
    assert _jobs_cli(tmp_path, monkeypatch, "m5-max-48g") == set()  # not on the list in config.json, so never scheduled


def test_unknown_runners_and_nothing_asked_schedule_no_resident_mac(matrix, tmp_path, monkeypatch):
    assert _jobs_cli(tmp_path, monkeypatch) <= {p.id for p in matrix.platforms.values() if p.runpod_gpu_type}
