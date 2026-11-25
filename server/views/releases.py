from __future__ import annotations

import functools
import json
import os
import urllib.request
from zoneinfo import ZoneInfo

SITE_TZ = ZoneInfo("America/Los_Angeles")


def local(ts) -> str:
    return ts.astimezone(SITE_TZ).strftime("%Y-%m-%d %H:%M") if ts is not None else ""


def is_diag_tag(tag: str) -> bool:
    return "-diag-" in f"-{tag}-"


def tag_date(tag: str, meta: dict) -> str | None:
    if meta["kind"] != "release":
        return local(meta["at"])
    published = release_dates()
    if tag in published:
        return published[tag]
    try:
        return str(_github(f"repos/pie-project/pie/commits/{tag}")["commit"]["committer"]["date"])[
            :10
        ]
    except Exception:
        return None


@functools.cache
def release_dates() -> dict[str, str]:
    out: dict[str, str] = {}
    try:
        for page in (1, 2, 3):
            batch = _github(f"repos/pie-project/pie/releases?per_page=100&page={page}")
            out.update(
                {r["tag_name"]: str(r["published_at"])[:10] for r in batch if r.get("published_at")}
            )
            if len(batch) < 100:
                break
    except Exception:
        pass
    return out


@functools.cache
def _github(path: str) -> dict:
    req = urllib.request.Request(
        f"https://api.github.com/{path}",
        headers={"Accept": "application/vnd.github+json", "User-Agent": "pie-bench-api"},
    )
    if os.environ.get("GITHUB_TOKEN"):
        req.add_header("Authorization", f"Bearer {os.environ['GITHUB_TOKEN']}")
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read())
