from __future__ import annotations

import json
from pathlib import Path

from pie_bench.paths import CONFIG

SUITES = ("targeted", "full")
DEFAULT_SUITE = "targeted"


def suites(config: dict) -> dict[str, list[str]]:
    listed = dict(config.get("suites") or {})
    if not listed and config.get("models"):
        listed = {DEFAULT_SUITE: list(config["models"])}
    return {name: list(listed.get(name) or []) for name in SUITES}


def suite_models(config: dict, suite: str = DEFAULT_SUITE) -> list[str]:
    if suite not in SUITES:
        raise ValueError(f"unknown suite {suite!r} (have {', '.join(SUITES)})")
    return suites(config)[suite]


def all_models(config: dict) -> list[str]:
    return list(dict.fromkeys(a for arms in suites(config).values() for a in arms))


def load_config(path: Path | str = CONFIG) -> dict:
    p = Path(path)
    return json.loads(p.read_text()) if p.is_file() else {}
