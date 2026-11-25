from __future__ import annotations

import json
import math

from fastapi import HTTPException

from server import encoding
from server.submissions import NAME

TOL = 0.10
MAX_CELLS = 5000
UNCLASSIFIED_MAX = 0.25
IDLE_MAX = 0.50


def _fail(msg: str) -> None:
    raise HTTPException(422, msg)


def _num(value) -> float | None:
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) else None


def _positive(value) -> float | None:
    n = _num(value)
    return n if n and n > 0 else None


def _side(raw) -> dict:
    if not isinstance(raw, dict) or not isinstance(raw.get("engine"), str) or not NAME.match(raw["engine"]):
        _fail("a profile must name both engines")
    wall, forward = _positive(raw.get("wall_ms")), _num(raw.get("forward_ms"))
    if (raw.get("wall_ms"), raw.get("forward_ms")) != (None, None) and (wall is None or forward is None or not 0 <= forward <= wall):
        _fail(f"{raw['engine']}: wall_ms and forward_ms must be the ms per unit of the profiled run and of its forward pass, 0 <= forward <= wall")
    return {"engine": raw["engine"], "unit": str(raw.get("unit") or "")[:160], "benchmark_step_ms": _positive(raw.get("benchmark_step_ms")),
            "wall_ms": wall, "forward_ms": forward, "tracer": str(raw.get("tracer") or "")[:40] or None,
            "benchmark_status": raw.get("benchmark_status") if isinstance(raw.get("benchmark_status"), str) else None}


def check(doc: dict) -> list[dict]:
    cells = doc.get("profiles")
    if not isinstance(cells, list) or not cells:
        _fail("profiles must be a non-empty list")
    if len(cells) > MAX_CELLS:
        _fail("too many profiles in one upload")
    out = []
    for raw in cells:
        if not isinstance(raw, dict) or not all(isinstance(raw.get(k), str) and NAME.match(raw[k]) for k in ("hardware", "model", "setup")):
            _fail("a profile must name its hardware, model and setup")
        gap = _num(raw.get("gap_pct"))
        if gap is None or gap < 0:
            _fail(f"{raw['hardware']}|{raw['model']}|{raw['setup']}: gap_pct must be the benchmark's gap in percent")
        out.append({"hardware": raw["hardware"], "model": raw["model"], "setup": raw["setup"], "gap_pct": gap,
                    "slice": raw["slice"] if isinstance(raw.get("slice"), str) else None,
                    "fastest": _side(raw.get("fastest")), "second": _side(raw.get("second"))})
    return out


def times(side: dict) -> dict | None:
    if side.get("wall_ms") and side.get("forward_ms") is not None:
        return {"wall": side["wall_ms"], "forward": side["forward_ms"], "idle": side["wall_ms"] - side["forward_ms"]}
    stages = side.get("stage_ms")
    if stages and side.get("profiled_step_ms"):
        return {"wall": side["profiled_step_ms"], "forward": sum(v for k, v in stages.items() if k != "gpu_idle"), "idle": stages["gpu_idle"]}
    return None


def stage_doubts(side: dict) -> list[str]:
    stages = side.get("stage_ms")
    total = sum(stages.values()) if stages else 0
    if not total:
        return []
    return ([f"unclassified GPU work is {100 * stages['other_gpu'] / total:.0f}% of {side['engine']}'s step"] if stages["other_gpu"] / total > UNCLASSIFIED_MAX else []) \
        + ([f"the GPU sits idle {100 * stages['gpu_idle'] / total:.0f}% of {side['engine']}'s step"] if stages["gpu_idle"] / total > IDLE_MAX else [])


def in_fastest_unit(f: dict, tf: dict, s: dict, ts: dict) -> dict:
    k = f["speed"] * tf["wall"] / (s["speed"] * ts["wall"])
    return {key: v * k for key, v in ts.items()}


def judge(doc: dict) -> dict | None:
    f, s = doc["fastest"], doc["second"]
    tf, ts = times(f), times(s)
    if not (tf and ts and f["benchmark_step_ms"] and s["benchmark_step_ms"]):
        return None
    why = [f"{b['engine']} profiled {t['wall']:.4g} ms vs benchmark {b['benchmark_step_ms']:.4g} ms"
           for b, t in ((f, tf), (s, ts)) if abs(t["wall"] / b["benchmark_step_ms"] - 1) > TOL]
    why += [f"{b['engine']}'s forward pass and idle add up to {100 * (t['forward'] + t['idle']) / t['wall']:.0f}% of its step"
            for b, t in ((f, tf), (s, ts)) if abs((t["forward"] + t["idle"]) / t["wall"] - 1) > TOL]
    why += [f"{b['engine']}'s benchmark run was noisy" for b in (f, s) if b.get("benchmark_status") == "noisy"]
    why += stage_doubts(f) + stage_doubts(s)
    if f.get("speed") and s.get("speed"):
        ts = in_fastest_unit(f, tf, s, ts)
    ratio = ts["wall"] / tf["wall"]
    if abs(ratio / (1 + doc["gap_pct"] / 100) - 1) > TOL:
        why.append(f"profiled gap {100 * (ratio - 1):+.0f}% vs benchmark {doc['gap_pct']:+.0f}%")
    if ratio <= 1:
        why.append("the profile does not show the second engine slower")
    extra = {k: ts[k] - tf[k] for k in ("forward", "idle")}

    def side(b: dict, t: dict) -> dict:
        return {"engine": b["engine"], "wallMs": round(t["wall"], 3), "forwardMs": round(t["forward"], 3), "idleMs": round(t["idle"], 3),
                "benchMs": b["benchmark_step_ms"]}

    return {"verdict": "bad run" if why else "confirmed", "why": "; ".join(why), "where": None if why else max(extra, key=extra.get),
            "extraMs": {k: round(v, 3) for k, v in extra.items()}, "gapPct": doc["gap_pct"], "profiledGapPct": round(100 * (ratio - 1), 1),
            "unit": f["unit"], "fastest": side(f, tf), "second": side(s, ts)}


def store(cur, cells: list[dict], *, token_id: str | None, address: str) -> dict:
    cur.executemany("INSERT INTO profiles (hardware, model, setup, doc, token_id) VALUES (%s, %s, %s, %s, %s) "
                    "ON CONFLICT (hardware, model, setup) DO UPDATE SET doc = EXCLUDED.doc, token_id = EXCLUDED.token_id, submitted_at = now()",
                    [(c["hardware"], c["model"], c["setup"], json.dumps(c), token_id) for c in cells])
    verdicts = [(judge(c) or {}).get("verdict", "not profiled") for c in cells]
    counts = {v: verdicts.count(v) for v in ("confirmed", "bad run", "not profiled")}
    cur.execute("INSERT INTO ingest_log (token_id, address, action, detail) VALUES (%s, %s, 'profiles', %s)",
                (token_id, address, ", ".join(f"{n} {v}" for v, n in counts.items())))
    return {"profiles": len(cells), **counts}


def blob(cur) -> bytes:
    cur.execute("SELECT doc FROM profiles ORDER BY hardware, model, setup")
    out = {}
    for (doc,) in cur.fetchall():
        judged = judge(doc)
        if judged:
            out[f"{doc['hardware']}|{doc['model']}|{doc['setup']}"] = judged
    return encoding.gz(out)
