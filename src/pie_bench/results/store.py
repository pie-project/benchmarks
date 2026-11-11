from __future__ import annotations

import json
import os
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import median

import pyarrow as pa
import pyarrow.parquet as pq

from pie_bench.schema import CellStatus, Record, Tier
from pie_bench.schema.record import ARROW_SCHEMA, records_to_table

DB_ENV = "PIE_BENCH_DB"


def _aware(ts: datetime) -> datetime:
    return ts if ts.tzinfo else ts.replace(tzinfo=timezone.utc)


def default_store() -> str:
    return os.environ.get(DB_ENV) or "store"


def Store(root: Path | str | None = None) -> BaseStore:
    root = str(root) if root is not None else default_store()
    if root.startswith(("postgresql://", "postgres://")):
        return PgStore(root)
    return DirStore(root)


class BaseStore:
    def write_run(self, records: list[Record], *, tier: Tier, run_id: str, when: datetime | None = None,
                  tag: str | None = None, tag_kind: str | None = None) -> str:
        problems = {r.cell_id: r.validate_for_store() for r in records}
        bad = {k: v for k, v in problems.items() if v}
        if bad:
            raise ValueError(f"records missing mandatory provenance: {json.dumps(bad)[:2000]}")
        return self._write_table(records_to_table(records), tier=tier, run_id=run_id, when=when or datetime.now(timezone.utc),
                                 tag=tag, tag_kind=tag_kind)

    def import_node_output(self, node_out: Path, *, tier: Tier, run_id: str, tag: str | None = None,
                           tag_kind: str | None = None) -> str | None:
        f = node_out / "records.jsonl"
        if not f.exists():
            return None
        lines = [line for line in f.read_text().splitlines() if line.strip()]
        recs = []
        for i, line in enumerate(lines):
            try:
                recs.append(Record.model_validate_json(line))
            except ValueError:
                if i != len(lines) - 1:
                    raise
        if not recs:
            return None
        return self.write_run(recs, tier=tier, run_id=run_id, tag=tag, tag_kind=tag_kind)

    def _write_table(self, t: pa.Table, *, tier: Tier, run_id: str, when: datetime, tag=None, tag_kind=None) -> str:
        raise NotImplementedError

    def write_quality(self, summary: dict, *, tag: str | None = None, tag_kind: str | None = None) -> str:
        raise NotImplementedError

    def table(self, tier: Tier | None = None) -> pa.Table:
        raise NotImplementedError

    def describe(self) -> str:
        return str(self.root) if hasattr(self, "root") else "postgres"

    def quality(self, samples: bool = False) -> list[dict]:
        raise NotImplementedError

    def history(self, tier: Tier | None = None, *, limit: int = 20, engine: str | None = None, since: datetime | None = None) -> dict[str, list[float]]:
        t = self.table(tier)
        if t.num_rows == 0:
            return {}
        rows = t.select(["cell_id", "status", "primary_value", "started_at", "engine"]).to_pylist()
        rows = [r for r in rows if r["status"] == str(CellStatus.PASS) and r["primary_value"] is not None]
        if engine:
            rows = [r for r in rows if r["engine"] == engine]
        if since is not None:
            rows = [r for r in rows if r["started_at"] is not None and _aware(r["started_at"]) >= since]
        rows.sort(key=lambda r: r["started_at"])
        hist: dict[str, list[float]] = defaultdict(list)
        for r in rows:
            hist[r["cell_id"]].append(float(r["primary_value"]))
        return {k: v[-limit:] for k, v in hist.items()}

    def measured_minutes(self, *, limit: int = 5) -> dict[str, float]:
        t = self.table(None)
        if t.num_rows == 0:
            return {}
        rows = sorted((r for r in t.select(["cell_id", "status", "duration_s", "started_at"]).to_pylist() if r["status"] != "not_run" and r["duration_s"]), key=lambda r: r["started_at"])
        by: dict[str, list[float]] = defaultdict(list)
        for r in rows:
            by[r["cell_id"]].append(r["duration_s"] / 60)
        return {k: median(v[-limit:]) for k, v in by.items()}

    def latest_by_cell(self, tier: Tier | None = None) -> dict[str, dict]:
        t = self.table(tier)
        if t.num_rows == 0:
            return {}
        rows = sorted(t.to_pylist(), key=lambda r: r["started_at"])
        latest: dict[str, dict] = {}
        for r in rows:
            if r["status"] == "not_run" and r["cell_id"] in latest:
                continue
            latest[r["cell_id"]] = r
        return latest


class DirStore(BaseStore):
    def __init__(self, root: Path | str = "store"):
        self.root = Path(root)
        self.records_dir = self.root / "records"

    def _write_table(self, t, *, tier, run_id, when, tag=None, tag_kind=None) -> str:
        out = self.records_dir / str(tier) / when.strftime("%Y-%m") / f"{run_id}.parquet"
        out.parent.mkdir(parents=True, exist_ok=True)
        pq.write_table(t, out, compression="zstd")
        return str(out)

    def write_quality(self, summary: dict, *, tag: str | None = None, tag_kind: str | None = None) -> str:
        summary = {**summary, "tag": tag, "tag_kind": tag_kind} if tag else summary
        on = f"-{summary['platform']}" if summary.get("platform") else ""
        path = self.root / "quality" / f"{summary['artifact']}-{summary['task']}{on}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        if (tag_kind == "release" or summary.get("score") is None) and path.exists() and json.loads(path.read_text()).get("score") is not None:
            return f"{path} (kept: a score is stored)"
        path.write_text(json.dumps(summary, indent=1))
        return str(path)

    def files(self, tier: Tier | None = None) -> list[Path]:
        base = self.records_dir / str(tier) if tier else self.records_dir
        return sorted(f for f in base.rglob("*.parquet") if not f.name.startswith(".")) if base.exists() else []

    def table(self, tier: Tier | None = None) -> pa.Table:
        fs = self.files(tier)
        if not fs:
            return ARROW_SCHEMA.empty_table()
        return pa.concat_tables([pq.read_table(f, schema=ARROW_SCHEMA) for f in fs], promote_options="default")

    def quality(self, samples: bool = False) -> list[dict]:
        d = self.root / "quality"
        out = []
        for f in sorted(d.glob("*.json")) if d.exists() else []:
            q = json.loads(f.read_text())
            if not samples:
                q.pop("samples", None)
            out.append(q)
        return out


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
