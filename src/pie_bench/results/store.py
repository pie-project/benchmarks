from __future__ import annotations

import json
import os
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import median

import pyarrow as pa

from pie_bench.schema import CellStatus, Record, Tier
from pie_bench.schema.record import records_to_table

DB_ENV = "PIE_BENCH_DB"


def _aware(ts: datetime) -> datetime:
    return ts if ts.tzinfo else ts.replace(tzinfo=timezone.utc)


def default_store() -> str:
    return os.environ.get(DB_ENV) or "store"


def open_store(root: Path | str | None = None) -> BaseStore:
    root = str(root) if root is not None else default_store()
    if root.startswith(("postgresql://", "postgres://")):
        from pie_bench.results.pg_store import PgStore

        return PgStore(root)
    from pie_bench.results.dir_store import DirStore

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
