"""Cell: reruns grid cells' two fastest engines on this machine, benchmark and profile in one job.

Each engine reruns its benchmark row's matrix cell through the harness (the row's pie commit and engine version, the
same boot, recipe and bench client): the standard rounds, untraced, then one short round under the platform's tracer in
the same engine session. The run writes the benchmark records as `pie-bench run` uploads them (records.jsonl,
submission.json.gz) and the cells for POST /v1/profiles (profiles.json), each judged against the fresh benchmark: both
engines in one unit, taken from the faster engine's benchmark, and its step worked out from the fresh rate.
"""

from __future__ import annotations

import json
import os
import re
import shutil
from pathlib import Path

from pie_bench import local, submit
from pie_bench.paths import MATRIX
from pie_bench.plan.matrix import Matrix
from pie_bench.schema import Tier

from . import tracer_for, unit

# each setup's results workload and the rate its benchmark number is
RATES = {"decode": ("raw", "decode_tok_s"), "spec": ("spec", "decode_tok_s"), "prefill": ("raw", "prefill_tok_s"),
         "batching": ("throughput", "output_tok_s"), "pbatch": ("prefill_batch", "prefill_tok_s")}
MEASURED = ("pass", "noisy")
TRACES = ("*.trace", "*.nsys-rep", "*.sqlite", "*.xml", "rocprof", "xla", "hsa", "cupti")


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


def mini_params_b(artifact) -> float | None:
    """A slice's parameter count in billions as the results rows give it (server/views.py), to tell apart slices whose
    label is the same ("78 of 78 layers" at 16 or 12 experts)."""
    import yaml

    r = artifact.miniature if str(artifact.kind) == "miniature" else None
    arts = yaml.safe_load((MATRIX / "models.yaml").read_text())["artifacts"]
    f = {a["base_model"]: a for a in arts if a.get("kind", "full") == "full" and a.get("layers") and a.get("vocab")}.get(artifact.base_model)
    if not r or not f or not f.get("params_b"):
        return None
    kept = sum(int(x.split("-")[-1]) - int(x.split("-")[0]) + 1 for x in str(r.layers).split(","))
    emb = 2 * f["vocab"] * f["hidden_size"] / 1e9
    body, active = f["params_b"] - emb, (f.get("active_b") or f["params_b"]) - emb
    n, top = f.get("experts"), f.get("top_k") or 0
    idle = min(1.0, max(0, (r.experts or n) - top) / (n - top)) if n and n > top else 1.0
    return round(emb + (active + (body - active) * idle) * kept / f["layers"], 3)


def cut_size(artifact) -> tuple:
    """A slice's size as the site ranks cuts (server/views.py _cut_size): the full model, then layers, then experts."""
    m = artifact.miniature if str(artifact.kind) == "miniature" else None
    if not m:
        return (1, 0, 0)
    return (0, sum(int(x.split("-")[-1]) - int(x.split("-")[0]) + 1 for x in str(m.layers).split(",")), m.experts or 0)


def cell_of(m: Matrix, machine, row: dict, commit: str):
    """The matrix cell a results row measured, with the job that plans it."""
    # the machine's own tier first, then any tier that holds the benchmarked cell (NVIDIA's full runs are weekly cells);
    # a Mac's model slices are in no suite of the config, so a row none of its arms plans is looked for in every artifact
    for every in (False, True):
        for tier in (local.tier_for(machine), *Tier):
            job = local.plan(m, machine, pie_commit=commit, models=[row["model"]], engines=[row["engine"]], workloads=[row["benchmark"]], suite="targeted",
                             tier=tier, every_artifact=every)
            found = [c for c in (job.cells if job else []) if c.workload.id == row["benchmark"] and str(c.engine) == row["engine"]
                     and str(c.artifact.scheme) == row["scheme"] and same_cut(c.artifact, row.get("miniature") or "")]
            if found:
                break
        if found:
            break
    if len(found) > 1:
        found = [c for c in found if not c.mode.spec_dec] or found  # the grid's rows are the plain, unspeculated runs
    if len(found) > 1 and row.get("mini_params_b"):
        found = [c for c in found if mini_params_b(c.artifact) == row["mini_params_b"]] or found
    if len(found) > 1 and len({cut_size(c.artifact) for c in found}) == len(found):
        # one label, several cuts: the site shows the biggest cut an engine ran last (server/views.py share_cut), so
        # the rerun takes that one and its fresh rows become the cell's
        found = [max(found, key=lambda c: cut_size(c.artifact))]
    if len(found) != 1:
        raise SystemExit(f"{row['engine']} {row['model']} {row['benchmark']}: {len(found)} matrix cells match, need one: {[c.artifact.id for c in found]}")
    return job, found[0]


def side(rec, engine: str, setup: str, concurrency: int, prompt: int, tracer, out: Path) -> dict:
    """One engine's profile in the shared unit, from its fresh benchmark record and its profiled round's bench JSON and trace."""
    base = {"engine": engine, "tracer": tracer.name}
    rate = getattr(rec.perf, RATES[setup][1], None) if rec is not None and rec.perf else None
    if rec is None or str(rec.status) not in MEASURED or not rate:
        return {**base, "why": f"the benchmark run failed: {rec and (rec.error_message or rec.invalid_reason)}"}
    base.update(benchmark_step_ms=step_ms(rate, setup, concurrency, prompt), benchmark_status=str(rec.status))
    rnd = out / "cells" / rec.cell_id / "profile"
    try:
        measured = unit.measured(json.loads((rnd / "bench.json").read_text()), setup, concurrency, prompt)
        span = json.loads((rnd / "span.json").read_text())
        if min(s for s, _ in measured.windows) < span["start_ns"] or max(e for _, e in measured.windows) > span["stop_ns"]:
            raise ValueError("the measured windows fall outside the recording")
        return {**base, **unit.split(measured, tracer.intervals(rnd))}
    except (OSError, ValueError, KeyError, RuntimeError) as e:
        return {**base, "why": f"the profiled round: {e}"}


def versions(rows: list[dict]) -> dict[str, str]:
    """Each rival's engine version as its rows measured it, so the rerun replaces them like for like."""
    out: dict[str, str] = {}
    for r in rows:
        if r["engine"] == "pie" or not re.fullmatch(r"[A-Za-z0-9._-]+", r.get("version") or ""):
            continue  # pie runs at its commit; "0.33.0 (vllm 0.33.0+cpu)", "mlx-vlm 0.7.11" name no installable pin
        if out.setdefault(r["engine"], r["version"]) != r["version"]:
            raise SystemExit(f"{r['engine']} rows at {out[r['engine']]} and {r['version']}: one job runs one version, so run these cells apart")
    return out


def profile(hardware: str | None, cells: list[tuple[str, str]], out: Path, engines: list[str] | None = None, pie_root: Path | None = None,
            tag: str | None = None, pie_commit: str | None = None) -> list[dict]:
    """Reruns the cells' two fastest engines on this machine, benchmark and profile, and writes the run's records,
    its submission and out/profiles.json."""
    from pie_bench.node.machine import machine_lock
    from pie_bench.node.runner import NodeRunner

    m = Matrix.load(MATRIX)
    machine = local.detect(m, hardware)
    hw = machine.platform.id
    tracer = tracer_for(str(machine.platform.backend), out)
    if getattr(tracer, "whole_run", False):
        raise SystemExit(f"{tracer.name} traces the whole run, so the benchmark rounds would carry its cost: no combined job on this platform")
    live = submit.request("GET", "/v1/results")
    pairs = {(model, setup): pair(live["results"], hw, model, setup, engines) for model, setup in cells}
    rows = [r for p in pairs.values() for r in p]
    commits = {pie_commit} if pie_commit else {r["commit"] for r in rows if r["engine"] == "pie"}
    if len(commits) > 1:
        raise SystemExit(f"the cells' pie rows were measured at pie {', '.join(sorted(commits))}: one job builds one commit, so run them apart")
    commit = local.resolve_pie(commits.pop())[0] if commits else None
    key = lambda r: (r["engine"], r["model"], r["benchmark"], r["scheme"], r.get("miniature") or "")
    planned = {}
    for r in rows:
        planned.setdefault(key(r), cell_of(m, machine, r, commit or "0" * 40))
    jobs = [j for j, _ in planned.values()]
    runs = {c.cell_id: c for _, c in planned.values()}
    # each process's control A/A, as the standard job runs it
    controls = {x.cell_id: x for j, c in planned.values() for x in j.cells if str(x.workload.kind) == "control_aa"
                and (str(x.engine), x.artifact.artifact_key, x.mode.key) == (str(c.engine), c.artifact.artifact_key, c.mode.key)}
    # each engine's own pin (vLLM-TPU, SGLang-JAX), as its own plan carries it, then the version its rows ran
    pins = {k: v for j in jobs for k, v in j.baseline_versions.items()} | versions(rows)
    job = jobs[0].model_copy(update={"cells": [*controls.values(), *runs.values()], "pie_commit": commit, "baseline_versions": pins,
                                     "budget_s": sum(j.budget_s for j in jobs), "kill_s": sum(j.kill_s for j in jobs)})
    os.environ.update({**local.setup_engines(m, job, log=print), **tracer.env})
    with machine_lock(f"profile {hw} {len(cells)} cells", max_wait_s=3600, log=print):
        runner = NodeRunner(job, pie_root=(pie_root or local.HOME / "pie").resolve(), out_dir=out, download=True, tracer=tracer)
        records = runner.run()
    submit.pack(out, {"run_id": runner.run_id, "tier": str(job.tier), "tag": tag or live["id"], "tag_kind": "manual",
                      "platform": machine.platform.model_dump(mode="json"), "pie_commit": commit})
    by_cell = {r.cell_id: r for r in records}
    docs = []
    for (model, setup), (first, second) in pairs.items():
        params = planned[key(first)][1].workload.params
        concurrency, prompt = int(params.get("concurrency", 1)), int(params.get("prefill", 512))
        recs = [by_cell.get(planned[key(r)][1].cell_id) for r in (first, second)]
        sides = [side(rec, r["engine"], setup, concurrency, prompt, tracer, out) for rec, r in zip(recs, (first, second))]
        if all("benchmark_step_ms" in s for s in sides):
            sides.sort(key=lambda s: s["benchmark_step_ms"])  # the fresh benchmark decides which engine is the faster
        steps = [s.get("benchmark_step_ms") for s in sides]
        docs.append({"hardware": hw, "model": model, "setup": setup, "gap_pct": 100 * (steps[1] / steps[0] - 1) if all(steps) else None,
                     "slice": first.get("miniature") or None, "fastest": sides[0], "second": sides[1]})
    (out / "profiles.json").write_text(json.dumps({"format": 1, "profiles": docs}, indent=1))
    for pattern in TRACES if not os.environ.get("PIE_BENCH_PROFILER_KEEP_TRACES") else ():
        for p in out.rglob(pattern):
            shutil.rmtree(p, ignore_errors=True) if p.is_dir() else p.unlink(missing_ok=True)
    return docs
