from __future__ import annotations

import json

from pie_bench.results.pg_store import PgStore
from server import headline, split, views


def blobs(dsn: str, contributed: dict[str, dict], submissions: int = 0) -> dict[str, bytes]:
    store = PgStore(dsn)
    store._ready = True
    db, sealed, quality = views.build(store, contributed)
    catalog, latest, results = split.publish(db, sealed, quality)
    catalog["totals"] = {**(catalog.get("totals") or {}), "submissions": submissions}
    newest = {latest: json.loads(split.rows_json(sealed[latest]))} if latest else {}
    out = {"catalog": split.gz(catalog), "head-to-head": split.gz(headline.head_to_head({**db, "snapshots": newest}))}
    if results:
        out["results"] = results
    return out
