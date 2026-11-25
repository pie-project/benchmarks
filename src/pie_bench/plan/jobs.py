from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from pie_bench.results.store import BaseStore
from pie_bench.schema import Cell, JobSpec, RepetitionPolicy, Tier

if TYPE_CHECKING:
    from pie_bench.plan.matrix import Matrix


def process_key(c: Cell) -> tuple:
    return (str(c.engine), c.artifact.artifact_key, c.mode.key)


ENGINE_CELL_MINUTES = {"vllm": 4.0, "sglang": 3.5}


PIE_XLA_BOOT_MINUTES = 15.0


def cell_minutes(c: Cell, measured: dict[str, float] | None = None) -> float:
    if measured and c.cell_id in measured:
        return measured[c.cell_id]
    extra = ENGINE_CELL_MINUTES.get(str(c.engine), 0.0)
    if str(c.engine) == "pie" and str(getattr(c.platform.backend, "value", c.platform.backend)) == "xla":
        extra += PIE_XLA_BOOT_MINUTES
    return float(c.workload.est_minutes) + extra

def load_minutes(c: Cell) -> float:
    gib = float(c.artifact.expected_gib or 0)
    return gib / 30.0 if gib >= 200 else 0.0


def group_minutes(g: list[Cell], measured: dict[str, float] | None = None) -> float:
    return sum(cell_minutes(c, measured) for c in g) + (load_minutes(g[0]) if g else 0.0)


def shard_groups(cells: list[Cell], budget_minutes: float, measured: dict[str, float] | None = None) -> list[list[Cell]]:
    groups: dict[tuple, list[Cell]] = {}
    for c in cells:
        groups.setdefault(process_key(c), []).append(c)
    pieces: list[list[Cell]] = []
    for g in groups.values():
        if group_minutes(g, measured) <= budget_minutes:
            pieces.append(g)
            continue
        g = sorted(g, key=lambda c: (0 if c.workload.kind.value == "control_aa" else 1, -cell_minutes(c, measured)))
        cur: list[Cell] = []
        load = load_minutes(g[0])
        for c in g:
            if cur and load + cell_minutes(c, measured) > budget_minutes:
                pieces.append(cur)
                cur, load = [], load_minutes(g[0])
            cur.append(c)
            load += cell_minutes(c, measured)
        if cur:
            pieces.append(cur)
    ordered = sorted(pieces, key=lambda g: -group_minutes(g, measured))
    shards: list[list[Cell]] = []
    loads: list[float] = []
    for g in ordered:
        need = group_minutes(g, measured)
        for i, load in enumerate(loads):
            if load + need <= budget_minutes:
                shards[i].extend(g)
                loads[i] += need
                break
        else:
            shards.append(list(g))
            loads.append(need)
    return shards


def _groups(cells: list[Cell]) -> list[list[Cell]]:
    out: dict[tuple, list[Cell]] = {}
    for c in cells:
        out.setdefault(process_key(c), []).append(c)
    return list(out.values())


def make_jobs(
    matrix: Matrix,
    tier: Tier,
    *,
    pie_commit: str | None,
    store: BaseStore | None = None,
    platforms: list[str] | None = None,
    engines: list[str] | None = None,
    cells: list[Cell] | None = None,
    label: str | None = None,
) -> list[JobSpec]:
    if cells is None and platforms:
        cells = matrix.expand(platforms=platforms)
    cells = matrix.runnable(tier, cells)
    if platforms:
        cells = [c for c in cells if c.platform.id in platforms]
    if engines:
        cells = [c for c in cells if str(c.engine) in engines]
    history = store.history(limit=20) if store else {}
    measured = store.measured_minutes() if store else {}
    by_plat: dict[str, list[Cell]] = {}
    for c in cells:
        by_plat.setdefault(c.platform.id, []).append(c)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    budget = matrix.job_budget_minutes
    kill_s = int(budget * matrix.kill_factor * 60)
    if tier == Tier.TARGETED:
        kill_s = max(kill_s, 6 * 3600)
    jobs = []
    for plat, plat_cells in sorted(by_plat.items()):
        for idx, shard in enumerate(shard_groups(plat_cells, budget, measured)):
            shard.sort(key=lambda c: (str(c.engine), c.artifact.id, c.mode.key, c.program.id, c.workload.id))
            backend = shard[0].platform.backend.value
            pins = {e.id: e.pin_for(backend) for e in matrix.engines.values() if e.pin_for(backend) and any(str(c.engine) == e.id for c in shard)}
            seed = f"{tier}|{plat}|{idx}|{pie_commit}|{stamp}|{label or ''}"
            job_id = f"{tier}-{plat}-s{idx:02d}-{stamp}-" + hashlib.sha256(seed.encode()).hexdigest()[:6]
            est = sum(cell_minutes(c, measured) for c in shard) + sum(load_minutes(g[0]) for g in _groups(shard))
            job_kill_s = max(kill_s, int(est * matrix.kill_factor * 60))
            jobs.append(
                JobSpec(
                    job_id=job_id,
                    tier=tier,
                    platform_id=plat,
                    shard=idx,
                    pie_commit=pie_commit,
                    pie_build_features=[_feature_for(shard[0].platform.backend.value)],
                    baseline_versions=pins,
                    cells=shard,
                    repetition=RepetitionPolicy(min_rounds=1 if tier in (Tier.SMOKE, Tier.TARGETED) else 3,
                                                single_stream_rounds=3 if tier == Tier.TARGETED else None),
                    history={c.cell_id: history.get(c.cell_id, []) for c in shard if c.cell_id in history},
                    per_cell_timeout_s=min(max(1800 if tier in (Tier.SMOKE, Tier.TARGETED) else 5400, int(max(load_minutes(c) for c in shard) * 2 * 60)), job_kill_s),
                    budget_s=job_kill_s,
                    kill_s=job_kill_s,
                    control_marks_noisy=tier == Tier.TARGETED,
                    est_minutes=est,
                    load_timeout_s=max(1200, int(600 + max(float(c.artifact.expected_gib or 0) for c in shard) * 6)),
                )
            )
    jobs.sort(key=lambda j: (-len({str(c.engine) for c in j.cells}), -j.est_minutes))
    return jobs


def _feature_for(backend: str) -> str:
    return {"cuda": "cuda", "metal": "metal", "vulkan": "vulkan", "wgpu": "wgpu", "webgpu": "wgpu", "xla": "xla", "rocm": "rocm"}[backend]


BASELINE_RECIPE_PER_CELL_SINCE = datetime(2026, 9, 25, 6, 38, tzinfo=timezone.utc)


NOISY_BASELINE_IS_SETTLED_AFTER = 2
