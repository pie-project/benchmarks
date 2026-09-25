"""End-to-end of the node runner with a fake engine: no GPU, no pie build.
Exercises grouping, control A/A gating, adaptive repetition, NOISY marking,
failure classification and the records.jsonl output."""

from pathlib import Path

import pytest

from pie_evals.node import runner as runner_mod
from pie_evals.node.engines.base import BenchResult, Engine, EngineLaunchError
from pie_evals.orchestrate.jobs import make_jobs
from pie_evals.orchestrate.matrix import Matrix
from pie_evals.orchestrate.store import Store
from pie_evals.schema import CellStatus, ErrorClass, PerfMetrics, Record, Tier

ROOT = Path(__file__).resolve().parents[1]


class FakeEngine(Engine):
    name = "pie"
    script = "scripts/bench/fake.py"
    calls: list[str] = []
    behaviour: dict[str, object] = {}

    def default_python(self):
        return "python3"

    def model_arg(self):
        return self.artifact.base_model

    def engine_args(self, workload):
        return []

    def version(self):
        return "deadbeef"

    def run(self, workload, common_args, out_dir, timeout_s):
        FakeEngine.calls.append(workload.id)
        b = FakeEngine.behaviour.get(workload.id)
        if isinstance(b, EngineLaunchError):
            raise b
        values = b if isinstance(b, list) else [float(b or 100.0)]
        v = values[min(len([c for c in FakeEngine.calls if c == workload.id]) - 1, len(values) - 1)]
        perf = PerfMetrics(primary="decode_tok_s", decode_tok_s=v, output_tok_s=v * 8, prompt_tokens=128, output_tokens=64, requests=1, failed=0)
        return BenchResult(perf=perf, summary={}, requests=[{"ok": True, "prompt_tokens": 128, "output_token_ids": [1, 2, 3]}], argv=[], output_token_ids=[[1, 2, 3]])


@pytest.fixture
def job(tmp_path):
    m = Matrix.load(ROOT / "matrix")
    cells = [c for c in m.runnable(Tier.SMOKE) if c.platform.id == "l40s-x1" and c.artifact.id == "qwen3.5-0.8b-bf16" and c.program.id == "text-completion-bench" and c.mode.tp == 1]
    j = make_jobs(m, Tier.SMOKE, pie_commit="deadbeef", store=Store(tmp_path / "store"), platforms=["l40s-x1"], cells=cells)[0]
    assert {c.workload.id for c in j.cells} >= {"control-aa", "ss-128-64", "c8"}
    return j


@pytest.fixture
def patched(monkeypatch, tmp_path):
    FakeEngine.calls = []
    FakeEngine.behaviour = {}
    monkeypatch.setattr(runner_mod, "get_engine", lambda name: FakeEngine)
    monkeypatch.setattr(runner_mod, "load_recipe", lambda *a, **k: {})
    snap = tmp_path / "hf" / "models--Qwen--Qwen3.5-0.8B" / "snapshots" / "abc"
    snap.mkdir(parents=True)
    (snap / "config.json").write_text('{"num_hidden_layers": 28}')
    (snap / "model.safetensors").write_bytes(b"x")  # a snapshot without weights is not present (snapshots.has_weights)

    class P:
        def before_job(self, plat):
            return {"state": "ok"}

        def between_engines(self, plat, names):
            return {}

        def after_model(self, plat, before):
            return []

    monkeypatch.setattr(runner_mod.pf, "Preflight", P)
    monkeypatch.setattr(runner_mod.prov, "hardware_fingerprint", lambda: {"gpu": "fake"})
    monkeypatch.setattr(runner_mod.prov, "build_provenance", lambda *a, **k: runner_mod.prov.Provenance(harness_commit="h", engine_version="deadbeef", checkpoint_revision="abc", hardware_fingerprint={"gpu": "fake"}))
    # accuracy gate: no reference on this box → skipped, never a failure
    monkeypatch.setattr(runner_mod.NodeRunner, "_accuracy", lambda self, cell, engine, snap: runner_mod.AccuracyMetrics())
    return tmp_path / "hf"


def _run(job, hf, tmp_path):
    r = runner_mod.NodeRunner(job, pie_root=tmp_path / "pie", out_dir=tmp_path / "out", hf_cache=hf, build=False)
    recs = r.run()
    lines = (tmp_path / "out" / "records.jsonl").read_text().splitlines()
    assert len(lines) >= len(recs)
    return recs, [Record.model_validate_json(ln) for ln in lines]


def test_happy_path_one_process_all_cells(job, patched, tmp_path):
    recs, _ = _run(job, patched, tmp_path)
    assert {r.status for r in recs} == {CellStatus.PASS}
    assert FakeEngine.calls[0] == "control-aa"  # control runs first
    assert all(r.provenance.pie_commit == "deadbeef" for r in recs)
    # smoke: adaptive → without history, every cell confirms with extra rounds
    ss = next(r for r in recs if r.cell.workload.id == "ss-128-64")
    assert len(ss.perf.rounds) == 1 + job.repetition.confirm_rounds


def test_history_within_band_skips_confirmation(job, patched, tmp_path):
    cid = next(c.cell_id for c in job.cells if c.workload.id == "ss-128-64")
    job = job.model_copy(update={"history": {cid: [100.0, 100.5, 99.5, 100.2]}})
    recs, _ = _run(job, patched, tmp_path)
    ss = next(r for r in recs if r.cell.workload.id == "ss-128-64")
    assert len(ss.perf.rounds) == 1


def test_noisy_rounds_mark_cell_noisy(job, patched, tmp_path):
    FakeEngine.behaviour["ss-128-64"] = [100.0, 90.0, 110.0]
    recs, _ = _run(job, patched, tmp_path)
    ss = next(r for r in recs if r.cell.workload.id == "ss-128-64")
    assert ss.status == CellStatus.NOISY and "cov" in ss.invalid_reason


def test_control_failure_invalidates_process(job, patched, tmp_path):
    FakeEngine.behaviour["control-aa"] = [100.0, 130.0, 130.0, 100.0, 130.0, 130.0]  # three rounds a look; noisy twice
    recs, _ = _run(job, patched, tmp_path)
    ctrl = next(r for r in recs if r.cell.workload.id == "control-aa")
    assert ctrl.status == CellStatus.NOISY
    others = [r for r in recs if r.cell.workload.id != "control-aa"]
    assert others and all(r.status == CellStatus.NOISY and r.error_class == ErrorClass.HARNESS_INVALID for r in others)
    assert FakeEngine.calls.count("control-aa") == 6


def test_noisy_control_gets_one_more_look(job, patched, tmp_path):
    FakeEngine.behaviour["control-aa"] = [100.0, 130.0]  # the second look settles at 130 every round
    recs, _ = _run(job, patched, tmp_path)
    ctrl = next(r for r in recs if r.cell.workload.id == "control-aa")
    assert ctrl.status == CellStatus.PASS and FakeEngine.calls.count("control-aa") == 6
    assert all(r.status == CellStatus.PASS for r in recs if r.cell.workload.id != "control-aa")


def test_engine_failure_is_classified(job, patched, tmp_path):
    FakeEngine.behaviour["c8"] = EngineLaunchError(ErrorClass.OOM, "CUDA out of memory")
    recs, _ = _run(job, patched, tmp_path)
    c8 = next(r for r in recs if r.cell.workload.id == "c8")
    assert c8.status == CellStatus.FAIL and c8.error_class == ErrorClass.OOM


def test_missing_checkpoint_fails_load(job, patched, tmp_path):
    recs, _ = _run(job, tmp_path / "empty-hf", tmp_path)
    assert recs == []  # nothing ran …
    lines = [Record.model_validate_json(ln) for ln in (tmp_path / "out" / "records.jsonl").read_text().splitlines()]
    assert lines and all(r.status == CellStatus.FAIL and r.error_class == ErrorClass.LOAD_FAIL for r in lines)  # … but every cell is accounted for


def test_soft_budget_records_unreached_cells_as_not_run(job, patched, tmp_path):
    job = job.model_copy(update={"budget_s": 0, "kill_s": 600})  # budget already exhausted
    recs, lines = _run(job, patched, tmp_path)
    assert recs == []
    assert lines and all(r.status == CellStatus.NOT_RUN and "budget" in (r.invalid_reason or "") for r in lines)
    assert {r.cell_id for r in lines} == {c.cell_id for c in job.cells}  # every cell accounted for


def test_per_cell_timeout_is_bounded_by_kill_deadline(job, patched, tmp_path):
    seen = []
    orig = FakeEngine.run

    def spy(self, workload, common_args, out_dir, timeout_s):
        seen.append(timeout_s)
        return orig(self, workload, common_args, out_dir, timeout_s)

    FakeEngine.run = spy
    try:
        job = job.model_copy(update={"budget_s": 3600, "kill_s": 120, "per_cell_timeout_s": 1800})
        _run(job, patched, tmp_path)
    finally:
        FakeEngine.run = orig
    assert seen and all(t <= 120 for t in seen)


def test_out_dir_is_absolute_for_subprocesses(job, patched, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    r = runner_mod.NodeRunner(job, pie_root=tmp_path / "pie", out_dir=Path("out/rel"), hf_cache=patched, build=False)
    assert r.out.is_absolute() and r.out == (tmp_path / "out/rel").resolve()


def test_cell_priority_runs_control_then_cheap_shapes_first():
    from types import SimpleNamespace as NS

    from pie_evals.node.runner import cell_priority

    def cell(kind, est):
        return NS(workload=NS(kind=NS(value=kind), est_minutes=est))

    cells = [cell("closed_loop", 3.0), cell("single_stream", 0.5), cell("control_aa", 0.5), cell("long_context", 1.5)]
    got = sorted(cells, key=cell_priority)
    assert [c.workload.kind.value for c in got] == ["control_aa", "single_stream", "long_context", "closed_loop"]


def test_heavy_model_on_a_small_card_boots_short_and_long_shapes_apart():
    from pathlib import Path

    from pie_evals.node.engines.shape import context_tokens_for
    from pie_evals.node.runner import SHORT_CONTEXT_TOKENS, split_heavy_processes
    from pie_evals.orchestrate.jobs import make_jobs
    from pie_evals.orchestrate.matrix import Matrix
    from pie_evals.schema import Tier

    m = Matrix.load(Path(__file__).resolve().parents[1] / "matrix")
    # Qwen3.6-27B (14 GiB) on the 32 GB RTX 5090: two boots; the 0.8B: one
    for aid, split in (("qwen3.6-27b-mlx4", True), ("qwen3.5-0.8b-bf16", False)):
        cells = [c for c in m.expand() if c.artifact.id == aid and c.program.id == "text-completion-bench"]
        jobs = make_jobs(m, Tier.NIGHTLY, pie_commit="c" * 40, platforms=["rtx5090-x1"], engines=["pie"], cells=cells)
        groups = {}
        for j in jobs:
            groups.update(j.cells_by_process())
        out = split_heavy_processes(groups)
        keys = sorted(k[2] for k in out)
        if split:
            assert any(k.endswith("-short") for k in keys) and any(k.endswith("-long") for k in keys), keys
            for k, cs in out.items():
                longs = [context_tokens_for(c.workload) > SHORT_CONTEXT_TOKENS for c in cs]
                assert all(longs) if k[2].endswith("-long") else not any(longs)
        else:
            assert keys == sorted(k[2] for k in groups) and not any(k.endswith(("-short", "-long")) for k in keys)


def test_recipe_follows_the_cell_and_keeps_what_the_boot_added(job):
    # SGLang captured graphs to the first cell's concurrency and ran wider shapes eager (nightly 36099862659)
    ss = next(c for c in job.cells if c.workload.id == "ss-128-64")
    c8 = next(c for c in job.cells if c.workload.id == "c8")
    base = runner_mod.load_recipe("pie", "competitive", ss.platform, ss.workload, family=ss.artifact.family)
    base["snapshot_dir"], base["pin"] = "/snap", "0.30.0"
    fresh = runner_mod.recipe_for_cell(base, "competitive", c8)
    assert (base["max_forward_requests"], fresh["max_forward_requests"]) == (1, 8)
    assert fresh["snapshot_dir"] == "/snap" and fresh["pin"] == "0.30.0"
