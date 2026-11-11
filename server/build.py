from __future__ import annotations

import json

from pie_bench.results.store import PgStore
from server import headline, split, views


def blobs(dsn: str, contributed: dict[str, dict]) -> dict[str, bytes]:
    store = PgStore(dsn)
    store._ready = True
    db, sealed, quality = views.build(store, contributed)
    catalog, releases = split.publish(db, sealed, quality)
    latest = next((t["id"] for t in catalog.get("releases") or [] if t["counts"]["all"][0]), None)
    newest = {latest: json.loads(split.rows_json(sealed[latest]))} if latest else {}
    out = {"catalog": split.gz(catalog), "head-to-head": split.gz(headline.head_to_head({**db, "snapshots": newest}))}
    out.update({f"release:{t}": b for t, b in releases.items()})
    return out
