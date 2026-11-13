from __future__ import annotations

import json
import math

from fastapi import HTTPException

from server import split
from server.ingest import NAME

TOL = 0.10
REQUIRED = ["attention", "dense_matmul", "moe", "norm_rope_elementwise", "sampling", "other_gpu", "gpu_idle"]
OPTIONAL = ["linear_attention", "qkv_proj", "o_proj", "mlp", "lm_head"]
STAGES = ["attention", "linear_attention", "qkv_proj", "o_proj", "mlp", "lm_head", *REQUIRED[1:]]
LABEL = {"attention": "attention", "linear_attention": "linear attention", "qkv_proj": "QKV projection", "o_proj": "output projection",
         "mlp": "MLP", "lm_head": "LM head", "dense_matmul": "dense matmul", "moe": "MoE", "norm_rope_elementwise": "norm/rope/elementwise",
         "sampling": "sampling", "other_gpu": "other GPU work", "gpu_idle": "GPU idle within the step"}
MAX_CELLS = 5000


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
    stages = raw.get("stage_ms")
    if stages is not None and (not isinstance(stages, dict) or any(_num(stages.get(k)) is None or stages[k] < 0 for k in REQUIRED)
                               or any(stages.get(k) is not None and (_num(stages[k]) is None or stages[k] < 0) for k in OPTIONAL)):
        _fail(f"{raw['engine']}: stage_ms must give every stage in ms: {', '.join(REQUIRED)}, optionally {', '.join(OPTIONAL)}")
    return {"engine": raw["engine"], "unit": str(raw.get("unit") or "")[:160],
            "benchmark_step_ms": _positive(raw.get("benchmark_step_ms")), "profiled_step_ms": _positive(raw.get("profiled_step_ms")),
            "reference_step_ms": _positive(raw.get("reference_step_ms")), "speed": _positive(raw.get("speed")),
            "ane_ms": _num(raw.get("ane_ms")), "stage_ms": {k: float(stages.get(k) or 0) for k in STAGES} if stages else None}


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


def judge(doc: dict) -> dict | None:
    f, s = doc["fastest"], doc["second"]
    if not all(b["profiled_step_ms"] and b["benchmark_step_ms"] and b["stage_ms"] for b in (f, s)):
        return None
    speeds = f["speed"] and s["speed"]
    ratio = f["speed"] / s["speed"] if speeds else s["profiled_step_ms"] / f["profiled_step_ms"]
    scale = f["speed"] * f["profiled_step_ms"] / (s["speed"] * s["profiled_step_ms"]) if speeds else 1.0
    second = {k: s["stage_ms"][k] * scale for k in STAGES}
    delta = {k: second[k] - f["stage_ms"][k] for k in STAGES}
    why = [f"{b['engine']} profiled {b['profiled_step_ms']:.4g} ms vs benchmark {b['benchmark_step_ms']:.4g} ms"
           for b in (f, s) if abs(b["profiled_step_ms"] / b["benchmark_step_ms"] - 1) > TOL]
    if abs(ratio / (1 + doc["gap_pct"] / 100) - 1) > TOL:
        why.append(f"profiled gap {100 * (ratio - 1):+.0f}% vs benchmark {doc['gap_pct']:+.0f}%")
    if ratio <= 1:
        why.append("the profile does not show the second engine slower")
    top = None if why else max(STAGES, key=delta.__getitem__)

    def side(b: dict, stages: dict) -> dict:
        return {"engine": b["engine"], "stepMs": b["profiled_step_ms"], "benchMs": b["benchmark_step_ms"], "ane": b["ane_ms"],
                "stages": {k: round(stages[k], 3) for k in STAGES}}

    return {"verdict": "bad run" if why else "confirmed", "stage": top and LABEL[top], "stageKey": top,
            "stageMs": top and round(delta[top], 3), "gapPct": doc["gap_pct"], "profiledGapPct": round(100 * (ratio - 1), 1),
            "unit": f["unit"], "why": "; ".join(why), "fastest": side(f, f["stage_ms"]), "second": side(s, second)}


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
    return split.gz(out)
