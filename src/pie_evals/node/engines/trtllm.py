"""TensorRT-LLM adapter: ``trtllm-serve`` on its PyTorch backend, streamed through ``openai_bench.py``.

The PyTorch backend loads the HF checkpoint as it is (no per-model engine build), the same
snapshot or miniature vLLM and SGLang load. One server is booted per model and holds every
shape of the process, as llama.cpp and mlx-lm are served; the client stamps the first token
and the gaps between tokens the same way for every server.
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

_KV_DTYPES = {"bf16": "auto", "fp16": "auto", "auto": "auto", "fp8": "fp8", "fp8_e4m3": "fp8"}


@register
class TrtllmEngine(ServedEngine):
    name = EngineName.TRTLLM
    health_path = "/health"  # 200 once the executor is up
    # the OpenAI completion request takes ignore_eos: every request writes exactly max_tokens
    exact_length = "ignore_eos"

    def default_python(self) -> str:
        # openai_bench.py runs on the bench interpreter; the server runs from the engine's venv
        return super().default_python()

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
            **self.nccl_env(),
        }
        return env

    def llm_api_options(self, slots: int, context: int) -> dict[str, Any]:
        """The LLM API options trtllm-serve reads from ``--extra_llm_api_options``."""
        r = self.recipe
        kv: dict[str, Any] = {
            # cold prompts on every engine: no block reuse, as vLLM runs without prefix caching
            "enable_block_reuse": bool(r.get("block_reuse", False)),
            "dtype": str(r.get("kv_cache_dtype") or _KV_DTYPES.get(str(self.artifact.kv_dtype), "auto")),
        }
        if r.get("kv_free_mem_fraction") is not None:
            kv["free_gpu_memory_fraction"] = float(r["kv_free_mem_fraction"])
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
        py = Path(self.server_python())
        cfg = Path(r.get("options_dir") or "/tmp") / f"trtllm-{os.getpid()}-{port}.yaml"
        cfg.parent.mkdir(parents=True, exist_ok=True)
        cfg.write_text(yaml.safe_dump(self.llm_api_options(slots, context), sort_keys=True))
        serve = py.parent / "trtllm-serve"
        cmd = [str(serve)] if serve.exists() else [str(py), "-m", "tensorrt_llm.commands.serve"]
        cmd += [
            self.model_arg(), "--host", "127.0.0.1", "--port", str(port), "--backend", "pytorch",
            "--tp_size", str(max(1, int(self.mode.tp))),
            "--max_batch_size", str(max(1, slots)), "--max_seq_len", str(context),
            "--max_num_tokens", str(int(r.get("max_num_tokens") or 8192)),
            "--trust_remote_code", "--log_level", "warning",
            "--extra_llm_api_options", str(cfg),
        ]
        return cmd

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
        return ["trtllm-serve", "mpi4py", "tensorrt_llm"]
