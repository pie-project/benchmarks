from __future__ import annotations

import json

from pie_bench.results.store import PgStore
from server import headline, split, views

CATALOG_PARTS = {
    "machines": "hardware",
    "models": "models",
    "engines": "engines",
    "workloads": "workloads",
    "releases": "releases",
    "suites": "suites",
    "install": "install",
    "totals": "totals",
    "miniatures": "miniatures",
    "parity": "parity",
    "no-fit": "no_fit",
    "speed-gaps": "speed_gaps",
    "quality": "quality",
    "quality-tasks": "quality_tasks",
    "quality-parity": "quality_parity",
    "quality-kernels": "quality_kernels",
    "quality-gaps": "quality_gaps",
}


def blobs(dsn: str, contributed: dict[str, dict], submissions: int = 0) -> dict[str, bytes]:
    store = PgStore(dsn)
    store._ready = True
    db, sealed, quality = views.build(store, contributed)
    catalog, latest, results = split.publish(db, sealed, quality)
    catalog["totals"] = {**(catalog.get("totals") or {}), "submissions": submissions}
    newest = {latest: json.loads(split.rows_json(sealed[latest]))} if latest else {}
    out = {"catalog": split.gz(catalog), "head-to-head": split.gz(headline.head_to_head({**db, "snapshots": newest}))}
    for name, field in CATALOG_PARTS.items():
        out[name] = split.gz({"updated_at": catalog.get("updated_at"), name: catalog.get(field)})
    if results:
        out["results"] = results
    return out
