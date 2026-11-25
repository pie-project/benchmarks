from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from server.views.matrix_files import load

SEAT_FIX, SEAT_FIX_AT = "434fc3a158dd788ac7b1f62307c6d2eda0c69642", datetime(2026, 11, 10, 19, 54, 25, tzinfo=ZoneInfo("UTC"))
SOLO_FIX, SOLO_FIX_AT = "d6163483c48bfc00ab7e82236ab5f7012ba2c6e1", datetime(2026, 11, 10, 21, 12, 19, tzinfo=ZoneInfo("UTC"))
SEAT_ENGINES = {"pie", "trtllm", "llamacpp", "mlxlm", "vllm-metal", "splash"}
BACKEND = {p["id"]: p.get("backend") for p in load("platforms")["platforms"]}
QUEUES = {w["id"] for w in load("workloads")["workloads"]
          if (w.get("params") or {}).get("num_requests", 0) > ((w.get("params") or {}).get("concurrency") or 0)}
TIMINGS = ("ttft_ms_p50", "ttft_ms_p99", "latency_ms_p50", "latency_ms_p99")


HARNESS = json.loads((Path(__file__).parent / "timing_fixes.json").read_text())


def harness_has(fix: str, sha: str) -> bool | None:
    return HARNESS.get(fix, {}).get(sha)


def timed_with(fix: str, at: datetime, r: dict) -> bool:
    started = r["started_at"] if r["started_at"].tzinfo else r["started_at"].replace(tzinfo=ZoneInfo("UTC"))
    if started < at:
        return False
    sha = r.get("harness_commit") or ""
    return harness_has(fix, sha) is not False if re.fullmatch(r"[0-9a-f]{7,40}", sha) else True


def withhold_seat_ttft(row: dict, r: dict, hw: str, engine: str, cat: str) -> dict:
    seat = engine in SEAT_ENGINES or (engine == "sglang" and BACKEND.get(hw) == "xla")
    if not seat or BACKEND.get(hw) == "webgpu":
        return row
    if cat in ("throughput", "prefill_batch") and r["workload"] in QUEUES and not timed_with(SEAT_FIX, SEAT_FIX_AT, r):
        note = "TTFT and latency withheld: this run started each request's clock when it took a seat, not when it was sent, so they leave out the queue (rerun pending)"
    elif cat in ("raw", "spec") and engine != "pie" and timed_with(SEAT_FIX, SEAT_FIX_AT, r) and not timed_with(SOLO_FIX, SOLO_FIX_AT, r):
        note = "Prefill, TTFT and latency withheld: this run counted each request's wait on the one before it (rerun pending)"
        row["prefill_tok_s"] = None
    else:
        return row
    for m in TIMINGS:
        row[m] = None
    row["note"] = "; ".join(n for n in (row["note"], note) if n)
    return row
