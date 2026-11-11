from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from pie_bench.schema import PlatformSpec, WorkloadSpec

from ..shape import max_model_len_for, workload_concurrency, workload_num_requests

RECIPE_DIR = Path(__file__).resolve().parent

_OVERRIDE_AXES = ("family", "arch", "backend", "workload_kind", "artifact", "platform")


def recipe_path(engine: str) -> Path:
    return RECIPE_DIR / f"{engine}.yaml"


def _load_yaml(engine: str) -> dict[str, Any]:
    path = recipe_path(engine)
    if not path.is_file():
        raise FileNotFoundError(f"no recipe file for engine {engine!r}: {path}")
    data = yaml.safe_load(path.read_text()) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{path}: top level must be a mapping of recipe names")
    return data


def _split_knob(raw: Any) -> tuple[Any, str]:
    if isinstance(raw, dict) and "value" in raw:
        return raw["value"], str(raw.get("rationale", ""))
    return raw, ""


def _merge_knobs(into: dict[str, Any], rationale: dict[str, str], knobs: dict[str, Any] | None) -> None:
    for k, raw in (knobs or {}).items():
        v, why = _split_knob(raw)
        into[k] = v
        if why:
            rationale[k] = why


def _section_chain(data: dict[str, Any], name: str) -> list[dict[str, Any]]:
    chain: list[dict[str, Any]] = []
    seen: set[str] = set()
    cur: str | None = name
    while cur:
        if cur in seen:
            raise ValueError(f"recipe {name!r}: cyclic extends through {cur!r}")
        seen.add(cur)
        section = data.get(cur)
        if section is None:
            raise KeyError(f"recipe section {cur!r} not found (have {sorted(data)})")
        chain.append(section or {})
        cur = (section or {}).get("extends")
    chain.reverse()
    return chain


def _resolve_value(v: Any, subs: dict[str, Any]) -> Any:
    if isinstance(v, str) and v.startswith("$"):
        key = v[1:]
        if key not in subs:
            raise KeyError(f"unknown recipe substitution {v!r} (have {sorted('$' + s for s in subs)})")
        return subs[key]
    if isinstance(v, list):
        return [_resolve_value(x, subs) for x in v]
    if isinstance(v, dict):
        return {k: _resolve_value(x, subs) for k, x in v.items()}
    return v


def load_recipe(engine: str, name: str, platform: PlatformSpec, workload: WorkloadSpec, family: str | None = None, artifact: str | None = None) -> dict[str, Any]:
    data = _load_yaml(engine)
    knobs: dict[str, Any] = {}
    rationale: dict[str, str] = {}
    selectors = {
        "family": family or "",
        "arch": platform.arch,
        "backend": str(platform.backend),
        "workload_kind": str(workload.kind),
        "artifact": artifact or "",
        "platform": platform.id,
    }
    for section in _section_chain(data, name):
        _merge_knobs(knobs, rationale, section.get("knobs"))
        for axis in _OVERRIDE_AXES:
            override = (section.get(axis) or {}).get(selectors[axis])
            if override:
                _merge_knobs(knobs, rationale, override.get("knobs", override))
                for inner in _OVERRIDE_AXES:
                    exc = (override.get(inner) or {}).get(selectors[inner]) if inner != axis else None
                    if exc:
                        _merge_knobs(knobs, rationale, exc.get("knobs", exc))
    subs = {
        "concurrency": workload_concurrency(workload),
        "num_requests": workload_num_requests(workload),
        "max_model_len": max_model_len_for(workload),
        "serve_concurrency": "$serve_concurrency",
        "serve_context": "$serve_context",
    }
    out = {k: _resolve_value(v, subs) for k, v in knobs.items()}
    out["_recipe"] = name
    out["_rationale"] = rationale
    return out


def recipe_names(engine: str) -> list[str]:
    return sorted(k for k in _load_yaml(engine) if k != "fork")


def recipe_fork(engine: str) -> dict[str, Any] | None:
    path = recipe_path(engine)
    return (yaml.safe_load(path.read_text()) or {}).get("fork") if path.is_file() else None


__all__ = ["RECIPE_DIR", "load_recipe", "recipe_fork", "recipe_names", "recipe_path"]
