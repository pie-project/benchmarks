from __future__ import annotations

import os
import re
import shutil
import subprocess
from typing import Any

from pie_bench.checkpoints.hf_cache import hf_snapshot_dir
from pie_bench.engines import register
from pie_bench.schema import EngineName

from .served import ServedEngine

LOCAL_ORG = "pie-local/"


def splash_bin() -> str:
    return os.environ.get("SPLASH_BIN") or shutil.which("splash") or "/opt/homebrew/bin/splash"


@register
class SplashEngine(ServedEngine):
    name = EngineName.SPLASH
    chat = True
    exact_length = "ignore_eos"

    def extra_body(self) -> dict[str, Any]:
        return {"reasoning_effort": "none"}

    def model_arg(self) -> str:
        if self.artifact.gguf_file and self.artifact.tokenizer_from:
            snap = hf_snapshot_dir(self.artifact.tokenizer_from, None)
            return str(snap) if snap is not None else self.artifact.tokenizer_from
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
        if self.artifact.base_model.startswith(LOCAL_ORG) or self.artifact.gguf_file:
            snap = hf_snapshot_dir(self.artifact.base_model, self.artifact.revision)
            if snap is not None:
                cmd += ["--model-dir", str(snap / self.artifact.gguf_file if self.artifact.gguf_file else snap)]
        if r.get("queue_size") is not None:
            cmd += ["--queue-size", str(slots if r["queue_size"] == "$serve_concurrency" else r["queue_size"])]
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
