from __future__ import annotations

import pyarrow as pa

from pie_bench.results.store import BaseStore
from pie_bench.schema import Tier
from pie_bench.schema.record import ARROW_SCHEMA

_PG_TYPES = {pa.string(): "text", pa.float64(): "double precision", pa.int64(): "bigint", pa.int32(): "integer", pa.bool_(): "boolean"}
_LEAN = [n for n in ARROW_SCHEMA.names if n != "record_json"]


def _pg_type(t: pa.DataType) -> str:
    return "timestamptz" if pa.types.is_timestamp(t) else _PG_TYPES[t]


SCHEMA_SQL = (
    "CREATE TABLE IF NOT EXISTS records ("
    + ", ".join(f"{f.name} {_pg_type(f.type)}" for f in ARROW_SCHEMA)
    + ", stored_at timestamptz NOT NULL DEFAULT now(), tag text, tag_kind text);\n"
    "CREATE INDEX IF NOT EXISTS records_run ON records (run_id);\n"
    "CREATE INDEX IF NOT EXISTS records_tier_started ON records (tier, started_at);\n"
    "CREATE INDEX IF NOT EXISTS records_cell ON records (cell_id);\n"
    "CREATE INDEX IF NOT EXISTS records_cell_key ON records (cell_key);\n"
    "CREATE INDEX IF NOT EXISTS records_tag ON records (tag);\n"
    "CREATE TABLE IF NOT EXISTS quality (artifact text NOT NULL, task text NOT NULL, tag text NOT NULL DEFAULT '', "
    "platform text NOT NULL DEFAULT '', tag_kind text, model text, engine text, score double precision, n integer, "
    "date timestamptz, summary jsonb NOT NULL, samples jsonb, stored_at timestamptz NOT NULL DEFAULT now());\n"
    "CREATE UNIQUE INDEX IF NOT EXISTS quality_platform_key ON quality (artifact, task, tag, platform);\n"
)


def _good(status, decode, prefill) -> bool:
    return status in ("pass", "noisy") and (decode is not None or prefill is not None)


def _tag_keep(cur, rows: list, tag: str, cols: list[str]) -> set:
    ck = cols.index("cell_key")
    keys = sorted({r[ck] for r in rows if r[ck]})
    if not keys:
        return set()
    cur.execute("SELECT cell_key, status, decode_tok_s, prefill_tok_s FROM records WHERE tag = %s AND cell_key = ANY(%s)", (tag, keys))
    good, broken = set(), set()
    for key, status, dec, pre in cur.fetchall():
        (good if _good(status, dec, pre) else broken).add(key)
    st = cols.index("status")
    not_run = {r[ck] for r in rows if r[ck] and r[st] == "not_run"}
    good |= (not_run & (good | broken))
    dec, pre = cols.index("decode_tok_s"), cols.index("prefill_tok_s")
    newer = {r[ck] for r in rows if r[ck] and _good(r[st], r[dec], r[pre])}
    good -= newer
    replace = sorted((broken | newer) - good)
    if replace:
        cur.execute("DELETE FROM records WHERE tag = %s AND cell_key = ANY(%s)", (tag, replace))
    return good


class PgStore(BaseStore):
    def __init__(self, dsn: str):
        self.dsn = dsn
        self._ready = False

    def describe(self) -> str:
        return "postgres " + self.dsn.split("@")[-1]

    def connect(self):
        import psycopg

        conn = psycopg.connect(self.dsn, connect_timeout=15)
        if not self._ready:
            with conn.transaction():
                conn.execute("SELECT pg_advisory_xact_lock(7212031)")
                conn.execute(SCHEMA_SQL)
            self._ready = True
        return conn

    def _write_table(self, t, *, tier, run_id, when, tag=None, tag_kind=None) -> str:
        with self.connect() as conn, conn.transaction(), conn.cursor() as cur:
            written, kept = copy_records(cur, t, run_id=run_id, tag=tag, tag_kind=tag_kind)
        return f"postgres records run_id={run_id} ({written} rows written, {kept} kept)"

    def write_quality(self, summary: dict, *, tag: str | None = None, tag_kind: str | None = None) -> str:
        with self.connect() as conn, conn.transaction(), conn.cursor() as cur:
            upsert_quality(cur, summary, tag=tag, tag_kind=tag_kind)
        return f"postgres quality {summary['artifact']}/{summary['task']} tag={tag or 'legacy'}"

    def table(self, tier: Tier | None = None) -> pa.Table:
        sql = f"SELECT {', '.join(_LEAN)}, tag, tag_kind FROM records" + (" WHERE tier = %s" if tier else "")
        with self.connect() as conn, conn.cursor() as cur:
            cur.execute(sql, (str(tier),) if tier else None)
            rows = cur.fetchall()
        n = len(_LEAN)
        cols = {name: [r[i] for r in rows] for i, name in enumerate(_LEAN)}
        cols["record_json"] = [None] * len(rows)
        t = pa.table({name: cols[name] for name in ARROW_SCHEMA.names}, schema=ARROW_SCHEMA)
        return t.append_column("tag", pa.array([r[n] for r in rows], pa.string())).append_column(
            "tag_kind", pa.array([r[n + 1] for r in rows], pa.string()))

    def quality_answers(self) -> list[dict]:
        sql = ("SELECT summary, tag, tag_kind, (SELECT jsonb_agg(jsonb_build_object('id', x->'id', 'text', "
               "md5(regexp_replace(coalesce(x->>'text', ''), '^\\s+|\\s+$', '', 'g')))) "
               "FROM jsonb_array_elements(CASE WHEN jsonb_typeof(samples) = 'array' THEN samples ELSE '[]' END) x) "
               "FROM quality ORDER BY artifact, task, tag")
        with self.connect() as conn, conn.cursor() as cur:
            cur.execute(sql)
            return [{**summary, "tag": tag or None, "tag_kind": kind, "samples": answers or []} for summary, tag, kind, answers in cur.fetchall()]

    def quality(self, samples: bool = False) -> list[dict]:
        with self.connect() as conn, conn.cursor() as cur:
            cur.execute("SELECT summary, tag, tag_kind, samples FROM quality ORDER BY artifact, task, tag")
            return [{**r[0], "tag": r[1] or None, "tag_kind": r[2], **({"samples": r[3] or []} if samples else {})} for r in cur.fetchall()]


def copy_records(cur, t: pa.Table, *, run_id: str, tag: str | None, tag_kind: str | None) -> tuple[int, int]:
    cols = ARROW_SCHEMA.names + ["tag", "tag_kind"]
    rows = [tuple(r[c] for c in ARROW_SCHEMA.names) + (tag, tag_kind) for r in t.to_pylist()]
    ids = sorted({run_id} | {r[0] for r in rows if r[0]})
    cur.execute("DELETE FROM records WHERE run_id = ANY(%s)", (ids,))
    keep = _tag_keep(cur, rows, tag, cols) if tag else set()
    ck = cols.index("cell_key")
    written = [row for row in rows if row[ck] not in keep]
    with cur.copy(f"COPY records ({', '.join(cols)}) FROM STDIN") as cp:
        for row in written:
            cp.write_row(row)
    return len(written), len(rows) - len(written)


def upsert_quality(cur, summary: dict, *, tag: str | None, tag_kind: str | None) -> None:
    from psycopg.types.json import Jsonb

    head = {k: v for k, v in summary.items() if k != "samples"}
    cur.execute(
        "INSERT INTO quality (artifact, task, tag, platform, tag_kind, model, engine, score, n, date, summary, samples) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (artifact, task, tag, platform) DO UPDATE SET "
        "tag_kind = EXCLUDED.tag_kind, model = EXCLUDED.model, engine = EXCLUDED.engine, score = EXCLUDED.score, n = EXCLUDED.n, "
        "date = EXCLUDED.date, summary = EXCLUDED.summary, samples = EXCLUDED.samples, stored_at = now() "
        "WHERE EXCLUDED.score IS NOT NULL OR quality.score IS NULL",
        (summary["artifact"], summary["task"], tag or "", summary.get("platform") or "", tag_kind, summary.get("model"), summary.get("engine"),
         summary.get("score"), summary.get("n"), summary.get("date"), Jsonb(head), Jsonb(summary.get("samples"))),
    )
