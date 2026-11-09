"""Turn cells into JobSpecs: one job per platform per tier, carrying the
pins and the history each cell needs for adaptive repetition."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from pie_evals.results.store import Store
from pie_evals.schema import Cell, JobSpec, RepetitionPolicy, Tier

if TYPE_CHECKING:
    from pie_evals.plan.matrix import Matrix


def process_key(c: Cell) -> tuple:
    return (str(c.engine), c.artifact.artifact_key, c.mode.key)



#: minutes a cell costs on top of its workload: vLLM and SGLang boot a fresh
#: server per cell (2–3 min of import, CUDA graph capture and warm-up on an
#: L40S; nightly 35926457671 lost 33 of 78 vLLM cells to the soft budget
#: because shards were packed on workload time alone); pie serves one
#: process per model, so its per-cell overhead is a few seconds
ENGINE_CELL_MINUTES = {"vllm": 4.0, "sglang": 3.5}  # measured: 12 vLLM Qwen3.5-0.8B cells took 3860 s on an L40S (nightly 35935510089)


#: pie on a TPU boots its server inside each cell (pie_bench) and compiles its batch-shape ladder before it serves
#: (prewarm, #1507): 7 min of it for Qwen3-0.6B, 20 for Qwen3.5-0.8B's GDN layers on a v6e (tpu.yml 42528607059).
#: Packed on workload time alone, TPU shards ran into their 7200 s kill with cells left (42528607059, 42556218004).
PIE_XLA_BOOT_MINUTES = 15.0


def cell_minutes(c: Cell, measured: dict[str, float] | None = None) -> float:
    """The cell's median recorded duration where the store has one (the static
    estimate left s00 shards' last cells not_run on every platform), else the estimate."""
    if measured and c.cell_id in measured:
        return measured[c.cell_id]
    extra = ENGINE_CELL_MINUTES.get(str(c.engine), 0.0)
    if str(c.engine) == "pie" and str(getattr(c.platform.backend, "value", c.platform.backend)) == "xla":
        extra += PIE_XLA_BOOT_MINUTES
    return float(c.workload.est_minutes) + extra

def load_minutes(c: Cell) -> float:
    """Minutes a process group spends before its first cell on a checkpoint of hundreds of GiB (the datacenter
    models): its share of the download and the engine's load across every GPU. Smaller ones are in the noise."""
    gib = float(c.artifact.expected_gib or 0)
    return gib / 30.0 if gib >= 200 else 0.0  # Kimi-K3 (1454 GiB): 48 min


def group_minutes(g: list[Cell], measured: dict[str, float] | None = None) -> float:
    return sum(cell_minutes(c, measured) for c in g) + (load_minutes(g[0]) if g else 0.0)


def shard_groups(cells: list[Cell], budget_minutes: float, measured: dict[str, float] | None = None) -> list[list[Cell]]:
    """Bin-pack cells into jobs of ~budget_minutes. A process group (same
    engine, artifact, mode = one loaded model) is never split; groups are
    placed largest-first into the first shard with room (first-fit
    decreasing), so a shard holds a few whole models and nothing else."""
    groups: dict[tuple, list[Cell]] = {}
    for c in cells:
        groups.setdefault(process_key(c), []).append(c)
    # a group larger than the budget is split into budget-sized pieces (the
    # model loads once per piece; pieces after the first carry no control-aa
    # cell, so they run without the A/A gate — recorded in the job's notes)
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
    store: Store | None = None,
    platforms: list[str] | None = None,
    engines: list[str] | None = None,
    cells: list[Cell] | None = None,
    label: str | None = None,
) -> list[JobSpec]:
    if cells is None and platforms:  # expand only the platforms asked for, not the whole matrix
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
        # our own Macs, not rented pods: a shard may run long (first model pulls, slow engines) rather than be killed
        kill_s = max(kill_s, 6 * 3600)
    jobs = []
    for plat, plat_cells in sorted(by_plat.items()):
        for idx, shard in enumerate(shard_groups(plat_cells, budget, measured)):
            # one model per process: order by (engine, artifact, mode) so the node loads each model once
            shard.sort(key=lambda c: (str(c.engine), c.artifact.id, c.mode.key, c.program.id, c.workload.id))
            backend = shard[0].platform.backend.value
            pins = {e.id: e.pin_for(backend) for e in matrix.engines.values() if e.pin_for(backend) and any(str(c.engine) == e.id for c in shard)}
            seed = f"{tier}|{plat}|{idx}|{pie_commit}|{stamp}|{label or ''}"
            job_id = f"{tier}-{plat}-s{idx:02d}-{stamp}-" + hashlib.sha256(seed.encode()).hexdigest()[:6]
            est = sum(cell_minutes(c, measured) for c in shard) + sum(load_minutes(g[0]) for g in _groups(shard))
            # a shard of a terabyte checkpoint outlives the tier's kill: it gets its own estimate times the kill factor
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
                    # a release's single-stream rows decide pie against Splash within a few percent, and one round
                    # of a drafting engine spreads more than that (Splash 1.3.1 Qwen3.8-27B: 70-84 tok/s): three, median
                    repetition=RepetitionPolicy(min_rounds=1 if tier in (Tier.SMOKE, Tier.TARGETED) else 3,
                                                single_stream_rounds=3 if tier == Tier.TARGETED else None),
                    history={c.cell_id: history.get(c.cell_id, []) for c in shard if c.cell_id in history},
                    per_cell_timeout_s=min(max(1800 if tier in (Tier.SMOKE, Tier.TARGETED) else 5400, int(max(load_minutes(c) for c in shard) * 2 * 60)), job_kill_s),
                    # a first run spends much of its time downloading models (a fresh pod pulls ~12 MB/s from the Hub:
                    # 0.5.3-b5 lost most vLLM/SGLang cells to a 60-min soft budget): the soft budget is the hard limit
                    budget_s=job_kill_s,
                    kill_s=job_kill_s,
                    # a Mac release run reports every row: a noisy laptop marks its rows noisy rather than empty
                    control_marks_noisy=tier == Tier.TARGETED,
                    est_minutes=est,
                    # pie's boot reads every weight across the GPUs before it announces: scale its deadline with the checkpoint
                    load_timeout_s=max(1200, int(600 + max(float(c.artifact.expected_gib or 0) for c in shard) * 6)),
                )
            )
    # baseline comparisons first: a capped dispatch (--max-jobs) must not end up pie-only
    jobs.sort(key=lambda j: (-len({str(c.engine) for c in j.cells}), -j.est_minutes))
    return jobs


def available_platforms(matrix: Matrix, repo: str, token: str | None = None) -> tuple[list[str] | None, dict[str, str]]:
    """Platforms a job can actually land on right now: RunPod ones (an
    ephemeral runner is created per job) and resident ones with an *online*
    registered runner carrying the platform's label. Everything else is
    skipped with a reason — a job queued for a runner that never comes sits
    in GitHub's queue for 24 h and holds the workflow's concurrency group."""
    env = {**os.environ, **({"GH_TOKEN": token} if token else {})}
    try:
        out = subprocess.run(["gh", "api", f"repos/{repo}/actions/runners?per_page=100"], capture_output=True, text=True, env=env, check=True).stdout
        runners = json.loads(out).get("runners", [])
    except Exception as e:  # noqa: BLE001
        return None, {"*": f"runner list unavailable ({str(e).strip()[:120]})"}
    note = ""
    online = {lab["name"] for r in runners if r.get("status") == "online" for lab in r.get("labels", [])}
    ok, skipped = [], {}
    for p in matrix.platforms.values():
        if p.runpod_gpu_type:
            ok.append(p.id)
        elif p.id in online:
            ok.append(p.id)
        else:
            skipped[p.id] = note or f"no online runner with label '{p.id}'"
    return ok, skipped


def _feature_for(backend: str) -> str:
    return {"cuda": "cuda", "metal": "metal", "vulkan": "vulkan", "wgpu": "wgpu", "webgpu": "wgpu", "xla": "xla", "rocm": "rocm"}[backend]


#: baseline rows older than this were measured with the recipe of the process's first cell (runner.recipe_for_cell)
BASELINE_RECIPE_PER_CELL_SINCE = datetime(2026, 9, 25, 6, 38, tzinfo=timezone.utc)


#: a baseline that came out noisy this many times at one version is noisy by nature (a drafting engine's
#: speed follows the text): it is kept as measured instead of being repeated on every run
NOISY_BASELINE_IS_SETTLED_AFTER = 2


def _version_numbers(version: str | None) -> tuple[int, ...]:
    return tuple(int(n) for n in re.findall(r"\d+", str(version or "")))


def at_least_pinned(version: str | None, pin: str | None) -> bool:
    """The version that ran is the pinned one or a newer one. An app that
    updates itself (Splash from Homebrew) moves past its pin, and its
    numbers still stand until the pin is raised."""
    have, want = _version_numbers(version), _version_numbers(pin)
    return bool(have and want) and have >= want


def recorded_cell_keys(store: Store, tier: Tier, pie_commit: str, baseline_pins: dict[str, str] | None = None) -> set[str]:
    """Cells the store already holds: pie cells at this pie commit, and baseline
    cells at the engine version the matrix pins, or a newer one (a vLLM number
    does not change with pie's commit). A re-dispatch after lost launches, or a
    new pie commit, then repeats only what never ran."""
    t = store.table(tier)
    if t.num_rows == 0:
        return set()
    latest = {}
    for r in t.select(["run_id", "cell_id", "cell_key", "pie_commit", "status", "engine", "engine_version", "checkpoint_revision", "artifact_kind", "error_class", "started_at"]).to_pylist():
        latest[(r["run_id"], r["cell_id"] or r["cell_key"])] = r
    pins = baseline_pins or {}
    done = set()
    noisy: dict[str, int] = {}
    for r in latest.values():
        k, c, s, e, v, rev, kind, cls, at = (r["cell_key"], r["pie_commit"], r["status"], r["engine"], r["engine_version"], r["checkpoint_revision"],
                                             r["artifact_kind"], r["error_class"], r["started_at"])
        if e != "pie" and s == "noisy" and str(cls or "") != "harness_invalid" and at_least_pinned(v, pins.get(str(e))):
            noisy[k] = noisy.get(k, 0) + 1
            if noisy[k] >= NOISY_BASELINE_IS_SETTLED_AFTER:
                done.add(k)
            continue
        if s in ("not_run", "noisy"):  # never reached, or measured on a card that could not agree with itself: a re-dispatch measures again
            continue
        if str(cls or "") == "harness_invalid":
            continue  # the harness, not the engine, failed (dirty card, preflight, budget): no verdict on the cell
        if str(rev or "").startswith("mini") and str(kind or "") != "miniature":
            continue  # a full row that served the miniature built beside it (pie #680): not a result
        if e != "pie" and s != "pass":
            continue  # a baseline that failed is a recipe or install fault, fixed on the harness side: measure again
        if e != "pie" and at is not None and at < BASELINE_RECIPE_PER_CELL_SINCE:
            continue  # measured with the process's first shape's recipe (SGLang graphs at the wrong ceiling): not a number
        if (e == "pie" and c == pie_commit) or (e != "pie" and at_least_pinned(v, pins.get(str(e)))):
            done.add(k)
    return done


def plan_pods(matrix: Matrix, jobs: list[JobSpec], *, pod_per_job: bool = False, max_pods: int | None = None) -> list[dict]:
    """One pod per hardware configuration: every job whose platform names this pod
    (an x1 on its x2) is routed to it by runner label and runs there in turn, so the
    build, the checkpoints and the caches are shared. Resident runners (Macs) need
    no pod and are left out. The kill timer covers the whole queue.

    ``pod_per_job`` (a run on its own pods): every job gets its own pod, of its own
    platform first (a one-GPU L40S, not an x2 with one GPU masked) and its host second,
    so the shards run side by side instead of in turn on one pod; past ``max_pods`` per
    platform the pods share the rest of the queue (the runners take any job of the run)."""
    if pod_per_job:
        out = []
        per: dict[str, int] = {}
        for j in jobs:
            plat = matrix.platforms[j.platform_id]
            host = matrix.platforms[plat.pod or plat.id]
            if not (plat.runpod_gpu_type or host.runpod_gpu_type):
                continue
            order = [x for x in (plat, host) if x.runpod_gpu_type]
            per[plat.id] = per.get(plat.id, 0) + 1
            if max_pods is not None and per[plat.id] > max_pods:
                mine = [p for p in out if p["labels"] == sorted(set(plat.runner_labels))]
                q = mine[(per[plat.id] - 1) % len(mine)]
                q["jobs"].append(j.job_id)
                q["est_minutes"] = round(q["est_minutes"] + j.est_minutes, 1)
                q["kill_minutes"] = max(matrix.kill_minutes, int(q["est_minutes"] * matrix.kill_factor) + 30)
                continue
            out.append({"pod": f"{plat.id}-{j.shard}", "labels": sorted(set(plat.runner_labels)), "jobs": [j.job_id],
                        "est_minutes": round(j.est_minutes, 1),
                        "kill_minutes": max(matrix.kill_minutes, int(j.est_minutes * matrix.kill_factor) + 30),
                        "fallback": list(dict.fromkeys(x.id for x in order))})
        return sorted(out, key=lambda p: p["pod"])
    pods: dict[str, dict] = {}
    for j in jobs:
        plat = matrix.platforms[j.platform_id]
        host = matrix.platforms[plat.pod or plat.id]
        if not host.runpod_gpu_type:
            continue
        p = pods.setdefault(host.id, {"pod": host.id, "labels": list(host.runner_labels), "jobs": [], "est_minutes": 0.0})
        p["labels"] = sorted(set(p["labels"]) | set(plat.runner_labels))
        p["jobs"].append(j.job_id)
        p["est_minutes"] = round(p["est_minutes"] + j.est_minutes, 1)
    for p in pods.values():
        p["kill_minutes"] = max(matrix.kill_minutes, int(p["est_minutes"] * matrix.kill_factor) + 30)
        # no stock for the x2: the smaller hosted platforms' own pods are tried next; each
        # carries only the labels of what it can seat, and the gate drops the rest
        hosted = [matrix.platforms[x] for x in p["labels"] if x in matrix.platforms]
        p["fallback"] = [p["pod"]] + [h.id for h in sorted(hosted, key=lambda h: -h.count) if h.id != p["pod"] and h.runpod_gpu_type]
    return sorted(pods.values(), key=lambda p: p["pod"])
