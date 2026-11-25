from __future__ import annotations

from pie_bench.installers.desktop_engines import MAC_ENGINES, WINDOWS_ENGINES
from pie_bench.machine import Machine, tier_for
from pie_bench.paths import CONFIG
from pie_bench.plan.jobs import make_jobs
from pie_bench.plan.matrix import Matrix
from pie_bench.plan.suites import all_models, load_config, suite_models
from pie_bench.schema import JobSpec, Tier


def arms(m: Matrix, models: list[str] | None, suite: str, mac: bool = True) -> list[str]:
    config = load_config(CONFIG)
    pool = (
        (all_models(config) if models else suite_models(config, suite))
        if mac
        else [a.id for a in m.artifacts.values()]
    )
    match = lambda a: any(
        q.lower() in a.id.lower() or q.lower() in (a.base_model or "").lower() for q in models or []
    )
    wanted = {a for a in pool if a in m.artifacts and (not models or match(m.artifacts[a]))}
    pie = {m.artifacts[a].baseline_of for a in wanted if m.artifacts[a].baseline_of}
    return sorted(
        {
            a.id
            for a in m.artifacts.values()
            if a.id in wanted or a.id in pie or (a.id not in pie and a.baseline_of in wanted)
        }
    )


def plan(
    m: Matrix,
    machine: Machine,
    *,
    pie_commit: str,
    models: list[str] | None,
    engines: list[str] | None,
    workloads: list[str] | None,
    suite: str,
    tier: Tier | None = None,
    every_artifact: bool = False,
) -> JobSpec | None:
    tier = tier or tier_for(machine)
    config = load_config(CONFIG)
    laptop = machine.platform.os in ("macos", "windows")
    ids = arms(m, models, suite, laptop and not every_artifact) if laptop or models else None
    cells = m.expand(platforms=[machine.platform.id], artifacts=ids)
    wls = set(workloads or config.get("benchmarks") or [])
    if wls:
        cells = [c for c in cells if c.workload.id in wls or str(c.workload.kind) == "control_aa"]
    if machine.platform.os == "macos":
        engines = engines or list(MAC_ENGINES)
    elif machine.platform.os == "windows":
        engines = engines or list(WINDOWS_ENGINES)
    jobs = make_jobs(
        m,
        tier,
        pie_commit=pie_commit,
        platforms=[machine.platform.id],
        engines=engines,
        cells=cells,
        label="local",
    )
    if not jobs:
        return None
    first = jobs[0]
    return first.model_copy(
        update={
            "cells": [c for j in jobs for c in j.cells],
            "shard": 0,
            "est_minutes": sum(j.est_minutes for j in jobs),
            "kill_s": sum(j.kill_s for j in jobs),
            "budget_s": sum(j.budget_s for j in jobs),
        }
    )
