"""Cell: profiles a grid cell's two fastest engines end to end and writes the cell for POST /v1/profiles.

Each engine runs its benchmark row's workload through the harness (the same boot, recipe and bench client, one round
with fewer requests) under the platform's tracer. Both engines are measured in one unit, taken from the faster engine's
benchmark, and the benchmark's own step is worked out from its published rate in that unit.
"""

from __future__ import annotations

import gzip
import json
import os
import shutil
from pathlib import Path

from pie_bench import local, submit
from pie_bench.paths import MATRIX
from pie_bench.plan.matrix import Matrix
from pie_bench.schema import RepetitionPolicy, Tier

from . import tracer_for, unit

# each setup's results workload and the rate its benchmark number is
RATES = {"decode": ("raw", "decode_tok_s"), "spec": ("spec", "decode_tok_s"), "prefill": ("raw", "prefill_tok_s"),
         "batching": ("throughput", "output_tok_s"), "pbatch": ("prefill_batch", "prefill_tok_s")}
MEASURED = ("pass", "noisy")
TRACES = ("*.trace", "*.nsys-rep", "*.sqlite", "*.xml", "rocprof", "xla")


def pair(results: list[dict], hardware: str, model: str, setup: str, engines: list[str] | None = None) -> tuple[dict, dict]:
    """The cell's fastest and second fastest engines: each engine's best measured row, as the grid compares them."""
    workload, rate = RATES[setup]
    best: dict[str, dict] = {}
    for r in results:
        if (r["hardware"], r["model"], r["workload"]) == (hardware, model, workload) and r.get(rate) and r.get("status") in MEASURED \
                and r.get("benchmark") and (not engines or r["engine"] in engines) and r[rate] > best.get(r["engine"], {}).get(rate, 0):
            best[r["engine"]] = r
    ranked = sorted(best.values(), key=lambda r: -r[rate])
    if len(ranked) < 2:
        raise SystemExit(f"{hardware}|{model}|{setup}: fewer than two engines measured")
    return ranked[0], ranked[1]


def step_ms(rate: float, setup: str, concurrency: int, prompt: int) -> float:
    """The benchmark's step in the profile's unit, from its rate: a token, a prompt, a batched step or a wave."""
    tokens = {"decode": 1, "spec": 1, "prefill": prompt, "batching": concurrency, "pbatch": concurrency * prompt}[setup]
    return 1000 * tokens / rate


def same_cut(artifact, label: str) -> bool:
    """Whether an artifact is the model slice a results row names ("30 layers, 36 experts"), or the full model for none."""
    m = artifact.miniature if str(artifact.kind) == "miniature" else None
    if not m or not label:
        return not m and not label
    kept = sum(int(x.split("-")[-1]) - int(x.split("-")[0]) + 1 for x in str(m.layers).split(","))
    # a label that names no experts ("7 of 78 layers", the NVIDIA rows) is matched by its layers alone
    return label.startswith(f"{kept} ") and (m.experts is None or "experts" not in label or f"{m.experts} experts" in label)


def cell_of(m: Matrix, machine, row: dict, commit: str):
    """The matrix cell a results row measured, its requests cut to one short round."""
    # the machine's own tier first, then any tier that holds the benchmarked cell (NVIDIA's full runs are weekly cells)
    for tier in (local.tier_for(machine), *Tier):
        job = local.plan(m, machine, pie_commit=commit, models=[row["model"]], engines=[row["engine"]], workloads=[row["benchmark"]], suite="targeted", tier=tier)
        found = [c for c in (job.cells if job else []) if c.workload.id == row["benchmark"] and str(c.engine) == row["engine"]
                 and str(c.artifact.scheme) == row["scheme"] and same_cut(c.artifact, row.get("miniature") or "")]
        if found:
            break
    if len(found) != 1:
        raise SystemExit(f"{row['engine']} {row['model']} {row['benchmark']}: {len(found)} matrix cells match, need one: {[c.artifact.id for c in found]}")
    c, p = found[0], dict(found[0].workload.params)
    if "num_requests" in p:
        p["num_requests"] = min(int(p["num_requests"]), 3 * int(p.get("concurrency", 1)))
    else:
        p["requests"] = min(int(p.get("requests", 4)), 4)
    return job, c.model_copy(update={"workload": c.workload.model_copy(update={"params": p})})


def side(rec, row: dict, setup: str, concurrency: int, prompt: int, tracer, out: Path) -> dict:
    """One engine's profile in the shared unit, from its round's bench JSON and trace."""
    rate = row[RATES[setup][1]]
    base = {"engine": row["engine"], "benchmark_step_ms": step_ms(rate, setup, concurrency, prompt), "benchmark_status": row["status"],
            "tracer": tracer.name}
    if rec is None or str(rec.status) not in MEASURED:
        return {**base, "why": f"the profiled run failed: {rec and (rec.error_message or rec.invalid_reason)}"}
    rnd = out / "cells" / rec.cell_id / "r0"
    try:
        measured = unit.measured(json.loads((rnd / "bench.json").read_text()), setup, concurrency, prompt)
        span = json.loads((rnd / "span.json").read_text())
        if min(s for s, _ in measured.windows) < span["start_ns"] or max(e for _, e in measured.windows) > span["stop_ns"]:
            raise ValueError("the measured windows fall outside the recording")
        return {**base, **unit.split(measured, tracer.intervals(rnd))}
    except (OSError, ValueError, KeyError, RuntimeError) as e:
        return {**base, "why": str(e)}


def profile(hardware: str | None, model: str, setup: str, out: Path, engines: list[str] | None = None, pie_root: Path | None = None) -> dict:
    """Profiles the cell's two fastest engines on this machine and writes out/cell.json."""
    from pie_bench.node.machine import machine_lock
    from pie_bench.node.runner import NodeRunner

    m = Matrix.load(MATRIX)
    machine = local.detect(m, hardware)
    hw = machine.platform.id
    first, second = pair(submit.request("GET", "/v1/results")["results"], hw, model, setup, engines)
    pie = next((r for r in (first, second) if r["engine"] == "pie"), None)
    commit = local.resolve_pie(pie["commit"])[0] if pie else "0" * 40
    (job, a), (job_b, b) = cell_of(m, machine, first, commit), cell_of(m, machine, second, commit)
    params = a.workload.params
    concurrency, prompt = int(params.get("concurrency", 1)), int(params.get("prefill", 512))
    # each engine's own pin (vLLM-TPU, SGLang-JAX), as its own plan carries it
    job = job.model_copy(update={"cells": [a, b], "control_required": False, "pie_commit": commit if pie else None,
                                 "baseline_versions": {**job_b.baseline_versions, **job.baseline_versions},
                                 "repetition": RepetitionPolicy(min_rounds=1, max_rounds=1, confirm_rounds=0)})
    tracer = tracer_for(str(machine.platform.backend), out)
    os.environ.update({**local.setup_engines(m, job, log=print), **tracer.env})
    with machine_lock(f"profile {hw} {model} {setup}", max_wait_s=3600, log=print):
        records = NodeRunner(job, pie_root=(pie_root or local.HOME / "pie").resolve(), out_dir=out, download=True, tracer=tracer).run()
    by_cell = {r.cell_id: r for r in records}
    sides = [side(by_cell.get(c.cell_id), row, setup, concurrency, prompt, tracer, out) for c, row in ((a, first), (b, second))]
    doc = {"hardware": hw, "model": model, "setup": setup, "gap_pct": 100 * (first[RATES[setup][1]] / second[RATES[setup][1]] - 1),
           "slice": first.get("miniature") or None, "fastest": sides[0], "second": sides[1]}
    (out / "cell.json").write_text(json.dumps(doc, indent=1))
    for pattern in TRACES if not os.environ.get("PIE_BENCH_PROFILER_KEEP_TRACES") else ():
        for p in out.rglob(pattern):
            shutil.rmtree(p, ignore_errors=True) if p.is_dir() else p.unlink(missing_ok=True)
    return doc


def upload(doc: dict) -> dict:
    """Posts one cell to /v1/profiles, which judges it."""
    body = gzip.compress(json.dumps({"format": 1, "profiles": [doc]}).encode())
    return submit.request("POST", "/v1/profiles", body, token=submit.token(), content_type="application/gzip")
