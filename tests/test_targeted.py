from pathlib import Path

import pytest

from pie_evals.node import build as pb
from pie_evals.plan.matrix import Matrix
from pie_evals.results import flops
from pie_evals.schema import CellStatus, PerfMetrics, Provenance, Record, Tier

ROOT = Path(__file__).resolve().parents[1]

QWEN35_08B = {
    "hidden_size": 1024, "num_hidden_layers": 24, "num_attention_heads": 8, "num_key_value_heads": 2, "head_dim": 256,
    "intermediate_size": 3584, "vocab_size": 248320, "attn_output_gate": True,
    "layer_types": (["linear_attention"] * 3 + ["full_attention"]) * 6,
    "linear_num_key_heads": 16, "linear_num_value_heads": 16, "linear_key_head_dim": 128, "linear_value_head_dim": 128,
    "linear_conv_kernel_dim": 4,
}


@pytest.fixture(scope="module")
def matrix():
    return Matrix.load(ROOT / "matrix")


@pytest.fixture(scope="module")
def mac_cells(matrix):
    """The targeted tier runs on the Macs only: their cells, expanded once instead of the whole matrix."""
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
    assert not any(c.artifact.baseline_of for c in cells if c.engine.value == "pie")  # pie never runs another engine's copy
    # on the site's benchmarks pie runs its own checkpoints only, and every other engine only its arms
    site = [c for c in cells if c.workload.id.startswith(("ob-", "ctx-")) or c.workload.id == "c4"]
    assert all((c.artifact.baseline_of is None) == (c.engine.value == "pie") for c in site)
    assert {c.artifact.baseline_label for c in site if c.engine.value != "pie"} >= {"llama.cpp", "mlx-lm", "Splash"}
    assert {c.workload.id for c in cells} == {"control-aa", "ss-128-64", "ss-512-256", "lc-1k-128", "lc-2k-128", "c8", "c32",
                                              "ob-story-200", "ob-512-200", "raw-512-256", "spec-512-256", "ob-short-100", "ob-advanced-500", "ctx-4k-256", "ctx-8k-256", "c4", "pf256-512", "pf32-512", "pf8-512",
                                              "cold-ss-128-64", "cold-ss-512-200", "cold-ctx-4k-256"}
    # the targeted job count is not enforced (suites.yaml enforce_budget: false), but every process group still fits a job
    assert not [p for p in matrix.check_budget(Tier.TARGETED, mac_cells) if "cannot fit" in p]


def test_metal_build_is_cached_without_a_wheel(tmp_path):
    d = pb.cache_dir("a" * 40, ["metal"], tmp_path)
    (d / "wasm").mkdir(parents=True)
    (d / "pie").write_text("")
    (d / "wasm" / "x.wasm").write_text("")
    assert pb.is_cached("a" * 40, ["metal"], tmp_path)
    assert not pb.is_cached("a" * 40, ["cuda"], tmp_path)


def test_flops_scale_with_the_rate():
    one = flops.tflops({"decode_tok_s": 100.0, "prefill_tok_s": 1000.0}, {"prefill": 128, "decode": 64}, QWEN35_08B)
    two = flops.tflops({"decode_tok_s": 200.0, "prefill_tok_s": 2000.0}, {"prefill": 128, "decode": 64}, QWEN35_08B)
    assert two["decode_tflops"] == pytest.approx(2 * one["decode_tflops"])
    assert two["prefill_tflops"] == pytest.approx(2 * one["prefill_tflops"])
    per_token = flops.decode_flops_per_token(QWEN35_08B, 160)
    assert 1.4e9 < per_token < 1.8e9
    batched = flops.tflops({"output_tok_s": 1000.0, "prefill_tok_s": 5.0}, {"prefill": 128, "decode": 128, "concurrency": 8}, QWEN35_08B)
    assert batched["prefill_tflops"] is None and batched["decode_tflops"] > 0
    assert flops.tflops({"decode_tok_s": 1.0}, {"prefill": 1}, None) == {"prefill_tflops": None, "decode_tflops": None}
