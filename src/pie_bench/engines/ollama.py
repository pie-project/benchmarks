from __future__ import annotations

import hashlib
import os
import re
import subprocess
from pathlib import Path

from pie_bench.engines import register
from pie_bench.engines.engine import EngineLaunchError
from pie_bench.schema import EngineName, ErrorClass, WorkloadSpec

from .llamacpp import LlamacppEngine
from .served import ServedEngine


@register
class OllamaEngine(ServedEngine):
    name = EngineName.OLLAMA
    health_path = "/api/version"
    exact_length = "ignore_eos"
    one_request_server = True

    gguf_path = LlamacppEngine.gguf_path
    model_arg = LlamacppEngine.model_arg

    def server_bin(self) -> str:
        return str(self.recipe.get("server_bin") or os.environ.get("OLLAMA_BIN") or "ollama")

    def models_dir(self) -> Path:
        return Path(os.environ.get("OLLAMA_MODELS") or Path.home() / ".pie-bench" / "ollama-models")

    def tag(self) -> str:
        return "piebench-" + hashlib.sha1(str(self.gguf_path()).encode()).hexdigest()[:12]

    def api_model(self) -> str:
        return self.tag()

    def server_cmd(self, port: int, slots: int, context: int) -> list[str]:
        self._shape = (port, slots, context)
        return [self.server_bin(), "serve"]

    def server_env(self) -> dict[str, str]:
        port, slots, context = self._shape
        return {
            "OLLAMA_HOST": f"127.0.0.1:{port}", "OLLAMA_MODELS": str(self.models_dir()),
            "OLLAMA_NUM_PARALLEL": str(slots), "OLLAMA_CONTEXT_LENGTH": str(context),
            "OLLAMA_FLASH_ATTENTION": "1" if self.recipe.get("flash_attn", "on") == "on" else "0",
            "OLLAMA_KEEP_ALIVE": "-1", "OLLAMA_MAX_LOADED_MODELS": "1",
        }

    def serve(self, workload: WorkloadSpec, log_path: Path, timeout_s: int) -> None:
        fresh = self._server_proc is None
        super().serve(workload, log_path, timeout_s)
        if not fresh:
            return
        modelfile = Path(log_path).with_suffix(".Modelfile")
        modelfile.write_text(f"FROM {self.single_gguf(timeout_s)}\nTEMPLATE {{{{ .Prompt }}}}\n")
        out = subprocess.run([self.server_bin(), "create", self.tag(), "-f", str(modelfile)], env=self.process_env(self.server_env()),
                             capture_output=True, text=True, timeout=timeout_s)
        if out.returncode != 0:
            self.stop()
            raise EngineLaunchError(ErrorClass.LOAD_FAIL, f"ollama create failed: {(out.stderr or out.stdout).strip()[-400:]}")

    def single_gguf(self, timeout_s: int) -> Path:
        path = self.gguf_path()
        m = re.match(r"(.+)-00001-of-(\d{5})\.gguf$", path.name)
        if not m or not path.with_name(f"{m.group(1)}-00002-of-{m.group(2)}.gguf").exists():
            return path
        merged = self.models_dir().parent / "ollama-merged" / f"{m.group(1)}.gguf"
        if merged.exists():
            return merged
        tool = Path(os.environ.get("LLAMA_SERVER_BIN") or "llama-server").with_name("llama-gguf-split" + (".exe" if os.name == "nt" else ""))
        merged.parent.mkdir(parents=True, exist_ok=True)
        tmp = merged.with_suffix(".part")
        out = subprocess.run([str(tool), "--merge", str(path), str(tmp)], capture_output=True, text=True, timeout=timeout_s)
        if out.returncode != 0 or not tmp.exists():
            raise EngineLaunchError(ErrorClass.LOAD_FAIL, f"merging the split GGUF failed: {(out.stderr or out.stdout).strip()[-300:]}")
        os.replace(tmp, merged)
        return merged

    def version(self) -> str:
        try:
            out = subprocess.run([self.server_bin(), "--version"], capture_output=True, text=True, timeout=30, check=False)
        except Exception:
            return "unknown"
        m = re.search(r"version is (\S+)", (out.stdout or "") + (out.stderr or ""))
        return m.group(1) if m else "unknown"

    def leftover_process_names(self) -> list[str]:
        return ["ollama", "llama-server"]
