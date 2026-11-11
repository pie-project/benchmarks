from __future__ import annotations

from pie_bench.results.store import PgStore
from server import split, views


def blobs(dsn: str, contributed: dict[str, dict]) -> dict[str, bytes]:
    store = PgStore(dsn)
    store._ready = True
    core, parts, _ = views.build(store, contributed)
    out = {"db.js": split.gz(core, "const DB = ", ";\n")}
    out.update({f"tag:{t}": b for t, b in parts.items()})
    return out
