from __future__ import annotations

from server.views.picking import measured
from server.views.workloads import METRICS, WL_PRIORITY


def empty_row(key: tuple, tag: str, status: str, note: str) -> dict:
    hw, engine, model, cat = key
    return {"hardware": hw, "engine": engine, "release": tag, "group": tag, "version": "", "model": model, "scheme": None,
            "workload": cat, **{m: None for m in METRICS}, "accuracy": None, "commit": "", "measured": "",
            "status": status, "note": note, "stale": None}


def attempts_by_tag(store, a2m, hardware_ids, engine_ids) -> dict[str, dict[tuple, dict]]:
    cols = (["platform", "engine", "artifact", "workload", "status", "error_class", "error_message", "invalid_reason", "started_at", "tag"]
            + ["decode_tok_s", "prefill_tok_s", "output_tok_s"])
    rows = store.table().select(cols).to_pylist()
    crashed: dict[tuple, dict] = {}
    for r in sorted((r for r in rows if r["workload"] == "control-aa" and r["status"] == "fail"), key=lambda r: r["started_at"]):
        crashed[(r["platform"], r["engine"], r["artifact"], r["tag"])] = r
    out: dict[str, dict[tuple, dict]] = {}
    for r in rows:
        if measured(r) or r["platform"] not in hardware_ids or r["engine"] not in engine_ids:
            continue
        if r["status"] in ("pass", "noisy"):
            crash = crashed.get((r["platform"], r["engine"], r["artifact"], r["tag"]))
            r = {**r, "status": "fail", "error_message": f"Could not start: {first_line(crash)}" if crash else "Finished without numbers"}
        cat = WL_PRIORITY.get(r["workload"], (None,))[0]
        if not cat:
            continue
        key = (r["platform"], r["engine"], a2m.get(r["artifact"], r["artifact"]), cat)
        t = r["tag"]
        if not t or t.startswith("test-"):
            continue
        if key not in out.setdefault(t, {}) or r["started_at"] > out[t][key]["started_at"]:
            out[t][key] = r
    return out


def first_line(r: dict) -> str:
    lines = (r.get("error_message") or r.get("invalid_reason") or r.get("error_class") or "").strip().splitlines()
    return lines[0].removeprefix("RuntimeError: ").rstrip(": ") if lines else ""


def attempt_note(r: dict) -> str:
    msg = (r.get("error_message") or r.get("invalid_reason") or r.get("error_class") or "").strip().splitlines()
    msg = msg[0] if msg else ""
    if r["status"] == "not_run" and "hard deadline" in msg:
        return "The job ran out of time before this setup started"
    return (msg[:1].upper() + msg[1:])[:160] if msg else ("Failed" if r["status"] == "fail" else "Not run")
