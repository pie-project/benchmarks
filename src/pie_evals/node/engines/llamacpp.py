"""llama.cpp adapter: boots ``llama-server`` on one GGUF and streams from it.

``--model`` of the bench script is the TOKENIZER source (the chat template is
rendered with ``transformers.AutoTokenizer``); the GGUF file goes to the
server. A GGUF repo ships no tokenizer, so it comes from the checkpoint the
GGUF was converted from.
"""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path
from typing import Any

from pie_evals.schema import EngineName, ErrorClass

from .base import EngineLaunchError, register
from .served import ServedEngine
from .shape import hf_snapshot_dir, hf_snapshot_file

_TOKENIZER_FILES = ("tokenizer.json", "tokenizer_config.json", "tokenizer.model")


@register
class LlamacppEngine(ServedEngine):
    name = EngineName.LLAMACPP
    health_path = "/health"  # 503 while the model loads
    # llama-server honours ignore_eos: every request writes exactly max_tokens (checked on b11703)
    exact_length = "ignore_eos"
    # llama-server adds BOS to a text prompt that already starts with the template's BOS
    token_ids = True

    # ---- inputs ------------------------------------------------------------
    def server_bin(self) -> str:
        return str(self.recipe.get("server_bin") or os.environ.get("LLAMA_SERVER_BIN") or "llama-server")

    def gguf_path(self) -> Path:
        a = self.artifact
        if not a.gguf_file:
            raise EngineLaunchError(ErrorClass.LOAD_FAIL, f"artifact {a.id}: gguf_file not set (the arm must be named)")
        p = Path(a.gguf_file).expanduser()
        if p.is_absolute() and p.is_file():
            return p
        # a model slice is cut beside the repo's snapshots (miniature.py); the runner names its dir
        if a.miniature is not None and self.recipe.get("snapshot_dir"):
            return Path(self.recipe["snapshot_dir"]) / Path(a.gguf_file).name
        found = hf_snapshot_file(a.base_model, a.gguf_file, a.revision)
        if found is None:
            raise EngineLaunchError(
                ErrorClass.LOAD_FAIL,
                f"{a.gguf_file} not found in cache for {a.base_model}: resolve_local_model would fail; download it before benchmarking",
            )
        return found

    def draft_path(self) -> Path:
        """The draft GGUF (the artifact's ``draft_model`` / ``draft_gguf_file``), fetched with the artifact."""
        a = self.artifact
        found = hf_snapshot_file(a.draft_model, a.draft_gguf_file, None) if a.draft_model and a.draft_gguf_file else None
        if found is None:
            raise EngineLaunchError(ErrorClass.LOAD_FAIL, f"draft {a.draft_gguf_file} of {a.draft_model} not in cache for {a.id}; download it before benchmarking")
        return found

    def draft_args(self) -> list[str]:
        """A separate draft model (``--spec-type draft-simple``), fully offloaded like the target.
        ``draft_max``/``draft_min`` unset keep llama-server's own defaults (3 / 0)."""
        r = self.recipe
        args = ["--spec-type", "draft-simple", "--model-draft", str(self.draft_path()),
                "--n-gpu-layers-draft", str(r.get("draft_gpu_layers", "all"))]
        if r.get("draft_max") is not None:
            args += ["--spec-draft-n-max", str(r["draft_max"])]
        if r.get("draft_min") is not None:
            args += ["--spec-draft-n-min", str(r["draft_min"])]
        return args

    def model_arg(self) -> str:
        """Tokenizer source for ``--model``: recipe ``tokenizer_model``, else the
        GGUF repo's own snapshot when it ships a tokenizer, else the checkpoint
        named by ``tokenizer_from``, else the repo name minus ``-GGUF``."""
        if self.recipe.get("tokenizer_model"):
            return str(self.recipe["tokenizer_model"])
        for repo in (self.artifact.base_model, self.artifact.tokenizer_from or self.artifact.gguf_config_from):
            snap = hf_snapshot_dir(repo, self.artifact.revision if repo == self.artifact.base_model else None) if repo else None
            if snap is not None and any((snap / f).is_file() for f in _TOKENIZER_FILES):
                return str(snap)
        return self.artifact.tokenizer_from or self.artifact.gguf_config_from or re.sub(r"[-_]GGUF$", "", self.artifact.base_model, flags=re.IGNORECASE)

    # ---- server ------------------------------------------------------------
    def server_cmd(self, port: int, slots: int, context: int) -> list[str]:
        r = self.recipe
        extra = r.get("server_extra") or []
        if isinstance(extra, str):
            extra = extra.split()
        extra = [str(x) for x in extra]
        if self.mode.tp > 1 and "--split-mode" not in extra:
            # llama.cpp has no TP proper; row split is its closest shape.
            extra += ["--split-mode", str(r.get("split_mode", "row"))]
        return [
            self.server_bin(), "--model", str(self.gguf_path()), "--host", "127.0.0.1", "--port", str(port),
            # llama.cpp splits --ctx-size ACROSS the slots, so a slot gets `context`
            "--ctx-size", str(context * slots), "--parallel", str(slots),
            "--n-gpu-layers", str(r.get("gpu_layers", "all")), "--flash-attn", str(r.get("flash_attn", "on")),
            *extra,
        ]

    def extra_body(self) -> dict[str, Any]:
        return {"cache_prompt": bool(self.recipe.get("cache_prompt", False))}

    # ---- provenance --------------------------------------------------------
    def version(self) -> str:
        """The release tag (``b11312``), which is what the matrix pins: the
        binary prints it as ``version: 11312 (commit)`` or ``(build 11312, ...)``."""
        try:
            out = subprocess.run([self.server_bin(), "--version"], capture_output=True, text=True, timeout=30, check=False)
        except Exception:
            return "unknown"
        text = (out.stdout or "") + "\n" + (out.stderr or "")
        m = re.search(r"build\s+(\d{3,})", text) or re.search(r"version:\s*(\d{3,})", text)
        if m:
            return f"b{m.group(1)}"
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        return lines[0][:80] if lines else "unknown"

    def leftover_process_names(self) -> list[str]:
        return ["llama-server"]
