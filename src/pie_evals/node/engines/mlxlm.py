"""mlx-lm adapter: boots ``python -m mlx_lm server`` on one MLX checkpoint and
streams from it (macOS only).

mlx-lm's server has no ``ignore_eos``, so a request may stop before its token
budget; the summary counts those as ``short_responses``.
"""

from __future__ import annotations

import os
import subprocess

from pie_evals.schema import EngineName, ErrorClass

from .base import EngineLaunchError, register
from .served import ServedEngine
from .shape import hf_snapshot_dir


@register
class MlxlmEngine(ServedEngine):
    name = EngineName.MLXLM
    # mlx-lm has no ignore_eos, but from 0.32 its batched server applies logit_bias: blocking the special
    # tokens makes every request write exactly max_tokens (0.31.3 dropped the bias on that path)
    exact_length = "logit_bias"

    def server_python(self) -> str:
        """The interpreter that has the pinned mlx-lm (not the bench client's)."""
        return str(self.recipe.get("server_python") or os.environ.get("MLX_PY") or "/tmp/pievenv/bin/python")

    def model_arg(self) -> str:
        """Snapshot directory of the MLX checkpoint (mlx-lm and the tokenizer
        both read it from disk; an HF id would make mlx-lm try the network)."""
        snap = hf_snapshot_dir(self.artifact.base_model, self.artifact.revision)
        if snap is None:
            raise EngineLaunchError(
                ErrorClass.LOAD_FAIL,
                f"no local snapshot for {self.artifact.base_model!r}; download it before benchmarking",
            )
        return str(snap)

    def draft_args(self) -> list[str]:
        """``--draft-model``: a separate draft checkpoint. mlx-lm then serves one request at a
        time (a draft makes its server unbatchable), which a single-stream row is anyway."""
        snap = hf_snapshot_dir(self.artifact.draft_model, None) if self.artifact.draft_model else None
        if snap is None:
            raise EngineLaunchError(ErrorClass.LOAD_FAIL, f"no local snapshot of draft {self.artifact.draft_model!r} for {self.artifact.id}; download it before benchmarking")
        args = ["--draft-model", str(snap)]
        if self.recipe.get("num_draft_tokens") is not None:
            args += ["--num-draft-tokens", str(int(self.recipe["num_draft_tokens"]))]
        return args

    def api_model(self) -> str:
        # mlx-lm loads whatever a request names; naming the served path keeps it on the loaded model
        return self.model_arg()

    def server_cmd(self, port: int, slots: int, context: int) -> list[str]:
        r = self.recipe
        extra = r.get("server_extra") or []
        if isinstance(extra, str):
            extra = extra.split()
        module = str(r.get("server_module") or "mlx_lm server").split()
        return [
            self.server_python(), "-m", *module, "--model", self.model_arg(), "--host", "127.0.0.1", "--port", str(port),
            "--decode-concurrency", str(slots), "--prompt-concurrency", str(int(r.get("prompt_concurrency", 8))),
            # 0 keeps the prompt cache out of the measurement; the prefix_shared recipe turns it on
            "--prompt-cache-size", str(int(r.get("prompt_cache_size", 0))), "--log-level", "ERROR",
            *[str(x) for x in extra],
        ]

    def version(self) -> str:
        try:
            out = subprocess.run(
                [self.server_python(), "-c", "import mlx_lm; print(mlx_lm.__version__)"],
                capture_output=True, text=True, timeout=120, check=False,
            )
            v = out.stdout.strip().splitlines()
            return v[-1] if out.returncode == 0 and v else "unknown"
        except Exception:
            return "unknown"

    def leftover_process_names(self) -> list[str]:
        # the server is `python -m mlx_lm server`; its process name is the
        # interpreter's, which cannot be swept by name.
        return []
