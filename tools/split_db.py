"""Split the site's db.js into a core and one file per tag, so the site draws without reading every tag.

    python3 tools/split_db.py [web/data/db.js]

web/data/db.js keeps the catalogs, parity, quality and the tags the site shows by default (the newest run and the
ones the release menu offers); every other tag's results and quality scores go to web/data/tags/<tag>.json, which
the site fetches when a page asks for that tag (core/store.js). Each tag in the core carries its row counts, so the
menus still know what to offer without its rows. A db.js already split is left as it is; tools/webdb.py writes the
split files itself.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BETA = re.compile(r"^\d+\.\d+\.\d+-b\d+$")  # a pre-release (0.5.3-b5), as core/query.js names it
PLATFORMS = ["Mac", "GPU", "TPU", "AMD", "Wafer"]  # the order core/store.js lists a model's platforms in


def shown(db: dict) -> set[str]:
    """The tags the site shows without a pick: the newest, the releases, the newest run and the newest pre-release."""
    snaps = db.get("snapshots") or {}
    tags = db.get("tags") or []
    have = [t for t in tags if snaps.get(t["id"])]
    keep = {t["id"] for t in have if t.get("kind") == "release"}
    keep |= {next((t["id"] for t in have if t.get("kind") != "release"), None), next((t["id"] for t in have if BETA.match(t["id"])), None)}
    keep |= {have[0]["id"] if have else None, tags[0]["id"] if tags else None}  # the newest with rows, and the phone's newest
    return keep - {None}


def counts(db: dict, rows: list[dict]) -> dict[str, list[int]]:
    """Each suite's rows, measured rows and fresh measured rows ("all" for no suite), as core/store.js counts them."""
    measured = lambda r: not r.get("status") or r["status"] in ("pass", "noisy")  # noqa: E731
    catalog = {m["id"] for m in db.get("models") or [] if m.get("catalog")}
    out = {}
    for suite, ids in [("all", None), *(db.get("suites") or {}).items()]:
        keep = [r for r in rows if ids is None or r.get("model") in ids or r.get("model") in catalog]
        out[suite] = [len(keep), sum(map(measured, keep)), sum(1 for r in keep if not r.get("stale") and measured(r))]
    return out


def split(db: dict) -> tuple[dict, dict[str, dict]]:
    """The core and each other tag's own part: {"snapshots": rows, "quality_snapshots": rows}."""
    snaps = db.get("snapshots") or {}
    quality = db.get("quality_snapshots")
    keep = shown(db)
    # what core/store.js works out from every tag's rows is worked out here, over every tag: each model's platforms
    # and whether any result is a miniature
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


def replace(path: Path, text: str) -> None:
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text)
    os.replace(tmp, path)


def write(db: dict, data: Path) -> None:
    """The split files under data/: tags/<tag>.json first, then db.js, so a core never names a tag file not yet written."""
    core, parts = split(db)
    # the data is public: a machine's home directory in a run's note (/Users/<name>, /home/<name>) is written as ~
    home = re.compile(r"/(?:Users|home)/[A-Za-z0-9._-]+")
    dump = lambda v: home.sub("~", json.dumps(v, separators=(",", ":"), default=str))  # noqa: E731
    (data / "tags").mkdir(parents=True, exist_ok=True)
    for tag, part in parts.items():
        replace(data / "tags" / f"{tag}.json", dump(part))
    for old in (data / "tags").glob("*.json"):
        if old.stem not in parts:
            old.unlink()
    replace(data / "db.js", "const DB = " + dump(core) + ";\n")
    # the same core as plain JSON, for anyone to fetch (the tags it lists are data/tags/<tag>.json)
    replace(data / "db.json", dump(core))


def main() -> None:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "web" / "data" / "db.js"
    text = path.read_text()
    db = json.loads(text[text.index("{"):text.rindex("}") + 1])
    if any("counts" in t for t in db.get("tags") or []):
        print(f"{path}: already split")
        return
    stamp = path.stat().st_mtime
    write(db, path.parent)
    # the split db.js keeps the downloaded file's time, so a sync's `curl -z` still asks only for a newer one
    os.utime(path, (stamp, stamp))
    print(f"{path}: {len(db.get('tags') or [])} tags, {len(list((path.parent / 'tags').glob('*.json')))} apart, core {path.stat().st_size >> 20} MB")


if __name__ == "__main__":
    main()
