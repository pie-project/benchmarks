"""SGLang adapter: drives ``scripts/bench/sglang_bench.py``.

The one flag that must never be left to the engine's default is
``--sglang-cuda-graph-max-bs``: SGLang derives its graph ceiling from a
hardware-tier heuristic and a decode batch beyond it silently runs eager
(4,642 vs 14,042 tok/s on the same cell). It is always set to the shape's
concurrency, the way vLLM captures up to ``max_num_seqs``.
"""

from __future__ import annotations

import os
import subprocess

from pie_evals.schema import EngineName, WorkloadSpec

from .base import Engine, register
from .served import ServedEngine
from .shape import max_model_len_for, workload_concurrency


@register
class SglangEngine(Engine):
    name = EngineName.SGLANG
    script = "scripts/bench/sglang_bench.py"
    #: the runner image has no nvcc: DeepGEMM's JIT (gemma / gpt-oss on
    #: Blackwell, nightly 35921789513) would abort every cell; the FlashInfer
    #: kernels come precompiled (baselines.ensure_flashinfer_aot).
    env_defaults = {"SGL_ENABLE_JIT_DEEPGEMM": "0", "SGLANG_ENABLE_JIT_DEEPGEMM": "0"}  # 0.5.20 reads the second, warns on the first

    def __new__(cls, *args, **kwargs):
        # the TPU build (sglang-jax) has no offline engine sglang_bench.py can drive: it is served
        platform = kwargs.get("platform")
        if cls is SglangEngine and platform is not None and str(platform.backend) == "xla":
            return SglangTpuEngine(*args, **kwargs)  # not an SglangEngine: Python skips __init__ on the return
        return super().__new__(cls)

    def default_env(self) -> dict[str, str]:
        # sgl_kernel_jit builds land on the volume instead of the pod's
        # container disk, so a kernel compiles once per (version, arch)
        from pie_evals.node.baselines import cache_root

        jit = cache_root() / "jit"
        return {
            "SGLANG_JIT_CACHE_DIR": str(jit / "sglang"),
            "TRITON_CACHE_DIR": str(jit / "triton"),
            "TORCHINDUCTOR_CACHE_DIR": str(jit / "inductor"),
            **self.nccl_env(),
        }

    def default_python(self) -> str:
        if os.environ.get("SGLANG_PY"):
            return os.environ["SGLANG_PY"]
        from pie_evals.node.baselines import baseline_python

        pin = self.recipe.get("pin")
        py = baseline_python("sglang", pin) if pin else None
        return str(py) if py else "/root/.venv/sglang/bin/python"

    def model_arg(self) -> str:
        # The runner resolves the checkpoint (a miniature lives under a snapshot
        # dir with no refs/main, so an HF id would not find it) and passes the
        # path through the recipe; a bare HF id is the fallback.
        return str(self.recipe.get("snapshot_dir") or self.artifact.base_model)

    def engine_args(self, workload: WorkloadSpec) -> list[str]:
        r = self.recipe
        args: list[str] = ["--tp-size", str(max(1, int(self.mode.tp)))]
        gmu = r.get("gpu_mem_util", 0.90)
        card = float(self.platform.memory_gib or 0.0) / max(1, int(self.mode.tp))
        if gmu is not None:
            # SGLang counts the loaded weights against mem_fraction_static and refuses when
            # they leave no KV room under it (kimi-k3 mini, 18.4 GiB on a 32 GB 5090: "raise
            # --mem-fraction-static above 0.935"); a heavy checkpoint gets the fraction it needs
            weights = float(self.artifact.expected_gib or 0.0)
            if weights and card and weights / card > 0.5:
                gmu = max(float(gmu), 0.95)
            elif self.artifact.family == "kimi_k3":
                # past the static pool SGLang keeps only graphs and activations; Kimi-K3's MoE
                # prefill wanted 1.5 GiB more than 0.85 left on 80/96 GB cards (nightly 36103857543)
                # and OOMs from c32 at 0.9 on a 48 GB L40S (36226636518), while the L40S at 0.75
                # has no KV left beside a 256-wide graph (36212036845) and at 0.82 kv-oversub OOMs in prefill (36264810212)
                wide = card < 80 and workload_concurrency(workload) >= 128
                gmu = min(float(gmu), 0.79 if wide else 0.75)
            args += ["--gpu-mem-util", str(gmu)]  # -> mem_fraction_static
        graph_bs = r.get("cuda_graph_max_bs")
        if graph_bs is None:
            graph_bs = workload_concurrency(workload)
        if gmu is not None and card >= 80 and int(graph_bs) >= 64:
            # mem_fraction_static leaves the graphs and activations whatever is past it; on a
            # 96 GB card at 0.9 that was 9.5 GiB, and kimi-k3 mini at c64 wanted 1.2 GiB more
            # (nightly 36089882075 s04: OOM at c64, c256, mixed, prefix; c32 served)
            capped = 0.80 if int(graph_bs) >= 256 else 0.85
            if float(gmu) > capped:
                args[-1] = str(capped)
        args += ["--max-model-len", str(max_model_len_for(workload))]  # -> context_length
        args += ["--sglang-cuda-graph-max-bs", str(int(graph_bs))]

        if r.get("report_timing", True):
            args += ["--report-timing"]
        if r.get("attention_backend"):
            args += ["--sglang-attention-backend", str(r["attention_backend"])]
        if r.get("sampling_backend"):
            args += ["--sglang-sampling-backend", str(r["sampling_backend"])]
        if r.get("page_size"):
            args += ["--sglang-page-size", str(int(r["page_size"]))]
        if r.get("max_total_tokens"):
            args += ["--sglang-max-total-tokens", str(int(r["max_total_tokens"]))]
        if r.get("disable_cuda_graph"):
            args.append("--sglang-disable-cuda-graph")
        if r.get("disable_piecewise_cuda_graph"):
            args.append("--sglang-disable-piecewise-cuda-graph")

        hybrid_swa = r.get("disable_hybrid_swa_memory")
        if hybrid_swa is None:
            # Sliding-window families (Gemma): SGLang's hybrid sizer derives a
            # budget from the SWA layers and then refuses to start because the
            # full-attention layers cannot hold it (common.py's flag help).
            # One uniform pool is what vLLM does, so it is the comparable
            # policy as well as the one that runs.
            hybrid_swa = self.artifact.family.startswith("gemma")
        if hybrid_swa:
            args.append("--sglang-disable-hybrid-swa-memory")

        # TODO(pie/benches): sglang_bench.py hard-codes disable_radix_cache=True
        # and has no flag to enable it, so the prefix_shared shape cannot hand
        # SGLang its prefix cache (recipe knob `radix_cache` is recorded only).
        # TODO(pie/benches): no --sglang-enable-torch-compile flag (recipe knob
        # `torch_compile` is recorded only).

        if r.get("cpu_affinity"):
            args += ["--cpu-affinity", str(r["cpu_affinity"])]
        if r.get("request_timeout"):
            args += ["--request-timeout", str(r["request_timeout"])]
        return args

    def version(self) -> str:
        try:
            out = subprocess.run(
                [self.python, "-c", "import sglang; print(sglang.__version__)"],
                capture_output=True, text=True, timeout=120, check=False,
            )
            v = out.stdout.strip().splitlines()
            return v[-1] if out.returncode == 0 and v else "unknown"
        except Exception:
            return "unknown"

    def leftover_process_names(self) -> list[str]:
        return ["sglang::scheduler", "sglang::detokenizer", "sglang::scheduler_TP0"]


class SglangTpuEngine(ServedEngine):
    """SGLang's TPU build: ``python -m sgl_jax.launch_server`` (sgl-project/sglang-jax, at the
    engines.yaml backend pin) on the bf16 checkpoint, streamed through ``openai_bench.py`` the way
    llama.cpp and mlx-lm are. Its warmup and JIT precompile run before the server answers."""

    name = EngineName.SGLANG
    health_path = "/health"
    exact_length = "ignore_eos"

    def server_python(self) -> str:
        if os.environ.get("SGLANG_PY"):
            return os.environ["SGLANG_PY"]
        from pie_evals.node.baselines import baseline_python

        pin = self.recipe.get("pin")
        py = baseline_python("sglang", pin, backend="xla") if pin else None
        return str(py) if py else "python3"

    def model_arg(self) -> str:
        return str(self.recipe.get("snapshot_dir") or self.artifact.base_model)

    def server_cmd(self, port: int, slots: int, context: int) -> list[str]:
        r = self.recipe
        cmd = [
            self.server_python(), "-m", "sgl_jax.launch_server", "--model-path", self.model_arg(),
            "--host", "127.0.0.1", "--port", str(port), "--device", "tpu", "--tp-size", str(max(1, int(self.mode.tp))),
            "--context-length", str(context), "--max-running-requests", str(slots),
            # a cold prompt every request, as on every other engine
            "--disable-radix-cache", "--log-level", "warning",
        ]
        if r.get("gpu_mem_util") is not None:
            cmd += ["--mem-fraction-static", str(r["gpu_mem_util"])]
        if r.get("page_size"):
            cmd += ["--page-size", str(int(r["page_size"]))]
        return cmd

    def version(self) -> str:
        try:
            out = subprocess.run(
                [self.server_python(), "-c", "import sgl_jax; print(sgl_jax.__version__)"],
                capture_output=True, text=True, timeout=120, check=False,
            )
            v = out.stdout.strip().splitlines()
            return v[-1] if out.returncode == 0 and v else "unknown"
        except Exception:
            return "unknown"

    def leftover_process_names(self) -> list[str]:
        return ["sglang::scheduler", "sglang::detokenizer", "sgl_jax"]
