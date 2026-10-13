"""Which models a run measures. ``config.json`` keeps two suites of competitor arms under
``suites``: ``targeted`` (Tier 1, what a release runs) and ``full`` (every model on the
site). They differ only in the list; each arm brings the pie artifact it is compared with
(its ``baseline_of``). A config with only the older ``models`` list reads it as ``targeted``."""

from __future__ import annotations

import json
from pathlib import Path

SUITES = ("targeted", "full")
DEFAULT_SUITE = "targeted"


def suites(config: dict) -> dict[str, list[str]]:
    """{suite: [arm ids]}, every suite named; ``models`` stands in for a config without ``suites``."""
    listed = dict(config.get("suites") or {})
    if not listed and config.get("models"):
        listed = {DEFAULT_SUITE: list(config["models"])}
    return {name: list(listed.get(name) or []) for name in SUITES}


def suite_models(config: dict, suite: str = DEFAULT_SUITE) -> list[str]:
    if suite not in SUITES:
        raise ValueError(f"unknown suite {suite!r} (have {', '.join(SUITES)})")
    return suites(config)[suite]


def all_models(config: dict) -> list[str]:
    """Every arm of every suite, once, in suite order."""
    return list(dict.fromkeys(a for arms in suites(config).values() for a in arms))


def load_config(path: Path | str = "config.json") -> dict:
    p = Path(path)
    return json.loads(p.read_text()) if p.is_file() else {}
