"""vLLM adapter: drives ``scripts/bench/vllm_bench.py``.

vllm_bench.py boots the ``LLM`` (or ``AsyncLLM`` under ``--report-timing``)
in-process, so there is no persistent-server path; each run loads the model.
Every flag emitted here is parsed by vllm_bench.py or scripts/bench/common.py.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

from pie_evals.schema import EngineName, WorkloadSpec

from .base import Engine, register
from .shape import is_prefix_workload, max_model_len_for, workload_concurrency

_VLLM_KV_DTYPES = {"bf16": "auto", "fp16": "auto", "auto": "auto", "fp8": "fp8", "fp8_e4m3": "fp8_e4m3", "fp8_e5m2": "fp8_e5m2"}


@register
class VllmEngine(Engine):
    name = EngineName.VLLM
    script = "scripts/bench/vllm_bench.py"
    #: no nvcc on the runner image, so no DeepGEMM JIT (see SglangEngine)
    env_defaults = {"VLLM_USE_DEEP_GEMM": "0"}

    def default_env(self) -> dict[str, str]:
        # FlashInfer's JIT workspace (<base>/.cache/flashinfer) on the volume:
        # the head_dim-512 gemma prefill kernel then compiles once, not per pod
        from pie_evals.node.baselines import cache_root

        # Triton autotune / inductor / vLLM compile caches on the volume as well: a fresh pod's
        # first round at each batch shape autotuned inside the measurement (H100 gpt-oss mini
        # c256 14.5k then 20.4k and 20.3k tok/s, nightly 36103844715 s05) and was read as noise
        jit = cache_root() / "jit"
        env = {
            "FLASHINFER_WORKSPACE_BASE": str(jit / "flashinfer"),
            "TRITON_CACHE_DIR": str(jit / "triton"),
            "TORCHINDUCTOR_CACHE_DIR": str(jit / "inductor"),
            "VLLM_CACHE_ROOT": str(jit / "vllm"),
            # FlashAttention 4's CuTe DSL kernels compile per shape and, unasked, only in memory: every
            # round's fresh server compiled them inside the measurement (Gemma-4-E4B pf64-512 on
            # h100-sxm-x1: 20.9k tok/s against 62.0k with them warm)
            "FLASH_ATTENTION_CUTE_DSL_CACHE_ENABLED": "1",
            "FLASH_ATTENTION_CUTE_DSL_CACHE_DIR": str(jit / "cute_dsl"),
            **self.nccl_env(),
        }
        if self.platform is not None and str(self.platform.backend) == "rocm":
            # AMD's own kernels (AITER) are vLLM's recommended Instinct path and off unless asked for:
            # Qwen3.5-0.8B raw-512-256 on the MI300X decoded 512 tok/s with them, 478 without
            env["VLLM_ROCM_USE_AITER"] = "1"
            # AITER JIT-builds the kernels its wheel lacks (Muse-Glimmer-30B's mha_varlen_fwd) with the hipcc it finds
            # on PATH, and the image venv's comes first: a python wrapper over the image's SDK that links nothing
            # ("cannot find -lamdhip64", mi300x-x1). Without the image's bin dirs it takes the pod's own ROCm
            venv = os.environ.get("VIRTUAL_ENV") or "/opt/venv"
            env["PATH"] = ":".join(d for d in os.environ.get("PATH", "").split(":") if d and not d.startswith(venv + "/"))
            # 0.32.0 picks its V2 model runner for Qwen3.8-27B by itself, and the ROCm wheel's _C lacks the op it maps
            # host buffers with ("'_C' object has no attribute 'get_cuda_view_from_cpu_tensor'", mi300x-x1); the
            # models that need the V2 runner (Qwen3.8-Flash-Next's PLE inputs, Muse Spark) keep it
            if self.artifact.family == "qwen3_6":
                env["VLLM_USE_V2_MODEL_RUNNER"] = "0"
        if self.artifact.family == "mimo_v2" and self.platform is not None and str(self.platform.arch) == "blackwell" and "RTX" in str(self.platform.accelerator):
            # 0.31.0's CUTLASS block-FP8 GEMM aborts on sm_120 for MiMo's FP8 projections ("cutlass_gemm_caller:
            # Invalid status", weekly 39680748696); vLLM then takes the next kernel it ranks for block FP8
            env["VLLM_DISABLED_KERNELS"] = "CutlassFp8BlockScaledMMKernel"
        if self.artifact.family in ("deepseek_v41", "deepseek_v4") and self.platform is not None and str(self.platform.arch) == "blackwell" and "RTX" not in str(self.platform.accelerator):
            # on sm_100 0.32.0's mega attention runs wo_a through DeepGEMM's fp8_einsum, whose grouped weight
            # only DeepGEMM's MXFP8 linear kernel lays out; without it boot dies on "t.dim() == N" (b200-x1). V4-Flash's
            # fused wq_a/wkv projection also dies in CUTLASS block-FP8 dispatch_scaled_mm there (b200-x1)
            env["VLLM_USE_DEEP_GEMM"] = "1"
        if self.artifact.family == "deepseek_v4" and self.platform is not None and str(self.platform.arch) == "hopper":
            # on sm_90 0.32.0's CUTLASS block-FP8 GEMM refuses DeepSeek-V4-Flash's projections (dispatch_scaled_mm,
            # h200-x1) and the path past it dies on the grouped wo_a; DeepGEMM serves both (raw decode 445 tok/s)
            env["VLLM_USE_DEEP_GEMM"] = "1"
        if self.artifact.family in ("deepseek_v41", "deepseek_v4") and self.platform is not None and self.platform.id == "l4-x1":
            # on the L4 a breakable graph replaying a DeepSeek-V4.1 prefill piece faults at c128 ("an illegal memory
            # access", breakable_cudagraph.replay), as on Hopper (pie-project/vllm#15); plain graphs serve it (1275 tok/s)
            env["VLLM_USE_BREAKABLE_CUDAGRAPH"] = "0"
        if int(self.mode.tp) > 1:
            # 0.31.0 forked its tp workers after CUDA was up in the engine core, and every worker
            # died on "Cannot re-initialize CUDA in forked subprocess" (L40S x2, weekly 39545360541)
            env["VLLM_WORKER_MULTIPROC_METHOD"] = "spawn"
        if self.no_peer_all_reduce():
            # vllm_bench.py honours VLLM_DISABLE_CUSTOM_AR only on its offline path; the streaming
            # `tput` path every cell runs builds AsyncEngineArgs without it, and 0.31.0 kept
            # ['CUSTOM', 'PYNCCL'] and died with "unspecified launch failure" (weekly 39652187264)
            env["VLLM_DISABLE_CUSTOM_AR"] = "1"
            env.update(self.no_peer_env())
        return env

    #: the AMD SGLang image's ROCm SDK (its venv) in the pod's environment: vLLM's ROCm wheel brings its own
    #: torch/ROCm, and with the image's libraries first on the loader path torch died importing amdsmi
    #: ("libamd_smi.so: undefined symbol amdsmi_set_gpu_clk_range"); the image's max-autotune inductor
    #: defaults are SGLang's, not vLLM's
    ROCM_IMAGE_ENV = ("LD_LIBRARY_PATH", "LIBRARY_PATH", "CPATH", "ROCM_PATH", "ROCM_HOME", "VIRTUAL_ENV",
                      "PIP_CONSTRAINT", "TORCHINDUCTOR_MAX_AUTOTUNE", "TORCHINDUCTOR_MAX_AUTOTUNE_POINTWISE")

    def drop_env(self) -> set[str]:
        if self.platform is not None and str(self.platform.backend) == "rocm":
            return set(self.ROCM_IMAGE_ENV)
        return set()

    def default_python(self) -> str:
        if os.environ.get("VLLM_PY"):
            return os.environ["VLLM_PY"]
        from pie_evals.node.baselines import baseline_python

        pin = self.recipe.get("pin")
        # on the TPU the pin's vllm-tpu build (baselines.BACKEND_SPECS), in its own venv
        backend = str(self.platform.backend) if self.platform is not None else None
        py = baseline_python("vllm", pin, backend=backend) if pin else None
        return str(py) if py else "/root/.venv/vllm/bin/python"

    def model_arg(self) -> str:
        # vLLM resolves HF ids itself (offline cache under HF_HUB_CACHE); a
        # local snapshot path is taken as-is.
        # The runner resolves the checkpoint (a miniature lives under a snapshot
        # dir with no refs/main, so an HF id would not find it) and passes the
        # path through the recipe; a bare HF id is the fallback.
        return str(self.recipe.get("snapshot_dir") or self.artifact.base_model)

    def build_argv(self, workload: WorkloadSpec, common_args: list[str], json_out: Path) -> list[str]:
        # vllm_bench.py's `latency` mode is offline LLM.generate: it times whole requests and
        # stamps no first token, so a single-stream row had no decode or prefill number
        # (0.5.3-b5: every vLLM Raw row empty). Its streaming client at concurrency 1 runs the
        # same requests one at a time and stamps each token as it arrives, the vantage pie and
        # SGLang report from.
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
                # Kimi-K3's MoE activations at c256 outgrow what vLLM's profile run leaves past 0.9
                # on a 48 GB L40S (nightly 36212036845 s06: OOM on 1.38 GiB); 80 GB cards serve it at 0.9
                # up to c256, while at c512 the KDA prefill's state gather OOMs past 0.85 on the 96 GB RTX PRO 6000
                gmu = min(float(gmu), 0.85 if card < 80 else 0.75)
            elif self.mode.spec_dec and 0 < card < 40:
                # a latency boot seats one sequence and hands the rest to kv, then the speculative
                # warm-up asks 394 MiB past 0.9 on a 24 GB 4090 (gemma-4-E4B ngram, nightly
                # 36226645744 s05; Kimi-K3 on the 5090 the same); the tput boots of the cell pass
                gmu = min(float(gmu), 0.85)
            args += ["--gpu-mem-util", str(gmu)]
        args += ["--max-model-len", str(max_model_len_for(workload))]

        # max_num_seqs: vllm_bench.py derives it from --concurrency (1 in
        # latency mode) and there is no --max-num-seqs flag; nothing to emit.
        # TODO(pie/benches): none needed unless admission should differ from
        # the client's offered concurrency.

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
        if r.get("num_gpu_blocks_override"):
            args += ["--num-gpu-blocks-override", str(int(r["num_gpu_blocks_override"]))]
        if r.get("block_size"):
            args += ["--block-size", str(int(r["block_size"]))]
        if r.get("enforce_eager"):
            args.append("--enforce-eager")
        if r.get("compilation_config"):
            cfg = r["compilation_config"]
            args += ["--compilation-config", cfg if isinstance(cfg, str) else json.dumps(cfg)]
        if r.get("language_model_only"):
            args.append("--language-model-only")

        kv = r.get("kv_cache_dtype") or _VLLM_KV_DTYPES.get(str(self.artifact.kv_dtype), str(self.artifact.kv_dtype))
        if kv and kv != "auto":
            args += ["--kv-cache-dtype", str(kv)]

        # speculative modes: the comparable vLLM feature per pie mode.
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
        # eagle / dflash2 / dspark need a drafter checkpoint the recipe must
        # name via `speculative_config`; without it the cell runs without
        # speculation and the program's baseline_equivalents decide whether
        # that is a comparison at all.

        if r.get("cpu_affinity"):
            args += ["--cpu-affinity", str(r["cpu_affinity"])]
        if r.get("request_timeout"):
            args += ["--request-timeout", str(r["request_timeout"])]
        # TODO(pie/benches): no flag for torch.compile / cudagraph capture
        # sizes (vLLM compilation_config); vLLM's defaults apply.
        return args

    def version(self) -> str:
        try:
            out = subprocess.run(
                [self.python, "-c", "import vllm; print(vllm.__version__)"],
                # the engine's own env: on ROCm the image's loader path breaks the wheel's torch import
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
