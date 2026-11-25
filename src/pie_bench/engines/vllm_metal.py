from __future__ import annotations

import os
import subprocess
from pathlib import Path

from pie_bench.engines import register
from pie_bench.schema import EngineName

from .mlxlm import MlxlmEngine


@register
class VllmMetalEngine(MlxlmEngine):
    name = EngineName.VLLM_METAL
    exact_length = "ignore_eos"
    token_ids = True
    one_request_server = True

    def vlm(self) -> bool:
        return False

    def server_python(self) -> str:
        return str(
            self.recipe.get("server_python")
            or os.environ.get("VLLM_METAL_PY")
            or "/tmp/pievenv/bin/python"
        )

    def server_env(self) -> dict[str, str]:
        r = self.recipe
        env = {"HF_HUB_OFFLINE": "1"}
        if r.get("multimodal_mode"):
            env["VLLM_METAL_MULTIMODAL_MODE"] = str(r["multimodal_mode"])
        return env

    def server_cmd(self, port: int, slots: int, context: int) -> list[str]:
        r = self.recipe
        extra = r.get("server_extra") or []
        if isinstance(extra, str):
            extra = extra.split()
        vllm = Path(self.server_python()).parent / "vllm"
        cmd = [
            str(vllm),
            "serve",
            self.model_arg(),
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--max-num-seqs",
            str(slots),
            "--max-model-len",
            str(context),
            "--enable-prefix-caching" if r.get("prefix_caching") else "--disable-prefix-caching",
            "--disable-log-stats",
            "--uvicorn-log-level",
            "warning",
        ]
        if r.get("gpu_mem_util") is not None:
            cmd += ["--gpu-memory-utilization", str(r["gpu_mem_util"])]
        return cmd + [str(x) for x in extra]

    def draft_args(self) -> list[str]:
        return []

    def version(self) -> str:
        out = subprocess.run(
            [
                self.server_python(),
                "-c",
                "from importlib.metadata import version; print(version('vllm-metal'), version('vllm'))",
            ],
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        v = out.stdout.strip().split()
        return f"{v[0]} (vllm {v[1]})" if out.returncode == 0 and len(v) == 2 else "unknown"

    def leftover_process_names(self) -> list[str]:
        return ["VLLM::EngineCore"]
