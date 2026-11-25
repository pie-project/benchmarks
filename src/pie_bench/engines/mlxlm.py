from __future__ import annotations

import os
import subprocess

from pie_bench.checkpoints.hf_cache import hf_snapshot_dir
from pie_bench.engines import register
from pie_bench.engines.engine import EngineLaunchError
from pie_bench.schema import EngineName, ErrorClass

from .served import ServedEngine


@register
class MlxlmEngine(ServedEngine):
    name = EngineName.MLXLM
    exact_length = "logit_bias"

    def vlm(self) -> bool:
        return str(self.recipe.get("server_module") or "").startswith("mlx_vlm")

    @property
    def chat(self) -> bool:
        return self.vlm()

    def server_python(self) -> str:
        if self.vlm():
            return str(
                self.recipe.get("server_python")
                or os.environ.get("MLX_VLM_PY")
                or "/tmp/pievenv/bin/python"
            )
        return str(
            self.recipe.get("server_python")
            or os.environ.get("MLX_PY")
            or "/tmp/pievenv/bin/python"
        )

    def model_arg(self) -> str:
        if self.artifact.miniature is not None and self.recipe.get("snapshot_dir"):
            return str(self.recipe["snapshot_dir"])
        snap = hf_snapshot_dir(self.artifact.base_model, self.artifact.revision)
        if snap is None:
            raise EngineLaunchError(
                ErrorClass.LOAD_FAIL,
                f"no local snapshot for {self.artifact.base_model!r}; download it before benchmarking",
            )
        return str(snap)

    def draft_args(self) -> list[str]:
        snap = (
            hf_snapshot_dir(self.artifact.draft_model, None) if self.artifact.draft_model else None
        )
        if snap is None:
            raise EngineLaunchError(
                ErrorClass.LOAD_FAIL,
                f"no local snapshot of draft {self.artifact.draft_model!r} for {self.artifact.id}; download it before benchmarking",
            )
        args = ["--draft-model", str(snap)]
        if self.recipe.get("num_draft_tokens") is not None:
            args += ["--num-draft-tokens", str(int(self.recipe["num_draft_tokens"]))]
        return args

    def api_model(self) -> str:
        return self.model_arg()

    def server_cmd(self, port: int, slots: int, context: int) -> list[str]:
        r = self.recipe
        extra = r.get("server_extra") or []
        if isinstance(extra, str):
            extra = extra.split()
        module = str(r.get("server_module") or "mlx_lm server").split()
        if self.vlm():
            return [
                self.server_python(),
                "-m",
                *module,
                "--model",
                self.model_arg(),
                "--host",
                "127.0.0.1",
                "--port",
                str(port),
                "--max-num-seqs",
                str(slots),
                "--log-level",
                "ERROR",
                *[str(x) for x in extra],
            ]
        return [
            self.server_python(),
            "-m",
            *module,
            "--model",
            self.model_arg(),
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--decode-concurrency",
            str(slots),
            "--prompt-concurrency",
            str(int(r.get("prompt_concurrency", 8))),
            "--prompt-cache-size",
            str(int(r.get("prompt_cache_size", 0))),
            "--log-level",
            "ERROR",
            *[str(x) for x in extra],
        ]

    def extra_body(self) -> dict:
        return {"enable_thinking": False} if self.vlm() else {}

    def version(self) -> str:
        if self.vlm():
            out = subprocess.run(
                [self.server_python(), "-c", "import mlx_vlm; print(mlx_vlm.__version__)"],
                capture_output=True,
                text=True,
                timeout=120,
                check=False,
            )
            v = out.stdout.strip().splitlines()
            return f"mlx-vlm {v[-1]}" if out.returncode == 0 and v else "unknown"
        try:
            out = subprocess.run(
                [self.server_python(), "-c", "import mlx_lm; print(mlx_lm.__version__)"],
                capture_output=True,
                text=True,
                timeout=120,
                check=False,
            )
            v = out.stdout.strip().splitlines()
            return v[-1] if out.returncode == 0 and v else "unknown"
        except Exception:
            return "unknown"
