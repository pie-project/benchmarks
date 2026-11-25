from __future__ import annotations

import ast
import json
import os
import re
import sys
from pathlib import Path

import pytest

from pie_bench.node.build import bench_dir
from pie_bench.node.engines import get_engine
from pie_bench.node.engines.base import Engine
from pie_bench.node.engines.llamacpp import LlamacppEngine
from pie_bench.node.engines.mlxlm import MlxlmEngine
from pie_bench.node.engines.pie import PieEngine
from pie_bench.node.engines.recipes import load_recipe, recipe_names
from pie_bench.node.engines.served import SCRIPT as OPENAI_SCRIPT
from pie_bench.node.engines.sglang import SglangEngine
from pie_bench.node.engines.shape import max_model_len_for, workload_concurrency
from pie_bench.node.engines.splash import SplashEngine
from pie_bench.node.engines.vllm import VllmEngine
from pie_bench.node.workloads import common_args_for
from pie_bench.node.workloads.synthetic import WORDS_PER_TOKEN
from pie_bench.paths import MATRIX
from pie_bench.schema import ArtifactSpec, Backend, Mode, PlatformSpec, WorkloadSpec


def _default_pie_root() -> str:
    try:
        return "/root/pie" if Path("/root/pie").is_dir() else str(Path.home() / "pie")
    except OSError:
        return str(Path.home() / "pie")


PIE_ROOT = Path(os.environ.get("PIE_ROOT") or _default_pie_root())
BENCHES = bench_dir()


def _first_arg_flags(call: ast.Call, loop_iters: list[ast.AST]) -> list[str]:
    if not call.args:
        return []
    first = call.args[0]
    if isinstance(first, ast.Constant) and isinstance(first.value, str):
        return [first.value]
    if isinstance(first, ast.Name):
        out = []
        for it in loop_iters:
            for node in ast.walk(it):
                if isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value.startswith("--"):
                    out.append(node.value)
        return out
    return []


def _flags_in(node: ast.AST, loop_iters: list[ast.AST] | None = None) -> set[str]:
    flags: set[str] = set()
    loop_iters = list(loop_iters or [])

    def visit(n: ast.AST, iters: list[ast.AST]) -> None:
        if isinstance(n, ast.For):
            iters = iters + [n.iter]
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "add_argument":
            names = _first_arg_flags(n, iters)
            boolean_optional = any(
                kw.arg == "action" and isinstance(kw.value, ast.Attribute) and kw.value.attr == "BooleanOptionalAction"
                for kw in n.keywords
            )
            for name in names:
                if not name.startswith("--"):
                    continue
                flags.add(name)
                if boolean_optional:
                    flags.add("--no-" + name[2:])
        for child in ast.iter_child_nodes(n):
            visit(child, iters)

    visit(node, loop_iters)
    return flags


def _called_names(node: ast.AST) -> set[str]:
    return {n.id for n in ast.walk(node) if isinstance(n, ast.Name)}


def common_flags_by_function() -> dict[str, tuple[set[str], set[str]]]:
    tree = ast.parse((BENCHES / "common.py").read_text())
    out = {}
    for fn in tree.body:
        if isinstance(fn, ast.FunctionDef):
            out[fn.name] = (_flags_in(fn), _called_names(fn))
    return out


def argparse_flags(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(), filename=str(path))
    flags = _flags_in(tree)
    if path.resolve() == (BENCHES / "common.py").resolve():
        return flags
    common = common_flags_by_function()
    todo = [n for n in _called_names(tree) if n in common]
    seen: set[str] = set()
    while todo:
        fn = todo.pop()
        if fn in seen:
            continue
        seen.add(fn)
        fn_flags, refs = common[fn]
        flags |= fn_flags
        todo += [n for n in refs if n in common]
    return flags


def accepted_flags(script: str) -> set[str]:
    return argparse_flags(BENCHES / script)


_FLAG_RE = re.compile(r"^--[a-z0-9][a-z0-9-]*$")


def emitted_flags(argv: list[str]) -> list[str]:
    return [a for a in argv if _FLAG_RE.match(a)]


def flag_value(argv: list[str], flag: str) -> str:
    i = argv.index(flag)
    return argv[i + 1]


def platform(backend: Backend = Backend.CUDA, arch: str = "ada", count: int = 2) -> PlatformSpec:
    return PlatformSpec(
        id=f"{backend}-{arch}", os="macos" if backend == Backend.METAL else "linux", backend=backend,
        accelerator="dummy", arch=arch, count=count, memory_gib=48.0, tp_capable=count > 1,
    )


def artifact(**over) -> ArtifactSpec:
    base = {"id": "qwen3-8b-bf16", "base_model": "Qwen/Qwen3-8B", "family": "qwen3", "scheme": "bf16"}
    base.update(over)
    return ArtifactSpec(**base)


WORKLOADS = {
    "ss-128-64": WorkloadSpec(id="ss-128-64", kind="single_stream", params={"prefill": 128, "decode": 64}),
    "c32": WorkloadSpec(id="c32", kind="concurrency", params={"concurrency": 32, "num_requests": 128, "prefill": 128, "decode": 128}),
    "lc-8k-128": WorkloadSpec(id="lc-8k-128", kind="long_context", params={"prefill": 8192, "decode": 128, "concurrency": 1}),
    "prefix-1k-x64": WorkloadSpec(
        id="prefix-1k-x64", kind="prefix_shared",
        params={"shared_prefix": 1024, "unique_suffix": 64, "variants": 64, "decode": 64, "concurrency": 16},
    ),
    "mixed-256": WorkloadSpec(
        id="mixed-256", kind="mixed_length",
        params={"num_requests": 256, "concurrency": 32, "prompt_lognormal": [6.0, 0.8], "output_lognormal": [5.0, 0.7], "max_prompt": 4096, "max_output": 1024},
    ),
    "replay": WorkloadSpec(id="replay", kind="replay", params={"arrival_rate": 4.0, "concurrency": 16, "num_requests": 64}),
}


def make(cls: type[Engine], *, plat: PlatformSpec | None = None, art: ArtifactSpec | None = None, mode: Mode | None = None,
         recipe_name: str = "competitive", workload: WorkloadSpec | None = None, **kw) -> Engine:
    plat = plat or platform()
    workload = workload or WORKLOADS["c32"]
    art = art or artifact()
    recipe = load_recipe(str(cls.name), recipe_name, plat, workload, family=art.family)
    return cls(pie_root=PIE_ROOT, artifact=art, platform=plat, mode=mode or Mode(), recipe=recipe, **kw)


def argv_for(engine: Engine, workload: WorkloadSpec, tmp_path: Path) -> list[str]:
    return engine.build_argv(workload, common_args_for(workload), tmp_path / "bench.json")


@pytest.fixture
def hf_cache(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    hub = tmp_path / "hub"
    monkeypatch.setenv("HF_HUB_CACHE", str(hub))
    gguf = hub / "models--Qwen--Qwen3-8B-GGUF"
    (gguf / "snapshots" / "abc123").mkdir(parents=True)
    (gguf / "refs").mkdir()
    (gguf / "refs" / "main").write_text("abc123")
    (gguf / "snapshots" / "abc123" / "Qwen3-8B-Q4_K_M.gguf").write_bytes(b"GGUF")
    mlx = hub / "models--mlx-community--Qwen3.6-27B-4bit"
    (mlx / "snapshots" / "def456").mkdir(parents=True)
    (mlx / "refs").mkdir()
    (mlx / "refs" / "main").write_text("def456")
    (mlx / "snapshots" / "def456" / "tokenizer.json").write_text("{}")
    return hub


def test_registry_resolves_every_engine():
    assert get_engine("pie") is PieEngine
    assert get_engine("splash") is SplashEngine
    assert get_engine("vllm") is VllmEngine
    assert get_engine("sglang") is SglangEngine
    assert get_engine("llamacpp") is LlamacppEngine
    assert get_engine("mlxlm") is MlxlmEngine


@pytest.mark.parametrize("engine", ["pie", "vllm", "sglang", "llamacpp", "mlxlm", "atom"])
def test_recipes_have_default_and_competitive_with_rationale(engine):
    names = recipe_names(engine)
    assert "default" in names and "competitive" in names
    for wl in WORKLOADS.values():
        r = load_recipe(engine, "competitive", platform(), wl)
        assert r["_recipe"] == "competitive"
        assert r["_rationale"], f"{engine}: competitive recipe carries no rationale"
        for k, v in r.items():
            assert not (isinstance(v, str) and v.startswith("$")), f"{engine}.{k} left unresolved: {v}"


def test_recipe_resolves_concurrency_and_overrides():
    r = load_recipe("sglang", "competitive", platform(), WORKLOADS["c32"])
    assert r["cuda_graph_max_bs"] == 32
    r = load_recipe("sglang", "competitive", platform(), WORKLOADS["ss-128-64"])
    assert r["cuda_graph_max_bs"] == 1
    r = load_recipe("vllm", "competitive", platform(arch="hopper"), WORKLOADS["c32"])
    assert r["attention_backend"] == "FLASH_ATTN"
    r = load_recipe("vllm", "competitive", platform(arch="ada"), WORKLOADS["c32"], family="gpt_oss")
    assert not r.get("attention_backend"), "FlashInfer rejects gpt-oss's attention sinks off Hopper"
    r = load_recipe("vllm", "competitive", platform(arch="hopper"), WORKLOADS["c32"], family="gpt_oss")
    assert r["attention_backend"] == "FLASH_ATTN"
    r = load_recipe("vllm", "competitive", platform(arch="hopper"), WORKLOADS["c32"], family="kimi_k3")
    assert not r.get("attention_backend"), "FA3 has no MLA path; Kimi keeps vLLM's own pick on Hopper too"
    r = load_recipe("vllm", "competitive", platform(arch="ada"), WORKLOADS["prefix-1k-x64"])
    assert r["prefix_caching"] is True
    r = load_recipe("pie", "competitive", platform(Backend.METAL, "apple9", count=1), WORKLOADS["c32"])
    assert r["gpu_mem_util"] is None and r["max_forward_requests"] == 32


def test_shape_helpers():
    assert workload_concurrency(WORKLOADS["ss-128-64"]) == 1
    assert workload_concurrency(WORKLOADS["c32"]) == 32
    assert max_model_len_for(WORKLOADS["c32"]) == 2048
    assert max_model_len_for(WORKLOADS["lc-8k-128"]) == 10240
    assert max_model_len_for(WORKLOADS["mixed-256"]) == 6144
    assert max_model_len_for(WORKLOADS["prefix-1k-x64"]) == 2048


def test_pie_cuda_tp2(tmp_path):
    eng = make(PieEngine, mode=Mode(id="tp2", tp=2))
    argv = argv_for(eng, WORKLOADS["c32"], tmp_path)
    assert argv[1].endswith("clients/bench_pie.py") and argv[2] == "tput"
    expected = "cuda_native" if '"cuda_native"' in eng.script_path().read_text() else "cuda"
    assert flag_value(argv, "--engine") == expected
    assert flag_value(argv, "--tp-size") == "2"
    assert argv.count("--device") == 1
    assert flag_value(argv, "--device").split(",") == ["cuda:0", "cuda:1"]
    assert flag_value(argv, "--max-model-len") == "2048"
    assert flag_value(argv, "--gpu-mem-util") == "0.9"
    assert flag_value(argv, "--concurrency") == "32"
    assert "--report-timing" in argv
    assert "--dump-all-token-ids" in argv and "--json-out" in argv
    assert flag_value(argv, "--inferlet-dir") == str(PIE_ROOT / "examples/text-completion-bench")
    assert eng.env["PIE_BENCH_INFERLET_DIR"] == str(PIE_ROOT / "examples/text-completion-bench")
    assert eng.env["PYTHONPATH"].startswith(f"{PIE_ROOT}/python/client/src:{PIE_ROOT}/python/server/python")
    assert "--kv-pages" not in argv


def test_pie_program_path_is_settable(tmp_path):
    eng = make(PieEngine)
    eng.program_path = "examples/dflash-speculative-bench"
    assert eng.env["PIE_BENCH_INFERLET_DIR"].endswith("dflash-speculative-bench")
    argv = argv_for(eng, WORKLOADS["ss-128-64"], tmp_path)
    assert flag_value(argv, "--inferlet-dir").endswith("dflash-speculative-bench")
    assert argv[2] == "latency" and flag_value(argv, "--requests") == "8"
    eng2 = make(PieEngine, recipe_name="default")
    eng2.recipe["program_path"] = "x/y"
    eng3 = PieEngine(pie_root=PIE_ROOT, artifact=artifact(), platform=platform(), mode=Mode(), recipe={"program_path": "x/y"})
    assert eng3.program_path == "x/y" and eng3.inferlet_dir == PIE_ROOT / "x/y"


def test_pie_metal_and_recipe_passthrough(tmp_path):
    plat = platform(Backend.METAL, "apple9", count=1)
    eng = make(PieEngine, plat=plat, workload=WORKLOADS["c32"])
    eng.recipe.update({"frame_submit_depth": 4, "engine_option": {"max_state_slots": 128, "sku": "$pie_sku"}, "pretokenized_prompts": False})
    argv = argv_for(eng, WORKLOADS["c32"], tmp_path)
    assert flag_value(argv, "--engine") == "metal"
    assert "--gpu-mem-util" not in argv and "--tp-size" not in argv and "--device" not in argv
    assert flag_value(argv, "--frame-submit-depth") == "4"
    assert flag_value(argv, "--max-forward-requests") == "32"
    assert "--no-pretokenized-prompts" in argv
    i = argv.index("--engine-option")
    assert argv[i + 1] == "max_state_slots=128"
    assert argv.count("--engine-option") == 1
    eng.artifact = artifact(pie_sku="qwen3-8b-bf16-kv-bf16")
    argv = argv_for(eng, WORKLOADS["c32"], tmp_path)
    assert "sku=qwen3-8b-bf16-kv-bf16" in argv


def test_pie_counters_from_summary():
    eng = make(PieEngine)
    summary = {
        "wall_s": 2.0,
        "config": {
            "total batches": 400, "device idle us": 200_000, "cumulative_batch_latency_us": 1_600_000,
            "avg batch latency us": 4000.0, "fire.execute.engine_fire_us": 3500.0,
            "turnaround sum us": 90_000, "turnaround n": 300, "wave fires": 400,
        },
    }
    c = eng.counters_from_summary(summary)
    assert c["batches"] == 400
    assert c["device_idle_pct"] == pytest.approx(10.0)
    assert c["host_us_per_step"] == pytest.approx(500.0)
    assert c["guest_turnaround_us"] == pytest.approx(300.0)
    assert c["batch_latency_us"] == pytest.approx(4000.0)
    assert eng.counters_from_summary({"wall_s": 1.0, "config": {}}) == {}
    c = eng.counters_from_summary({"wall_s": 1.0, "config": {"default.total_batches": 10, "default.fire.quorum.device_idle_us": 100_000}})
    assert c["batches"] == 10 and c["device_idle_pct"] == pytest.approx(10.0)


@pytest.mark.skipif(not (PIE_ROOT / ".git").exists(), reason=f"no pie checkout at {PIE_ROOT}")
def test_pie_version_is_git_short_sha():
    v = make(PieEngine).version()
    assert re.fullmatch(r"[0-9a-f]{7,12}", v), v


def test_pie_serve_only_for_cli_engines_is_noop(tmp_path):
    eng = make(PieEngine, plat=platform(Backend.METAL, "apple9", count=1))
    assert eng.serve(WORKLOADS["c32"], tmp_path / "serve.log", 5) is None
    assert eng.server_url is None and eng._server_proc is None


def test_pie_serve_parses_url_and_stop(tmp_path, monkeypatch):
    fake_root = tmp_path / "pie"
    bench = tmp_path / "bench"
    bench.mkdir()
    monkeypatch.setenv("PIE_BENCH_BENCH_DIR", str(bench))
    (bench / "bench_pie.py").write_text(
        "import os, sys, time\n"
        "assert os.environ.get('PIE_BENCH_SERVE_ONLY') == '1'\n"
        "assert 'PIE_BENCH_SERVER_URL' not in os.environ\n"
        "print('booting', flush=True)\n"
        "print('PIE_BENCH_SERVER_URL=ws://127.0.0.1:43210', flush=True)\n"
        "time.sleep(60)\n"
    )
    eng = PieEngine(pie_root=fake_root, artifact=artifact(), platform=platform(), mode=Mode(),
                    recipe=load_recipe("pie", "competitive", platform(), WORKLOADS["c32"]))
    eng.serve(WORKLOADS["c32"], tmp_path / "serve.log", timeout_s=30)
    assert eng.server_url == "ws://127.0.0.1:43210"
    assert eng._server_proc is not None and eng._server_proc.poll() is None
    eng.stop()
    assert eng.server_url is None and eng._server_proc is None
    assert "PIE_BENCH_SERVER_URL=" in (tmp_path / "serve.log").read_text()


def test_vllm_args(tmp_path):
    eng = make(VllmEngine, mode=Mode(id="tp2", tp=2))
    argv = argv_for(eng, WORKLOADS["c32"], tmp_path)
    assert argv[1].endswith("clients/vllm_bench.py")
    assert flag_value(argv, "--model") == "Qwen/Qwen3-8B"
    assert flag_value(argv, "--tp-size") == "2"
    assert flag_value(argv, "--gpu-mem-util") == "0.9"
    assert flag_value(argv, "--max-model-len") == "2048"
    assert flag_value(argv, "--attention-backend") == "FLASHINFER"
    assert "--report-timing" in argv
    assert "--no-prefix-caching" in argv
    assert "--no-chunked-prefill" not in argv
    assert "--kv-cache-dtype" not in argv
    eng = make(VllmEngine, plat=platform(arch="hopper"), workload=WORKLOADS["prefix-1k-x64"])
    argv = argv_for(eng, WORKLOADS["prefix-1k-x64"], tmp_path)
    assert "--prefix-caching" in argv and flag_value(argv, "--attention-backend") == "FLASH_ATTN"
    assert flag_value(argv, "--shared-prefix-words") == str(int(round(1024 * WORDS_PER_TOKEN)))
    eng = make(VllmEngine, art=artifact(kv_dtype="fp8"), mode=Mode(id="ngram", spec_dec="ngram"))
    argv = argv_for(eng, WORKLOADS["ss-128-64"], tmp_path)
    assert flag_value(argv, "--kv-cache-dtype") == "fp8"
    assert flag_value(argv, "--spec-method") == "ngram" and flag_value(argv, "--spec-tokens") == "4"


def test_vllm_defaults():
    eng = make(VllmEngine)
    assert eng.python.endswith("python")
    assert "EngineCore" in eng.leftover_process_names()


def test_sglang_cuda_graph_max_bs_tracks_concurrency(tmp_path):
    eng = make(SglangEngine, workload=WORKLOADS["c32"])
    argv = argv_for(eng, WORKLOADS["c32"], tmp_path)
    assert flag_value(argv, "--sglang-cuda-graph-max-bs") == "32"
    assert flag_value(argv, "--tp-size") == "1"
    assert flag_value(argv, "--gpu-mem-util") == "0.9"
    assert flag_value(argv, "--max-model-len") == "2048"
    assert flag_value(argv, "--sglang-page-size") == "16"
    assert "--report-timing" in argv
    assert "--sglang-disable-hybrid-swa-memory" not in argv
    eng = make(SglangEngine, workload=WORKLOADS["ss-128-64"])
    argv = argv_for(eng, WORKLOADS["ss-128-64"], tmp_path)
    assert flag_value(argv, "--sglang-cuda-graph-max-bs") == "1"
    assert argv[2] == "latency"
    big = platform(count=1)
    big = big.model_copy(update={"memory_gib": 96.0})

    def conc(n):
        return WorkloadSpec(id=f"c{n}", kind="concurrency", params={"concurrency": n, "num_requests": 4 * n, "prefill": 128, "decode": 128})

    for n, want in ((32, "0.9"), (64, "0.85"), (256, "0.8")):
        argv = argv_for(make(SglangEngine, plat=big, workload=conc(n)), conc(n), tmp_path)
        assert flag_value(argv, "--gpu-mem-util") == want, n
    argv = argv_for(make(SglangEngine, workload=conc(256)), conc(256), tmp_path)
    assert flag_value(argv, "--gpu-mem-util") == "0.9"
    kimi = artifact(id="kimi-k3-mini8", base_model="moonshotai/Kimi-K3", family="kimi_k3", expected_gib=22.0)
    big = platform(count=1).model_copy(update={"memory_gib": 80.0})
    argv = argv_for(make(SglangEngine, plat=big, art=kimi, workload=conc(32)), conc(32), tmp_path)
    assert flag_value(argv, "--gpu-mem-util") == "0.75"
    l40s = platform(count=1)
    argv = argv_for(make(SglangEngine, plat=l40s, art=kimi, workload=conc(256)), conc(256), tmp_path)
    assert flag_value(argv, "--gpu-mem-util") == "0.79"
    argv = argv_for(make(SglangEngine, plat=l40s, art=kimi, workload=conc(32)), conc(32), tmp_path)
    assert flag_value(argv, "--gpu-mem-util") == "0.75"
    small = platform(count=1).model_copy(update={"memory_gib": 32.0})
    argv = argv_for(make(SglangEngine, plat=small, art=kimi, workload=conc(8)), conc(8), tmp_path)
    assert flag_value(argv, "--gpu-mem-util") == "0.95"
    eng = make(SglangEngine, art=artifact(id="gemma-3-4b-bf16", base_model="google/gemma-3-4b-it", family="gemma3"))
    argv = argv_for(eng, WORKLOADS["c32"], tmp_path)
    assert "--sglang-disable-hybrid-swa-memory" in argv
    eng = make(SglangEngine, art=artifact(id="gemma-4-e4b-bf16", base_model="google/gemma-4-E4B-it", family="gemma4"))
    argv = argv_for(eng, WORKLOADS["c32"], tmp_path)
    assert "--sglang-disable-hybrid-swa-memory" not in argv


def test_sglang_heavy_checkpoint_gets_the_fraction_it_needs(tmp_path):
    plat = platform(count=1)
    plat = plat.model_copy(update={"memory_gib": 32.0})
    eng = make(SglangEngine, plat=plat, art=artifact(expected_gib=18.4), workload=WORKLOADS["ss-128-64"])
    assert flag_value(argv_for(eng, WORKLOADS["ss-128-64"], tmp_path), "--gpu-mem-util") == "0.95"
    eng = make(SglangEngine, plat=plat, art=artifact(expected_gib=1.6), workload=WORKLOADS["ss-128-64"])
    assert flag_value(argv_for(eng, WORKLOADS["ss-128-64"], tmp_path), "--gpu-mem-util") == "0.9"


def test_llamacpp_args(tmp_path, hf_cache, monkeypatch):
    monkeypatch.setenv("LLAMA_SERVER_BIN", "/opt/llama/llama-server")
    art = artifact(id="qwen3-8b-gguf-q4km", base_model="Qwen/Qwen3-8B-GGUF", scheme="gguf_q4_k_m",
                   source_format="gguf", gguf_file="Qwen3-8B-Q4_K_M.gguf")
    eng = make(LlamacppEngine, art=art, workload=WORKLOADS["c32"], python="/usr/bin/python3")
    cmd = eng.server_cmd(8123, 32, 2048)
    assert cmd[0] == "/opt/llama/llama-server"
    assert flag_value(cmd, "--model") == str(hf_cache / "models--Qwen--Qwen3-8B-GGUF/snapshots/abc123/Qwen3-8B-Q4_K_M.gguf")
    assert flag_value(cmd, "--parallel") == "32" and flag_value(cmd, "--ctx-size") == str(2048 * 32)
    assert flag_value(cmd, "--n-gpu-layers") == "all" and flag_value(cmd, "--flash-attn") == "on"
    assert cmd[cmd.index("--batch-size"):][:4] == ["--batch-size", "2048", "--ubatch-size", "512"]
    argv = argv_for(eng, WORKLOADS["c32"], tmp_path)
    assert Path(argv[1]) == OPENAI_SCRIPT
    assert flag_value(argv, "--model") == "Qwen/Qwen3-8B"
    assert json.loads(flag_value(argv, "--extra-body")) == {"cache_prompt": False, "ignore_eos": True}
    assert "--ignore-eos" in argv and "--no-ignore-eos" not in argv
    assert "--chat" not in argv and "--no-flush-cache" not in argv
    assert "--token-ids" in argv
    eng = make(LlamacppEngine, art=art, workload=WORKLOADS["prefix-1k-x64"], python="/usr/bin/python3")
    assert "--cache-reuse" in eng.server_cmd(8123, 16, 2048)
    argv = argv_for(eng, WORKLOADS["prefix-1k-x64"], tmp_path)
    assert "--no-flush-cache" in argv and json.loads(flag_value(argv, "--extra-body"))["cache_prompt"] is True
    eng = make(LlamacppEngine, art=art, plat=platform(Backend.METAL, "apple9", count=1), python="/usr/bin/python3")
    assert "--no-mmap" not in eng.server_cmd(8123, 1, 2048)


def test_llamacpp_takes_its_tokenizer_from_the_named_checkpoint(hf_cache):
    art = artifact(base_model="Qwen/Qwen3-8B-GGUF", scheme="gguf_q4_k_m", source_format="gguf", gguf_file="Qwen3-8B-Q4_K_M.gguf",
                   tokenizer_from="mlx-community/Qwen3.6-27B-4bit")
    (hf_cache / "models--mlx-community--Qwen3.6-27B-4bit/snapshots/def456/tokenizer.json").write_text("{}")
    eng = make(LlamacppEngine, art=art, python="/usr/bin/python3")
    assert eng.model_arg() == str(hf_cache / "models--mlx-community--Qwen3.6-27B-4bit/snapshots/def456")


@pytest.mark.parametrize("printed,tag", [("version: 0.5.0-dev (build 11312, commit 0c1e57098)", "b11312"), ("version: 10270 (071327508)", "b10270")])
def test_llamacpp_version_is_the_release_tag_the_matrix_pins(printed, tag, tmp_path, hf_cache, monkeypatch):
    fake = tmp_path / "llama-server"
    fake.write_text(f"#!/bin/sh\necho '{printed}' >&2\n")
    fake.chmod(0o755)
    monkeypatch.setenv("LLAMA_SERVER_BIN", str(fake))
    art = artifact(base_model="Qwen/Qwen3-8B-GGUF", scheme="gguf_q4_k_m", source_format="gguf", gguf_file="Qwen3-8B-Q4_K_M.gguf")
    assert make(LlamacppEngine, art=art, python="/usr/bin/python3").version() == tag


def test_llamacpp_missing_gguf_is_load_fail(hf_cache):
    art = artifact(base_model="Qwen/Qwen3-8B-GGUF", scheme="gguf_q4_k_m", source_format="gguf", gguf_file="nope.gguf")
    eng = make(LlamacppEngine, art=art, python="/usr/bin/python3")
    from pie_bench.node.engines import EngineLaunchError

    with pytest.raises(EngineLaunchError) as e:
        eng.gguf_path()
    assert str(e.value.error_class) == "load_fail"


def test_mlxlm_args(tmp_path, hf_cache, monkeypatch):
    monkeypatch.setenv("MLX_PY", "/opt/mlx/bin/python")
    art = artifact(id="qwen3.6-27b-mlx4", base_model="mlx-community/Qwen3.6-27B-4bit", family="qwen3_6",
                   scheme="affine_u4_g64", source_format="mlx")
    plat = platform(Backend.METAL, "apple9", count=1)
    snap = str(hf_cache / "models--mlx-community--Qwen3.6-27B-4bit/snapshots/def456")
    eng = make(MlxlmEngine, art=art, plat=plat, workload=WORKLOADS["c32"], python="/usr/bin/python3")
    cmd = eng.server_cmd(8123, 32, 2048)
    assert cmd[:4] == ["/opt/mlx/bin/python", "-m", "mlx_lm", "server"]
    assert flag_value(cmd, "--model") == snap and flag_value(cmd, "--decode-concurrency") == "32"
    assert flag_value(cmd, "--prompt-cache-size") == "0"
    argv = argv_for(eng, WORKLOADS["c32"], tmp_path)
    assert argv[0] == "/usr/bin/python3" and Path(argv[1]) == OPENAI_SCRIPT
    assert flag_value(argv, "--model") == snap and flag_value(argv, "--api-model") == snap
    assert "--ignore-eos" in argv and "--no-ignore-eos" not in argv
    eng = make(MlxlmEngine, art=art, plat=plat, workload=WORKLOADS["prefix-1k-x64"], python="/usr/bin/python3")
    assert flag_value(eng.server_cmd(8123, 16, 2048), "--prompt-cache-size") == "64"
    assert "--no-flush-cache" in argv_for(eng, WORKLOADS["prefix-1k-x64"], tmp_path)


def splash_artifact() -> ArtifactSpec:
    return artifact(id="qwen3.6-27b-splash", base_model="mlx-community/Qwen3.6-27B-4bit", family="qwen3_6",
                    scheme="affine_u4_g64", source_format="splash", baseline_of="qwen3.6-27b-mlx4", baseline_label="Splash")


def test_splash_args(tmp_path, hf_cache, monkeypatch):
    monkeypatch.setenv("SPLASH_BIN", "/opt/splash/bin/splash")
    plat = platform(Backend.METAL, "apple10", count=1)
    eng = make(SplashEngine, art=splash_artifact(), plat=plat, workload=WORKLOADS["c32"], python="/usr/bin/python3")
    cmd = eng.server_cmd(8123, 32, 2048)
    assert cmd[:4] == ["/opt/splash/bin/splash", "serve", "--model", "mlx-community/Qwen3.6-27B-4bit"]
    assert flag_value(cmd, "--max-context") == "2048" and "--no-webui" in cmd
    argv = argv_for(eng, WORKLOADS["c32"], tmp_path)
    assert Path(argv[1]) == OPENAI_SCRIPT and "--chat" in argv
    assert flag_value(argv, "--api-model") == "mlx-community/Qwen3.6-27B-4bit"
    assert flag_value(argv, "--model") == str(hf_cache / "models--mlx-community--Qwen3.6-27B-4bit/snapshots/def456")
    assert json.loads(flag_value(argv, "--extra-body")) == {"reasoning_effort": "none", "ignore_eos": True}
    default = make(SplashEngine, art=splash_artifact(), plat=plat, recipe_name="default", python="/usr/bin/python3")
    assert "--max-context" not in default.server_cmd(8123, 1, 2048)


def test_served_engines_boot_and_stop_a_server(tmp_path, hf_cache, monkeypatch):
    import sys

    fake = tmp_path / "server.py"
    fake.write_text(
        "import http.server, sys\n"
        "class H(http.server.BaseHTTPRequestHandler):\n"
        "    def do_GET(self):\n"
        "        self.send_response(200); self.end_headers(); self.wfile.write(b'{}')\n"
        "    def log_message(self, *a): pass\n"
        "http.server.HTTPServer(('127.0.0.1', int(sys.argv[1])), H).serve_forever()\n"
    )

    class Fake(SplashEngine):
        def server_cmd(self, port, slots, context):
            return [sys.executable, str(fake), str(port)]

    eng = make(Fake, art=splash_artifact(), plat=platform(Backend.METAL, "apple10", count=1), python="/usr/bin/python3")
    eng.serve(WORKLOADS["ss-128-64"], tmp_path / "serve.log", 30)
    try:
        assert eng.server_url and eng.server_url.startswith("http://127.0.0.1:")
        assert flag_value(argv_for(eng, WORKLOADS["ss-128-64"], tmp_path), "--url") == eng.server_url
        assert eng.counters_from_summary({})["server_load_s"] >= 0 and eng.watch_pids()
    finally:
        eng.stop()
    assert eng.server_url is None and eng.watch_pids() == []


def test_a_served_engine_that_dies_at_startup_is_a_load_fail(tmp_path, hf_cache):
    import sys

    from pie_bench.node.engines import EngineLaunchError

    class Dead(SplashEngine):
        def server_cmd(self, port, slots, context):
            return [sys.executable, "-c", "import sys; print('no such model'); sys.exit(3)"]

    eng = make(Dead, art=splash_artifact(), plat=platform(Backend.METAL, "apple10", count=1), python="/usr/bin/python3")
    with pytest.raises(EngineLaunchError) as e:
        eng.serve(WORKLOADS["ss-128-64"], tmp_path / "serve.log", 30)
    assert str(e.value.error_class) == "load_fail" and "no such model" in str(e.value)


_CASES = []
for _wl in WORKLOADS:
    _CASES += [
        ("pie", PieEngine, _wl, {}),
        ("pie-metal", PieEngine, _wl, {"plat": platform(Backend.METAL, "apple9", count=1)}),
        ("pie-tp2", PieEngine, _wl, {"mode": Mode(id="tp2", tp=2)}),
        ("vllm", VllmEngine, _wl, {}),
        ("vllm-ngram-fp8", VllmEngine, _wl, {"mode": Mode(id="ngram", spec_dec="ngram"), "art": artifact(kv_dtype="fp8")}),
        ("sglang", SglangEngine, _wl, {}),
        ("sglang-gemma", SglangEngine, _wl, {"art": artifact(family="gemma4")}),
    ]


@pytest.mark.parametrize("label,cls,wl,over", _CASES, ids=[f"{c[0]}/{c[2]}" for c in _CASES])
def test_every_emitted_flag_is_parsed_by_the_script(label, cls, wl, over, tmp_path, hf_cache):
    workload = WORKLOADS[wl]
    eng = make(cls, workload=workload, **over)
    argv = argv_for(eng, workload, tmp_path)
    accepted = accepted_flags(cls.script)
    assert accepted, f"no flags parsed from {cls.script}"
    unknown = sorted(set(emitted_flags(argv)) - accepted)
    assert not unknown, f"{label}/{wl}: {cls.script} does not accept {unknown}"


def test_argparse_flag_extraction_sees_loop_registered_and_boolean_optional_flags():
    flags = argparse_flags(BENCHES / "bench_pie.py")
    assert {"--inferlet-dir", "--engine", "--wasm-warm-slots", "--frame-submit-depth", "--pretokenized-prompts", "--no-pretokenized-prompts"} <= flags
    common = argparse_flags(BENCHES / "common.py")
    assert {"--model", "--ignore-eos", "--no-ignore-eos", "--tp-size", "--sglang-cuda-graph-max-bs", "--json-out"} <= common
    assert "--dump-all-token-ids" in argparse_flags(BENCHES / "vllm_bench.py")
    assert "--dump-all-token-ids" in argparse_flags(BENCHES / "sglang_bench.py")
    assert "--dump-all-token-ids" in flags


def test_tensor_parallel_baselines_disable_nccl_p2p_on_a_pod(monkeypatch):
    monkeypatch.setenv("RUNPOD_POD_ID", "abc")
    for cls in (VllmEngine, SglangEngine, PieEngine):
        assert make(cls, mode=Mode(id="tp2", tp=2)).env["NCCL_P2P_DISABLE"] == "1"
        assert "NCCL_P2P_DISABLE" not in make(cls).env
        nvlink = platform().model_copy(update={"interconnect": "nvlink"})
        assert "NCCL_P2P_DISABLE" not in make(cls, plat=nvlink, mode=Mode(id="tp2", tp=2)).env
    monkeypatch.delenv("RUNPOD_POD_ID")
    assert "NCCL_P2P_DISABLE" not in make(VllmEngine, mode=Mode(id="tp2", tp=2)).env


def test_baselines_keep_all_reduce_on_nccl_without_peer_access():
    nopeer = platform().model_copy(update={"peer_access": False})
    tp2 = Mode(id="tp2", tp=2)
    assert make(VllmEngine, plat=nopeer, mode=tp2).env["VLLM_DISABLE_CUSTOM_AR"] == "1"
    for cls in (VllmEngine, SglangEngine):
        env = make(cls, plat=nopeer, mode=tp2).env
        assert env["PIE_BENCH_NO_CUSTOM_AR"] == "1" and env["PYTHONPATH"].split(":")[0].endswith("no_peer_site")
    for cls in (VllmEngine, SglangEngine):
        for plat, mode in ((platform(), tp2), (nopeer, Mode())):
            env = make(cls, plat=plat, mode=mode).env
            assert "VLLM_DISABLE_CUSTOM_AR" not in env and "PIE_BENCH_NO_CUSTOM_AR" not in env
    assert make(VllmEngine, mode=tp2).env["VLLM_WORKER_MULTIPROC_METHOD"] == "spawn"
    assert "VLLM_WORKER_MULTIPROC_METHOD" not in make(VllmEngine).env


def test_no_peer_sitecustomize_turns_the_p2p_checks_off(tmp_path):
    import subprocess
    import sys

    from pie_bench.node.engines.base import NO_PEER_SITE

    mods = {"vllm/distributed/device_communicators/custom_all_reduce.py": "_can_p2p",
            "sglang/srt/distributed/device_communicators/custom_all_reduce_utils.py": "can_p2p"}
    for rel, attr in mods.items():
        f = tmp_path / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        for d in [f.parent, *f.parent.parents]:
            if d == tmp_path:
                break
            (d / "__init__.py").touch()
        f.write_text(f"def {attr}(rank, world_size):\n    return True\n")
    code = ";".join(f"import {r[:-3].replace('/', '.')} as m{i}; print(m{i}.{a}(0, 2))" for i, (r, a) in enumerate(mods.items()))
    for flag, want in (("1", "False"), ("0", "True")):
        env = {"PYTHONPATH": f"{NO_PEER_SITE}:{tmp_path}", "PIE_BENCH_NO_CUSTOM_AR": flag, "PATH": "/usr/bin:/bin"}
        out = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True, check=True, cwd=tmp_path).stdout.split()
        assert out == [want, want], (flag, out)


def test_baseline_jit_caches_live_on_the_volume():
    for cls in (VllmEngine, SglangEngine):
        env = make(cls).env
        assert env["TRITON_CACHE_DIR"].endswith("jit/triton") and env["TORCHINDUCTOR_CACHE_DIR"].endswith("jit/inductor")
    assert make(VllmEngine).env["VLLM_CACHE_ROOT"].endswith("jit/vllm")


def test_vllm_kimi_leaves_activation_room_at_c256_on_a_48gb_card(tmp_path):
    kimi = artifact(id="kimi-k3-mini8", base_model="moonshotai/Kimi-K3", family="kimi_k3", expected_gib=22.0)
    c256 = WorkloadSpec(id="c256", kind="concurrency", params={"concurrency": 256, "num_requests": 1024, "prefill": 128, "decode": 128})
    argv = argv_for(make(VllmEngine, plat=platform(count=1), art=kimi, workload=c256), c256, tmp_path)
    assert flag_value(argv, "--gpu-mem-util") == "0.85"
    argv = argv_for(make(VllmEngine, plat=platform(count=1), art=kimi, workload=WORKLOADS["c32"]), WORKLOADS["c32"], tmp_path)
    assert flag_value(argv, "--gpu-mem-util") == "0.9"


def test_vllm_speculative_boots_leave_warmup_room_on_small_cards(tmp_path):
    small = platform(count=1).model_copy(update={"memory_gib": 24.0})
    ss = WORKLOADS["ss-128-64"]
    argv = argv_for(make(VllmEngine, plat=small, mode=Mode(id="ngram", spec_dec="ngram"), workload=ss), ss, tmp_path)
    assert flag_value(argv, "--gpu-mem-util") == "0.85"
    argv = argv_for(make(VllmEngine, plat=small, workload=ss), ss, tmp_path)
    assert flag_value(argv, "--gpu-mem-util") == "0.9"


def mac_platform(arch: str = "apple9", memory_gib: float = 48.0) -> PlatformSpec:
    return PlatformSpec(id=f"mac-{arch}", os="macos", backend=Backend.METAL, accelerator="dummy", arch=arch,
                        memory_gib=memory_gib, interconnect="uma")


def mac_artifact(**over) -> ArtifactSpec:
    base = {"id": "muse-glimmer-30b-mlx4", "base_model": "mlx-community/Qwen3.6-27B-4bit", "family": "qwen3_6",
            "scheme": "affine_u4_g64", "source_format": "mlx"}
    base.update(over)
    return ArtifactSpec(**base)


MAC_WORKLOADS = {
    "control-aa": WorkloadSpec(id="control-aa", kind="control_aa", params={"prefill": 128, "decode": 64, "rounds": 2}),
    "ob-story-200": WorkloadSpec(id="ob-story-200", kind="single_stream", params={"prompt": "Tell a story about a llama.", "decode": 200, "requests": 6, "warmup": 1}),
    "ss-128-64": WorkloadSpec(id="ss-128-64", kind="single_stream", params={"prefill": 128, "decode": 64}),
    "lc-2k-128": WorkloadSpec(id="lc-2k-128", kind="long_context", params={"prefill": 2048, "decode": 128, "concurrency": 1}),
    "c8": WorkloadSpec(id="c8", kind="concurrency", params={"concurrency": 8, "num_requests": 32, "prefill": 128, "decode": 128}),
    "c32": WorkloadSpec(id="c32", kind="concurrency", params={"concurrency": 32, "num_requests": 128, "prefill": 128, "decode": 128}),
}

MAC_RECIPE = {PieEngine: "default", LlamacppEngine: "competitive", MlxlmEngine: "competitive", SplashEngine: "competitive"}


def mac_make(cls: type[Engine], *, plat: PlatformSpec | None = None, art: ArtifactSpec | None = None, mode: Mode | None = None,
             recipe_name: str | None = None, workload: WorkloadSpec | None = None, **kw) -> Engine:
    plat = plat or mac_platform()
    workload = workload or MAC_WORKLOADS["c32"]
    art = art or mac_artifact()
    recipe = load_recipe(str(cls.name), recipe_name or MAC_RECIPE[cls], plat, workload, family=art.family)
    kw.setdefault("python", "/usr/bin/python3")
    return cls(pie_root=PIE_ROOT, artifact=art, platform=plat, mode=mode or Mode(), recipe=recipe, **kw)


@pytest.mark.parametrize("engine", ["pie"])
def test_mac_recipes_resolve_with_rationale(engine):
    names = recipe_names(engine)
    assert "default" in names
    for name in names:
        for wl in MAC_WORKLOADS.values():
            r = load_recipe(engine, name, mac_platform(), wl, family="qwen3_6")
            assert r["_recipe"] == name
            assert r["_rationale"], f"{engine}.{name}: recipe carries no rationale"
            for k, v in r.items():
                if isinstance(v, str) and v.startswith("$"):
                    assert v in ("$serve_concurrency", "$serve_context"), f"{engine}.{k} left unresolved: {v}"


def test_recipe_overrides_by_family_and_backend():
    r = load_recipe("pie", "default", mac_platform(), MAC_WORKLOADS["c32"], family="qwen3_6")
    assert r["total_pages"] == 1024 and r["engine_option"] == {"max_state_slots": 64}
    r = load_recipe("pie", "default", mac_platform(), MAC_WORKLOADS["c32"], family="gemma4")
    assert "total_pages" not in r
    r = load_recipe("pie", "default", mac_platform(), MAC_WORKLOADS["c32"], family="qwen3_6_moe")
    assert r["total_pages"] == 1024 and r["engine_option"] == {"max_state_slots": 64}


def test_literal_prompt_param_is_sent_as_is():
    args = common_args_for(MAC_WORKLOADS["ob-story-200"])
    assert flag_value(args, "--prompt") == "Tell a story about a llama."
    assert flag_value(args, "--max-tokens") == "200"


def _a_page_count_pie(monkeypatch):
    has = PieEngine._bench_has
    monkeypatch.setattr(PieEngine, "_bench_has", lambda self, flag: flag != "--device-kv-budget" and has(self, flag))


def test_pie_metal_args(tmp_path, monkeypatch):
    _a_page_count_pie(monkeypatch)
    eng = mac_make(PieEngine)
    argv = argv_for(eng, MAC_WORKLOADS["c32"], tmp_path)
    assert argv[1].endswith("clients/bench_pie.py") and argv[2] == "tput"
    assert flag_value(argv, "--engine") == "metal"
    assert flag_value(argv, "--max-model-len") == "2048"
    assert flag_value(argv, "--concurrency") == "32"
    assert "--report-timing" in argv and "--pretokenized-prompts" in argv
    assert "--dump-all-token-ids" in argv and "--json-out" in argv
    assert "--gpu-mem-util" not in argv and "--tp-size" not in argv and "--device" not in argv
    assert flag_value(argv, "--inferlet-dir") == str(PIE_ROOT / "examples/text-completion-bench")
    assert eng.env["PIE_BENCH_INFERLET_DIR"] == str(PIE_ROOT / "examples/text-completion-bench")
    assert eng.env["PYTHONPATH"].startswith(f"{PIE_ROOT}/python/client/src:{PIE_ROOT}/python/server/python")


def test_the_metal_pool_holds_one_request_at_the_declared_context(tmp_path, monkeypatch):
    _a_page_count_pie(monkeypatch)
    eng = mac_make(PieEngine)
    lc = WorkloadSpec(id="lc-32k-128", kind="long_context", params={"prefill": 32768, "decode": 128, "concurrency": 1})
    argv = argv_for(eng, lc, tmp_path)
    mml = int(flag_value(argv, "--max-model-len"))
    assert int(flag_value(argv, "--total-pages")) * 32 >= mml
    eng.recipe["total_pages"] = 1024
    assert int(flag_value(argv_for(eng, lc, tmp_path), "--total-pages")) * 32 >= mml
    eng.recipe["total_pages"] = 4096
    assert flag_value(argv_for(eng, lc, tmp_path), "--total-pages") == "4096"
    eng.recipe["total_pages"] = 1024
    assert flag_value(argv_for(eng, MAC_WORKLOADS["c32"], tmp_path), "--total-pages") == "1024"
    eng.recipe.pop("total_pages")
    assert "--total-pages" not in argv_for(eng, MAC_WORKLOADS["c32"], tmp_path)


def test_a_pie_that_sizes_its_pool_in_bytes_gets_no_page_count(tmp_path, monkeypatch):
    eng = mac_make(PieEngine)
    monkeypatch.setattr(PieEngine, "_bench_has", lambda self, flag: True)
    eng.recipe["total_pages"] = 1024
    argv = argv_for(eng, MAC_WORKLOADS["c32"], tmp_path)
    assert "--total-pages" not in argv
    assert flag_value(argv, "--gpu-mem-util") == "0.9"
    assert "--device-kv-budget" not in argv
    eng.recipe["device_kv_budget"] = "8GiB"
    assert flag_value(argv_for(eng, MAC_WORKLOADS["c32"], tmp_path), "--device-kv-budget") == "8GiB"


def test_pie_cuda_card_cap_never_widens_a_narrow_shape(tmp_path):
    eng = make(PieEngine, workload=WORKLOADS["c32"])
    eng.recipe["max_forward_requests"] = 384
    assert flag_value(argv_for(eng, WORKLOADS["c32"], tmp_path), "--max-forward-requests") == "32"
    eng.recipe["max_forward_requests"] = 16
    assert flag_value(argv_for(eng, WORKLOADS["c32"], tmp_path), "--max-forward-requests") == "16"


def test_pie_recipe_passthrough(tmp_path):
    eng = mac_make(PieEngine, art=mac_artifact(family="gemma4"))
    eng.recipe.update({"frame_submit_depth": 4, "max_forward_requests": 32, "engine_option": {"max_state_slots": 128, "sku": "$pie_sku"}})
    argv = argv_for(eng, MAC_WORKLOADS["c32"], tmp_path)
    assert flag_value(argv, "--frame-submit-depth") == "4"
    assert flag_value(argv, "--max-forward-requests") == "32"
    i = argv.index("--engine-option")
    assert argv[i + 1] == "max_state_slots=128"
    assert argv.count("--engine-option") == 1
    eng.artifact = mac_artifact(pie_sku="qwen3-8b-bf16-kv-bf16")
    argv = argv_for(eng, MAC_WORKLOADS["c32"], tmp_path)
    assert "sku=qwen3-8b-bf16-kv-bf16" in argv


def test_pie_serve_is_a_noop_on_metal(tmp_path):
    eng = mac_make(PieEngine)
    assert eng.serve(MAC_WORKLOADS["c32"], tmp_path / "serve.log", 5) is None
    assert eng.server_url is None and eng._server_proc is None


def test_advanced_shape_carries_temperature_and_seed(tmp_path):
    adv = WorkloadSpec(id="ob-advanced-500", kind="single_stream", params={"prompt": "p", "decode": 500, "temperature": 0.7, "top_p": 0.95, "seed": 42})
    assert flag_value(common_args_for(adv), "--temperature") == "0.7"
    assert flag_value(common_args_for(adv), "--top-p") == "0.95"
    argv = argv_for(mac_make(MlxlmEngine), adv, tmp_path)
    assert flag_value(argv, "--seed") == "42"
    assert "--seed" not in argv_for(mac_make(PieEngine), adv, tmp_path)


def test_top_p_defaults_to_one():
    plain = WorkloadSpec(id="ob-story-200", kind="single_stream", params={"prompt": "p", "decode": 200})
    assert flag_value(common_args_for(plain), "--top-p") == "1"


_MAC_CASES = []
for _mwl in MAC_WORKLOADS:
    _MAC_CASES += [
        ("pie", PieEngine, _mwl, {}),
        ("pie-gemma", PieEngine, _mwl, {"art": mac_artifact(family="gemma4")}),
        ("llamacpp", LlamacppEngine, _mwl, {"recipe_name": "competitive", "art": mac_artifact(base_model="Qwen/Qwen3-8B-GGUF", scheme="gguf_q4_k_m", source_format="gguf", gguf_file="Qwen3-8B-Q4_K_M.gguf")}),
        ("mlxlm", MlxlmEngine, _mwl, {"recipe_name": "competitive"}),
        ("splash", SplashEngine, _mwl, {"recipe_name": "competitive", "art": mac_artifact(source_format="splash")}),
    ]


@pytest.mark.parametrize("label,cls,wl,over", _MAC_CASES, ids=[f"{c[0]}/{c[2]}" for c in _MAC_CASES])
def test_every_emitted_flag_on_a_mac_is_parsed_by_the_script(label, cls, wl, over, tmp_path, hf_cache):
    workload = MAC_WORKLOADS[wl]
    eng = mac_make(cls, workload=workload, **over)
    argv = argv_for(eng, workload, tmp_path)
    accepted = argparse_flags(eng.script_path())
    assert accepted, f"no flags parsed from {eng.script_path()}"
    unknown = sorted(set(emitted_flags(argv)) - accepted)
    assert not unknown, f"{label}/{wl}: {eng.script_path().name} does not accept {unknown}"


def test_argparse_flags_of_the_openai_script():
    got = argparse_flags(OPENAI_SCRIPT)
    assert {"--model", "--max-tokens", "--concurrency", "--num-requests", "--requests", "--dump-all-token-ids"} <= got
    assert {"--url", "--api-model", "--extra-body", "--chat", "--flush-cache", "--no-flush-cache"} <= got


def test_openai_bench_builds_a_completion_or_a_chat_request():
    sys.path.insert(0, str(BENCHES))
    sys.path.insert(0, str(OPENAI_SCRIPT.parent))
    try:
        import openai_bench
    finally:
        sys.path.remove(str(BENCHES))
        sys.path.remove(str(OPENAI_SCRIPT.parent))
    base = ["latency", "--model", "X", "--url", "http://h", "--prompt", "p", "--max-tokens", "4", "--no-ignore-eos", "--warmup", "1",
            "--requests", "1", "--json-out", "f", "--dump-all-token-ids", "--no-think", "--system", "be brief"]
    args = openai_bench.build_parser().parse_args(base + ["--extra-body", '{"ignore_eos": true}'])
    body = openai_bench.payload_for(args, "<rendered>", 4)
    assert body["prompt"] == "<rendered>" and body["ignore_eos"] is True and body["stream"] is True and "messages" not in body
    args = openai_bench.build_parser().parse_args(base + ["--chat", "--api-model", "m"])
    body = openai_bench.payload_for(args, "hello", 4)
    assert body["messages"] == [{"role": "system", "content": "be brief"}, {"role": "user", "content": "hello"}]
    assert body["model"] == "m" and "prompt" not in body


def _openai_bench():
    sys.path.insert(0, str(BENCHES))
    sys.path.insert(0, str(OPENAI_SCRIPT.parent))
    try:
        import openai_bench
    finally:
        sys.path.remove(str(BENCHES))
        sys.path.remove(str(OPENAI_SCRIPT.parent))
    return openai_bench


def test_openai_bench_keeps_the_whole_batch_in_flight_on_a_small_mac(monkeypatch):
    import asyncio
    import threading

    ob = _openai_bench()
    monkeypatch.setattr(os, "cpu_count", lambda: 4)
    if hasattr(os, "process_cpu_count"):
        monkeypatch.setattr(os, "process_cpu_count", lambda: 4)
    monkeypatch.setattr(ob, "make_prompts", lambda args, n: ["p"] * n)
    monkeypatch.setattr(ob, "hf_chat_prompts_and_counts", lambda model, system, raw, think: (raw, [1] * len(raw)))
    monkeypatch.setattr(ob, "summarize", lambda **kw: kw)
    together = threading.Barrier(32)

    def run_one(args, endpoint, prompt, count, max_tokens, server, retries=None):
        together.wait(timeout=10)
        return ob.RequestResult(True, 0.0, 1, 1)

    monkeypatch.setattr(ob, "run_one", run_one)
    args = ob.build_parser().parse_args([
        "tput", "--model", "X", "--url", "http://h", "--prompt", "p", "--max-tokens", "4", "--no-ignore-eos",
        "--warmup", "0", "--num-requests", "64", "--concurrency", "32", "--json-out", "f", "--no-flush-cache",
    ])
    summary, results = asyncio.run(ob.run(args))
    assert all(r.ok for r in results) and summary["config"]["client_in_flight"] == 32


def test_openai_bench_single_stream_ttft_is_its_own_request(monkeypatch):
    import asyncio
    import time

    ob = _openai_bench()
    monkeypatch.setattr(ob, "make_prompts", lambda args, n: ["p"] * n)
    monkeypatch.setattr(ob, "hf_chat_prompts_and_counts", lambda model, system, raw, think: (raw, [1] * len(raw)))
    monkeypatch.setattr(ob, "summarize", lambda **kw: kw)

    def run_one(args, endpoint, prompt, count, max_tokens, server, retries=None):
        time.sleep(0.05)
        return ob.RequestResult(True, 0.05, 1, 1, ttft_s=0.01)

    monkeypatch.setattr(ob, "run_one", run_one)
    base = ["--model", "X", "--url", "http://h", "--prompt", "p", "--max-tokens", "4", "--no-ignore-eos", "--warmup", "0",
            "--json-out", "f", "--no-flush-cache"]
    _, results = asyncio.run(ob.run(ob.build_parser().parse_args(["latency", *base, "--requests", "4"])))
    assert [r.ttft_s for r in results] == [0.01] * 4
    _, results = asyncio.run(ob.run(ob.build_parser().parse_args(["tput", *base, "--num-requests", "4", "--concurrency", "1"])))
    assert max(r.ttft_s for r in results) > 0.1


def test_a_single_stream_request_starts_on_a_cool_mac(monkeypatch):
    import asyncio

    ob = _openai_bench()
    cool = ob.cool_before_request
    common = cool.__globals__
    monkeypatch.delenv("PIE_BENCH_SETTLE", raising=False)
    states = iter(["fair", "fair", "nominal"] + ["nominal"] * 10)
    monkeypatch.setitem(common, "mac_thermal_state", lambda: next(states))
    monkeypatch.setattr(common["time"], "sleep", lambda s: None)
    assert cool() >= 0 and next(states) == "nominal"
    monkeypatch.setenv("PIE_BENCH_SETTLE", "0")
    monkeypatch.setitem(common, "mac_thermal_state", lambda: "serious")
    assert cool() == 0.0
    monkeypatch.delenv("PIE_BENCH_SETTLE")
    calls = []
    monkeypatch.setattr(ob, "cool_before_request", lambda: calls.append(1) or 30.0)
    monkeypatch.setattr(ob, "make_prompts", lambda args, n: ["p"] * n)
    monkeypatch.setattr(ob, "hf_chat_prompts_and_counts", lambda model, system, raw, think: (raw, [1] * len(raw)))
    monkeypatch.setattr(ob, "summarize", lambda **kw: kw)
    monkeypatch.setattr(ob, "run_one", lambda *a, **k: ob.RequestResult(True, 0.01, 1, 1, ttft_s=0.01))
    base = ["--model", "X", "--url", "http://h", "--prompt", "p", "--max-tokens", "4", "--no-ignore-eos", "--warmup", "0",
            "--json-out", "f", "--no-flush-cache"]
    summary, results = asyncio.run(ob.run(ob.build_parser().parse_args(["latency", *base, "--requests", "3"])))
    assert len(calls) == 3 and summary["config"]["cooled_s"] == 90.0 and summary["wall_s"] < 1
    assert [r.ttft_s for r in results] == [0.01] * 3
    calls.clear()
    asyncio.run(ob.run(ob.build_parser().parse_args(["tput", *base, "--num-requests", "4", "--concurrency", "2"])))
    assert not calls


def test_openai_bench_sends_token_ids_so_the_bos_is_not_doubled(monkeypatch):
    import asyncio
    import types

    ob = _openai_bench()
    monkeypatch.setattr(ob, "make_prompts", lambda args, n: ["p"] * n)
    monkeypatch.setattr(ob, "hf_chat_prompts_and_counts", lambda model, system, raw, think: (["<bos>p"] * len(raw), [2] * len(raw)))
    monkeypatch.setattr(ob, "summarize", lambda **kw: kw)
    tok = types.SimpleNamespace(encode=lambda text, add_special_tokens: [2, 79] if not add_special_tokens else [2, 2, 79])
    monkeypatch.setitem(sys.modules, "transformers", types.SimpleNamespace(AutoTokenizer=types.SimpleNamespace(from_pretrained=lambda *a, **k: tok)))
    sent = []
    monkeypatch.setattr(ob, "run_one", lambda args, endpoint, prompt, count, max_tokens, server, retries=None: sent.append(prompt) or ob.RequestResult(True, 0.0, 1, 1))
    argv = ["tput", "--model", "X", "--url", "http://h", "--prompt", "p", "--max-tokens", "4", "--no-ignore-eos",
            "--warmup", "0", "--num-requests", "2", "--concurrency", "2", "--json-out", "f", "--no-flush-cache"]
    asyncio.run(ob.run(ob.build_parser().parse_args(argv + ["--token-ids"])))
    assert sent == [[2, 79], [2, 79]]
    sent.clear()
    asyncio.run(ob.run(ob.build_parser().parse_args(argv)))
    assert sent == ["<bos>p", "<bos>p"]


def test_openai_bench_resends_only_a_request_the_server_never_read(monkeypatch):
    import errno
    import urllib.error

    ob = _openai_bench()
    monkeypatch.setattr(ob.time, "sleep", lambda s: None)
    calls = []

    def flaky(url, payload, timeout, on_chunk):
        calls.append(1)
        if len(calls) <= 2:
            raise urllib.error.URLError(ConnectionResetError(errno.ECONNRESET, "Connection reset by peer"))

    monkeypatch.setattr(ob, "post_stream", flaky)
    retries: list[int] = []
    ob.post_stream_retrying("http://h", {}, 1.0, None, retries)
    assert len(calls) == 3 and len(retries) == 2

    def reset_mid_stream(url, payload, timeout, on_chunk):
        calls.append(1)
        raise ConnectionResetError(errno.ECONNRESET, "Connection reset by peer")

    calls.clear()
    monkeypatch.setattr(ob, "post_stream", reset_mid_stream)
    with pytest.raises(ConnectionResetError):
        ob.post_stream_retrying("http://h", {}, 1.0, None, retries)
    assert len(calls) == 1

    def always_reset(url, payload, timeout, on_chunk):
        calls.append(1)
        raise urllib.error.URLError(ConnectionResetError(errno.ECONNRESET, "Connection reset by peer"))

    calls.clear()
    monkeypatch.setattr(ob, "post_stream", always_reset)
    with pytest.raises(urllib.error.URLError):
        ob.post_stream_retrying("http://h", {}, 1.0, None, [])
    assert len(calls) == ob.CONNECT_TRIES


def test_a_shape_can_score_on_prefill(tmp_path):
    import sys

    from pie_bench.node.engines.base import Engine

    fake = tmp_path / "fake_bench.py"
    fake.write_text(
        "import json, sys\n"
        "out = sys.argv[sys.argv.index('--json-out') + 1]\n"
        "req = {'ok': True, 'latency_s': 0.2, 'ttft_s': 0.1, 'output_tokens': 1, 'prompt_tokens': 512, 'cached_prompt_tokens': 0}\n"
        "json.dump({'summary': {'wall_s': 0.2, 'output_tokens': 1, 'prompt_tokens': 512}, 'requests': [req]}, open(out, 'w'))\n"
    )
    root = tmp_path / "pie"

    class Stub(Engine):
        name = "pie"

        def script_path(self):
            return fake

        def default_python(self):
            return sys.executable

        def model_arg(self):
            return "m"

        def engine_args(self, workload):
            return []

    eng = Stub(pie_root=root, artifact=mac_artifact(), platform=mac_platform(), mode=Mode(), recipe={})
    pp = WorkloadSpec(id="lb-pp512", kind="single_stream", params={"prefill": 512, "decode": 1, "primary": "prefill_tok_s"})
    res = eng.run(pp, [], tmp_path / "out", 60)
    assert res.perf.primary == "prefill_tok_s" and res.perf.prefill_tok_s == 512 / 0.1


def test_lifeline_stops_its_child_when_the_parent_goes_away():
    import subprocess
    import sys
    import time

    sup = subprocess.Popen([sys.executable, "-m", "pie_bench.node.engines.lifeline", sys.executable, "-c", "import time; time.sleep(60)"],
                           stdin=subprocess.PIPE)
    time.sleep(0.5)
    sup.stdin.close()
    assert sup.wait(timeout=30) != 0 or sup.returncode == 0
    assert sup.poll() is not None


def test_an_idle_bench_is_stopped_as_a_hang():
    import subprocess
    import sys

    from pie_bench.node.engines.base import wait_with_stall_check

    idle = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
    rc, timed_out, stalled = wait_with_stall_check(idle, timeout_s=60, stall_s=2, poll_s=0.5, device_busy=lambda: False)
    assert stalled and not timed_out and idle.poll() is not None


def test_a_bench_waiting_on_a_busy_mac_gpu_is_left_to_finish():
    import subprocess
    import sys

    from pie_bench.node.engines.base import wait_with_stall_check

    waiting = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(4)"])
    rc, timed_out, stalled = wait_with_stall_check(waiting, timeout_s=60, stall_s=2, poll_s=0.5, device_busy=lambda: True)
    assert (rc, timed_out, stalled) == (0, False, False)


@pytest.mark.skipif(not Path("/proc").is_dir(), reason="the dump reads each thread from /proc (Linux nodes)")
def test_a_hang_leaves_a_dump_of_what_the_tree_was_doing():
    import subprocess
    import sys

    from pie_bench.node.engines.base import stall_dump, wait_with_stall_check

    idle = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
    dumps = []
    rc, timed_out, stalled = wait_with_stall_check(
        idle, timeout_s=60, stall_s=2, poll_s=0.5, on_stall=lambda pids: dumps.append(stall_dump(pids))
    )
    assert stalled and len(dumps) == 1
    assert f"== pid {idle.pid}:" in dumps[0] and "time.sleep" in dumps[0]
    assert "-- tid" in dumps[0] or "Thread" in dumps[0], "every thread of the stalled process is listed"


def test_a_busy_bench_is_left_to_finish():
    import subprocess
    import sys

    from pie_bench.node.engines.base import wait_with_stall_check

    busy = subprocess.Popen([sys.executable, "-c", "import time\nt = time.time()\nwhile time.time() - t < 4: pass"])
    rc, timed_out, stalled = wait_with_stall_check(busy, timeout_s=60, stall_s=2, poll_s=0.5)
    assert (rc, timed_out, stalled) == (0, False, False)


def test_pie_prefills_cold_when_its_bench_can_turn_the_prefix_cache_off(tmp_path, monkeypatch):
    for script, cold in (("p.add_argument('--no-prefix-cache')\n", True), ("# an older bench\n", False)):
        bench = tmp_path / str(cold)
        bench.mkdir()
        monkeypatch.setenv("PIE_BENCH_BENCH_DIR", str(bench))
        (bench / "bench_pie.py").write_text(script)
        eng = PieEngine(pie_root=tmp_path, artifact=artifact(), platform=platform(), mode=Mode(), recipe={})
        assert ("--no-prefix-cache" in argv_for(eng, WORKLOADS["c32"], tmp_path)) is cold


def test_pie_speculates_single_stream_and_the_recipe_can_force_it(tmp_path):
    single, conc = MAC_WORKLOADS["ss-128-64"], MAC_WORKLOADS["c32"]
    eng = mac_make(PieEngine, art=mac_artifact(pie_sku="qwen36-27b-dflash-u4g64-kv-bf16"))
    assert eng.speculates(single) and not eng.speculates(conc)
    assert flag_value(argv_for(eng, single, tmp_path), "--inferlet-dir").endswith("examples/dflash-speculative-bench")
    argv = argv_for(eng, conc, tmp_path)
    assert flag_value(argv, "--inferlet-dir").endswith("examples/text-completion-bench")
    assert "--no-system-speculation" in argv
    eng.recipe["speculation"] = "on"
    assert eng.speculates(conc)
    eng.recipe["speculation"] = "off"
    assert not eng.speculates(single)
    eng = mac_make(PieEngine, art=mac_artifact())
    assert not eng.speculates(single)


def test_pie_rows_that_do_not_speculate_serve_the_plain_deployment(tmp_path):
    single, conc = MAC_WORKLOADS["ss-128-64"], MAC_WORKLOADS["c32"]
    eng = mac_make(PieEngine, art=mac_artifact(pie_sku="gemma4-26b-a4b-dflash-u4g64-kv-bf16"))
    eng.recipe["snapshot_dir"], eng.recipe["plain_snapshot_dir"] = "/a/dflash.zt", "/a-plain/plain.zt"
    assert flag_value(argv_for(eng, single, tmp_path), "--model") == "/a/dflash.zt"
    assert flag_value(argv_for(eng, conc, tmp_path), "--model") == "/a-plain/plain.zt"


def test_pie_in_served_mode_has_its_server_watched(tmp_path):
    import subprocess
    import sys

    eng = PieEngine(pie_root=tmp_path, artifact=artifact(), platform=platform(), mode=Mode(), recipe={})
    assert eng.watch_pids() == []
    server = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
    try:
        eng._server_proc = server
        assert eng.watch_pids() == [server.pid], "the stall watchdog must count the engine's CPU, not only the client's"
    finally:
        server.kill()
        server.wait()
    assert eng.watch_pids() == [], "a server that exited is not watched"


def test_a_dflash2_row_drafts_at_its_trained_block(tmp_path):
    single, conc = MAC_WORKLOADS["ss-128-64"], MAC_WORKLOADS["c32"]
    eng = mac_make(PieEngine, art=mac_artifact(pie_sku="qwen38-27b-dflash2-u4g64-kv-bf16"))
    argv = argv_for(eng, single, tmp_path)
    assert "block=8" in argv and "no_mask=true" in argv
    assert "block=8" not in argv_for(eng, conc, tmp_path)
    v1 = mac_make(PieEngine, art=mac_artifact(pie_sku="qwen36-27b-dflash-u4g64-kv-bf16"))
    assert "block=8" not in argv_for(v1, single, tmp_path)


def test_a_dflash2_row_of_a_moe_target_verifies_what_its_draft_pays_for(tmp_path):
    single = MAC_WORKLOADS["ss-128-64"]
    moe = mac_make(PieEngine, art=mac_artifact(family="qwen3_6_moe", pie_sku="qwen36-35b-a3b-dflash2-u4g64-kv-bf16"))
    argv = argv_for(moe, single, tmp_path)
    assert "verify_budget=true" in argv and "verify_rows=8" not in argv
    dense = mac_make(PieEngine, art=mac_artifact(pie_sku="qwen38-27b-dflash2-u4g64-kv-bf16"))
    argv = argv_for(dense, single, tmp_path)
    assert "verify_rows=8" in argv and "priced=false" in argv and "verify_budget=true" not in argv


def test_mlxlm_blocks_every_special_token(tmp_path, monkeypatch):
    from pie_bench.node.engines import served

    snap = tmp_path / "snap"
    snap.mkdir()
    (snap / "tokenizer.json").write_text(json.dumps({"added_tokens": [{"id": 248046, "content": "<|im_end|>"}, {"id": 248069, "content": "</think>"}]}))
    monkeypatch.setattr("pie_bench.node.engines.shape.hf_snapshot_dir", lambda *a, **k: snap)
    from types import SimpleNamespace
    eng = SimpleNamespace(artifact=SimpleNamespace(base_model="m", revision=None))
    assert served.ServedEngine.stop_token_bias(eng) == {"248046": -100.0, "248069": -100.0}


def test_vllm_single_stream_streams_one_request_at_a_time(tmp_path):
    argv = make(VllmEngine).build_argv(WORKLOADS["ss-128-64"], [], tmp_path / "o.json")
    assert argv[2] == "tput" and "--report-timing" in argv
    assert argv[argv.index("--concurrency") + 1] == "1" and "--requests" not in argv
    assert make(VllmEngine).build_argv(WORKLOADS["c32"], [], tmp_path / "o.json")[2] == "tput"


def test_vllm_on_the_tpu_runs_its_tpu_build(tmp_path, monkeypatch):
    from pie_bench.node import baselines

    monkeypatch.setenv("PIE_BENCH_CACHE", str(tmp_path))
    monkeypatch.delenv("VLLM_PY", raising=False)
    tpu = platform(Backend.XLA, "trillium", count=1)
    venv = baselines.venv_dir("vllm", "0.30.0", backend="xla")
    assert venv.name == "venv-vllm-tpu-0.30.0" and baselines.venv_dir("vllm", "0.30.0").name == "venv-vllm-0.30.0"
    assert baselines.BACKEND_SPECS[("vllm", "xla")]("0.30.0") == ["vllm-tpu==0.30.0"]
    (venv / "bin").mkdir(parents=True)
    (venv / ".ok").write_text("0.30.0\n")
    raw = WorkloadSpec(id="raw-512-256", kind="single_stream", params={"prefill": 512, "decode": 256, "requests": 6})
    recipe = load_recipe("vllm", "competitive", tpu, raw, family="qwen3_5")
    eng = VllmEngine(pie_root=PIE_ROOT, artifact=artifact(), platform=tpu, mode=Mode(), recipe={**recipe, "pin": "0.30.0"})
    assert eng.python == str(venv / "bin" / "python")
    argv = eng.build_argv(raw, [], tmp_path / "o.json")
    assert "--attention-backend" not in argv and argv[argv.index("--cpu-affinity") + 1] == "none"
    assert argv[argv.index("--max-model-len") + 1] == str(max_model_len_for(raw))
    assert argv[2] == "tput" and argv[argv.index("--concurrency") + 1] == "1"


def test_the_tpu_runs_pie_vllm_and_sglang_raw_prefill_and_batch_rows():
    from pie_bench.plan.matrix import Matrix
    from pie_bench.schema import Tier

    m = Matrix.load(MATRIX)
    cells = [c for c in m.runnable(Tier.WEEKLY, m.expand(platforms=["tpu-v6e-1"])) if c.platform.id == "tpu-v6e-1"]
    tpu = {(str(c.engine), c.artifact.id, c.workload.id) for c in cells}
    assert ("vllm", "qwen3.5-0.8b-bf16", "raw-512-256") in tpu and ("pie", "qwen3.5-0.8b-xla", "raw-512-256") in tpu
    assert {e for e, _, _ in tpu} == {"pie", "vllm", "sglang"}
    arms = {(e, a) for e, a, _ in tpu}
    assert all((e, a, "raw-512-256") in tpu and {(e, a, "pf256-512"), (e, a, "pf32-512")} & tpu for e, a in arms)
    assert {a for _, a, w in tpu if w == "pf32-512"} == {"qwen3.8-27b-mini20"}
    assert {w for e, a, w in tpu if a != "qwen3.5-0.8b-xla"} <= {"raw-512-256", "pf256-512", "pf32-512", "c32", "c64", "c256"}
    more = {"qwen3-0.6b-tpu", "gemma-4-e2b-tpu", "gemma-4-e4b-tpu", "gemma-4-12b-tpu", "gpt-oss-20b-tpu"}
    assert more <= {a for e, a in arms if e == "vllm"} and more <= {a for e, a in arms if e == "pie"}
    assert {a for e, a in arms if e == "sglang"} & more == {"qwen3-0.6b-tpu"}
    assert {c.engine_version for c in cells if str(c.engine) == "sglang"} == {m.engines["sglang"].backend_pins["xla"]}


def test_sglang_on_the_tpu_serves_its_jax_build(tmp_path, monkeypatch):
    from pie_bench.node import baselines
    from pie_bench.node.engines.sglang import SglangTpuEngine

    monkeypatch.setenv("PIE_BENCH_CACHE", str(tmp_path))
    monkeypatch.delenv("SGLANG_PY", raising=False)
    tpu = platform(Backend.XLA, "trillium", count=1)
    assert baselines.BACKEND_SPECS[("sglang", "xla")]("0.1.0rc0") == ["sglang-jax[tpu]==0.1.0rc0"]
    venv = baselines.venv_dir("sglang", "0.1.0rc0", backend="xla")
    assert venv.name == "venv-sglang-tpu-0.1.0rc0"
    (venv / "bin").mkdir(parents=True)
    (venv / ".ok").write_text("0.1.0rc0\n")
    raw = WorkloadSpec(id="raw-512-256", kind="single_stream", params={"prefill": 512, "decode": 256, "requests": 6})
    recipe = load_recipe("sglang", "competitive", tpu, raw, family="qwen3_5")
    eng = SglangEngine(pie_root=PIE_ROOT, artifact=artifact(), platform=tpu, mode=Mode(), recipe={**recipe, "pin": "0.1.0rc0"})
    assert isinstance(eng, SglangTpuEngine) and eng.recipe["pin"] == "0.1.0rc0"
    cmd = eng.server_cmd(8000, 1, max_model_len_for(raw))
    assert cmd[:3] == [str(venv / "bin" / "python"), "-m", "sgl_jax.launch_server"]
    assert cmd[cmd.index("--device") + 1] == "tpu" and "--disable-radix-cache" in cmd
    assert cmd[cmd.index("--context-length") + 1] == str(max_model_len_for(raw))
    assert type(SglangEngine(pie_root=PIE_ROOT, artifact=artifact(), platform=platform(), mode=Mode(), recipe=recipe)) is SglangEngine


def test_a_queued_single_stream_request_starts_when_the_one_before_it_ends():
    from pie_bench.node.engines.base import serial_clock

    rows = [{"ok": True, "client_send_s": 0.0, "client_return_s": 9.9, "ttft_s": 0.1, "latency_s": 9.9},
            {"ok": True, "client_send_s": 0.0, "client_return_s": 19.8, "ttft_s": 10.0, "latency_s": 19.8}]
    fixed = serial_clock(rows)
    assert abs(fixed[1]["ttft_s"] - 0.1) < 1e-9 and abs(fixed[1]["latency_s"] - 9.9) < 1e-9
    sequential = [{**rows[0]}, {**rows[1], "client_send_s": 9.95, "ttft_s": 0.1, "latency_s": 9.85}]
    assert serial_clock(sequential) == sequential


def test_each_round_gets_its_own_cold_prompts(tmp_path):
    import json as _json

    eng = make(VllmEngine)
    wl = WORKLOADS["ss-128-64"].model_copy(update={"params": {**WORKLOADS["ss-128-64"].params, "cold_cache": True}})
    lists = []
    for r in ("r0", "r1", "r2"):
        (tmp_path / r).mkdir()
        eng.cold_common_args(wl, [], tmp_path / r)
        lists.append(_json.loads((tmp_path / r / "cold_prompts.json").read_text()))
    tags = [{p.split("]")[0] for p in ps} for ps in lists]
    assert not (tags[0] & tags[1]) and not (tags[1] & tags[2]) and not (tags[0] & tags[2])


def test_a_16_gb_mac_gets_a_smaller_forward_budget(tmp_path):
    raw = WorkloadSpec(id="raw-512-256", kind="single_stream", params={"prefill": 512, "decode": 256, "requests": 6})

    def args(memory, recipe=None):
        mac = platform(Backend.METAL, "apple9", count=1).model_copy(update={"memory_gib": memory})
        eng = PieEngine(pie_root=PIE_ROOT, artifact=artifact(), platform=mac, mode=Mode(), recipe=recipe or {})
        a = eng.engine_args(raw)
        return a[a.index("--max-forward-tokens") + 1] if "--max-forward-tokens" in a else None

    assert args(16.0) == "2048" and args(48.0) is None
    assert args(16.0, {"max_forward_tokens": 4096}) == "4096"


def test_trtllm_serves_the_checkpoint_with_graphs_to_the_batch_and_no_block_reuse(tmp_path):
    import yaml

    from pie_bench.node.engines.trtllm import TrtllmEngine

    eng = make(TrtllmEngine, plat=platform(count=1))
    eng.recipe["options_dir"] = str(tmp_path)
    cmd = eng.server_cmd(8123, 32, 768)
    assert cmd[1].endswith("trtllm_bench.py") and cmd[2] == "serve"
    assert cmd[cmd.index("--max-batch-size") + 1] == "32" and cmd[cmd.index("--max-seq-len") + 1] == "768"
    opts = yaml.safe_load(Path(cmd[cmd.index("--options") + 1]).read_text())
    assert opts["cuda_graph_config"] == {"enable_padding": True, "max_batch_size": 32}
    assert opts["kv_cache_config"]["enable_block_reuse"] is False and opts["kv_cache_config"]["dtype"] == "auto"
    assert "enable_chunked_prefill" not in opts
    assert eng.server_cmd(8123, 1, 32768) and eng.llm_api_options(1, 32768)["enable_chunked_prefill"] is True
    argv = argv_for(eng, WORKLOADS["c32"], tmp_path)
    body = json.loads(flag_value(argv, "--extra-body"))
    assert body == {"add_special_tokens": False, "ignore_eos": True} and "--ignore-eos" in argv
    assert argv[1].endswith("trtllm_bench.py") and "--url" in argv


def test_trtllm_takes_the_same_share_of_the_card_as_the_other_engines():
    from pie_bench.node.engines.trtllm import TRTLLM_RUNTIME_GIB, TrtllmEngine

    eng = make(TrtllmEngine, plat=platform(count=1).model_copy(update={"memory_gib": 80}), art=artifact(expected_gib=50.0))
    f = eng.kv_free_mem_fraction()
    left = 80 - 50 - TRTLLM_RUNTIME_GIB
    assert abs(50 + TRTLLM_RUNTIME_GIB + f * left - 0.9 * 80) < 0.05
    assert eng.llm_api_options(32, 768)["kv_cache_config"]["free_gpu_memory_fraction"] == f
    two = make(TrtllmEngine, plat=platform(count=2).model_copy(update={"memory_gib": 160}), art=artifact(expected_gib=100.0),
               mode=Mode(tp=2))
    assert two.kv_free_mem_fraction() == f
    big = make(TrtllmEngine, plat=platform(count=1).model_copy(update={"memory_gib": 180}), art=artifact(expected_gib=2.0))
    big.recipe["gpu_mem_util"] = 0.95
    assert big.kv_free_mem_fraction() == 0.9
    eng.recipe["kv_free_mem_fraction"] = 0.6
    assert eng.kv_free_mem_fraction() == 0.6
    assert make(TrtllmEngine, plat=platform(count=1), art=artifact(expected_gib=None)).kv_free_mem_fraction() is None


def test_trtllm_runs_on_nvidia_gpus_only():
    from pie_bench.plan.matrix import Matrix

    m = Matrix.load(MATRIX)
    cells = [c for c in m.expand(platforms={"l40s-x1", "tpu-v6e-1", "mi300x-x1"}, artifacts={"qwen3.5-0.8b-bf16"}) if str(c.engine) == "trtllm"]
    assert cells and {c.platform.id for c in cells} == {"l40s-x1"}


def test_atom_serves_its_openai_server_at_the_shape_with_exact_lengths(tmp_path, monkeypatch):
    from pie_bench.node.engines.atom import AtomEngine

    monkeypatch.setenv("ATOM_PY", "/opt/venv/bin/python3")
    assert get_engine("atom") is AtomEngine
    eng = make(AtomEngine, plat=platform(Backend.ROCM, "cdna3", count=1))
    cmd = eng.server_cmd(8127, 32, 2048)
    assert cmd[:3] == ["/opt/venv/bin/python3", "-m", "atom.entrypoints.openai_server"]
    assert flag_value(cmd, "--server-port") == "8127" and flag_value(cmd, "--max-num-seqs") == "32" and flag_value(cmd, "--max-model-len") == "2048"
    assert flag_value(cmd, "--kv_cache_dtype") == "bf16" and flag_value(cmd, "--gpu-memory-utilization") == "0.9"
    assert "--no-enable_prefix_caching" in cmd and "--cudagraph-capture-sizes" not in cmd and "--index-cache-dtype" not in cmd
    wide = eng.server_cmd(8127, 1024, 2048)
    assert flag_value(wide, "--cudagraph-capture-sizes") == "[1,2,3,4,5,6,7,8,16,32,48,64,128,256,512,1024]"
    v4 = make(AtomEngine, plat=platform(Backend.ROCM, "cdna4", count=1), art=artifact(family="deepseek_v4"))
    assert flag_value(v4.server_cmd(8127, 1, 2048), "--index-cache-dtype") == "fp8"
    argv = argv_for(eng, WORKLOADS["c32"], tmp_path)
    assert json.loads(flag_value(argv, "--extra-body")) == {"ignore_eos": True} and "--ignore-eos" in argv and "--token-ids" in argv
    assert eng.server_env()["HOME"].endswith("/atom-home/qwen3-8b-bf16")


def test_atom_runs_on_amd_gpus_only():
    from pie_bench.plan.matrix import Matrix

    m = Matrix.load(MATRIX)
    cells = [c for c in m.expand(platforms={"l40s-x1", "tpu-v6e-1", "mi300x-x1", "mi355x-x1"}, artifacts={"qwen3.5-0.8b-bf16"}) if str(c.engine) == "atom"]
    assert cells and {c.platform.id for c in cells} == {"mi300x-x1", "mi355x-x1"}


def _browser_stubs(monkeypatch, tmp_path):
    from pie_bench.node.engines import browser

    monkeypatch.setattr(browser, "ensure_harness", lambda log=print: "/usr/bin/node")
    monkeypatch.setenv("PIE_BENCH_CACHE", str(tmp_path / "cache"))
    return browser


def _options(cmd: list[str]) -> dict:
    return json.loads(flag_value(cmd, "--options"))


def test_pie_on_a_webgpu_platform_is_its_browser_runtime():
    from pie_bench.node.engines.browser import LlamacppWebgpuEngine, PieWebEngine, WebllmEngine

    assert get_engine("pie", "webgpu") is PieWebEngine
    assert get_engine("pie", "cuda") is PieEngine and get_engine("pie") is PieEngine
    assert get_engine("webllm") is WebllmEngine and get_engine("llamacpp-webgpu") is LlamacppWebgpuEngine


def test_webllm_serves_the_mlc_build_and_its_library_from_disk(monkeypatch, tmp_path):
    browser = _browser_stubs(monkeypatch, tmp_path)
    snap = tmp_path / "snap"
    snap.mkdir()
    (snap / "mlc-chat-config.json").write_text("{}")
    lib = tmp_path / "lib.wasm"
    lib.write_text("wasm")
    art = artifact(id="qwen3.5-4b-webllm", base_model="mlc-ai/Qwen3.5-4B-q4f16_1-MLC", family="qwen3_5", scheme="mlc_q4f16_1",
                   source_format="mlc", tokenizer_from="mlx-community/Qwen3.5-4B-4bit")
    eng = make(browser.WebllmEngine, plat=platform(backend=Backend.WEBGPU, count=1), art=art)
    eng.recipe["snapshot_dir"] = str(snap)
    monkeypatch.setattr(browser.WebllmEngine, "model_lib", lambda self: lib)
    cmd = eng.server_cmd(8124, 1, 1024)
    assert cmd[1].endswith("bridge.mjs") and flag_value(cmd, "--engine") == "webllm"
    files = Path(flag_value(cmd, "--files"))
    assert (files / "model" / "resolve" / "main").resolve() == snap.resolve() and (files / "lib.wasm").resolve() == lib.resolve()
    assert _options(cmd)["overrides"]["context_window_size"] == 4096 and eng.model_arg() == "mlx-community/Qwen3.5-4B-4bit"
    argv = argv_for(eng, WORKLOADS["ss-128-64"], tmp_path)
    assert argv[1].endswith("browser_bench.py") and "--ignore-eos" in argv and flag_value(argv, "--engine-name") == "webllm"


def test_llamacpp_webgpu_gets_a_slot_per_request_and_the_whole_context_each(monkeypatch, tmp_path):
    browser = _browser_stubs(monkeypatch, tmp_path)
    gguf = tmp_path / "m.gguf"
    gguf.write_text("gguf")
    art = artifact(id="qwen3.5-4b-llamacpp", base_model="unsloth/Qwen3.5-4B-GGUF", family="qwen3_5", scheme="gguf_q4_k_m",
                   source_format="gguf", gguf_file="m.gguf", tokenizer_from="mlx-community/Qwen3.5-4B-4bit")
    eng = make(browser.LlamacppWebgpuEngine, plat=platform(backend=Backend.WEBGPU, count=1), art=art)
    monkeypatch.setattr(browser.LlamacppEngine, "gguf_path", lambda self: gguf)
    monkeypatch.setattr(browser.LlamacppWebgpuEngine, "build_dir", lambda self: tmp_path)
    o = _options(eng.server_cmd(8125, 32, 768))
    assert o["n_slots"] == 32 and o["n_ctx"] == 32 * 768 and o["n_batch"] == 2048 and o["n_ubatch"] == 512
    assert _options(eng.server_cmd(8125, 32, 2048))["n_ctx"] == 32 * 1024


def test_pie_in_the_tab_sizes_its_pool_and_slots_to_the_shape(monkeypatch, tmp_path):
    browser = _browser_stubs(monkeypatch, tmp_path)
    zt = tmp_path / "a.qwen35-d4b-u4g64-kv-bf16.wgpu.zt"
    zt.write_bytes(b"\0" * 1024)
    dist, wasm = tmp_path / "dist", tmp_path / "tcb.wasm"
    dist.mkdir()
    (dist / "pie.mjs").write_text("")
    wasm.write_text("")
    art = artifact(id="qwen3.5-4b-mlx4", base_model="mlx-community/Qwen3.5-4B-4bit", family="qwen3_5", scheme="affine_u4_g64", source_format="mlx")
    plat = platform(backend=Backend.WEBGPU, count=1)
    eng = make(browser.PieWebEngine, plat=plat, art=art, recipe_name="default")
    eng.recipe["snapshot_dir"] = str(zt)
    monkeypatch.setattr(browser.PieWebEngine, "web_dist", lambda self: dist)
    monkeypatch.setattr(browser.PieWebEngine, "inferlet", lambda self: wasm)
    o = _options(eng.server_cmd(8126, 32, 768))
    assert "max_state_slots = 32\n" in o["config"] and "max_forward_requests = 32\n" in o["config"] and "max_model_len = 768\n" in o["config"]
    assert "max_forward_tokens = 512\n" in o["config"]


def test_the_webgpu_platforms_run_the_browser_engines_only():
    from pie_bench.plan.matrix import Matrix
    from pie_bench.schema import Tier

    m = Matrix.load(MATRIX)
    cells = m.runnable(Tier.TARGETED, m.expand(platforms={"web-rtx4090"}))
    engines = {str(c.engine) for c in cells}
    assert engines == {"pie", "webllm", "llamacpp-webgpu"}
    assert {c.workload.id for c in cells if str(c.engine) == "webllm"} == {"raw-512-256"}
    assert len({c.artifact.id for c in cells if str(c.engine) == "pie"}) == 12


def test_every_engine_resolves_without_importing_its_module_first():
    import subprocess
    import sys

    code = "from pie_bench.node.engines import get_engine; [get_engine(e, 'metal') for e in ('pie', 'llamacpp', 'mlxlm', 'splash', 'vllm', 'sglang')]"
    assert subprocess.run([sys.executable, "-c", code]).returncode == 0
