from pathlib import Path

import pytest

from pie_evals.node import build as pb
from pie_evals.orchestrate.matrix import Matrix
from pie_evals.schema import CellStatus, PerfMetrics, Provenance, Record, Tier

ROOT = Path(__file__).resolve().parents[1]



@pytest.fixture(scope="module")
def matrix():
    return Matrix.load(ROOT / "matrix")


def _cell(matrix, platform, workload):
    return next(c for c in matrix.runnable(Tier.TARGETED)
                if c.platform.id == platform and c.workload.id == workload)


def _rec(cell, value, when, *, commit, status=CellStatus.PASS, run="r"):
    prov = Provenance(harness_commit="h", pie_commit=commit, engine_version=commit, checkpoint_revision="rev", hardware_fingerprint={"gpu_cores": "40"})
    return Record(run_id=run, job_id="j", tier=Tier.TARGETED, cell_id=cell.cell_id, cell_key=cell.cell_key, cell=cell, status=status,
                  perf=PerfMetrics(primary="decode_tok_s", decode_tok_s=value, prefill_tok_s=value * 30, rounds=[value], cov=0.002),
                  provenance=prov, started_at=when, duration_s=30.0)


def _node_out(tmp_path, records):
    d = tmp_path / "out"
    d.mkdir()
    (d / "records.jsonl").write_text("\n".join(r.model_dump_json() for r in records) + "\n")
    return d


def test_targeted_is_small_and_baselines_run_on_their_copies(matrix):
    cells = matrix.runnable(Tier.TARGETED)
    assert cells and all(c.mode.tp == 1 for c in cells)
    assert {c.engine.value for c in cells} == {"pie", "mlxlm", "llamacpp"}
    assert all(c.engine.value == "pie" or c.workload.id != "control-aa" for c in cells)
    assert {c.engine.value for c in cells if c.artifact.baseline_of} >= {"mlxlm", "llamacpp"}
    assert {c.workload.id for c in cells} == {"control-aa", "ss-128-64", "lc-1k-128", "lc-2k-128", "c8", "c32"}
    assert not matrix.check_budget(Tier.TARGETED)


def test_metal_build_is_cached_without_a_wheel(tmp_path):
    d = pb.cache_dir("a" * 40, ["metal"], tmp_path)
    (d / "wasm").mkdir(parents=True)
    (d / "pie").write_text("")
    (d / "wasm" / "x.wasm").write_text("")
    assert pb.is_cached("a" * 40, ["metal"], tmp_path)
    assert not pb.is_cached("a" * 40, ["cuda"], tmp_path)
