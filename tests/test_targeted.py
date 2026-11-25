from pathlib import Path

import pytest

from pie_bench.installers import pie as pb
from pie_bench.paths import MATRIX
from pie_bench.plan.matrix import Matrix
from pie_bench.schema import CellStatus, PerfMetrics, Provenance, Record, Tier

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def matrix():
    return Matrix.load(MATRIX)


@pytest.fixture(scope="module")
def mac_cells(matrix):
    return matrix.expand(platforms=[p for p, spec in matrix.platforms.items() if spec.os == "macos"])


def _cell(matrix, platform, workload, artifact="gemma-4-26b-a4b-mlx4"):
    return next(c for c in matrix.runnable(Tier.TARGETED, matrix.expand(platforms=[platform], artifacts=[artifact]))
                if c.platform.id == platform and c.workload.id == workload and c.artifact.id == artifact)


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


def test_targeted_is_small_and_baselines_run_on_their_copies(matrix, mac_cells):
    cells = matrix.runnable(Tier.TARGETED, mac_cells)
    assert cells and all(c.mode.tp == 1 for c in cells)
    assert {c.engine.value for c in cells} == {"pie", "mlxlm", "llamacpp", "splash", "vllm-metal"}
    assert all(c.engine.value == "pie" or c.workload.id != "control-aa" for c in cells)
    assert {c.engine.value for c in cells if c.artifact.baseline_of} >= {"mlxlm", "llamacpp", "splash"}
    assert all(c.artifact.baseline_of for c in cells if c.engine.value == "splash")
    assert not any(c.artifact.baseline_of for c in cells if c.engine.value == "pie")
    site = [c for c in cells if c.workload.id.startswith(("ob-", "ctx-")) or c.workload.id == "c4"]
    assert all((c.artifact.baseline_of is None) == (c.engine.value == "pie") for c in site)
    assert {c.artifact.baseline_label for c in site if c.engine.value != "pie"} >= {"llama.cpp", "mlx-lm", "Splash"}
    assert {c.workload.id for c in cells} == {"control-aa", "ss-128-64", "ss-512-256", "lc-1k-128", "lc-2k-128", "c8", "c32",
                                              "ob-story-200", "ob-512-200", "raw-512-256", "spec-512-256", "ob-short-100", "ob-advanced-500", "ctx-4k-256", "ctx-8k-256", "c4", "pf256-512", "pf32-512", "pf8-512",
                                              "cold-ss-128-64", "cold-ss-512-200", "cold-ctx-4k-256"}
    assert not [p for p in matrix.check_budget(Tier.TARGETED, mac_cells) if "cannot fit" in p]


def test_metal_build_is_cached_without_a_wheel(tmp_path):
    d = pb.cache_dir("a" * 40, ["metal"], tmp_path)
    (d / "wasm").mkdir(parents=True)
    (d / "pie").write_text("")
    (d / "wasm" / "x.wasm").write_text("")
    assert pb.is_cached("a" * 40, ["metal"], tmp_path)
    assert not pb.is_cached("a" * 40, ["cuda"], tmp_path)
