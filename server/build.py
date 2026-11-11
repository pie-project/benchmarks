from __future__ import annotations

from pie_bench.results.store import PgStore
from server import split, views

CATALOG = ("hardware", "engines", "models", "workloads", "suites", "quality_tasks", "updated_at")


def blobs(dsn: str, contributed: dict[str, dict]) -> dict[str, bytes]:
    store = PgStore(dsn)
    store._ready = True
    core, parts = views.build(store, contributed)
    out = {"grid": split.gz(core), "db.js": split.gz(core, "const DB = ", ";\n"), "catalog": split.gz({k: core.get(k) for k in CATALOG})}
    out.update({f"tag:{t}": split.gz(p) for t, p in parts.items()})
    everything = {**core, "snapshots": {**core.get("snapshots", {}), **{t: p["snapshots"] for t, p in parts.items()}}}
    if "quality_snapshots" in core:
        everything["quality_snapshots"] = {**core["quality_snapshots"], **{t: p.get("quality_snapshots", []) for t, p in parts.items()}}
    out["export"] = split.gz(everything)
    return out
