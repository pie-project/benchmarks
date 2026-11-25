from __future__ import annotations

import json
import os
import re
import shutil
from pathlib import Path

from pie_bench import api_client, submission
from pie_bench.installers.desktop_engines import setup_engines
from pie_bench.installers.pie import resolve_pie
from pie_bench.machine import detect, tier_for
from pie_bench.paths import HOME, MATRIX
from pie_bench.plan.local import plan as machine_plan
from pie_bench.plan.matrix import Matrix
from pie_bench.profiler import breakdown
from pie_bench.profiler.tracers import tracer_for
from pie_bench.schema import Tier

RATES = {
    "decode": ("raw", "decode_tok_s"),
    "spec": ("spec", "decode_tok_s"),
    "prefill": ("raw", "prefill_tok_s"),
    "batching": ("throughput", "output_tok_s"),
    "pbatch": ("prefill_batch", "prefill_tok_s"),
}
MEASURED = ("pass", "noisy")
TRACES = ("*.trace", "*.nsys-rep", "*.sqlite", "*.xml", "rocprof", "xla", "hsa", "cupti")


def pair(
    results: list[dict], hardware: str, model: str, setup: str, engines: list[str] | None = None
) -> tuple[dict, dict]:
    workload, rate = RATES[setup]
    best: dict[str, dict] = {}
    for r in results:
        if (
            (r["hardware"], r["model"], r["workload"]) == (hardware, model, workload)
            and r.get(rate)
            and r.get("status") in MEASURED
            and r.get("benchmark")
            and (not engines or r["engine"] in engines)
            and r[rate] > best.get(r["engine"], {}).get(rate, 0)
        ):
            best[r["engine"]] = r
    ranked = sorted(best.values(), key=lambda r: -r[rate])
    if len(ranked) < 2:
        raise SystemExit(f"{hardware}|{model}|{setup}: fewer than two engines measured")
    return ranked[0], ranked[1]


def step_ms(rate: float, setup: str, concurrency: int, prompt: int) -> float:
    tokens = {
        "decode": 1,
        "spec": 1,
        "prefill": prompt,
        "batching": concurrency,
        "pbatch": concurrency * prompt,
    }[setup]
    return 1000 * tokens / rate


def model_slice(artifact):
    return artifact.miniature if str(artifact.kind) == "miniature" else None


def kept_layers(miniature) -> int:
    spans = [x.split("-") for x in str(miniature.layers).split(",")]
    return sum(int(span[-1]) - int(span[0]) + 1 for span in spans)


def same_cut(artifact, label: str) -> bool:
    m = model_slice(artifact)
    if not m or not label:
        return not m and not label
    kept = kept_layers(m)
    return label.startswith(f"{kept} ") and (
        m.experts is None or "experts" not in label or f"{m.experts} experts" in label
    )


def mini_params_b(artifact) -> float | None:
    import yaml

    r = model_slice(artifact)
    arts = yaml.safe_load((MATRIX / "models.yaml").read_text())["artifacts"]
    f = {
        a["base_model"]: a
        for a in arts
        if a.get("kind", "full") == "full" and a.get("layers") and a.get("vocab")
    }.get(artifact.base_model)
    if not r or not f or not f.get("params_b"):
        return None
    kept = kept_layers(r)
    emb = 2 * f["vocab"] * f["hidden_size"] / 1e9
    body, active = f["params_b"] - emb, (f.get("active_b") or f["params_b"]) - emb
    n, top = f.get("experts"), f.get("top_k") or 0
    idle = min(1.0, max(0, (r.experts or n) - top) / (n - top)) if n and n > top else 1.0
    return round(emb + (active + (body - active) * idle) * kept / f["layers"], 3)


def cut_size(artifact) -> tuple:
    m = model_slice(artifact)
    if not m:
        return (1, 0, 0)
    return (0, kept_layers(m), m.experts or 0)


def cell_of(m: Matrix, machine, row: dict, commit: str):
    for every in (False, True):
        for tier in (tier_for(machine), *Tier):
            job = machine_plan(
                m,
                machine,
                pie_commit=commit,
                models=[row["model"]],
                engines=[row["engine"]],
                workloads=[row["benchmark"]],
                suite="targeted",
                tier=tier,
                every_artifact=every,
            )
            found = [
                c
                for c in (job.cells if job else [])
                if c.workload.id == row["benchmark"]
                and str(c.engine) == row["engine"]
                and str(c.artifact.scheme) == row["scheme"]
                and same_cut(c.artifact, row.get("miniature") or "")
            ]
            if found:
                break
        if found:
            break
    if len(found) > 1 and machine.platform.os != "macos":
        found = [c for c in found if str(c.artifact.source_format) != "mlx"] or found
    if len(found) > 1:
        found = [c for c in found if not c.mode.spec_dec] or found
    if len(found) > 1 and row.get("mini_params_b"):
        found = [c for c in found if mini_params_b(c.artifact) == row["mini_params_b"]] or found
    if len(found) > 1 and len({cut_size(c.artifact) for c in found}) == len(found):
        found = [max(found, key=lambda c: cut_size(c.artifact))]
    if len(found) != 1:
        raise SystemExit(
            f"{row['engine']} {row['model']} {row['benchmark']}: {len(found)} matrix cells match, need one: {[c.artifact.id for c in found]}"
        )
    return job, found[0]


def side(rec, engine: str, setup: str, concurrency: int, prompt: int, tracer, out: Path) -> dict:
    base = {"engine": engine, "tracer": tracer.name}
    rate = getattr(rec.perf, RATES[setup][1], None) if rec is not None and rec.perf else None
    if rec is None or str(rec.status) not in MEASURED or not rate:
        return {
            **base,
            "why": f"the benchmark run failed: {rec and (rec.error_message or rec.invalid_reason)}",
        }
    base.update(
        benchmark_step_ms=step_ms(rate, setup, concurrency, prompt),
        benchmark_status=str(rec.status),
    )
    rnd = out / "cells" / rec.cell_id / "profile"
    try:
        measured = breakdown.measured(
            json.loads((rnd / "bench.json").read_text()), setup, concurrency, prompt
        )
        span = json.loads((rnd / "span.json").read_text())
        if (
            min(s for s, _ in measured.windows) < span["start_ns"]
            or max(e for _, e in measured.windows) > span["stop_ns"]
        ):
            raise ValueError("the measured windows fall outside the recording")
        return {**base, **breakdown.split(measured, tracer.intervals(rnd))}
    except (OSError, ValueError, KeyError, RuntimeError) as e:
        return {**base, "why": f"the profiled round: {e}"}


def versions(rows: list[dict]) -> dict[str, str]:
    out: dict[str, str] = {}
    for r in rows:
        if r["engine"] == "pie" or not re.fullmatch(r"[A-Za-z0-9._-]+", r.get("version") or ""):
            continue
        if out.setdefault(r["engine"], r["version"]) != r["version"]:
            raise SystemExit(
                f"{r['engine']} rows at {out[r['engine']]} and {r['version']}: one job runs one version, so run these cells apart"
            )
    return out


def profile(
    hardware: str | None,
    cells: list[tuple[str, str]],
    out: Path,
    engines: list[str] | None = None,
    pie_root: Path | None = None,
    tag: str | None = None,
    pie_commit: str | None = None,
) -> list[dict]:
    from pie_bench.runner.job import JobRunner
    from pie_bench.runner.machine_lock import machine_lock

    m = Matrix.load(MATRIX)
    machine = detect(m, hardware)
    hw = machine.platform.id
    tracer = tracer_for(str(machine.platform.backend), out)
    if getattr(tracer, "whole_run", False):
        raise SystemExit(
            f"{tracer.name} traces the whole run, so the benchmark rounds would carry its cost: no combined job on this platform"
        )
    live = api_client.request("GET", "/v1/results")
    pairs = {
        (model, setup): pair(live["results"], hw, model, setup, engines) for model, setup in cells
    }
    rows = [r for p in pairs.values() for r in p]
    commits = {pie_commit} if pie_commit else {r["commit"] for r in rows if r["engine"] == "pie"}
    if len(commits) > 1:
        raise SystemExit(
            f"the cells' pie rows were measured at pie {', '.join(sorted(commits))}: one job builds one commit, so run them apart"
        )
    commit = resolve_pie(commits.pop())[0] if commits else None
    key = lambda r: (r["engine"], r["model"], r["benchmark"], r["scheme"], r.get("miniature") or "")
    planned = {}
    for r in rows:
        planned.setdefault(key(r), cell_of(m, machine, r, commit or "0" * 40))
    jobs = [j for j, _ in planned.values()]
    runs = {c.cell_id: c for _, c in planned.values()}
    controls = {
        x.cell_id: x
        for j, c in planned.values()
        for x in j.cells
        if str(x.workload.kind) == "control_aa"
        and (str(x.engine), x.artifact.artifact_key, x.mode.key)
        == (str(c.engine), c.artifact.artifact_key, c.mode.key)
    }
    pins = {k: v for j in jobs for k, v in j.baseline_versions.items()} | versions(rows)
    job = jobs[0].model_copy(
        update={
            "cells": [*controls.values(), *runs.values()],
            "pie_commit": commit,
            "baseline_versions": pins,
            "budget_s": sum(j.budget_s for j in jobs),
            "kill_s": sum(j.kill_s for j in jobs),
        }
    )
    os.environ.update({**setup_engines(m, job, log=print), **tracer.env})
    with machine_lock(f"profile {hw} {len(cells)} cells", max_wait_s=3600, log=print):
        runner = JobRunner(
            job,
            pie_root=(pie_root or HOME / "pie").resolve(),
            out_dir=out,
            download=True,
            tracer=tracer,
        )
        records = runner.run()
    submission.pack(
        out,
        {
            "run_id": runner.run_id,
            "tier": str(job.tier),
            "tag": tag or live["id"],
            "tag_kind": "manual",
            "platform": machine.platform.model_dump(mode="json"),
            "pie_commit": commit,
        },
    )
    by_cell = {r.cell_id: r for r in records}
    docs = []
    for (model, setup), (first, second) in pairs.items():
        params = planned[key(first)][1].workload.params
        concurrency, prompt = int(params.get("concurrency", 1)), int(params.get("prefill", 512))
        recs = [by_cell.get(planned[key(r)][1].cell_id) for r in (first, second)]
        sides = [
            side(rec, r["engine"], setup, concurrency, prompt, tracer, out)
            for rec, r in zip(recs, (first, second))
        ]
        if all("benchmark_step_ms" in s for s in sides):
            sides.sort(key=lambda s: s["benchmark_step_ms"])
        steps = [s.get("benchmark_step_ms") for s in sides]
        docs.append(
            {
                "hardware": hw,
                "model": model,
                "setup": setup,
                "gap_pct": 100 * (steps[1] / steps[0] - 1) if all(steps) else None,
                "slice": first.get("miniature") or None,
                "fastest": sides[0],
                "second": sides[1],
            }
        )
    (out / "profiles.json").write_text(json.dumps({"format": 1, "profiles": docs}, indent=1))
    for pattern in TRACES if not os.environ.get("PIE_BENCH_PROFILER_KEEP_TRACES") else ():
        for p in out.rglob(pattern):
            shutil.rmtree(p, ignore_errors=True) if p.is_dir() else p.unlink(missing_ok=True)
    return docs
