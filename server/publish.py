from __future__ import annotations

import json
import zlib

from pie_bench.results.pg_store import PgStore
from server.encoding import dumps, gz, gz_text
from server.head_to_head import head_to_head

PLATFORMS = ["Mac", "Windows", "GPU", "TPU", "AMD", "Wafer"]


def counts(db: dict, rows: list[dict]) -> dict[str, list[int]]:
    measured = lambda r: not r.get("status") or r["status"] in ("pass", "noisy")
    catalog = {m["id"] for m in db.get("models") or [] if m.get("catalog")}
    out = {}
    for suite, ids in [("all", None), *(db.get("suites") or {}).items()]:
        keep = [r for r in rows if ids is None or r.get("model") in ids or r.get("model") in catalog]
        out[suite] = [len(keep), sum(map(measured, keep)), sum(1 for r in keep if not r.get("stale") and measured(r))]
    return out


def seal(rows: list[dict], ctx: dict) -> dict:
    return {"json": zlib.compress(dumps(rows).encode(), 6), "counts": counts(ctx, rows),
            "seen": {(r.get("model"), r.get("hardware")) for r in rows if r.get("status") in ("pass", "noisy")},
            "mini": any(r.get("miniature") for r in rows)}


def rows_json(sealed: dict) -> str:
    return zlib.decompress(sealed["json"]).decode()


def annotate(db: dict, sealed: dict[str, dict]) -> None:
    names = {"mac": "Mac", "windows": "Windows", "gpu": "GPU", "tpu": "TPU", "wafer": "Wafer"}
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


def blobs(dsn: str, contributed: dict[str, dict], submissions: int = 0) -> dict[str, bytes]:
    from server.views import build

    store = PgStore(dsn)
    store._ready = True
    db, sealed, quality = build(store, contributed)
    catalog, latest, results = publish(db, sealed, quality)
    catalog["totals"] = {**(catalog.get("totals") or {}), "submissions": submissions}
    newest = {latest: json.loads(rows_json(sealed[latest]))} if latest else {}
    out = {"catalog": gz(catalog), "head-to-head": gz(head_to_head({**db, "snapshots": newest}))}
    if results:
        out["results"] = results
    return out
