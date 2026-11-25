from __future__ import annotations

import os
import subprocess
from typing import Any

from pie_bench.engines import register
from pie_bench.engines.engine import Engine
from pie_bench.engines.shapes import max_model_len_for, workload_concurrency
from pie_bench.installers.bench_env import cache_root
from pie_bench.schema import EngineName, WorkloadSpec

from .served import ServedEngine


def _capped(gmu: Any, caps: tuple[tuple[bool, float], ...]) -> Any:
    for applies, cap in caps:
        if applies:
            gmu = min(float(gmu), cap)
    return gmu


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
        if (
            self.artifact.family == "deepseek_v41"
            and self.platform is not None
            and str(self.platform.arch) == "blackwell"
            and "RTX" not in str(self.platform.accelerator)
        ):
            env["SGLANG_ENABLE_JIT_DEEPGEMM"] = env["SGL_ENABLE_JIT_DEEPGEMM"] = "1"
        if (
            self.artifact.id == "gpt-oss-120b-mxfp4"
            and self.platform is not None
            and str(self.platform.arch) == "hopper"
            and float(self.platform.memory_gib or 0) <= 80
        ):
            env["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
        return env

    def default_python(self) -> str:
        if os.environ.get("SGLANG_PY"):
            return os.environ["SGLANG_PY"]
        from pie_bench.installers.baselines import baseline_python

        pin = self.recipe.get("pin")
        backend = str(self.platform.backend) if self.platform is not None else None
        py = baseline_python("sglang", pin, backend=backend) if pin else None
        return str(py) if py else "/root/.venv/sglang/bin/python"

    def model_arg(self) -> str:
        return str(self.recipe.get("snapshot_dir") or self.artifact.base_model)

    def engine_args(self, workload: WorkloadSpec) -> list[str]:
        r = self.recipe
        args: list[str] = ["--tp-size", str(max(1, int(self.mode.tp)))]
        card = float(self.platform.memory_gib or 0.0) / max(1, int(self.mode.tp))
        graph_bs = r.get("cuda_graph_max_bs")
        if graph_bs is None:
            graph_bs = workload_concurrency(workload)
        gmu = r.get("gpu_mem_util", 0.90)
        if gmu is not None:
            gmu = self.memory_fraction(gmu, card, workload_concurrency(workload))
            args += ["--gpu-mem-util", str(self.graph_capped(gmu, card, int(graph_bs)))]
        args += ["--max-model-len", str(max_model_len_for(workload))]
        args += ["--sglang-cuda-graph-max-bs", str(int(graph_bs))]
        if r.get("report_timing", True):
            args += ["--report-timing"]
        if r.get("attention_backend"):
            args += ["--sglang-attention-backend", str(r["attention_backend"])]
        args += self.sparse_attention_args()
        moe = r.get("moe_runner_backend")
        if moe is None:
            moe = self.default_moe_runner()
        if moe:
            args += ["--sglang-moe-runner-backend", str(moe)]
        if moe is None and self.artifact.family == "gpt_oss" and self.datacenter_blackwell():
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
        if piecewise_off is None:
            piecewise_off = (
                self.artifact.family in ("minimax_m3", "glm_moe_dsa", "hy_v4")
                and str(self.platform.arch) == "ampere"
            )
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

    def blackwell(self) -> bool:
        return str(self.platform.arch) == "blackwell"

    def rtx_blackwell(self) -> bool:
        return self.blackwell() and "RTX" in str(self.platform.accelerator)

    def datacenter_blackwell(self) -> bool:
        return self.blackwell() and "RTX" not in str(self.platform.accelerator)

    def memory_fraction(self, gmu: Any, card: float, concurrency: int) -> Any:
        family, arch, platform = self.artifact.family, str(self.platform.arch), self.platform.id
        weights = float(self.artifact.expected_gib or 0.0)
        share = weights / card if card else 0.0
        if (
            weights
            and card
            and share > 0.5
            and not (family in ("qwen3_6", "muse_glimmer") and share < 0.65)
        ):
            gmu = max(float(gmu), 0.95)
        elif family == "kimi_k3":
            gmu = min(float(gmu), 0.79 if card < 80 and concurrency >= 128 else 0.75)
            if card < 48:
                gmu = min(gmu, 0.6)
        elif family == "deepseek_v4" and card < 80 and arch in ("ada", "ampere"):
            gmu = min(float(gmu), 0.75)
        elif family in ("glm5_next", "qwen4_exp"):
            gmu = min(float(gmu), 0.85 if card >= 80 else 0.75)
        gmu = _capped(
            gmu,
            (
                (platform == "l4-x1", 0.85),
                (
                    self.artifact.id == "gpt-oss-120b-mxfp4" and arch == "ampere" and card >= 80,
                    0.85,
                ),
                (family == "qwen3_6" and arch == "ampere" and card >= 80 and share < 0.7, 0.9),
                (family in ("minimax_m3", "glm_moe_dsa") and card >= 80, 0.88),
                (family in ("glm_moe_dsa", "hy_v4", "minimax_m3") and card < 48, 0.80),
                (family == "deepseek_v4" and arch == "hopper", 0.85),
                (family == "muse_spark" and card <= 80, 0.85 if card >= 48 else 0.75),
                (card < 80 and concurrency >= 512, 0.85),
                (family == "nemotron_h" and 40 <= card < 80, 0.85),
            ),
        )
        if family == "muse_glimmer" and card < 80 and (concurrency >= 128 or card <= 32):
            gmu = 0.85
        if family == "glm5_next" and self.rtx_blackwell() and card >= 80:
            gmu = 0.88
        return _capped(
            gmu,
            (
                (family in ("glm5_next", "hy_v4", "muse_spark") and card <= 32, 0.78),
                (family == "qwen3_6_moe" and card <= 32, 0.88),
                (family == "nemotron_h" and card <= 32, 0.85),
                (platform == "rtx4090-x1", 0.85 if share > 0.6 else 0.80),
                (platform == "rtx4090-x1" and family == "kimi_k3", 0.70),
            ),
        )

    def graph_capped(self, gmu: Any, card: float, graph_bs: int) -> Any:
        if card < 80 or graph_bs < 64:
            return gmu
        share = float(self.artifact.expected_gib or 0.0) / card
        cap = 0.80 if graph_bs >= 256 and share <= 0.5 else 0.85
        if (
            self.artifact.id == "gpt-oss-120b-mxfp4"
            and str(self.platform.arch) == "hopper"
            and card <= 80
        ):
            cap = float(gmu)
        return cap if float(gmu) > cap else gmu

    def sparse_attention_args(self) -> list[str]:
        family = self.artifact.family
        args: list[str] = []
        dsa = self.recipe.get("dsa_backend")
        if dsa is None and family == "glm5_next" and self.rtx_blackwell():
            dsa = "tilelang"
        if family in ("glm_moe_dsa", "glm5_next", "hy_v4") and self.blackwell():
            args += ["--sglang-kv-cache-dtype", "bfloat16"]
            if dsa is None and family == "glm_moe_dsa" and self.rtx_blackwell():
                dsa = "flashmla_sparse"
        if dsa:
            args += ["--sglang-dsa-backend", str(dsa)]
        return args

    def default_moe_runner(self) -> str | None:
        family, arch = self.artifact.family, str(self.platform.arch)
        defaults = (
            (family == "deepseek_v41" and int(self.mode.tp) == 4, "marlin"),
            (family == "gpt_oss" and self.rtx_blackwell(), "marlin"),
            (family == "gpt_oss" and arch == "ampere", "marlin"),
            (family == "kimi_k3" and self.datacenter_blackwell(), "marlin"),
            (family == "nemotron_h" and str(self.platform.backend) == "rocm", "triton"),
        )
        return next((runner for applies, runner in defaults if applies), None)

    def version(self) -> str:
        try:
            out = subprocess.run(
                [self.python, "-c", "import sglang; print(sglang.__version__)"],
                capture_output=True,
                text=True,
                timeout=120,
                check=False,
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
        from pie_bench.installers.baselines import baseline_python

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
            self.server_python(),
            "-m",
            "sgl_jax.launch_server",
            "--model-path",
            self.model_arg(),
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--device",
            "tpu",
            "--tp-size",
            str(max(1, int(self.mode.tp))),
            "--context-length",
            str(context),
            "--max-running-requests",
            str(slots),
            "--disable-radix-cache",
            "--log-level",
            "warning",
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
                capture_output=True,
                text=True,
                timeout=120,
                check=False,
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
