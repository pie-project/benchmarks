"""Keep baselines current: check PyPI / GitHub releases against the pins in
engines.yaml and report what is newer. The nightly workflow bumps the lock
and re-runs baseline cells when this reports a change."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from pie_evals.plan.matrix import Matrix


@dataclass
class ReleaseCheck:
    engine: str
    pinned: str | None
    latest: str | None
    newer: bool
    source: str


def _pypi_latest(pkg: str) -> str | None:
    import requests

    r = requests.get(f"https://pypi.org/pypi/{pkg}/json", timeout=30)
    if r.status_code != 200:
        return None
    return r.json()["info"]["version"]


def _github_latest(repo: str) -> str | None:
    import requests

    r = requests.get(f"https://api.github.com/repos/{repo}/releases/latest", timeout=30, headers={"Accept": "application/vnd.github+json"})
    if r.status_code != 200:
        return None
    if _has_binaries(r.json()):
        return r.json().get("tag_name")
    # llama.cpp's v0.9.0 (2026-11-04) is "latest" with only nightly-tag.txt, its b-builds marked pre-release: a pin
    # without binaries leaves every Mac with no llama-server, so take the newest release that ships them
    r = requests.get(f"https://api.github.com/repos/{repo}/releases", timeout=30, params={"per_page": 20}, headers={"Accept": "application/vnd.github+json"})
    if r.status_code != 200:
        return None
    return next((x["tag_name"] for x in r.json() if not x.get("draft") and _has_binaries(x)), None)


def _has_binaries(release: dict) -> bool:
    return any(not a["name"].endswith(".txt") for a in release.get("assets") or [])


def _github_newest(repo: str) -> str | None:
    """The newest non-draft release, pre-releases included."""
    import requests

    r = requests.get(f"https://api.github.com/repos/{repo}/releases", timeout=30, params={"per_page": 20}, headers={"Accept": "application/vnd.github+json"})
    if r.status_code != 200:
        return None
    return next((x["tag_name"] for x in r.json() if not x.get("draft") and _has_binaries(x)), None)


def _vkey(v: str) -> tuple:
    nums = [int(x) for x in re.findall(r"\d+", v)]
    return tuple(nums)


def check(matrix: Matrix) -> list[ReleaseCheck]:
    out = []
    for e in matrix.engines.values():
        if not e.release_source:
            continue
        kind, ident = e.release_source.split(":", 1)
        latest = _pypi_latest(ident) if kind == "pypi" else _github_latest(ident)
        newer = bool(latest and e.pin and _vkey(latest) > _vkey(e.pin))
        out.append(ReleaseCheck(e.id, e.pin, latest, newer, e.release_source))
    return out


def write_lock(checks: list[ReleaseCheck], path: Path) -> None:
    path.write_text(json.dumps({c.engine: {"pinned": c.pinned, "latest": c.latest, "newer": c.newer} for c in checks}, indent=1) + "\n")
