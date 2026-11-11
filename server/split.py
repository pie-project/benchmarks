from __future__ import annotations

import gzip
import io
import json
import re

BETA = re.compile(r"^\d+\.\d+\.\d+-b\d+$")
PLATFORMS = ["Mac", "GPU", "TPU", "AMD", "Wafer"]


def shown(db: dict) -> set[str]:
    snaps = db.get("snapshots") or {}
    tags = db.get("tags") or []
    have = [t for t in tags if snaps.get(t["id"])]
    keep = {t["id"] for t in have if t.get("kind") == "release"}
    keep |= {next((t["id"] for t in have if t.get("kind") != "release"), None), next((t["id"] for t in have if BETA.match(t["id"])), None)}
    keep |= {have[0]["id"] if have else None, tags[0]["id"] if tags else None}
    return keep - {None}


def counts(db: dict, rows: list[dict]) -> dict[str, list[int]]:
    measured = lambda r: not r.get("status") or r["status"] in ("pass", "noisy")
    catalog = {m["id"] for m in db.get("models") or [] if m.get("catalog")}
    out = {}
    for suite, ids in [("all", None), *(db.get("suites") or {}).items()]:
        keep = [r for r in rows if ids is None or r.get("model") in ids or r.get("model") in catalog]
        out[suite] = [len(keep), sum(map(measured, keep)), sum(1 for r in keep if not r.get("stale") and measured(r))]
    return out


def split(db: dict) -> tuple[dict, dict[str, dict]]:
    snaps = db.get("snapshots") or {}
    quality = db.get("quality_snapshots")
    keep = shown(db)
    names = {"mac": "Mac", "gpu": "GPU", "tpu": "TPU", "wafer": "Wafer"}
    platform = {h["id"]: "AMD" if h.get("class") == "gpu" and h.get("backend") == "rocm" else names.get(h.get("class")) for h in db.get("hardware") or []}
    seen: dict[str, set] = {}
    for rows in snaps.values():
        for r in rows:
            if r.get("status") in ("pass", "noisy") and platform.get(r.get("hardware")):
                seen.setdefault(r.get("model"), set()).add(platform[r["hardware"]])
    for m in db.get("models") or []:
        has = seen.get(m["id"], set()) | set(filter(None, str(m.get("platforms") or "").split(", ")))
        m["platforms"] = ", ".join(p for p in PLATFORMS if p in has)
    db["miniatures"] = any(r.get("miniature") for rows in snaps.values() for r in rows)
    parts = {}
    for tag in db.get("tags") or []:
        tag["counts"] = counts(db, snaps.get(tag["id"]) or [])
        if tag["id"] in keep or "/" in tag["id"] or tag["id"] not in snaps:
            continue
        parts[tag["id"]] = {"snapshots": snaps[tag["id"]], **({"quality_snapshots": quality.get(tag["id"], [])} if quality is not None else {})}
    core = {k: v for k, v in db.items() if k not in ("snapshots", "quality_snapshots")}
    core["snapshots"] = {t: rows for t, rows in snaps.items() if t not in parts}
    if quality is not None:
        core["quality_snapshots"] = {t: rows for t, rows in quality.items() if t not in parts}
    return core, parts


HOME = re.compile(r"/(?:Users|home)/[A-Za-z0-9._-]+")


def dumps(value) -> str:
    return HOME.sub("~", json.dumps(value, separators=(",", ":"), default=str))


def gz(value, prefix: str = "", suffix: str = "") -> bytes:
    out = io.BytesIO()
    with gzip.GzipFile(fileobj=out, mode="wb", compresslevel=6, mtime=0) as f:
        f.write(prefix.encode())
        for chunk in json.JSONEncoder(separators=(",", ":"), default=str).iterencode(value):
            f.write(HOME.sub("~", chunk).encode())
        f.write(suffix.encode())
    return out.getvalue()
