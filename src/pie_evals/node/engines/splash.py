"""Splash adapter: boots ``splash serve`` on one upstream model and streams
from it (Apple Silicon only).

Splash fetches and prepares the model itself the first time it serves it, pairs
it with its own draft model, and batches concurrent requests on its own, so the
server takes only the model, the port and the context limit. It serves chat
completions, so it gets the user's words and renders the chat template itself.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from typing import Any

from pie_evals.schema import EngineName

from .base import register
from .served import ServedEngine
from .shape import hf_snapshot_dir


def splash_bin() -> str:
    return os.environ.get("SPLASH_BIN") or shutil.which("splash") or "/opt/homebrew/bin/splash"


@register
class SplashEngine(ServedEngine):
    name = EngineName.SPLASH
    chat = True  # Splash 1.1 serves chat completions only
    # Splash rejects logit_bias (400) but honours ignore_eos: every request writes exactly max_tokens (1.3.2)
    exact_length = "ignore_eos"

    def extra_body(self) -> dict[str, Any]:
        # the shared client renders every other engine's prompt with thinking off
        return {"reasoning_effort": "none"}

    def model_arg(self) -> str:
        """Tokenizer source: the local snapshot of the model Splash serves."""
        snap = hf_snapshot_dir(self.artifact.base_model, self.artifact.revision)
        return str(snap) if snap is not None else self.artifact.base_model

    def api_model(self) -> str:
        return self.artifact.base_model

    def server_cmd(self, port: int, slots: int, context: int) -> list[str]:
        r = self.recipe
        extra = r.get("server_extra") or []
        if isinstance(extra, str):
            extra = extra.split()
        cmd = [splash_bin(), "serve", "--model", self.artifact.base_model, "--host", "127.0.0.1", "--port", str(port), "--no-webui"]
        if r.get("max_context") is not None:
            cmd += ["--max-context", str(context if r["max_context"] == "$serve_context" else r["max_context"])]
        return cmd + [str(x) for x in extra]

    def version(self) -> str:
        try:
            out = subprocess.run([splash_bin(), "--version"], capture_output=True, text=True, timeout=30, check=False)
        except OSError:
            return "unknown"
        found = re.findall(r"(\d+\.\d+(?:\.\d+)?)", (out.stdout or "") + (out.stderr or ""))
        return found[-1] if found else "unknown"

    def leftover_process_names(self) -> list[str]:
        return []
