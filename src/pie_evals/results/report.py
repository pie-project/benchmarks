"""Reports: coverage matrix, regression diff, baseline ratios. Markdown out,
rendered by the collect workflow into the repo and GitHub Pages."""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from pie_evals.node.metrics.stats import regression_verdict
from pie_evals.plan.matrix import Matrix
from pie_evals.results.store import Store
from pie_evals.schema import Cell, CellStatus, RepetitionPolicy, Tier


@dataclass
class CellView:
    cell: Cell
    status: str
    latest: dict | None
    history: list[float]


def coverage(matrix: Matrix, store: Store, tier: Tier, cells: list[Cell] | None = None) -> list[CellView]:
    cells = matrix.cells_for(tier, cells)
    latest = store.latest_by_cell()
    hist = store.history()
    views = []
    for c in cells:
        if c.declared_unsupported_reason:
            st = str(CellStatus.DECLARED_UNSUPPORTED)
            row = None
        else:
            row = latest.get(c.cell_id)
            st = row["status"] if row else str(CellStatus.NOT_RUN)
        views.append(CellView(c, st, row, hist.get(c.cell_id, [])))
    return views


def coverage_markdown(views: list[CellView], tier: Tier) -> str:
    counts = defaultdict(int)
    for v in views:
        counts[v.status] += 1
    lines = [f"# Coverage — {tier}", "", "| status | cells |", "|---|---|"]
    for k in [s.value for s in CellStatus]:
        lines.append(f"| {k} | {counts.get(k, 0)} |")
    lines += ["", "## Gaps (expected supported, but not passing)", "", "| engine | platform | artifact | workload | program | mode | status | error | message |", "|---|---|---|---|---|---|---|---|---|"]
    gaps = [v for v in views if v.status not in (str(CellStatus.PASS), str(CellStatus.DECLARED_UNSUPPORTED))]
    for v in sorted(gaps, key=lambda v: (v.status, v.cell.platform.id, v.cell.artifact.id)):
        c = v.cell
        err = (v.latest or {}).get("error_class") or ""
        msg = ((v.latest or {}).get("error_message") or "").replace("|", "\\|")[:120]
        lines.append(f"| {c.engine} | {c.platform.id} | {c.artifact.id} | {c.workload.id} | {c.program.id} | {c.mode.key} | {v.status} | {err} | {msg} |")
    lines += ["", "## Declared unsupported", "", "| reason | cells |", "|---|---|"]
    reasons = defaultdict(int)
    for v in views:
        if v.cell.declared_unsupported_reason:
            reasons[v.cell.declared_unsupported_reason] += 1
    for r, n in sorted(reasons.items(), key=lambda kv: -kv[1]):
        lines.append(f"| {r} | {n} |")
    # per-family × platform grid of pie pass rate
    lines += ["", "## pie pass rate by family × platform", ""]
    grid: dict[tuple[str, str], list[int]] = defaultdict(lambda: [0, 0])
    plats = sorted({v.cell.platform.id for v in views})
    for v in views:
        if str(v.cell.engine) != "pie" or v.status == str(CellStatus.DECLARED_UNSUPPORTED):
            continue
        g = grid[(v.cell.artifact.family, v.cell.platform.id)]
        g[1] += 1
        if v.status == str(CellStatus.PASS):
            g[0] += 1
    fams = sorted({k[0] for k in grid})
    lines.append("| family | " + " | ".join(plats) + " |")
    lines.append("|---|" + "---|" * len(plats))
    for f in fams:
        cells = []
        for p in plats:
            ok, n = grid.get((f, p), [0, 0])
            cells.append(f"{ok}/{n}" if n else "·")
        lines.append(f"| {f} | " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


def regressions(matrix: Matrix, store: Store, tier: Tier, *, sigma: float = 2.0, window_days: int = 7, peak_days: int = 30) -> list[dict]:
    """Each cell's latest PASS value against its own last ``window_days`` (as vLLM's nightly gate does: the change must
    pass ``sigma`` spreads of that window and the noise bound a single measurement is allowed), with the gap to the
    best value of the last ``peak_days`` beside it, so a slow drift over many nights shows too."""
    now = datetime.now(timezone.utc)
    latest = store.latest_by_cell(tier)
    hist = store.history(tier, limit=500, since=now - timedelta(days=window_days))
    peaks = store.history(tier, limit=2000, since=now - timedelta(days=peak_days))
    out = []
    for cid, row in latest.items():
        if row["status"] != str(CellStatus.PASS) or row["primary_value"] is None:
            continue
        value = float(row["primary_value"])
        h = hist.get(cid, [])
        prior = h[:-1] if h and abs(h[-1] - value) < 1e-12 else h
        if len(prior) < 3:
            continue
        # a change smaller than the spread a single measurement is allowed (the node's NOISY bound)
        # is not a regression: a 1 % floor failed nightlies on -1.2 % single-stream drifts
        wl = matrix.workloads.get(str(row["workload"]))
        steady = wl is not None and str(wl.kind) in ("single_stream", "control_aa", "long_context")
        policy = RepetitionPolicy()
        floor = policy.cov_noisy_threshold if steady else policy.cov_noisy_threshold_concurrent
        v = regression_verdict(value, prior, sigma=sigma, floor_rel=floor)
        if v.regressed or v.improved:
            p = peaks.get(cid, [])
            peak = max(p) if p else None
            out.append(
                {
                    "cell_id": cid, "cell_key": row["cell_key"], "engine": row["engine"], "platform": row["platform"],
                    "artifact": row["artifact"], "workload": row["workload"], "program": row["program"], "mode": row["mode"],
                    "metric": row["primary_metric"], "value": value, "delta_rel": v.delta_rel,
                    "threshold_rel": v.threshold_rel, "kind": "regression" if v.regressed else "improvement",
                    "vs_peak_rel": (value - peak) / peak if peak else None, "window_runs": len(prior),
                    "pie_commit": row["pie_commit"], "engine_version": row["engine_version"], "family": row["family"],
                }
            )
    return sorted(out, key=lambda r: r["delta_rel"])


def regressions_markdown(rows: list[dict]) -> str:
    lines = ["# Regressions / improvements against the last 7 days", "", "| kind | engine | platform | artifact | workload | metric | value | Δ 7 days | threshold | vs 30-day best | commit/version |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        peak = f"{r['vs_peak_rel']*100:+.1f}%" if r.get("vs_peak_rel") is not None else ""
        lines.append(
            f"| {r['kind']} | {r['engine']} | {r['platform']} | {r['artifact']} | {r['workload']} | {r['metric']} | {r['value']:.4g} | {r['delta_rel']*100:+.1f}% | ±{r['threshold_rel']*100:.1f}% | {peak} | {r['pie_commit'] or r['engine_version'] or ''} |"
        )
    if len(lines) == 4:
        lines.append("| (none) | | | | | | | | | | |")
    return "\n".join(lines) + "\n"


def model_of(matrix: Matrix, artifact_id: str) -> str:
    """One name per model across its artifacts (mlx, gguf, bf16 builds of one checkpoint), as the site groups them."""
    art = matrix.artifacts.get(artifact_id)
    base = (art.base_model if art else None) or artifact_id
    drop = {"4bit", "bf16", "gguf", "mlx", "mxfp4", "q4", "q4km", "mtp", "instruct", "it", "base", "8k", "mini5", "mini8"}
    return "-".join(p for p in base.split("/")[-1].split("-") if p.lower() not in drop).lower()


def output_length_mismatches(matrix: Matrix, store: Store, tier: Tier | None = None, *, rel: float = 0.10) -> list[dict]:
    """Every engine is asked to write exactly the shape's length; this catches one that still stops early.
    For each machine, model and workload, compare every engine's mean output tokens per request with pie's;
    a gap past ``rel`` means their decode numbers do not describe the same work."""
    groups: dict[tuple, dict[str, dict]] = defaultdict(dict)
    for row in store.latest_by_cell(tier).values():
        done = int(row.get("requests") or 0) - int(row.get("failed") or 0)
        if row["status"] not in ("pass", "noisy") or not row.get("output_tokens") or done <= 0:
            continue
        key = (row["platform"], model_of(matrix, str(row["artifact"])), str(row["workload"]))
        prev = groups[key].get(row["engine"])
        if prev is None or row["started_at"] > prev["started_at"]:
            groups[key][row["engine"]] = {**row, "per_request": row["output_tokens"] / done}
    out = []
    for (platform, model, workload), by_engine in groups.items():
        pie = by_engine.get("pie")
        if not pie:
            continue
        for engine, row in by_engine.items():
            if engine == "pie":
                continue
            gap = row["per_request"] / pie["per_request"] - 1
            if abs(gap) > rel:
                out.append({"platform": platform, "model": model, "workload": workload, "engine": engine,
                            "per_request": row["per_request"], "pie_per_request": pie["per_request"], "gap_rel": gap})
    return sorted(out, key=lambda r: -abs(r["gap_rel"]))


def _declared_unsupported(matrix: Matrix, row: dict) -> bool:
    """Whether a support.yaml rule rules out the row's cell as the matrix stands now."""
    from pie_evals.plan.matrix import selector_matches
    from pie_evals.schema import EngineName

    try:
        cell = Cell(engine=EngineName(str(row["engine"])), platform=matrix.platforms[str(row["platform"])],
                    artifact=matrix.artifacts[str(row["artifact"])], workload=matrix.workloads[str(row["workload"])],
                    program=matrix.programs[str(row.get("program") or "text-completion-bench")], mode=matrix.modes[str(row.get("mode") or "tp1").split(",")[0]])
    except (AttributeError, KeyError, ValueError):
        return False
    return any(selector_matches(rule.when, cell) for rule in matrix.unsupported)


def prompt_length_mismatches(matrix: Matrix, store: Store, tier: Tier | None = None, *, rel: float = 0.01) -> list[dict]:
    """Every engine of a cold-prompt workload is sent the same prompts; a spread past ``rel`` in the mean prompt
    tokens per request the engines report means one prefilled more work than another (a chat template only one applied)."""
    groups: dict[tuple, dict[str, dict]] = defaultdict(dict)
    for row in store.latest_by_cell(tier).values():
        done = int(row.get("requests") or 0) - int(row.get("failed") or 0)
        wl = matrix.workloads.get(str(row["workload"]))
        if row["status"] not in ("pass", "noisy") or not row.get("prompt_tokens") or done <= 0 or not (wl and wl.params.get("cold_cache")):
            continue
        # a row of a cell the matrix now declares unsupported (Splash's c32 from before it was ruled out) is never
        # measured again, so its older prompts would fail every collect; the site does not show it either
        if _declared_unsupported(matrix, row):
            continue
        key = (row["platform"], model_of(matrix, str(row["artifact"])), str(row["workload"]))
        prev = groups[key].get(row["engine"])
        if prev is None or row["started_at"] > prev["started_at"]:
            groups[key][row["engine"]] = {**row, "per_request": row["prompt_tokens"] / done}
    out = []
    for (platform, model, workload), by_engine in groups.items():
        per = {e: r["per_request"] for e, r in by_engine.items()}
        if len(per) > 1 and max(per.values()) / min(per.values()) - 1 > rel:
            out.append({"platform": platform, "model": model, "workload": workload, "per_request": per,
                        "spread_rel": max(per.values()) / min(per.values()) - 1})
    return sorted(out, key=lambda r: -r["spread_rel"])


def output_length_markdown(rows: list[dict]) -> str:
    lines = ["# Output length against pie", "", "| machine | model | workload | engine | tokens per request | pie | gap |", "|---|---|---|---|---|---|---|"]
    for r in rows:
        lines.append(f"| {r['platform']} | {r['model']} | {r['workload']} | {r['engine']} | {r['per_request']:.0f} | {r['pie_per_request']:.0f} | {r['gap_rel']*100:+.0f}% |")
    if len(lines) == 4:
        lines.append("| (none) | | | | | | |")
    return "\n".join(lines) + "\n"


def _close(a, b, rel: float = 0.01) -> bool:
    if a is None or b is None:
        return a == b
    return abs(a - b) <= rel * max(a, b)


def baseline_ratios(matrix: Matrix, store: Store, tier: Tier) -> list[dict]:
    """pie vs each baseline arm on the same (platform, model, workload, program, mode).
    A baseline arm is its engine on pie's own artifact, or its own artifact (llama.cpp
    serves its own GGUF copy of the weights) paired with pie's through ``baseline_of``."""
    latest = store.latest_by_cell(tier)
    pie_key = {a.id: matrix.artifacts[a.baseline_of].artifact_key for a in matrix.artifacts.values() if a.baseline_of in matrix.artifacts}
    by_key: dict[tuple, dict[str, dict]] = defaultdict(dict)
    for row in latest.values():
        if row["status"] != str(CellStatus.PASS) or row["primary_value"] is None:
            continue
        key = (row["platform"], pie_key.get(row["artifact"], row["artifact_key"]), row["workload"], row["program"], row["mode"])
        arm = "pie" if row["engine"] == "pie" else row["artifact"] if row["artifact"] in pie_key else row["engine"]
        by_key[key][arm] = row
    out = []
    for key, arms in by_key.items():
        pie = arms.get("pie")
        if not pie:
            continue
        for arm, row in arms.items():
            if arm == "pie":
                continue
            eng = row["engine"]
            # the same measurement on both sides: aggregate output tok/s whenever
            # both rows carry it (a pie row recorded before the primary metric
            # followed the shape keys on the per-request decode rate and would
            # otherwise be set against vLLM's aggregate), else the primary
            metric = "output_tok_s" if row.get("output_tok_s") and pie.get("output_tok_s") else row["primary_metric"]
            pv = float(pie[metric]) if metric in pie and pie[metric] is not None else float(pie["primary_value"])
            bv = float(row[metric]) if metric in row and row[metric] is not None else float(row["primary_value"])
            ratio = bv / pv if pv else None
            out.append(
                {
                    "platform": key[0], "artifact": pie["artifact"], "workload": key[2], "program": key[3], "mode": key[4],
                    "baseline": eng, "baseline_artifact": row["artifact"], "baseline_version": row["engine_version"], "metric": metric, "pie_value": pv,
                    "baseline_value": bv, "baseline_over_pie": ratio,
                    "pie_leads": (ratio is not None and ratio < 1.0), "pie_cov": pie["cov"], "baseline_cov": row["cov"],
                    "input_ok": _close(pie["prompt_tokens"], row["prompt_tokens"]) and pie["output_tokens"] == row["output_tokens"],
                    "baseline_recipe": row["engine_config_recipe"],
                }
            )
    return sorted(out, key=lambda r: -(r["baseline_over_pie"] or 0))


def baseline_markdown(rows: list[dict]) -> str:
    lines = ["# pie vs baselines (latest, best-of-recipe)", "", "| platform | artifact | workload | program | mode | baseline | metric | pie | baseline | baseline/pie | inputs match | recipe |", "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        flag = "" if r["pie_leads"] else " **pie trails**"
        lines.append(
            f"| {r['platform']} | {r['artifact']} | {r['workload']} | {r['program']} | {r['mode']} | {r['baseline'] if r['baseline_artifact'] == r['artifact'] else r['baseline_artifact']} {r['baseline_version'] or ''} | {r.get('metric') or ''} | {r['pie_value']:.4g} | {r['baseline_value']:.4g} | {r['baseline_over_pie']:.3f}×{flag} | {'yes' if r['input_ok'] else '**NO**'} | {r['baseline_recipe'] or ''} |"
        )
    return "\n".join(lines) + "\n"


def escalation_families(matrix: Matrix, store: Store) -> list[str]:
    """Families with a confirmed smoke regression → promote to nightly."""
    if not matrix.escalation.get("on_smoke_regression_promote_family_to_nightly"):
        return []
    return sorted({r["family"] for r in regressions(matrix, store, Tier.SMOKE) if r["kind"] == "regression"})


def to_json(rows: list[dict]) -> str:
    return json.dumps(rows, indent=1, default=str)
