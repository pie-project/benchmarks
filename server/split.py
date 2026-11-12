from __future__ import annotations

import gzip
import io
import json
import re
import zlib

PLATFORMS = ["Mac", "GPU", "TPU", "AMD", "Wafer"]


def counts(db: dict, rows: list[dict]) -> dict[str, list[int]]:
    measured = lambda r: not r.get("status") or r["status"] in ("pass", "noisy")
    catalog = {m["id"] for m in db.get("models") or [] if m.get("catalog")}
    out = {}
    for suite, ids in [("all", None), *(db.get("suites") or {}).items()]:
        keep = [r for r in rows if ids is None or r.get("model") in ids or r.get("model") in catalog]
        out[suite] = [len(keep), sum(map(measured, keep)), sum(1 for r in keep if not r.get("stale") and measured(r))]
    return out


HOME = re.compile(r"/(?:Users|home)/[A-Za-z0-9._-]+")


def dumps(value) -> str:
    return HOME.sub("~", json.dumps(value, separators=(",", ":"), default=str))


def gz(value) -> bytes:
    out = io.BytesIO()
    with gzip.GzipFile(fileobj=out, mode="wb", compresslevel=6, mtime=0) as f:
        for chunk in json.JSONEncoder(separators=(",", ":"), default=str).iterencode(value):
            f.write(HOME.sub("~", chunk).encode())
    return out.getvalue()


def gz_text(text: str) -> bytes:
    return gzip.compress(text.encode(), compresslevel=6, mtime=0)


def seal(rows: list[dict], ctx: dict) -> dict:
    return {"json": zlib.compress(dumps(rows).encode(), 6), "counts": counts(ctx, rows),
            "seen": {(r.get("model"), r.get("hardware")) for r in rows if r.get("status") in ("pass", "noisy")},
            "mini": any(r.get("miniature") for r in rows)}


def rows_json(sealed: dict) -> str:
    return zlib.decompress(sealed["json"]).decode()


def annotate(db: dict, sealed: dict[str, dict]) -> None:
    names = {"mac": "Mac", "gpu": "GPU", "tpu": "TPU", "wafer": "Wafer"}
    platform = {h["id"]: "AMD" if h.get("class") == "gpu" and h.get("backend") == "rocm" else names.get(h.get("class")) for h in db.get("hardware") or []}
    seen: dict[str, set] = {}
    for s in sealed.values():
        for model, hw in s["seen"]:
            if platform.get(hw):
                seen.setdefault(model, set()).add(platform[hw])
    for m in db.get("models") or []:
        has = seen.get(m["id"], set()) | set(filter(None, str(m.get("platforms") or "").split(", ")))
        m["platforms"] = ", ".join(p for p in PLATFORMS if p in has)
    db["miniatures"] = any(s["mini"] for s in sealed.values())
    for tag in db.get("tags") or []:
        tag["counts"] = sealed[tag["id"]]["counts"] if tag["id"] in sealed else counts(db, [])


def publish(db: dict, sealed: dict[str, dict], quality: dict) -> tuple[dict, str | None, bytes | None]:
    annotate(db, sealed)
    catalog = {("releases" if k == "tags" else k): v for k, v in db.items()}
    latest = next((tag["id"] for tag in catalog.get("releases") or [] if tag["counts"]["all"][0]), None)
    if not latest:
        return catalog, None, None
    return catalog, latest, gz_text('{"id":' + dumps(latest) + ',"results":' + rows_json(sealed[latest]) + ',"quality":' + dumps(quality.get(latest, [])) + "}")
