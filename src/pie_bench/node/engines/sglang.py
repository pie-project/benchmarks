from __future__ import annotations

import os
import subprocess

from pie_bench.schema import EngineName, WorkloadSpec

from .base import Engine, register
from .served import ServedEngine
from .shape import max_model_len_for, workload_concurrency


@register
class SglangEngine(Engine):
    name = EngineName.SGLANG
    script = "sglang_bench.py"
    env_defaults = {"SGL_ENABLE_JIT_DEEPGEMM": "0", "SGLANG_ENABLE_JIT_DEEPGEMM": "0"}

    def __new__(cls, *args, **kwargs):
        platform = kwargs.get("platform")
        if cls is SglangEngine and platform is not None and str(platform.backend) == "xla":
            return SglangTpuEngine(*args, **kwargs)
        return super().__new__(cls)

    def default_env(self) -> dict[str, str]:
        from pie_bench.node.baselines import cache_root

        jit = cache_root() / "jit"
        env = {
            "SGLANG_JIT_CACHE_DIR": str(jit / "sglang"),
            "TRITON_CACHE_DIR": str(jit / "triton"),
            "TORCHINDUCTOR_CACHE_DIR": str(jit / "inductor"),
            "FLASH_ATTENTION_CUTE_DSL_CACHE_ENABLED": "1",
            "FLASH_ATTENTION_CUTE_DSL_CACHE_DIR": str(jit / "cute_dsl"),
            **self.nccl_env(),
        }
        env.update(self.no_peer_env())
        if self.artifact.family == "deepseek_v41" and self.platform is not None and str(self.platform.arch) == "blackwell" and "RTX" not in str(self.platform.accelerator):
            env["SGLANG_ENABLE_JIT_DEEPGEMM"] = env["SGL_ENABLE_JIT_DEEPGEMM"] = "1"
        if self.artifact.id == "gpt-oss-120b-mxfp4" and self.platform is not None and str(self.platform.arch) == "hopper" and float(self.platform.memory_gib or 0) <= 80:
            env["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
        return env

    def default_python(self) -> str:
        if os.environ.get("SGLANG_PY"):
            return os.environ["SGLANG_PY"]
        from pie_bench.node.baselines import baseline_python

        pin = self.recipe.get("pin")
        backend = str(self.platform.backend) if self.platform is not None else None
        py = baseline_python("sglang", pin, backend=backend) if pin else None
        return str(py) if py else "/root/.venv/sglang/bin/python"

    def model_arg(self) -> str:
        return str(self.recipe.get("snapshot_dir") or self.artifact.base_model)

    def engine_args(self, workload: WorkloadSpec) -> list[str]:
        r = self.recipe
        args: list[str] = ["--tp-size", str(max(1, int(self.mode.tp)))]
        gmu = r.get("gpu_mem_util", 0.90)
        card = float(self.platform.memory_gib or 0.0) / max(1, int(self.mode.tp))
        if gmu is not None:
            weights = float(self.artifact.expected_gib or 0.0)
            if weights and card and weights / card > 0.5 and not (self.artifact.family in ("qwen3_6", "muse_glimmer") and weights / card < 0.65):
                gmu = max(float(gmu), 0.95)
            elif self.artifact.family == "kimi_k3":
                wide = card < 80 and workload_concurrency(workload) >= 128
                gmu = min(float(gmu), 0.79 if wide else 0.75)
                if card < 48:
                    gmu = min(float(gmu), 0.6)
            elif self.artifact.family == "deepseek_v4" and card < 80 and str(self.platform.arch) in ("ada", "ampere"):
                gmu = min(float(gmu), 0.75)
            elif self.artifact.family in ("glm5_next", "qwen4_exp"):
                gmu = min(float(gmu), 0.85 if card >= 80 else 0.75)
            if self.platform.id == "l4-x1":
                gmu = min(float(gmu), 0.85)
            if self.artifact.id == "gpt-oss-120b-mxfp4" and str(self.platform.arch) == "ampere" and card >= 80:
                gmu = min(float(gmu), 0.85)
            if self.artifact.family == "qwen3_6" and str(self.platform.arch) == "ampere" and card >= 80 and weights / card < 0.7:
                gmu = min(float(gmu), 0.9)
            if self.artifact.family in ("minimax_m3", "glm_moe_dsa") and card >= 80:
                gmu = min(float(gmu), 0.88)
            if self.artifact.family in ("glm_moe_dsa", "hy_v4", "minimax_m3") and card < 48:
                gmu = min(float(gmu), 0.80)
            if self.artifact.family == "deepseek_v4" and str(self.platform.arch) == "hopper":
                gmu = min(float(gmu), 0.85)
            if self.artifact.family == "muse_spark" and card <= 80:
                gmu = min(float(gmu), 0.85 if card >= 48 else 0.75)
            if card < 80 and workload_concurrency(workload) >= 512:
                gmu = min(float(gmu), 0.85)
            if self.artifact.family == "nemotron_h" and 40 <= card < 80:
                gmu = min(float(gmu), 0.85)
            if self.artifact.family == "muse_glimmer" and card < 80 and (workload_concurrency(workload) >= 128 or card <= 32):
                gmu = 0.85
            if self.artifact.family == "glm5_next" and str(self.platform.arch) == "blackwell" and "RTX" in str(self.platform.accelerator) and card >= 80:
                gmu = 0.88
            if self.artifact.family in ("glm5_next", "hy_v4", "muse_spark") and card <= 32:
                gmu = min(float(gmu), 0.78)
            if self.artifact.family == "qwen3_6_moe" and card <= 32:
                gmu = min(float(gmu), 0.88)
            if self.artifact.family == "nemotron_h" and card <= 32:
                gmu = min(float(gmu), 0.85)
            if self.platform.id == "rtx4090-x1":
                gmu = min(float(gmu), 0.85 if weights / card > 0.6 else 0.80)
                if self.artifact.family == "kimi_k3":
                    gmu = min(float(gmu), 0.70)
            args += ["--gpu-mem-util", str(gmu)]
        graph_bs = r.get("cuda_graph_max_bs")
        if graph_bs is None:
            graph_bs = workload_concurrency(workload)
        if gmu is not None and card >= 80 and int(graph_bs) >= 64:
            capped = 0.80 if int(graph_bs) >= 256 and float(self.artifact.expected_gib or 0.0) / card <= 0.5 else 0.85
            if self.artifact.id == "gpt-oss-120b-mxfp4" and str(self.platform.arch) == "hopper" and card <= 80:
                capped = float(gmu)
            if float(gmu) > capped:
                args[-1] = str(capped)
        args += ["--max-model-len", str(max_model_len_for(workload))]
        args += ["--sglang-cuda-graph-max-bs", str(int(graph_bs))]

        if r.get("report_timing", True):
            args += ["--report-timing"]
        if r.get("attention_backend"):
            args += ["--sglang-attention-backend", str(r["attention_backend"])]
        dsa = r.get("dsa_backend")
        if dsa is None and self.artifact.family == "glm5_next" and self.platform is not None and str(self.platform.arch) == "blackwell" and "RTX" in str(self.platform.accelerator):
            dsa = "tilelang"
        blackwell = self.platform is not None and str(self.platform.arch) == "blackwell"
        rtx_blackwell = blackwell and "RTX" in str(self.platform.accelerator)
        if self.artifact.family in ("glm_moe_dsa", "glm5_next", "hy_v4") and blackwell:
            args += ["--sglang-kv-cache-dtype", "bfloat16"]
            if dsa is None and self.artifact.family == "glm_moe_dsa" and rtx_blackwell:
                dsa = "flashmla_sparse"
        if dsa:
            args += ["--sglang-dsa-backend", str(dsa)]
        moe = r.get("moe_runner_backend")
        if moe is None and self.artifact.family == "deepseek_v41" and int(self.mode.tp) == 4:
            moe = "marlin"
        if moe is None and self.artifact.family == "gpt_oss" and self.platform is not None and str(self.platform.arch) == "blackwell" and "RTX" in str(self.platform.accelerator):
            moe = "marlin"
        if moe is None and self.artifact.family == "gpt_oss" and self.platform is not None and str(self.platform.arch) == "ampere":
            moe = "marlin"
        if moe is None and self.artifact.family == "kimi_k3" and blackwell and not rtx_blackwell:
            moe = "marlin"
        if moe is None and self.artifact.family == "nemotron_h" and self.platform is not None and str(self.platform.backend) == "rocm":
            moe = "triton"
        if moe:
            args += ["--sglang-moe-runner-backend", str(moe)]
        if moe is None and self.artifact.family == "gpt_oss" and blackwell and not rtx_blackwell:
            args += ["--sglang-flashinfer-mxfp4-moe-precision", "bf16"]
        if r.get("sampling_backend"):
            args += ["--sglang-sampling-backend", str(r["sampling_backend"])]
        if r.get("page_size"):
            args += ["--sglang-page-size", str(int(r["page_size"]))]
        if r.get("max_total_tokens"):
            args += ["--sglang-max-total-tokens", str(int(r["max_total_tokens"]))]
        if r.get("disable_cuda_graph"):
            args.append("--sglang-disable-cuda-graph")
        piecewise_off = r.get("disable_piecewise_cuda_graph")
        if piecewise_off is None and self.artifact.family in ("minimax_m3", "glm_moe_dsa", "hy_v4") and self.platform is not None and str(self.platform.arch) == "ampere":
            piecewise_off = True
        if piecewise_off:
            args.append("--sglang-disable-piecewise-cuda-graph")

        hybrid_swa = r.get("disable_hybrid_swa_memory")
        if hybrid_swa is None:
            hybrid_swa = self.artifact.family.startswith("gemma")
        if hybrid_swa:
            args.append("--sglang-disable-hybrid-swa-memory")


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

    name = EngineName.SGLANG
    health_path = "/health"
    exact_length = "ignore_eos"

    def server_python(self) -> str:
        if os.environ.get("SGLANG_PY"):
            return os.environ["SGLANG_PY"]
        from pie_bench.node.baselines import baseline_python

        pin = self.recipe.get("pin")
        py = baseline_python("sglang", pin, backend="xla") if pin else None
        return str(py) if py else "python3"

    def model_arg(self) -> str:
        return str(self.recipe.get("snapshot_dir") or self.artifact.base_model)

    def api_model(self) -> str:
        return self.model_arg()

    def server_cmd(self, port: int, slots: int, context: int) -> list[str]:
        r = self.recipe
        if r.get("max_running_requests"):
            slots = min(slots, int(r["max_running_requests"]))
        cmd = [
            self.server_python(), "-m", "sgl_jax.launch_server", "--model-path", self.model_arg(),
            "--host", "127.0.0.1", "--port", str(port), "--device", "tpu", "--tp-size", str(max(1, int(self.mode.tp))),
            "--context-length", str(context), "--max-running-requests", str(slots),
            "--disable-radix-cache", "--log-level", "warning",
            "--trust-remote-code",
        ]
        if r.get("gpu_mem_util") is not None:
            cmd += ["--mem-fraction-static", str(r["gpu_mem_util"])]
        if r.get("page_size"):
            cmd += ["--page-size", str(int(r["page_size"]))]
        if r.get("chunked_prefill_size"):
            cmd += ["--chunked-prefill-size", str(int(r["chunked_prefill_size"]))]
        return cmd

    def version(self) -> str:
        try:
            out = subprocess.run(
                [self.server_python(), "-c", "import sgl_jax; print(sgl_jax.__version__)"],
                capture_output=True, text=True, timeout=120, check=False,
            )
            v = out.stdout.strip().splitlines()
            pin = str(self.recipe.get("pin") or "")
            if pin.startswith("git-"):
                return pin
            return v[-1] if out.returncode == 0 and v else "unknown"
        except Exception:
            return "unknown"

    def leftover_process_names(self) -> list[str]:
        return ["sglang::scheduler", "sglang::detokenizer", "sgl_jax"]
