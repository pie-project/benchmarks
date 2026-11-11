from __future__ import annotations

from pie_bench.results.store import PgStore
from server import split, views

CATALOG = ("hardware", "engines", "models", "workloads", "suites", "quality_tasks", "updated_at")


def blobs(dsn: str, contributed: dict[str, dict]) -> dict[str, bytes]:
    store = PgStore(dsn)
    store._ready = True
    core, parts, export = views.build(store, contributed)
    out = {"grid": split.gz(core), "db.js": split.gz(core, "const DB = ", ";\n"), "catalog": split.gz({k: core.get(k) for k in CATALOG})}
    out.update({f"tag:{t}": b for t, b in parts.items()})
    out["export"] = export
    return out
