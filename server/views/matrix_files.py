from __future__ import annotations

import yaml

from pie_bench.paths import MATRIX

CONTRIBUTED: dict[str, dict] = {}


def catalog(name: str) -> dict:
    return yaml.safe_load((MATRIX / f"{name}.yaml").read_text())


def load(name: str) -> dict:
    data = catalog(name)
    if name == "platforms":
        known = {p["id"] for p in data["platforms"]}
        data["platforms"] += [p for pid, p in CONTRIBUTED.items() if pid not in known]
    return data


def contributed_platform(spec: dict) -> dict:
    return {**spec, "tiers": ["community"], "contributed": True}
