"""The engines a quality run can score a model on, and how each one generates.

Every engine gets the same rendered prompt (the chat template of the checkpoint's
own tokenizer) and greedy decoding, so the answers can be compared exactly. A
server that only takes chat messages (Splash) gets the raw question instead and
renders its own template; its output is not compared exactly.
"""

from __future__ import annotations

import json
import os
import re
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from pie_evals.schema import SourceFormat

ENGINES = ("pie", "llamacpp", "mlxlm", "splash")
PARALLEL = 4


def engine_for(art) -> str:
    """The engine an artifact runs on, read from its format (and its label for mlx-lm, the one MLX arm that is not pie)."""
    if art.source_format == SourceFormat.GGUF:
        return "llamacpp"
    if art.source_format == SourceFormat.SPLASH:
        return "splash"
    if (art.baseline_label or "").lower() == "mlx-lm":
        return "mlxlm"
    return "pie"


def strip_bos(rendered: str, bos: str | None) -> str:
    """Servers add the BOS token themselves; a rendered template already carries it, so one copy is removed."""
    return rendered[len(bos):] if bos and rendered.startswith(bos) else rendered


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def _get(url: str, timeout: float = 5.0) -> bytes:
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return r.read()


def _post(url: str, body: dict, timeout: float = 1200.0) -> dict:
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def _version(argv: list[str]) -> str:
    try:
        out = subprocess.run(argv, capture_output=True, text=True, timeout=120, check=False)
    except OSError:
        return "unknown"
    text = (out.stdout or "") + "\n" + (out.stderr or "")
    # llama-server prints "version: 11312 (commit)" or "(build 11312, ...)": its release tag is b<build>
    build = re.search(r"(?:build|version:)\s*(\d{3,})", text)
    if build:
        return f"b{build.group(1)}"
    found = re.search(r"\d+\.\d+(?:\.\d+)?", text)
    return found.group(0) if found else "unknown"


def _serve(cmd: list[str], env: dict[str, str], port: int, health: str, timeout_s: float):
    """Boots one server (under the lifeline wrapper, so it dies with us) and waits until ``health`` answers."""
    url = f"http://127.0.0.1:{port}"
    log = tempfile.NamedTemporaryFile("w", prefix="quality-server-", suffix=".log", delete=False)
    proc = subprocess.Popen([sys.executable, "-m", "pie_evals.node.engines.lifeline", *cmd], env={**os.environ, **env},
                            stdin=subprocess.PIPE, stdout=log, stderr=subprocess.STDOUT)
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            raise RuntimeError(f"{cmd[0]} exited during startup (see {log.name})")
        try:
            _get(url + health, timeout=3)
            return proc, url
        except OSError:
            time.sleep(0.5)
    _stop(proc)
    raise RuntimeError(f"{cmd[0]} did not answer {health} within {timeout_s:.0f}s (see {log.name})")


def _stop(proc) -> None:
    proc.terminate()
    try:
        proc.wait(timeout=30)
    except subprocess.TimeoutExpired:
        proc.kill()


def _map(fn, items: list) -> list[str]:
    with ThreadPoolExecutor(max_workers=PARALLEL) as pool:
        return list(pool.map(fn, items))


def mlxlm_generate(snapshot: Path, rendered: list[str], max_tokens: int, bos: str | None, log) -> tuple[list[str], str]:
    py = os.environ.get("MLX_PY") or "/tmp/pievenv/bin/python"
    port = _free_port()
    cmd = [py, "-m", "mlx_lm", "server", "--model", str(snapshot), "--host", "127.0.0.1", "--port", str(port),
           "--decode-concurrency", str(PARALLEL), "--prompt-concurrency", str(PARALLEL), "--prompt-cache-size", "0", "--log-level", "ERROR"]
    proc, url = _serve(cmd, {}, port, "/v1/models", 1800)
    try:
        def one(p: str) -> str:
            body = {"model": str(snapshot), "prompt": strip_bos(p, bos), "max_tokens": max_tokens, "temperature": 0.0, "top_p": 1.0}
            return _post(f"{url}/v1/completions", body)["choices"][0].get("text", "")

        texts = _map(one, rendered)
    finally:
        _stop(proc)
    return texts, _version([py, "-c", "import mlx_lm; print(mlx_lm.__version__)"])


def llamacpp_generate(art, rendered: list[str], max_tokens: int, bos: str | None, log) -> tuple[list[str], str]:
    from huggingface_hub import hf_hub_download

    server = os.environ.get("LLAMA_SERVER_BIN") or "llama-server"
    gguf = hf_hub_download(art.base_model, art.gguf_file)
    port = _free_port()
    cmd = [server, "--model", gguf, "--host", "127.0.0.1", "--port", str(port), "--ctx-size", str(4096 * PARALLEL),
           "--parallel", str(PARALLEL), "--n-gpu-layers", "all", "--flash-attn", "on"]
    proc, url = _serve(cmd, {}, port, "/health", 1800)
    try:
        def one(p: str) -> str:
            # the native endpoint takes the rendered text as it is: greedy (top_k 1), no prompt cache reuse
            body = {"prompt": strip_bos(p, bos), "n_predict": max_tokens, "temperature": 0.0, "top_k": 1, "top_p": 1.0,
                    "cache_prompt": False, "seed": 0}
            return _post(f"{url}/completion", body)["content"]

        texts = _map(one, rendered)
    finally:
        _stop(proc)
    return texts, _version([server, "--version"])


def splash_generate(art, questions: list[str], system: str, max_tokens: int, log) -> tuple[list[str], str]:
    binary = os.environ.get("SPLASH_BIN") or "splash"
    port = _free_port()
    cmd = [binary, "serve", "--model", art.base_model, "--host", "127.0.0.1", "--port", str(port), "--no-webui"]
    proc, url = _serve(cmd, {}, port, "/v1/models", 1800)
    try:
        def one(q: str) -> str:
            body = {"model": art.base_model, "max_tokens": max_tokens, "temperature": 0.0, "top_p": 1.0, "reasoning_effort": "none",
                    "messages": [{"role": "system", "content": system}, {"role": "user", "content": q}]}
            return _post(f"{url}/v1/chat/completions", body)["choices"][0]["message"].get("content") or ""

        texts = _map(one, questions)
    finally:
        _stop(proc)
    return texts, _version([binary, "--version"])
