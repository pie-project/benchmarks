from __future__ import annotations

import json
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from pie_bench.results.store import BaseStore
from pie_bench.schema import Tier
from pie_bench.schema.record import ARROW_SCHEMA


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
