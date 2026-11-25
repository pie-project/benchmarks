from __future__ import annotations

import os
from pathlib import Path

from pie_bench.results.dir_store import DirStore
from pie_bench.results.pg_store import PgStore

DB_ENV = "PIE_BENCH_DB"


def default_store() -> str:
    return os.environ.get(DB_ENV) or "store"


def open_store(root: Path | str | None = None) -> DirStore | PgStore:
    root = str(root) if root is not None else default_store()
    if root.startswith(("postgresql://", "postgres://")):
        return PgStore(root)
    return DirStore(root)
