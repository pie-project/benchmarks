import os
from pathlib import Path

import pytest

from pie_bench.engines.engine import BenchResult, Engine, EngineLaunchError
from pie_bench.paths import MATRIX
from pie_bench.plan.jobs import make_jobs
from pie_bench.plan.matrix import Matrix
from pie_bench.results.store import Store
from pie_bench.runner import job as runner_mod
from pie_bench.schema import CellStatus, ErrorClass, PerfMetrics, Record, Tier, WorkloadSpec

os.environ.setdefault("PIE_BENCH_SETTLE", "0")
os.environ.setdefault("PIE_BENCH_GPU_IDLE", "0")

ROOT = Path(__file__).resolve().parents[1]
REAL_ACCURACY = runner_mod.NodeRunner._accuracy


def _asked(workload):
    from pie_bench.engines.shapes import workload_mode_args
    from pie_bench.runner.round_checks import expected_requests
    return expected_requests(workload_mode_args(workload)[1]) or 1

class FakeEngine(Engine):
    name = "pie"
    script = "fake.py"
    calls: list[str] = []
    common: dict[str, list[str]] = {}
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
        FakeEngine.common[workload.id] = list(common_args)
        b = FakeEngine.behaviour.get(workload.id)
        if isinstance(b, EngineLaunchError):
            raise b
        values = b if isinstance(b, list) else [float(b or 100.0)]
        v = values[min(len([c for c in FakeEngine.calls if c == workload.id]) - 1, len(values) - 1)]
        perf = PerfMetrics(primary="decode_tok_s", decode_tok_s=v, output_tok_s=v * 8, prompt_tokens=128, output_tokens=64, requests=_asked(workload), failed=0)
        return BenchResult(perf=perf, summary={}, requests=[{"ok": True, "prompt_tokens": 128, "output_token_ids": [1, 2, 3]}], argv=[], output_token_ids=[[1, 2, 3]])


@pytest.fixture
def job(tmp_path):
    m = Matrix.load(MATRIX)
    cells = [c for c in m.runnable(Tier.SMOKE, m.expand(platforms=["l40s-x1"], artifacts=["qwen3.5-0.8b-bf16"])) if c.platform.id == "l40s-x1" and c.artifact.id == "qwen3.5-0.8b-bf16" and c.program.id == "text-completion-bench" and c.mode.tp == 1]
    j = make_jobs(m, Tier.SMOKE, pie_commit="deadbeef", store=Store(tmp_path / "store"), platforms=["l40s-x1"], cells=cells)[0]
    assert {c.workload.id for c in j.cells} >= {"control-aa", "ss-128-64", "c8"}
    return j


@pytest.fixture
def mac_job(tmp_path):
    m = Matrix.load(MATRIX)
    cells = [c for c in m.runnable(Tier.TARGETED, m.expand(platforms=["m4-pro-48g"], artifacts=["gemma-4-26b-a4b-mlx4"])) if c.platform.id == "m4-pro-48g" and c.artifact.id == "gemma-4-26b-a4b-mlx4" and str(c.engine) == "pie"]
    c8 = WorkloadSpec(id="c8", kind="concurrency", params={"concurrency": 8, "num_requests": 32, "prefill": 128, "decode": 128}, est_minutes=1)
    cells.append(cells[0].model_copy(update={"workload": c8}))
    j = make_jobs(m, Tier.TARGETED, pie_commit="deadbeef", store=Store(tmp_path / "store"), platforms=["m4-pro-48g"], cells=cells)[0]
    assert {c.workload.id for c in j.cells} >= {"control-aa", "ob-story-200", "c8"}
    return j


@pytest.fixture
def patched(monkeypatch, tmp_path):
    FakeEngine.calls = []
    FakeEngine.common = {}
    FakeEngine.behaviour = {}
    monkeypatch.setattr(runner_mod, "get_engine", lambda name, backend=None: FakeEngine)
    monkeypatch.setattr(runner_mod, "load_recipe", lambda *a, **k: {})
    for repo in ("models--Qwen--Qwen3.5-0.8B", "models--mlx-community--gemma-4-26b-a4b-it-4bit"):
        snap = tmp_path / "hf" / repo / "snapshots" / "abc"
        snap.mkdir(parents=True)
        (snap / "config.json").write_text('{"num_hidden_layers": 28}')
        (snap / "model.safetensors").write_bytes(b"x")

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
    monkeypatch.setattr(runner_mod.NodeRunner, "_accuracy", lambda self, cell, engine, snap: runner_mod.AccuracyMetrics())
    monkeypatch.setattr("pie_bench.runner.disk_space.reclaim", lambda *a, **k: 0.0)
    monkeypatch.setattr("pie_bench.checkpoints.pie_import.ensure_artifact", lambda art, snap, *a, **k: snap)
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
    assert FakeEngine.calls[0] == "control-aa"
    assert all(r.provenance.pie_commit == "deadbeef" for r in recs)
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
    FakeEngine.behaviour["control-aa"] = [100.0, 130.0, 130.0, 100.0, 130.0, 130.0]
    recs, _ = _run(job, patched, tmp_path)
    ctrl = next(r for r in recs if r.cell.workload.id == "control-aa")
    assert ctrl.status == CellStatus.NOISY
    others = [r for r in recs if r.cell.workload.id != "control-aa"]
    assert others and all(r.status == CellStatus.NOISY and r.error_class == ErrorClass.HARNESS_INVALID for r in others)
    assert FakeEngine.calls.count("control-aa") == 6


def test_a_mac_run_keeps_numbers_after_a_failed_control(job, patched, tmp_path):
    FakeEngine.behaviour["control-aa"] = [100.0, 130.0, 130.0, 100.0, 130.0, 130.0]
    recs, _ = _run(job.model_copy(update={"control_marks_noisy": True}), patched, tmp_path)
    others = [r for r in recs if r.cell.workload.id != "control-aa"]
    assert others and all(r.status == CellStatus.NOISY and r.error_class is None and r.perf and r.perf.rounds for r in others)
    assert all("control A/A failed" in (r.invalid_reason or "") for r in others)


def test_a_workload_round_timeout_lifts_the_job_cap(job, tmp_path):
    from types import SimpleNamespace as NS

    r = runner_mod.NodeRunner(job.model_copy(update={"per_cell_timeout_s": 1800, "kill_s": 99999}), pie_root=tmp_path, out_dir=tmp_path / "o", build=False)
    slow = NS(workload=NS(est_minutes=1.5, params={"round_timeout_s": 3000}))
    plain = NS(workload=NS(est_minutes=1.5, params={}))
    assert r.cell_timeout_s(slow) == 3000 and r.cell_timeout_s(plain) == 900


def test_noisy_control_gets_one_more_look(job, patched, tmp_path):
    FakeEngine.behaviour["control-aa"] = [100.0, 130.0]
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
    assert recs == []
    lines = [Record.model_validate_json(ln) for ln in (tmp_path / "out" / "records.jsonl").read_text().splitlines()]
    assert lines and all(r.status == CellStatus.FAIL and r.error_class == ErrorClass.LOAD_FAIL for r in lines)


def test_soft_budget_records_unreached_cells_as_not_run(job, patched, tmp_path):
    job = job.model_copy(update={"budget_s": 0, "kill_s": 600})
    recs, lines = _run(job, patched, tmp_path)
    assert recs == []
    assert lines and all(r.status == CellStatus.NOT_RUN and "budget" in (r.invalid_reason or "") for r in lines)
    assert {r.cell_id for r in lines} == {c.cell_id for c in job.cells}


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

    from pie_bench.runner.grouping import cell_priority

    def cell(kind, est):
        return NS(workload=NS(kind=NS(value=kind), est_minutes=est))

    cells = [cell("closed_loop", 3.0), cell("single_stream", 0.5), cell("control_aa", 0.5), cell("long_context", 1.5)]
    got = sorted(cells, key=cell_priority)
    assert [c.workload.kind.value for c in got] == ["control_aa", "single_stream", "long_context", "closed_loop"]


def test_heavy_model_on_a_small_card_boots_short_and_long_shapes_apart():

    from pie_bench.engines.shapes import context_tokens_for
    from pie_bench.plan.jobs import make_jobs
    from pie_bench.plan.matrix import Matrix
    from pie_bench.runner.grouping import SHORT_CONTEXT_TOKENS, split_heavy_processes
    from pie_bench.schema import Tier

    m = Matrix.load(MATRIX)
    lc32k = WorkloadSpec(id="lc-32k-128", kind="long_context", params={"prefill": 32768, "decode": 128, "concurrency": 1})
    for aid, split in (("qwen3.6-27b-mlx4", True), ("qwen3.5-0.8b-bf16", False)):
        cells = [c for c in m.expand(artifacts=[aid]) if c.program.id == "text-completion-bench"]
        jobs = make_jobs(m, Tier.NIGHTLY, pie_commit="c" * 40, platforms=["rtx5090-x1"], engines=["pie"], cells=cells)
        groups = {}
        for j in jobs:
            groups.update(j.cells_by_process())
        groups = {k: cs + [cs[0].model_copy(update={"workload": lc32k})] for k, cs in groups.items()}
        out = split_heavy_processes(groups)
        keys = sorted(k[2] for k in out)
        if split:
            assert any(k.endswith("-short") for k in keys) and any(k.endswith("-long") for k in keys), keys
            for k, cs in out.items():
                longs = [context_tokens_for(c.workload) > SHORT_CONTEXT_TOKENS for c in cs]
                assert all(longs) if k[2].endswith("-long") else not any(longs)
        else:
            assert keys == sorted(k[2] for k in groups) and not any(k.endswith(("-short", "-long")) for k in keys)


def test_pie_cuda_cells_boot_at_their_own_shape_as_vllm_does():
    from pie_bench.engines.shapes import max_model_len_for, workload_concurrency
    from pie_bench.plan.jobs import make_jobs
    from pie_bench.runner.grouping import split_startups

    m = Matrix.load(MATRIX)
    cells = [c for c in m.expand(artifacts=["minimax-m3.1-flash-mini60-e16"]) if c.program.id == "text-completion-bench"]
    jobs = make_jobs(m, Tier.WEEKLY, pie_commit="c" * 40, platforms=["h100-sxm-x1"], engines=["pie", "vllm"], cells=cells)
    groups = {}
    for j in jobs:
        groups.update(j.cells_by_process())
    out = split_startups(groups)
    assert sum(len(cs) for cs in out.values()) == sum(len(cs) for cs in groups.values())
    for (engine, _, mode), cs in out.items():
        if engine == "pie":
            assert len({(workload_concurrency(c.workload), max_model_len_for(c.workload)) for c in cs}) == 1, mode
        else:
            assert "@" not in mode


def test_mac_rivals_serve_one_request_rows_on_one_slot():
    from pie_bench.engines.llamacpp import LlamacppEngine
    from pie_bench.engines.shapes import workload_concurrency
    from pie_bench.plan.jobs import process_key
    from pie_bench.runner.grouping import split_startups
    from pie_bench.runner.job import serve_envelope

    m = Matrix.load(MATRIX)
    for aid, split in (("gemma-4-e2b-llamacpp", True), ("gemma-4-e2b-mlxlm", False)):
        cells = [c for c in m.runnable(Tier.TARGETED, m.expand(platforms=["m5-max-64g"], artifacts=[aid])) if c.artifact.id == aid and c.platform.id == "m5-max-64g"]
        assert {workload_concurrency(c.workload) for c in cells} >= {1, 32}, aid
        groups = {process_key(cells[0]): cells}
        out = split_startups(groups)
        assert sum(len(cs) for cs in out.values()) == len(cells)
        if not split:
            assert out == groups
            continue
        (one_key, one), (wide_key, wide) = out.items()
        assert one_key[2].endswith("@c1") and wide_key == process_key(cells[0])
        assert {workload_concurrency(c.workload) for c in one} == {1} and 1 not in {workload_concurrency(c.workload) for c in wide}
        eng = LlamacppEngine(pie_root=ROOT, artifact=one[0].artifact, platform=one[0].platform, mode=one[0].mode, recipe={"gguf": "x"})
        eng.gguf_path = lambda: Path("/m.gguf")
        cmd = eng.server_cmd(1, 1, 2048)
        shape = serve_envelope([c.workload for c in one])
        assert workload_concurrency(shape) == 1 and cmd[cmd.index("--parallel") + 1] == "1" and cmd[cmd.index("--ctx-size") + 1] == "2048"


def test_recipe_follows_the_cell_and_keeps_what_the_boot_added(job):
    ss = next(c for c in job.cells if c.workload.id == "ss-128-64")
    c8 = next(c for c in job.cells if c.workload.id == "c8")
    base = runner_mod.load_recipe("pie", "competitive", ss.platform, ss.workload, family=ss.artifact.family)
    base["snapshot_dir"], base["pin"] = "/snap", "0.30.0"
    fresh = runner_mod.recipe_for_cell(base, "competitive", c8)
    assert (base["max_forward_requests"], fresh["max_forward_requests"]) == (1, 8)
    assert fresh["snapshot_dir"] == "/snap" and fresh["pin"] == "0.30.0"


def test_a_slow_first_round_is_confirmed_away_not_withheld(job, patched, tmp_path):
    job = job.model_copy(update={"repetition": job.repetition.model_copy(update={"min_rounds": 3, "confirm_rounds": 2, "max_rounds": 5})})
    FakeEngine.behaviour["ss-128-64"] = [90.0, 100.0, 101.0, 100.0, 100.0]
    FakeEngine.behaviour["c8"] = [100.0, 80.0, 120.0, 85.0, 118.0]
    recs, _ = _run(job, patched, tmp_path)
    ss = next(r for r in recs if r.cell.workload.id == "ss-128-64")
    assert ss.status == CellStatus.PASS and len(ss.perf.rounds) == 5 and ss.perf.decode_tok_s == 100.0
    c8 = next(r for r in recs if r.cell.workload.id == "c8")
    assert c8.status == CellStatus.NOISY and len(c8.perf.rounds) == 4


def test_one_slow_boot_among_five_rounds_is_dropped(job, patched, tmp_path):
    job = job.model_copy(update={"repetition": job.repetition.model_copy(update={"min_rounds": 3, "confirm_rounds": 2, "max_rounds": 5})})
    FakeEngine.behaviour["ss-128-64"] = [100.0, 101.0, 80.0, 100.0, 99.0]
    recs, _ = _run(job, patched, tmp_path)
    ss = next(r for r in recs if r.cell.workload.id == "ss-128-64")
    assert ss.status == CellStatus.PASS and len(ss.perf.rounds) == 5 and ss.perf.decode_tok_s == 100.0


def test_heavy_model_on_a_small_mac_boots_short_and_long_shapes_apart():
    from pie_bench.engines.shapes import context_tokens_for
    from pie_bench.plan.jobs import process_key
    from pie_bench.runner.grouping import SHORT_CONTEXT_TOKENS, split_heavy_processes

    m = Matrix.load(MATRIX)
    lc16k = WorkloadSpec(id="lc-16k-128", kind="long_context", params={"prefill": 16384, "decode": 128, "concurrency": 1})
    for plat, split in (("m1-max-32g", True), ("m5-max-128g", False)):
        cells = [c for c in m.runnable(Tier.TARGETED, m.expand(platforms=[plat], artifacts=["gemma-4-26b-a4b-mlx4"])) if c.artifact.id == "gemma-4-26b-a4b-mlx4" and c.platform.id == plat and str(c.engine) == "pie"]
        cells.append(cells[0].model_copy(update={"workload": lc16k}))
        groups = {process_key(cells[0]): cells}
        out = split_heavy_processes(groups)
        keys = sorted(k[2] for k in out)
        if split:
            assert keys == ["tp1-long", "tp1-short"], keys
            for k, cs in out.items():
                longs = [context_tokens_for(c.workload) > SHORT_CONTEXT_TOKENS for c in cs]
                assert all(longs) if k[2].endswith("-long") else not any(longs)
            assert sum(len(cs) for cs in out.values()) == len(cells)
        else:
            assert out == groups
        shipped = {process_key(cells[0]): cells[:-1]}
        assert (split_heavy_processes(shipped) == shipped) is not split


def test_recipe_keeps_the_knobs_the_server_booted_with(mac_job, monkeypatch):
    monkeypatch.setattr(runner_mod, "load_recipe", lambda engine, name, plat, wl, family=None, artifact=None: {"num_parallel": "$serve_concurrency", "_recipe": name})
    c8 = next(c for c in mac_job.cells if c.workload.id == "c8")
    assert runner_mod.recipe_for_cell({"num_parallel": 8}, "competitive", c8)["num_parallel"] == 8
    assert runner_mod.recipe_for_cell({}, "competitive", c8)["num_parallel"] == "$serve_concurrency"


def test_warmup_follows_the_workload(mac_job, patched, tmp_path):
    _run(mac_job, patched, tmp_path)

    def warm(wl):
        args = FakeEngine.common[wl]
        return args[args.index("--warmup") + 1]

    assert warm("ob-512-200") == "1" and warm("ob-advanced-500") == "2"


def test_mac_happy_path_runs_every_targeted_shape(mac_job, patched, tmp_path):
    recs, _ = _run(mac_job, patched, tmp_path)
    assert {r.status for r in recs} == {CellStatus.PASS}
    assert FakeEngine.calls[0] == "control-aa"
    assert {r.cell.workload.id for r in recs} == {c.workload.id for c in mac_job.cells}


def test_checkpoints_download_in_the_background(mac_job, patched, tmp_path, monkeypatch):
    import threading

    from pie_bench.checkpoints import snapshots

    real = snapshots.ensure_snapshot
    threads = []

    def spy(art, hf, **kw):
        threads.append(threading.current_thread().name)
        return real(art, hf, download=False)

    monkeypatch.setattr(snapshots, "ensure_snapshot", spy)
    from pie_bench.runner import disk_space as reclaim

    monkeypatch.setattr(reclaim, "free_gib", lambda *a, **k: 10_000.0)
    r = runner_mod.NodeRunner(mac_job, pie_root=tmp_path / "pie", out_dir=tmp_path / "out", hf_cache=patched, build=False, download=True)
    recs = r.run()
    assert recs and any(t.startswith("prefetch") for t in threads)


def test_an_imported_artifact_needs_no_source_weights(mac_job, patched, tmp_path, monkeypatch):
    from pie_bench.checkpoints import pie_import as importer
    from pie_bench.checkpoints import snapshots

    monkeypatch.setenv("PIE_BENCH_CACHE", str(tmp_path / "cache"))
    art = mac_job.cells[0].artifact
    for plain in (False, True):
        zt_dir = importer.artifact_dir(art, mac_job.pie_commit, plain=plain)
        zt_dir.mkdir(parents=True)
        (zt_dir / "m.zt").write_bytes(b"x")
    org, _, name = art.base_model.partition("/")
    snap = patched / f"models--{org}--{name}" / "snapshots" / "abc"
    for f in snap.glob("*.safetensors"):
        f.unlink()
    monkeypatch.setattr(snapshots, "ensure_snapshot", lambda *a, **k: (_ for _ in ()).throw(AssertionError("fetched the source")))
    r = runner_mod.NodeRunner(mac_job, pie_root=tmp_path / "pie", out_dir=tmp_path / "out", hf_cache=patched, build=False, download=True)
    assert r.snapshot_dir(mac_job.cells[0]) == snap


def test_t0_is_judged_once_the_engine_is_down(job, patched, tmp_path, monkeypatch):
    from pie_bench.accuracy import gate
    from pie_bench.schema import AccuracyMetrics, AccuracyStatus

    events: list[str] = []
    monkeypatch.setattr(runner_mod.NodeRunner, "_accuracy", REAL_ACCURACY)
    monkeypatch.setattr(gate, "skip_reason", lambda cell: None)
    monkeypatch.setattr("pie_bench.checkpoints.snapshots.with_tokenizer", lambda art, snap, hf, log=None: snap)
    monkeypatch.setattr(gate, "t0_engine_outputs", lambda engine, snap, **kw: gate.T0Outputs([[1]], [[2]]))
    monkeypatch.setattr(FakeEngine, "stop", lambda self: events.append("stop"), raising=False)

    def judge(outputs, cell, snap, platform_os, **kw):
        events.append("judge")
        return AccuracyMetrics(status=AccuracyStatus.FAIL)

    monkeypatch.setattr(gate, "t0_judge", judge)
    _, lines = _run(job, patched, tmp_path)
    assert events.index("judge") > events.index("stop")
    ss = [r for r in lines if r.cell.workload.id == "ss-128-64"][-1]
    assert ss.accuracy.status == AccuracyStatus.FAIL and ss.status == CellStatus.FAIL
    assert ss.error_class == ErrorClass.GATE_FAIL
