"""TensorRT-LLM adapter: its PyTorch backend's LLM API on the HF checkpoint, measured in-process.

The PyTorch backend loads the HF checkpoint as it is (no per-model engine build), the same snapshot or
miniature vLLM and SGLang load. One LLM is booted per model (``scripts/trtllm_bench.py serve``) and every
cell's bench runs inside its process, streaming from ``LLM.generate_async``: the in-process vantage
vllm_bench.py and sglang_bench.py measure vLLM and SGLang from, with openai_bench.py's prompts and summary.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any

import yaml

from pie_evals.schema import EngineName

from .base import register
from .served import ServedEngine

SCRIPT = Path(__file__).resolve().parent / "scripts" / "trtllm_bench.py"

#: what TensorRT-LLM holds beside its weights before it sizes the KV pool (CUDA context, torch, the profiling
#: forward's activations), GiB: Qwen3.8-27B on an 80 GB H100 at c256 (see ``kv_free_mem_fraction``)
TRTLLM_RUNTIME_GIB = 3.0
#: TensorRT-LLM's own ``free_gpu_memory_fraction`` default
TRTLLM_DEFAULT_FRACTION = 0.9

_KV_DTYPES = {"bf16": "auto", "fp16": "auto", "auto": "auto", "fp8": "fp8", "fp8_e4m3": "fp8"}


@register
class TrtllmEngine(ServedEngine):
    name = EngineName.TRTLLM
    health_path = "/health"  # 200 once the executor is up
    # the OpenAI completion request takes ignore_eos: every request writes exactly max_tokens
    exact_length = "ignore_eos"

    def script_path(self) -> Path:
        return SCRIPT

    def server_python(self) -> str:
        if os.environ.get("TRTLLM_PY"):
            return os.environ["TRTLLM_PY"]
        from pie_evals.node.baselines import baseline_python

        pin = self.recipe.get("pin")
        py = baseline_python("trtllm", pin) if pin else None
        return str(py) if py else "/root/.venv/trtllm/bin/python"

    def model_arg(self) -> str:
        return str(self.recipe.get("snapshot_dir") or self.artifact.base_model)

    def api_model(self) -> str:
        # trtllm-serve names the served model by the path it loaded
        return self.model_arg()

    def extra_body(self) -> dict[str, Any]:
        # the client sends the prompt with the chat template already rendered (its BOS too), as every server gets it
        return {"add_special_tokens": False}

    def default_env(self) -> dict[str, str]:
        from pie_evals.node.baselines import cache_root

        jit = cache_root() / "jit"
        env = {
            "TRITON_CACHE_DIR": str(jit / "triton"),
            "TORCHINDUCTOR_CACHE_DIR": str(jit / "inductor"),
            "FLASHINFER_WORKSPACE_BASE": str(jit / "flashinfer"),
            "TLLM_LOG_LEVEL": "WARNING",
            "TRTLLM_DG_CACHE_DIR": str(jit / "deepgemm"),
            **self.nccl_env(),
        }
        # DeepGEMM finds its JIT headers by running `pip show tensorrt_llm` ("could not open source file
        # deep_gemm/nvrtc_std.cuh (no directories in search list)", GLM-5.3 on h100-sxm-x1): the venv's pip goes first
        venv_bin = str(Path(self.server_python()).parent)
        env["PATH"] = ":".join([venv_bin] + [d for d in os.environ.get("PATH", "").split(":") if d and d != venv_bin])
        return env

    def kv_free_mem_fraction(self) -> float | None:
        """``free_gpu_memory_fraction`` for the KV pool. A recipe's ``kv_free_mem_fraction`` stands as it is.
        Otherwise the fraction that lands TensorRT-LLM's whole use at the share of the card vLLM, SGLang and pie
        take (``gpu_mem_util``, 0.9): TensorRT-LLM's fraction is of the memory left after its weights and runtime,
        so its default 0.9 gave it more cache than the others (Qwen3.8-27B on an 80 GB H100: about 21 GiB against
        pie's 15). With ``f = 1 - (1 - share) * card / left`` and ``left = card - weights - runtime``, its weights,
        runtime and ``f * left`` of KV add up to ``share * card``. Never past TensorRT-LLM's own default."""
        r = self.recipe
        if r.get("kv_free_mem_fraction") is not None:
            return float(r["kv_free_mem_fraction"])
        share = r.get("gpu_mem_util", 0.90)
        count = max(1, int(self.platform.count))
        card = float(self.platform.memory_gib or 0) / count
        weights = float(self.artifact.expected_gib or 0) / max(1, int(self.mode.tp))
        left = card - weights - float(r.get("runtime_gib", TRTLLM_RUNTIME_GIB))
        if share is None or card <= 0 or weights <= 0 or left <= 0:
            return None
        return round(min(TRTLLM_DEFAULT_FRACTION, max(0.05, 1.0 - (1.0 - float(share)) * card / left)), 3)

    def llm_api_options(self, slots: int, context: int) -> dict[str, Any]:
        """The LLM API options trtllm-serve reads from ``--extra_llm_api_options``."""
        r = self.recipe
        kv: dict[str, Any] = {
            # cold prompts on every engine: no block reuse, as vLLM runs without prefix caching
            "enable_block_reuse": bool(r.get("block_reuse", False)),
            "dtype": str(r.get("kv_cache_dtype") or _KV_DTYPES.get(str(self.artifact.kv_dtype), "auto")),
        }
        fraction = self.kv_free_mem_fraction()
        if fraction is not None:
            kv["free_gpu_memory_fraction"] = fraction
        opts: dict[str, Any] = {"kv_cache_config": kv}
        if r.get("cuda_graphs", True):
            # graphs up to the shape's batch, as SGLang's ceiling and vLLM's max_num_seqs; padded so every batch replays one
            opts["cuda_graph_config"] = {"enable_padding": True, "max_batch_size": int(r.get("cuda_graph_max_bs") or slots)}
        max_tokens = int(r.get("max_num_tokens") or 8192)
        if context > max_tokens or r.get("chunked_prefill"):
            # a prompt longer than one step's token budget is read in chunks (vLLM chunks by default)
            opts["enable_chunked_prefill"] = True
        if r.get("attn_backend"):
            opts["attn_backend"] = str(r["attn_backend"])
        if r.get("moe_backend"):
            opts["moe_config"] = {"backend": str(r["moe_backend"])}
        if r.get("disable_overlap_scheduler"):
            opts["disable_overlap_scheduler"] = True
        for k, v in (r.get("llm_api_options") or {}).items():
            opts[k] = v
        return opts

    def server_cmd(self, port: int, slots: int, context: int) -> list[str]:
        r = self.recipe
        if r.get("max_batch_cap"):
            # a hybrid model's recurrent-state pool holds every admitted sequence; past the cap the rest
            # queue in TensorRT-LLM's scheduler, as vLLM's max_num_seqs_cap does
            slots = min(slots, int(r["max_batch_cap"]))
        cfg = Path(r.get("options_dir") or "/tmp") / f"trtllm-{os.getpid()}-{port}.yaml"
        cfg.parent.mkdir(parents=True, exist_ok=True)
        cfg.write_text(yaml.safe_dump(self.llm_api_options(slots, context), sort_keys=True))
        return [
            self.server_python(), str(SCRIPT), "serve", "--model", self.model_arg(), "--port", str(port),
            "--options", str(cfg), "--tp-size", str(max(1, int(self.mode.tp))),
            "--max-batch-size", str(max(1, slots)), "--max-seq-len", str(context),
            "--max-num-tokens", str(int(r.get("max_num_tokens") or 8192)),
        ]

    def version(self) -> str:
        try:
            out = subprocess.run(
                [self.server_python(), "-c", "from importlib.metadata import version; print(version('tensorrt_llm'))"],
                capture_output=True, text=True, timeout=120, check=False, env=self.process_env(),
            )
            v = out.stdout.strip().splitlines()
            return v[-1] if out.returncode == 0 and v else "unknown"
        except Exception:
            return "unknown"

    def leftover_process_names(self) -> list[str]:
        return ["trtllm_bench.py", "mpi4py", "tensorrt_llm"]
