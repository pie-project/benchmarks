from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

from pie_bench.engines import register
from pie_bench.engines.engine import Engine
from pie_bench.engines.shapes import is_prefix_workload, max_model_len_for, workload_concurrency
from pie_bench.schema import EngineName, WorkloadSpec

_VLLM_KV_DTYPES = {"bf16": "auto", "fp16": "auto", "auto": "auto", "fp8": "fp8", "fp8_e4m3": "fp8_e4m3", "fp8_e5m2": "fp8_e5m2"}


@register
class VllmEngine(Engine):
    name = EngineName.VLLM
    script = "vllm_bench.py"
    env_defaults = {"VLLM_USE_DEEP_GEMM": "0"}

    def default_env(self) -> dict[str, str]:
        from pie_bench.installers.baselines import cache_root

        jit = cache_root() / "jit"
        env = {
            "FLASHINFER_WORKSPACE_BASE": str(jit / "flashinfer"),
            "TRITON_CACHE_DIR": str(jit / "triton"),
            "TORCHINDUCTOR_CACHE_DIR": str(jit / "inductor"),
            "VLLM_CACHE_ROOT": str(jit / "vllm"),
            "FLASH_ATTENTION_CUTE_DSL_CACHE_ENABLED": "1",
            "FLASH_ATTENTION_CUTE_DSL_CACHE_DIR": str(jit / "cute_dsl"),
            **self.nccl_env(),
        }
        if self.platform is not None and str(self.platform.backend) == "rocm":
            env["VLLM_ROCM_USE_AITER"] = "1"
            venv = os.environ.get("VIRTUAL_ENV") or "/opt/venv"
            env["PATH"] = ":".join(d for d in os.environ.get("PATH", "").split(":") if d and not d.startswith(venv + "/"))
            if self.artifact.family in ("qwen3_6", "mimo_v2"):
                env["VLLM_USE_V2_MODEL_RUNNER"] = "0"
        if self.platform is not None and str(self.platform.backend) == "xla" and str(self.artifact.scheme) == "mxfp4":
            env["MOE_REQUANTIZE_BLOCK_SIZE"] = "32"
            env["MOE_REQUANTIZE_WEIGHT_DTYPE"] = "int8"
        if self.platform is not None and str(self.platform.backend) == "xla":
            env.update(self._tpu_env())
        if self.artifact.family == "mimo_v2" and self.platform is not None and str(self.platform.arch) == "blackwell" and "RTX" in str(self.platform.accelerator):
            env["VLLM_DISABLED_KERNELS"] = "CutlassFp8BlockScaledMMKernel"
        if self.artifact.family in ("deepseek_v41", "deepseek_v4") and self.platform is not None and str(self.platform.arch) == "blackwell" and "RTX" not in str(self.platform.accelerator):
            env["VLLM_USE_DEEP_GEMM"] = "1"
        if self.artifact.family == "deepseek_v4" and self.platform is not None and str(self.platform.arch) == "hopper":
            env["VLLM_USE_DEEP_GEMM"] = "1"
        if self.artifact.family in ("gpt_oss", "gemma4", "gemma4_moe", "deepseek_v41") and self.platform is not None and str(self.platform.arch) == "hopper":
            # vLLM 0.32's model runner v2 faults at warmup on Hopper here (illegal memory access in FA3, CuTe flash
            # attention, DeepSeek-V4.1's launcher; plain runs on an H100 and an H200, 2026-11-25); v1 runs gpt-oss-20b on
            # an H100 at 308.1 tok/s, the stored row 304.8
            env["VLLM_USE_V2_MODEL_RUNNER"] = "0"
        if self.artifact.family in ("deepseek_v41", "deepseek_v4") and self.platform is not None and self.platform.id == "l4-x1":
            env["VLLM_USE_BREAKABLE_CUDAGRAPH"] = "0"
        if int(self.mode.tp) > 1:
            env["VLLM_WORKER_MULTIPROC_METHOD"] = "spawn"
        if self.no_peer_all_reduce():
            env["VLLM_DISABLE_CUSTOM_AR"] = "1"
            env.update(self.no_peer_env())
        return env

    def _tpu_env(self) -> dict[str, str]:
        snap = Path(str(self.recipe.get("snapshot_dir") or ""))
        try:
            cfg = json.loads((snap / "config.json").read_text())
        except (OSError, ValueError):
            cfg = {}
        keys = {**cfg, **(cfg.get("text_config") or {})}
        env: dict[str, str] = {}
        extra: dict[str, Any] = {}
        if "kv_lora_rank" in keys or str(cfg.get("model_type", "")).startswith("deepseek"):
            env["NEW_MODEL_DESIGN"] = "1"
            extra["additional_config"] = {"sharding": {"sharding_strategy": {"enable_dp_attention": True}}}
        if cfg.get("model_type") == "deepseek_v4":
            env["MODEL_IMPL_TYPE"] = "vllm"
            env["PIE_BENCH_TPU_XLA_CSA_GATHER"] = "1"
        if cfg.get("model_type") == "gemma4_unified":
            extra["hf_overrides"] = {"architectures": ["Gemma4ForCausalLM"]}
        if extra:
            env["PIE_BENCH_VLLM_ENGINE_ARGS"] = json.dumps(extra)
            existing = self.env.get("PYTHONPATH") or os.environ.get("PYTHONPATH")
            env["PYTHONPATH"] = ":".join([str(Path(__file__).resolve().parent / "site_hooks" / "vllm_tpu")] + ([existing] if existing else []))
        return env

    ROCM_IMAGE_ENV = ("LD_LIBRARY_PATH", "LIBRARY_PATH", "CPATH", "ROCM_PATH", "ROCM_HOME", "VIRTUAL_ENV",
                      "PIP_CONSTRAINT", "TORCHINDUCTOR_MAX_AUTOTUNE", "TORCHINDUCTOR_MAX_AUTOTUNE_POINTWISE")

    def drop_env(self) -> set[str]:
        if self.platform is not None and str(self.platform.backend) == "rocm":
            return set(self.ROCM_IMAGE_ENV)
        return set()

    def default_python(self) -> str:
        if os.environ.get("VLLM_PY"):
            return os.environ["VLLM_PY"]
        from pie_bench.installers.baselines import baseline_python

        pin = self.recipe.get("pin")
        backend = str(self.platform.backend) if self.platform is not None else None
        py = baseline_python("vllm", pin, backend=backend) if pin else None
        return str(py) if py else "/root/.venv/vllm/bin/python"

    def model_arg(self) -> str:
        return str(self.recipe.get("snapshot_dir") or self.artifact.base_model)

    def build_argv(self, workload: WorkloadSpec, common_args: list[str], json_out: Path) -> list[str]:
        argv = super().build_argv(workload, common_args, json_out)
        i = argv.index("latency") if "latency" in argv[:4] else -1
        if i >= 0 and "--requests" in argv and self.recipe.get("report_timing", True):
            argv[i] = "tput"
            j = argv.index("--requests")
            argv[j:j + 2] = ["--num-requests", argv[j + 1], "--concurrency", "1"]
        return argv

    def engine_args(self, workload: WorkloadSpec) -> list[str]:
        r = self.recipe
        args: list[str] = ["--tp-size", str(max(1, int(self.mode.tp)))]
        gmu = r.get("gpu_mem_util", 0.90)
        if gmu is not None:
            card = float(self.platform.memory_gib or 0.0) / max(1, int(self.mode.tp))
            if self.artifact.family == "kimi_k3" and ((40 <= card < 80 and workload_concurrency(workload) >= 128) or workload_concurrency(workload) >= 512):
                gmu = min(float(gmu), 0.85 if card < 80 else 0.75)
            elif self.mode.spec_dec and 0 < card < 40:
                gmu = min(float(gmu), 0.85)
            args += ["--gpu-mem-util", str(gmu)]
        args += ["--max-model-len", str(max_model_len_for(workload))]


        if r.get("report_timing", True):
            args += ["--report-timing"]
        if r.get("attention_backend"):
            args += ["--attention-backend", str(r["attention_backend"])]
        if r.get("moe_backend"):
            args += ["--moe-backend", str(r["moe_backend"])]

        prefix = r.get("prefix_caching")
        if prefix is None:
            prefix = is_prefix_workload(workload)
        args.append("--prefix-caching" if prefix else "--no-prefix-caching")

        if r.get("chunked_prefill") is False:
            args.append("--no-chunked-prefill")
        if r.get("max_num_batched_tokens"):
            args += ["--max-num-batched-tokens", str(int(r["max_num_batched_tokens"]))]
        if r.get("max_num_seqs_cap") and "--max-num-seqs" in self._script_text():
            args += ["--max-num-seqs", str(int(r["max_num_seqs_cap"]))]
        if r.get("num_gpu_blocks_override"):
            args += ["--num-gpu-blocks-override", str(int(r["num_gpu_blocks_override"]))]
        if r.get("block_size"):
            args += ["--block-size", str(int(r["block_size"]))]
        if r.get("enforce_eager"):
            args.append("--enforce-eager")
        cfg = r.get("compilation_config")
        c = workload_concurrency(workload)
        if c > 512 and not r.get("enforce_eager") and not isinstance(cfg, str):
            cfg = {**(cfg or {}), "max_cudagraph_capture_size": int(max((cfg or {}).get("max_cudagraph_capture_size", 0), c))}
        if cfg:
            args += ["--compilation-config", cfg if isinstance(cfg, str) else json.dumps(cfg)]
        if r.get("language_model_only"):
            args.append("--language-model-only")

        kv = r.get("kv_cache_dtype") or _VLLM_KV_DTYPES.get(str(self.artifact.kv_dtype), str(self.artifact.kv_dtype))
        if kv and kv != "auto":
            args += ["--kv-cache-dtype", str(kv)]

        spec = self.mode.spec_dec
        if r.get("speculative_config"):
            cfg = r["speculative_config"]
            args += ["--speculative-config", cfg if isinstance(cfg, str) else json.dumps(cfg)]
        elif spec == "ngram":
            args += ["--spec-method", "ngram", "--spec-tokens", str(int(r.get("spec_tokens", 4)))]
        elif spec == "mtp" and r.get("mtp_assistant_model"):
            args += ["--mtp-assistant-model", str(r["mtp_assistant_model"]), "--mtp-method", str(r.get("mtp_method", "gemma4_mtp"))]
            args += ["--mtp-num-drafts", str(int(r.get("mtp_num_drafts", 3)))]
            if r.get("mtp_draft_tp_size"):
                args += ["--mtp-draft-tp-size", str(int(r["mtp_draft_tp_size"]))]

        if r.get("cpu_affinity"):
            args += ["--cpu-affinity", str(r["cpu_affinity"])]
        if r.get("request_timeout"):
            args += ["--request-timeout", str(r["request_timeout"])]
        return args

    def _script_text(self) -> str:
        try:
            return self.script_path().read_text()
        except OSError:
            return ""

    def version(self) -> str:
        try:
            out = subprocess.run(
                [self.python, "-c", "import vllm; print(vllm.__version__)"],
                capture_output=True, text=True, timeout=120, check=False, env=self.process_env(),
            )
            v = out.stdout.strip().splitlines()
            return v[-1] if out.returncode == 0 and v else "unknown"
        except Exception:
            return "unknown"

    def counters_from_summary(self, summary: dict[str, Any]) -> dict[str, float]:
        cfg = summary.get("config") or {}
        out: dict[str, float] = {}
        for label, key in (
            ("spec_acceptance_rate", "vllm spec acceptance rate"),
            ("spec_mean_acceptance_length", "vllm spec mean acceptance length"),
            ("spec_drafts", "vllm spec drafts"),
        ):
            v = cfg.get(key)
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                out[label] = float(v)
        return out

    def leftover_process_names(self) -> list[str]:
        return ["VLLM::EngineCore", "EngineCore"]
