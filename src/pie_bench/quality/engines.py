from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from pie_bench.quality.servers import free_port, post, serve, stop
from pie_bench.schema import SourceFormat

ENGINES = ("pie", "llamacpp", "mlxlm", "splash")
PARALLEL = 4
SERVER_BOOT_S = 1800
MLXLM_TRIES = 6


def engine_for(art) -> str:
    if art.source_format == SourceFormat.GGUF:
        return "llamacpp"
    if art.source_format == SourceFormat.SPLASH:
        return "splash"
    if (art.baseline_label or "").lower() in ("mlx-lm", "mlx"):
        return "mlxlm"
    return "pie"


def strip_bos(rendered: str, bos: str | None) -> str:
    return rendered[len(bos) :] if bos and rendered.startswith(bos) else rendered


def adds_bos(snapshot: Path) -> bool:
    try:
        from transformers import AutoTokenizer

        tok = AutoTokenizer.from_pretrained(str(snapshot))
    except Exception:
        return True
    return tok.bos_token_id is not None and tok.encode("x")[:1] == [tok.bos_token_id]


def _version(argv: list[str]) -> str:
    try:
        out = subprocess.run(argv, capture_output=True, text=True, timeout=120, check=False)
    except OSError:
        return "unknown"
    text = (out.stdout or "") + "\n" + (out.stderr or "")
    build = re.search(r"(?:build|version:)\s*(\d{3,})", text)
    if build:
        return f"b{build.group(1)}"
    found = re.search(r"\d+\.\d+(?:\.\d+)?", text)
    return found.group(0) if found else "unknown"


def _map(fn, items: list) -> list[str]:
    with ThreadPoolExecutor(max_workers=PARALLEL) as pool:
        return list(pool.map(fn, items))


def mlxvlm_generate(
    snapshot: Path, rendered: list[str], max_tokens: int, bos: str | None, log
) -> tuple[list[str], str]:
    py = os.environ.get("MLX_VLM_PY") or "/tmp/pievenv/bin/python"
    script = Path(__file__).resolve().parent / "scripts" / "quality_mlxvlm.py"
    with tempfile.TemporaryDirectory() as tmp:
        items, out = Path(tmp) / "items.json", Path(tmp) / "out.json"
        items.write_text(
            json.dumps([{"prompt": strip_bos(p, bos), "max_tokens": max_tokens} for p in rendered])
        )
        subprocess.run(
            [py, str(script), str(snapshot), str(items), str(out)], check=True, timeout=12 * 3600
        )
        texts = json.loads(out.read_text())
    return texts, "mlx-vlm " + _version([py, "-c", "import mlx_vlm; print(mlx_vlm.__version__)"])


def _mlxlm_server_cmd(py: str, snapshot: Path, port: int) -> list[str]:
    return [
        *(py, "-m", "mlx_lm", "server", "--model", str(snapshot)),
        *("--host", "127.0.0.1", "--port", str(port)),
        *("--decode-concurrency", str(PARALLEL), "--prompt-concurrency", str(PARALLEL)),
        *("--prompt-cache-size", "0", "--log-level", "ERROR"),
    ]


def _require_loaded_model(url: str, snapshot: Path) -> None:
    try:
        post(
            f"{url}/v1/completions",
            {"model": str(snapshot), "prompt": "Hello", "max_tokens": 1},
            timeout=900,
        )
    except OSError as e:
        raise RuntimeError(f"mlx-lm loaded no model to answer with ({e})") from e


def mlxlm_generate(
    snapshot: Path,
    rendered: list[str],
    max_tokens: int,
    bos: str | None,
    log,
    family: str | None = None,
) -> tuple[list[str], str]:
    if family == "qwen4_exp":
        return mlxvlm_generate(snapshot, rendered, max_tokens, bos, log)
    py = os.environ.get("MLX_PY") or "/tmp/pievenv/bin/python"
    port = free_port()
    cmd = _mlxlm_server_cmd(py, snapshot, port)
    keep_bos = not adds_bos(snapshot)
    texts: list[str | None] = [None] * len(rendered)
    for attempt in range(MLXLM_TRIES):
        proc, url = serve(cmd, {}, port, "/v1/models", SERVER_BOOT_S)
        try:
            _require_loaded_model(url, snapshot)

            def one(i: int, url: str = url) -> None:
                p = rendered[i]
                body = {
                    "model": str(snapshot),
                    "prompt": p if keep_bos else strip_bos(p, bos),
                    "max_tokens": max_tokens,
                    "temperature": 0.0,
                    "top_p": 1.0,
                }
                texts[i] = post(f"{url}/v1/completions", body)["choices"][0].get("text", "")

            try:
                _map(one, [i for i, t in enumerate(texts) if t is None])
                break
            except OSError as e:
                if attempt == MLXLM_TRIES - 1:
                    raise
                log(
                    f"mlx-lm server died ({e}); {sum(t is None for t in texts)} prompts left, restarting it"
                )
        finally:
            stop(proc)
    return texts, _version([py, "-c", "import mlx_lm; print(mlx_lm.__version__)"])


def llamacpp_generate(
    art, rendered: list[str], max_tokens: int, bos: str | None, log
) -> tuple[list[str], str]:
    from huggingface_hub import hf_hub_download

    from pie_bench.checkpoints.snapshots import gguf_shards

    server = os.environ.get("LLAMA_SERVER_BIN") or "llama-server"
    gguf = [hf_hub_download(art.base_model, f) for f in gguf_shards(art.gguf_file)][0]
    port = free_port()
    cmd = [
        server,
        "--model",
        gguf,
        "--host",
        "127.0.0.1",
        "--port",
        str(port),
        "--ctx-size",
        str(4096 * PARALLEL),
        "--parallel",
        str(PARALLEL),
        "--n-gpu-layers",
        "all",
        "--flash-attn",
        "on",
    ]
    proc, url = serve(cmd, {}, port, "/health", SERVER_BOOT_S)
    try:

        def one(p: str) -> str:
            body = {
                "prompt": strip_bos(p, bos),
                "n_predict": max_tokens,
                "temperature": 0.0,
                "top_k": 1,
                "top_p": 1.0,
                "cache_prompt": False,
                "seed": 0,
            }
            return post(f"{url}/completion", body)["content"]

        texts = _map(one, rendered)
    finally:
        stop(proc)
    return texts, _version([server, "--version"])


def splash_generate(
    art, questions: list[str], system: str, max_tokens: int, log
) -> tuple[list[str], str]:
    binary = os.environ.get("SPLASH_BIN") or "splash"
    port = free_port()
    cmd = [
        binary,
        "serve",
        "--model",
        art.base_model,
        "--host",
        "127.0.0.1",
        "--port",
        str(port),
        "--no-webui",
    ]
    proc, url = serve(cmd, {}, port, "/v1/models", SERVER_BOOT_S)
    try:

        def one(q: str) -> str:
            body = {
                "model": art.base_model,
                "max_tokens": max_tokens,
                "temperature": 0.0,
                "top_p": 1.0,
                "reasoning_effort": "none",
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": q}],
            }
            return (
                post(f"{url}/v1/chat/completions", body)["choices"][0]["message"].get("content")
                or ""
            )

        texts = _map(one, questions)
    finally:
        stop(proc)
    return texts, _version([binary, "--version"])
