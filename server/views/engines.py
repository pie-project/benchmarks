from __future__ import annotations

from server.views.matrix_files import load

ENGINE_META = {
    "pie": ("Pie", "Apache-2.0", "pie-project/pie"),
    "vllm": ("vLLM", "Apache-2.0", "vllm-project/vllm"),
    "sglang": ("SGLang", "Apache-2.0", "sgl-project/sglang"),
    "trtllm": ("TensorRT-LLM", "Apache-2.0", "NVIDIA/TensorRT-LLM"),
    "llamacpp": ("llama.cpp", "MIT", "ggml-org/llama.cpp"),
    "mlxlm": ("MLX", "MIT", "ml-explore/mlx-lm"),
    "vllm-metal": ("vLLM Metal", "Apache-2.0", "vllm-project/vllm-metal"),
    "webllm": ("WebLLM", "Apache-2.0", "mlc-ai/web-llm"),
    "llamacpp-webgpu": ("llama.cpp", "MIT", "ggml-org/llama.cpp"),
    "splash": ("Splash", None, "incoai/splash"),
    "litert": ("LiteRT-LM", "Apache-2.0", "google-ai-edge/LiteRT-LM"),
    "mlc": ("MLC LLM", "Apache-2.0", "mlc-ai/mlc-llm"),
    "mlx-swift": ("MLX Swift", "MIT", "ml-explore/mlx-swift-lm"),
    "ollama": ("Ollama", "MIT", "ollama/ollama"),
    "atom": ("ATOM", "MIT", "ROCm/ATOM"),
}
ENGINE_COLOR = {
    "trtllm": "#a2845e",
    "litert": "#34a853",
    "mlc": "#5856d6",
    "mlx-swift": "#ff9500",
    "webllm": "#5e5ce6",
    "llamacpp-webgpu": "#8e8e93",
    "ollama": "#bf5af2",
    "atom": "#d86ecc",
}


DECODING = {
    "pie": (True, True),
    "llamacpp": (True, True),
    "mlxlm": (True, True),
    "splash": (False, True),
    "vllm": (True, True),
    "sglang": (True, True),
    "trtllm": (True, False),
    "vllm-metal": (True, False),
    "litert": (True, False),
    "mlc": (True, False),
    "mlx-swift": (True, False),
    "webllm": (True, False),
    "llamacpp-webgpu": (True, False),
    "ollama": (True, False),
    "atom": (True, False),
}


def engines() -> list[dict]:
    rows = []
    for e in load("engines")["engines"]:
        name, lic, repo = ENGINE_META.get(e["id"], (e["id"], None, None))
        rows.append(
            {
                "id": e["id"],
                "name": name,
                "version": e.get("pin") or "main",
                "license": lic,
                "repo": repo,
                "os": ", ".join(e.get("os", [])),
                "formats": ", ".join(e.get("formats", [])),
                "backends": ", ".join(e.get("backends", [])),
                **({"color": ENGINE_COLOR[e["id"]]} if e["id"] in ENGINE_COLOR else {}),
                **dict(
                    zip(
                        ("raw", "speculation"),
                        ("Yes" if ok else "No" for ok in DECODING.get(e["id"], (True, False))),
                    )
                ),
            }
        )
    return rows


def install_sizes() -> list[dict]:
    data = load("install")
    known = {e["id"] for e in load("engines")["engines"]}
    rows = []
    for platform, entries in data["install"].items():
        for e in entries:
            if e["engine"] not in known:
                raise ValueError(
                    f"matrix/install.yaml: {e['engine']} is not an engine in matrix/engines.yaml"
                )
            rows.append(
                {
                    "platform": platform,
                    "engine": e["engine"],
                    "version": str(e["version"]),
                    "bytes": int(e["bytes"]),
                    "method": " ".join(e["method"].split()),
                    "source": " ".join(e["source"].split()),
                    "parts": [[str(label), int(n)] for label, n in e.get("parts") or []],
                    "measured": str(e.get("measured") or data["measured"]),
                }
            )
    return rows
