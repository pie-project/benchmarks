from __future__ import annotations

import importlib

from pie_bench.engines.engine import Engine
from pie_bench.schema import EngineName

_REGISTRY: dict[str, type[Engine]] = {}


def register(cls: type[Engine]) -> type[Engine]:
    backend = getattr(cls, "only_backend", None)
    _REGISTRY[f"{cls.name}@{backend}" if backend else str(cls.name)] = cls
    return cls


ADAPTERS = (
    "atom",
    "browser.webgpu",
    "llamacpp",
    "mlxlm",
    "ollama",
    "pie",
    "sglang",
    "splash",
    "trtllm",
    "vllm",
    "vllm_metal",
)


def get_engine(name: str | EngineName, backend: str | None = None) -> type[Engine]:
    for module in ADAPTERS:
        importlib.import_module(f"{__package__}.{module}")
    return _REGISTRY.get(f"{name}@{backend}") or _REGISTRY[str(name)]
