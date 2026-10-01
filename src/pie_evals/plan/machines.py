"""Which Macs may be used. ``config.json`` lists them under ``machines``; a Mac
that is not listed is never given a job and never shown on the site, whoever
asks and however (a pushed commit, a manual run, the site's Bench button)."""

from __future__ import annotations

import json
from pathlib import Path


def allowed_macs(config: Path | str = "config.json") -> set[str] | None:
    """The Mac ids ``config.json`` allows, or None when it names none (every Mac is allowed)."""
    path = Path(config)
    if not path.is_file():
        return None
    listed = (json.loads(path.read_text()) or {}).get("machines") or []
    return set(listed) or None


def is_allowed(platform_id: str, os: str, allowed: set[str] | None) -> bool:
    return allowed is None or os != "macos" or platform_id in allowed
