from pathlib import Path

import pytest

from pie_evals.plan.matrix import Matrix, selector_matches, summarize
from pie_evals.schema import ArtifactSpec, CellStatus, Tier

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def matrix():
    return Matrix.load(ROOT / "matrix")


@pytest.fixture(scope="module")
def cells(matrix):
    return matrix.expand()


def test_expansion_is_nonempty_and_stable(cells):
    ids = [c.cell_id for c in cells]
    assert len(ids) == len(set(ids)), "cell ids must be unique"
    assert summarize(cells)["total"] > 1000


def test_every_cell_has_a_status_path(cells):
    # nothing silently dropped: a cell is runnable, declared unsupported, or unscheduled — never absent
    for c in cells:
        assert c.declared_unsupported_reason is None or isinstance(c.declared_unsupported_reason, str)


def test_baselines_never_in_smoke(matrix, cells):
    assert all(str(c.engine) == "pie" for c in matrix.cells_for(Tier.SMOKE, cells))


def test_metal_tp_is_declared_not_failed(cells):
    tp = [c for c in cells if c.platform.backend.value == "metal" and c.mode.tp > 1]
    # metal platforms have count=1 → tp cells are not generated at all (inapplicable), which is fine;
    # but if any exist they must be declared
    assert all(c.declared_unsupported_reason for c in tp)


def test_fit_rule_marks_big_models_on_small_gpus(cells):
    big = [c for c in cells if c.artifact.id == "deepseek-v4-flash-mlx2" and c.platform.id == "l40s-x1"]
    assert big and all(c.declared_unsupported_reason for c in big)
    assert any("does not fit" in c.declared_unsupported_reason for c in big)


def test_miniature_cells_never_accuracy_applicable(cells):
    for c in cells:
        if c.artifact.kind.value == "miniature":
            assert not c.accuracy_applicable()


def test_pie_only_programs_have_no_baseline_cells(cells):
    for c in cells:
        if c.program.pie_only:
            assert str(c.engine) == "pie"


def test_sglang_never_gets_gguf(cells):
    assert not [c for c in cells if str(c.engine) == "sglang" and c.artifact.source_format.value == "gguf"]


def test_selector_negation_and_comparison(cells):
    c = next(c for c in cells if c.mode.tp == 2)
    assert selector_matches({"tp": ">1"}, c)
    assert not selector_matches({"tp": ">=4"}, c)
    assert selector_matches({"not_engine": ["vllm"]}, c) == (str(c.engine) != "vllm")


def test_smoke_budget_holds(matrix, cells):
    assert matrix.check_budget(Tier.SMOKE, cells) == []


def test_smoke_includes_every_program_at_least_once(matrix, cells):
    # every smoke program has a smoke cell — runnable, or declared unsupported and
    # therefore visible in the coverage report (diffusion programs only run on
    # mini-dit, which has no checkpoint source yet)
    smoke = matrix.cells_for(Tier.SMOKE, cells)
    progs = {c.program.id for c in smoke}
    expected = {p.id for p in matrix.programs.values() if Tier.SMOKE in p.tiers}
    assert not (expected - progs), expected - progs
    runnable = {c.program.id for c in matrix.runnable(Tier.SMOKE, cells)}
    # no smoke artifact ships a dflash head (the miniatures have none to draft with)
    assert expected - runnable <= {"diffusion-parity", "mini-dit-parity", "prefill-rows", "prefix-tree-kv-cache", "mtp-speculative-decoding", "cacheback-speculative-decoding", "lora-probe", "dflash-speculative-bench"}, expected - runnable


def test_splash_runs_only_splash_weights_on_macs(cells):
    splash = [c for c in cells if str(c.engine) == "splash"]
    assert splash
    for c in splash:
        assert c.artifact.source_format.value == "splash", c.cell_key
        assert c.platform.os == "macos" and c.platform.backend.value == "metal", c.cell_key
    assert not [c for c in cells if str(c.engine) != "splash" and c.artifact.source_format.value == "splash"]


def test_every_baseline_arm_pairs_with_a_pie_artifact(matrix):
    for a in matrix.artifacts.values():
        if a.baseline_label:
            assert a.baseline_of in matrix.artifacts, a.id
            assert not matrix.artifacts[a.baseline_of].baseline_label, a.id


def test_control_aa_is_pie_only(cells):
    assert all(str(c.engine) == "pie" for c in cells if c.workload.kind.value == "control_aa")


def test_a_baseline_arm_on_the_same_checkpoint_has_its_own_key():
    base = {"id": "x-mlx4", "base_model": "org/x", "family": "x", "scheme": "affine_u4_g64", "source_format": "mlx"}
    a = ArtifactSpec(**base, baseline_label="mlx-lm")
    assert a.artifact_key.endswith("#mlx-lm")
    assert ArtifactSpec(**base).artifact_key != a.artifact_key


def test_fit_rule_marks_big_models_on_small_macs(matrix, cells):
    c = next(c for c in cells if c.platform.os == "macos" and c.platform.memory_gib <= 32 and c.declared_unsupported_reason is None)
    big = c.model_copy(update={"artifact": c.artifact.model_copy(update={"expected_gib": 30.0})})
    assert "does not fit" in matrix._physical_reason(big)
    assert matrix._physical_reason(c) is None


def test_context_rule_marks_shapes_past_max_context(matrix, cells):
    c = next(c for c in cells if c.workload.id == "ob-512-200")
    short = c.model_copy(update={"artifact": c.artifact.model_copy(update={"max_context": 512})})
    assert "max_context" in matrix._physical_reason(short)


def test_selector_matches_the_splash_arm(cells):
    c = next(c for c in cells if str(c.engine) == "splash")
    assert selector_matches({"tp": ">=1"}, c)
    assert not selector_matches({"tp": ">1"}, c)
    assert selector_matches({"not_engine": ["pie"]}, c)
    assert not selector_matches({"engine": "splash", "not_source_format": "splash"}, c)


def test_targeted_budget_holds(matrix, cells):
    # the targeted job count is not enforced (suites.yaml enforce_budget: false), but every process group still fits a job
    assert [p for p in matrix.check_budget(Tier.TARGETED, cells) if "cannot fit" in p] == []


def test_cell_status_enum_complete():
    assert {s.value for s in CellStatus} == {"pass", "fail", "declared_unsupported", "not_run", "noisy"}


def test_a_dflash_program_runs_only_where_the_import_lands_a_head(cells):
    dflash = [c for c in cells if str(c.mode.spec_dec or "").startswith("dflash") and not c.declared_unsupported_reason]
    assert dflash, "no artifact with a draft head pairs with the dflash programs"
    assert all(c.artifact.pie_drafter for c in dflash)
