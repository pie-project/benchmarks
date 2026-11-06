"""llama.cpp and mlx-lm draft with a small same-family model on exactly the rows pie speculates."""

from __future__ import annotations

from pathlib import Path

import pytest

from pie_evals.node.engines import EngineLaunchError
from pie_evals.node.engines.llamacpp import LlamacppEngine
from pie_evals.node.engines.mlxlm import MlxlmEngine
from pie_evals.node.engines.recipes import load_recipe
from pie_evals.node.engines.shape import serve_envelope
from pie_evals.node.engines.splash import SplashEngine
from pie_evals.node.runner import split_draft_processes
from pie_evals.node.snapshots import draft_artifact, ensure_snapshot
from pie_evals.plan.jobs import process_key
from pie_evals.plan.matrix import Matrix
from pie_evals.schema import ArtifactSpec, Backend, Mode, PlatformSpec, Tier, WorkloadSpec

ROOT = Path(__file__).resolve().parents[1]
SS = WorkloadSpec(id="ss-512-256", kind="single_stream", params={"prefill": 512, "decode": 256})
C32 = WorkloadSpec(id="c32", kind="concurrency", params={"concurrency": 32, "num_requests": 128, "prefill": 128, "decode": 128})
MAC = PlatformSpec(id="m5-max-48g", os="macos", backend=Backend.METAL, accelerator="Apple M5 Max", arch="apple10", memory_gib=48.0)


def _snap(hub: Path, repo: str, files: dict[str, bytes]) -> Path:
    d = hub / f"models--{repo.replace('/', '--')}"
    (d / "snapshots" / "r1").mkdir(parents=True)
    (d / "refs").mkdir()
    (d / "refs" / "main").write_text("r1")
    for name, data in files.items():
        (d / "snapshots" / "r1" / name).write_bytes(data)
    return d / "snapshots" / "r1"


@pytest.fixture
def hub(tmp_path, monkeypatch):
    hub = tmp_path / "hub"
    monkeypatch.setenv("HF_HUB_CACHE", str(hub))
    monkeypatch.setenv("LLAMA_SERVER_BIN", "/opt/llama/llama-server")
    monkeypatch.setenv("MLX_PY", "/opt/mlx/bin/python")
    _snap(hub, "unsloth/Qwen3.8-27B-GGUF", {"Qwen3.8-27B-UD-Q4_K_M.gguf": b"GGUF"})
    _snap(hub, "unsloth/Qwen3.5-0.8B-GGUF", {"Qwen3.5-0.8B-Q4_K_M.gguf": b"GGUF"})
    _snap(hub, "mlx-community/gemma-4-26b-a4b-it-4bit", {"config.json": b"{}", "model.safetensors": b""})
    _snap(hub, "mlx-community/gemma-4-e2b-it-4bit", {"config.json": b"{}", "model.safetensors": b""})
    return hub


def _engine(cls, art: ArtifactSpec, workload: WorkloadSpec = SS, **recipe_over):
    recipe = load_recipe(str(cls.name), "competitive", MAC, workload, family=art.family)
    recipe["speculation"] = "auto"  # the recipes ship plain; these tests exercise drafting
    recipe.update(recipe_over)
    return cls(pie_root=ROOT, artifact=art, platform=MAC, mode=Mode(), recipe=recipe, python="/usr/bin/python3")


def _art(aid: str) -> ArtifactSpec:
    return Matrix.load(ROOT / "matrix").artifacts[aid]


def test_competitors_of_every_speculating_pie_row_name_a_draft_or_say_why_not():
    m = Matrix.load(ROOT / "matrix")
    for arm in m.artifacts.values():
        pie = m.artifacts.get(arm.baseline_of or "")
        if pie is None or not (pie.pie_sku and "dflash" in pie.pie_sku) or arm.source_format == "splash":
            continue  # Splash drafts on its own
        if arm.id in ("qwen3.8-27b-mlxlm", "qwen3.6-35b-a3b-mlxlm", "qwen3.6-27b-mlxlm"):
            assert arm.draft_model is None  # mlx-lm cannot speculate on a hybrid's untrimmable cache
            continue
        assert arm.draft_model, arm.id
        assert (arm.draft_gguf_file is not None) == (arm.source_format == "gguf"), arm.id


def test_llamacpp_drafts_on_a_single_stream_row(hub):
    eng = _engine(LlamacppEngine, _art("qwen3.8-27b-llamacpp"))
    assert eng.speculates(SS) and not eng.speculates(C32)
    args = eng.draft_args()
    assert args[:2] == ["--spec-type", "draft-simple"]
    assert args[args.index("--model-draft") + 1] == str((hub / "models--unsloth--Qwen3.5-0.8B-GGUF/snapshots/r1/Qwen3.5-0.8B-Q4_K_M.gguf").resolve())
    assert args[args.index("--n-gpu-layers-draft") + 1] == "all"
    assert "--spec-draft-n-max" not in args  # llama-server's default draft length
    assert "--spec-draft-n-max" in _engine(LlamacppEngine, _art("qwen3.8-27b-llamacpp"), draft_max=8).draft_args()


def test_mlxlm_drafts_on_a_single_stream_row(hub):
    eng = _engine(MlxlmEngine, _art("gemma-4-26b-a4b-mlxlm"))
    assert eng.speculates(SS) and not eng.speculates(C32)
    assert eng.draft_args() == ["--draft-model", str(hub / "models--mlx-community--gemma-4-e2b-it-4bit/snapshots/r1")]
    # the hybrids' arms carry no draft: plain everywhere
    assert not _engine(MlxlmEngine, _art("qwen3.8-27b-mlxlm")).speculates(SS)


def test_speculation_knob_forces_it(hub):
    art = _art("qwen3.8-27b-llamacpp")
    assert not _engine(LlamacppEngine, art, speculation="off").speculates(SS)
    assert _engine(LlamacppEngine, art, speculation="on").speculates(C32)
    # an engine that cannot draft never speculates, whatever the artifact says
    assert not _engine(SplashEngine, art.model_copy(update={"source_format": "splash"})).speculates(SS)


def test_a_speculative_shape_drafts_wherever_the_engine_can(hub):
    spec = WorkloadSpec(id="spec-512-256", kind="single_stream", params={"prefill": 512, "decode": 256, "speculation": True})
    # on, whatever the recipe says; plain where the arm has nothing to draft with
    assert _engine(LlamacppEngine, _art("qwen3.8-27b-llamacpp"), speculation="off").speculates(spec)
    assert not _engine(MlxlmEngine, _art("qwen3.8-27b-mlxlm")).speculates(spec)
    # and the matrix runs it only where something drafts: Splash always, pie with its drafter row
    cells = [c for c in Matrix.load(ROOT / "matrix").expand(platforms=["m5-max-128g"]) if c.workload.id == "spec-512-256" and c.platform.id == "m5-max-128g"]
    why = {(str(c.engine), c.artifact.id): c.declared_unsupported_reason for c in cells}
    assert why[("splash", "qwen3.8-27b-splash")] is None and why[("pie", "qwen3.8-27b-mlx4")] is None
    assert why[("llamacpp", "qwen3.8-27b-llamacpp")] is None
    assert why[("mlxlm", "qwen3.8-27b-mlxlm")] == "mlxlm has no drafter for this model"


def test_the_server_drafts_only_for_the_rows_that_speculate(hub, tmp_path, monkeypatch):
    from pie_evals.node.engines import served

    booted = []

    class Proc:
        pid = 1

        def poll(self):
            return None

    monkeypatch.setattr(served.subprocess, "Popen", lambda cmd, **kw: booted.append(cmd) or Proc())
    monkeypatch.setattr(served.urllib.request, "urlopen", lambda *a, **k: type("R", (), {"__enter__": lambda s: s, "__exit__": lambda s, *a: None, "read": lambda s: b""})())
    art = _art("qwen3.8-27b-llamacpp")
    eng = _engine(LlamacppEngine, art)
    eng.serve(serve_envelope([SS]), tmp_path / "ss.log", 60)
    assert eng.drafting and "--model-draft" in booted[-1]
    assert eng.counters_from_summary({})["speculative"] == 1.0
    # a drafting server refuses a plain row instead of measuring it with the draft
    with pytest.raises(EngineLaunchError):
        eng.run(C32, [], tmp_path / "c32", 60)
    eng._server_proc = None
    eng = _engine(LlamacppEngine, art, workload=C32)
    eng.serve(serve_envelope([SS, C32]), tmp_path / "mixed.log", 60)
    assert not eng.drafting and "--model-draft" not in booted[-1]
    assert "speculative" not in eng.counters_from_summary({})
    eng._server_proc = None


def test_single_stream_rows_get_a_process_of_their_own():
    m = Matrix.load(ROOT / "matrix")
    for aid, drafts in (("qwen3.8-27b-llamacpp", True), ("gemma-4-26b-a4b-mlxlm", True), ("qwen3.8-27b-mlxlm", False)):
        cells = [c for c in m.runnable(Tier.TARGETED, m.expand(platforms=["m5-max-128g"], artifacts=[aid])) if c.artifact.id == aid and c.platform.id == "m5-max-128g"]
        assert {c.workload.kind.value for c in cells} >= {"single_stream", "concurrency"}, aid
        groups = {process_key(cells[0]): cells}
        out = split_draft_processes(groups)
        if not drafts:
            assert out == groups
            continue
        assert len(out) == 2 and sum(len(cs) for cs in out.values()) == len(cells)
        for k, cs in out.items():
            ss = [c.workload.kind.value == "single_stream" for c in cs]
            assert all(ss) if k[2].endswith("-draft") else not any(ss)
        # a process of single-stream rows only stays one process (and drafts)
        only = {process_key(cells[0]): [c for c in cells if c.workload.kind.value == "single_stream"]}
        assert split_draft_processes(only) == only


def test_the_draft_is_fetched_with_the_artifact(tmp_path, monkeypatch):
    import huggingface_hub

    got = []

    def fake(repo, cache_dir, token=None, **kw):
        got.append((repo, kw.get("allow_patterns")))
        return str(_snap(Path(cache_dir), repo, {p: b"GGUF" for p in kw.get("allow_patterns", []) if p.endswith(".gguf")}))

    monkeypatch.setattr(huggingface_hub, "snapshot_download", fake)
    art = _art("qwen3.8-27b-llamacpp").model_copy(update={"tokenizer_from": None, "gguf_config_from": None})
    ensure_snapshot(art, tmp_path / "hub", log=lambda m: None)
    assert [r for r, _ in got] == ["unsloth/Qwen3.8-27B-GGUF", "unsloth/Qwen3.5-0.8B-GGUF"]
    assert "Qwen3.5-0.8B-Q4_K_M.gguf" in got[1][1]
    assert draft_artifact(_art("qwen3.8-27b-mlxlm")) is None


def test_baselines_ship_plain():
    for cls in (LlamacppEngine, MlxlmEngine):
        recipe = load_recipe(str(cls.name), "competitive", MAC, SS, family="qwen3")
        assert str(recipe["speculation"]) == "off"
