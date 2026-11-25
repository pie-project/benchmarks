from __future__ import annotations

import gzip
import json
from pathlib import Path

from pie_bench import __version__
from pie_bench.api_client import ApiError

SUBMISSION = "submission.json.gz"
FORMAT = 1


def _jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text().splitlines():
        try:
            rows.append(json.loads(line))
        except ValueError:
            continue
    return rows


def pack(out: Path, meta: dict) -> Path:
    log = out / "run.log"
    quality = (
        [json.loads(p.read_text()) for p in sorted((out / "quality").glob("*.json"))]
        if (out / "quality").is_dir()
        else []
    )
    doc = {
        "format": FORMAT,
        "pie_bench": __version__,
        **meta,
        "records": _jsonl(out / "records.jsonl"),
        "quality": quality,
        "log": log.read_text(errors="replace") if log.exists() else "",
    }
    path = out / SUBMISSION
    path.write_bytes(gzip.compress(json.dumps(doc, default=str).encode()))
    return path


def merge(outs: list[Path], path: Path) -> Path:
    docs = [json.loads(gzip.decompress((o / SUBMISSION).read_bytes())) for o in outs]
    machines = {(d.get("platform") or {}).get("id") for d in docs}
    tags = {d.get("tag") for d in docs}
    if len(machines) > 1 or len(tags) > 1:
        raise ApiError(
            f"one submission holds one machine's runs for one release: {sorted(map(str, machines))}, tags {sorted(map(str, tags))}"
        )
    commits = {d.get("pie_commit") for d in docs}
    doc = {
        **docs[0],
        "pie_commit": commits.pop() if len(commits) == 1 else None,
        "records": [r for d in docs for r in d["records"]],
        "quality": [q for d in docs for q in d.get("quality") or []],
        "log": "\n".join(d.get("log") or "" for d in docs),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(gzip.compress(json.dumps(doc, default=str).encode()))
    return path
