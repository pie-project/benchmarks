from __future__ import annotations

import gzip
import io
import json
import math
import re
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException

from pie_bench.results.pg_store import copy_records, upsert_quality
from pie_bench.schema import Record
from pie_bench.schema.record import records_to_table

FORMAT = 1
MAX_COMPRESSED = 64 << 20
MAX_RAW = 512 << 20
MAX_RECORDS = 20000
NAME = re.compile(r"^[A-Za-z0-9._-]{1,128}$")
SHA = re.compile(r"^[0-9a-f]{40}$")


def _fail(msg: str) -> None:
    raise HTTPException(422, msg)


def decode(body: bytes) -> dict:
    if len(body) > MAX_COMPRESSED:
        raise HTTPException(413, "submission too large")
    try:
        with gzip.GzipFile(fileobj=io.BytesIO(body)) as f:
            raw = f.read(MAX_RAW + 1)
    except OSError:
        _fail("submission is not gzip")
    if len(raw) > MAX_RAW:
        raise HTTPException(413, "submission too large")
    try:
        doc = json.loads(raw)
    except ValueError:
        _fail("submission is not JSON")
    if not isinstance(doc, dict) or doc.get("format") != FORMAT:
        _fail("unsupported submission format; upgrade pie-bench (pip install -U pie-bench)")
    return doc


def _finite(value) -> bool:
    if isinstance(value, dict):
        return all(_finite(v) for v in value.values())
    if isinstance(value, list):
        return all(_finite(v) for v in value)
    if isinstance(value, float):
        return math.isfinite(value)
    return True


def check(doc: dict) -> tuple[list[Record], list[dict]]:
    run_id = doc.get("run_id")
    if not isinstance(run_id, str) or not NAME.match(run_id):
        _fail("run_id is missing or malformed")
    tag = doc.get("tag")
    if tag is not None and (not isinstance(tag, str) or not NAME.match(tag)):
        _fail("tag is malformed")
    if doc.get("tag_kind") not in (None, "release", "manual"):
        _fail("tag_kind must be release or manual")
    raw = doc.get("records") or []
    quality = doc.get("quality") or []
    if not isinstance(raw, list) or not isinstance(quality, list):
        _fail("records and quality must be lists")
    if not raw and not quality:
        _fail("submission holds no results")
    if len(raw) > MAX_RECORDS:
        _fail("too many records in one submission")
    records = []
    for i, row in enumerate(raw):
        try:
            rec = Record.model_validate(row)
        except ValueError as e:
            _fail(f"record {i} is invalid: {str(e)[:300]}")
        problem = rec.validate_for_store()
        if problem:
            _fail(f"record {i} lacks provenance: {problem}")
        if not _finite(rec.perf.model_dump() if rec.perf else {}):
            _fail(f"record {i} has a non-finite number")
        records.append(rec)
    platforms = {r.cell.platform.id for r in records}
    if len(platforms) > 1:
        _fail("one submission measures one machine")
    commit = doc.get("pie_commit")
    if commit is not None and not SHA.match(str(commit)):
        _fail("pie_commit must be a full sha")
    if commit and any(r.provenance.pie_commit and r.provenance.pie_commit != commit for r in records if str(r.cell.engine) == "pie"):
        _fail("records were measured on another pie commit than the submission names")
    future = datetime.now(timezone.utc) + timedelta(hours=1)
    if any(r.started_at and (r.started_at if r.started_at.tzinfo else r.started_at.replace(tzinfo=timezone.utc)) > future for r in records):
        _fail("records are dated in the future")
    for q in quality:
        if not isinstance(q, dict) or not q.get("artifact") or not q.get("task") or not _finite(q):
            _fail("a quality score is malformed")
    return records, quality


def store(cur, doc: dict, records: list[Record], quality: list[dict], *, token_id: str, address: str) -> dict:
    run_id, tag, kind = doc["run_id"], doc.get("tag"), doc.get("tag_kind")
    cur.execute("SELECT token_id FROM runs WHERE run_id = %s", (run_id,))
    row = cur.fetchone()
    if row and row[0] != token_id:
        raise HTTPException(409, "this run_id was uploaded by another token")
    cur.execute("SELECT quota, used, revoked FROM tokens WHERE id = %s FOR UPDATE", (token_id,))
    row = cur.fetchone()
    if not row or row[2]:
        raise HTTPException(401, "token revoked or unknown: run `pie-bench login`")
    quota, used, _ = row
    if used >= quota:
        raise HTTPException(429, f"upload quota reached ({quota}); ask the pie team to raise it")
    platform = records[0].cell.platform.id if records else (doc.get("platform") or {}).get("id")
    machine = json.dumps({"platform": doc.get("platform"), "pie_bench": doc.get("pie_bench")})
    cur.execute(
        "INSERT INTO runs (run_id, token_id, platform, tag, tag_kind, tier, pie_commit, pie_bench, results, quality, machine) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (run_id) DO UPDATE SET "
        "results = EXCLUDED.results, quality = EXCLUDED.quality, submitted_at = now()",
        (run_id, token_id, platform, tag, kind, doc.get("tier"), doc.get("pie_commit"), doc.get("pie_bench"), len(records), len(quality), machine),
    )
    written = kept = 0
    if records:
        written, kept = copy_records(cur, records_to_table(records), run_id=run_id, tag=tag, tag_kind=kind)
    for q in quality:
        upsert_quality(cur, q, tag=tag, tag_kind=kind)
    log = doc.get("log") or ""
    if log:
        cur.execute("INSERT INTO run_logs (run_id, log) VALUES (%s, %s) ON CONFLICT (run_id) DO UPDATE SET log = EXCLUDED.log",
                    (run_id, gzip.compress(str(log).encode())))
    cur.execute("UPDATE tokens SET used = used + 1 WHERE id = %s", (token_id,))
    cur.execute("INSERT INTO ingest_log (token_id, address, run_id, action, detail) VALUES (%s, %s, %s, 'submission', %s)",
                (token_id, address, run_id, f"{written} written, {kept} kept, {len(quality)} quality"))
    return {"run_id": run_id, "results": written, "kept": kept, "quality": len(quality), "quota_left": quota - used - 1}
