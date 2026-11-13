from __future__ import annotations

import os
from contextlib import contextmanager

from psycopg_pool import ConnectionPool

from pie_bench.results.store import SCHEMA_SQL, PgStore

API_SQL = """
CREATE TABLE IF NOT EXISTS tokens (
    id text PRIMARY KEY,
    name text NOT NULL,
    quota integer NOT NULL,
    used integer NOT NULL DEFAULT 0,
    admin_issued boolean NOT NULL DEFAULT false,
    address text,
    created_at timestamptz NOT NULL DEFAULT now(),
    revoked boolean NOT NULL DEFAULT false
);
CREATE TABLE IF NOT EXISTS runs (
    run_id text PRIMARY KEY,
    token_id text REFERENCES tokens (id),
    platform text,
    tag text,
    tag_kind text,
    tier text,
    pie_commit text,
    pie_bench text,
    results integer NOT NULL DEFAULT 0,
    quality integer NOT NULL DEFAULT 0,
    machine jsonb,
    submitted_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS run_logs (
    run_id text PRIMARY KEY REFERENCES runs (run_id) ON DELETE CASCADE,
    log bytea NOT NULL
);
CREATE TABLE IF NOT EXISTS ingest_log (
    id bigserial PRIMARY KEY,
    at timestamptz NOT NULL DEFAULT now(),
    token_id text,
    address text,
    run_id text,
    action text NOT NULL,
    detail text
);
CREATE TABLE IF NOT EXISTS hits (
    day date NOT NULL,
    path text NOT NULL,
    count bigint NOT NULL,
    PRIMARY KEY (day, path)
);
CREATE TABLE IF NOT EXISTS profiles (
    hardware text NOT NULL,
    model text NOT NULL,
    setup text NOT NULL,
    doc jsonb NOT NULL,
    token_id text,
    submitted_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (hardware, model, setup)
);
CREATE TABLE IF NOT EXISTS views (
    key text PRIMARY KEY,
    data bytea NOT NULL,
    built_at timestamptz NOT NULL DEFAULT now()
);
DROP VIEW IF EXISTS cell_latest;
CREATE VIEW cell_latest AS
    SELECT DISTINCT ON (cell_key) * FROM records WHERE cell_key IS NOT NULL ORDER BY cell_key, started_at DESC;
"""


def url() -> str:
    dsn = os.environ.get("DATABASE_URL") or os.environ.get("PIE_BENCH_DB")
    if not dsn:
        raise RuntimeError("DATABASE_URL is not set")
    return dsn


class Database:
    def __init__(self, dsn: str | None = None):
        self.dsn = dsn or url()
        self.pool = ConnectionPool(self.dsn, min_size=1, max_size=int(os.environ.get("DB_POOL", "8")), open=True,
                                   kwargs={"connect_timeout": 15})
        self.store = PgStore(self.dsn)
        self.store._ready = True
        with self.tx() as cur:
            cur.execute("SELECT pg_advisory_xact_lock(7212031)")
            cur.execute(SCHEMA_SQL)
            cur.execute(API_SQL)

    @contextmanager
    def tx(self):
        with self.pool.connection() as conn, conn.transaction(), conn.cursor() as cur:
            yield cur

    def close(self) -> None:
        self.pool.close()
