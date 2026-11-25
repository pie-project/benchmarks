from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

from pie_bench.paths import CONFIG
from server import publish
from server.views.attempts import attempt_note, attempts_by_tag, empty_row
from server.views.engines import engines as engine_rows
from server.views.engines import install_sizes
from server.views.hardware import cores_by_platform, phone_hardware
from server.views.hardware import hardware as hardware_rows
from server.views.matrix_files import CONTRIBUTED, contributed_platform, load
from server.views.models import artifact_to_model, suite_model_ids
from server.views.picking import as_row, results_by_tag
from server.views.quality import (
    mismatched_arms,
    parity_by_tag,
    quality_arms,
    quality_by_tag,
    quality_checks,
    quality_tasks,
)
from server.views.releases import is_diag_tag, local, tag_date
from server.views.support import (
    gpu_no_fit,
    gpu_note,
    gpu_unsupported,
    gpu_unsupported_setups,
    no_fit,
    stack,
    stack_sources,
    unsupported_reasons,
)
from server.views.workloads import CATEGORIES
from server.views.workloads import workloads as workload_rows

MEASURED = ("pass", "noisy")
PLATFORM_KINDS = ["Mac", "Windows", "GPU", "TPU", "AMD"]
QUALITY_MAC = "m5-max-128g"


class ReadOnce:
    def __init__(self, store):
        self.store = store
        self._table = None
        self._quality = None

    def table(self):
        if self._table is None:
            self._table = self.store.table()
        return self._table

    def quality(self):
        if self._quality is None:
            self._quality = self.store.quality()
        return [dict(q) for q in self._quality]

    def quality_answers(self):
        return self.store.quality_answers()


@dataclass
class Scope:
    a2m: dict[str, str]
    models: list[dict]
    config: dict
    mac_ids: list[str]
    gpu_ids: list[str]
    phone_rows: list[dict]
    phone_ids: list[str]
    suite_ids: dict[str, list[str]]
    model_ids: list[str]
    mac_engines: set[str]
    engine_ids: list[str]
    all_engines: list[str]


@dataclass
class EmptyCells:
    misfits: dict
    unsupported: dict
    memory: dict
    streams: dict
    ever: set

    def row(self, key: tuple, tag: str, tried: dict, cut: set) -> dict:
        hw, engine, model, _ = key
        gib = None if (hw, model) in cut else self.misfits.get(hw, {}).get(model, {}).get(engine)
        if gib:
            return empty_row(key, tag, "no_fit", self.no_fit_note(hw, model, gib))
        if (hw, engine, model) in self.unsupported or key in self.unsupported:
            return empty_row(
                key,
                tag,
                "unsupported",
                self.unsupported.get((hw, engine, model)) or self.unsupported[key],
            )
        if key in tried:
            status = "fail" if tried[key]["status"] == "fail" else "not_run"
            return empty_row(key, tag, status, attempt_note(tried[key]))
        return empty_row(
            key, tag, "not_run", "Not run in this release" if key in self.ever else "Not run yet"
        )

    def no_fit_note(self, hw: str, model: str, gib: float) -> str:
        stream = self.streams.get(model)
        streaming = f" {stream.lower()} SSD streaming" if stream in ("With", "Without") else ""
        where = "this Mac's GPU can use" if re.match(r"m\d", hw) else "this machine holds"
        return f"Needs about {round(gib)} GB{streaming}; {where} about {gpu_note(self.memory.get(hw))} GB"


@dataclass
class MissingScores:
    mac: str
    misfits: dict
    unsupported: dict
    memory: dict

    def reason(self, engine: str, model: str, otherwise: str) -> tuple[str, str]:
        gib = self.misfits.get(self.mac, {}).get(model, {}).get(engine)
        if gib:
            room = gpu_note(self.memory.get(self.mac))
            return (
                "no_fit",
                f"Needs about {round(gib)} GB; the quality Mac's GPU can use about {room} GB",
            )
        if (self.mac, engine, model) in self.unsupported:
            return "unsupported", self.unsupported[(self.mac, engine, model)]
        return otherwise, "Not run in this release" if otherwise == "not_run" else ""

    def row(
        self, model: str, engine: str, artifact: str, task: str, tag: str, otherwise: str
    ) -> dict:
        status, note = self.reason(engine, model, otherwise)
        return {
            "model": model,
            "engine": engine,
            "artifact": artifact,
            "task": task,
            "score": None,
            "release": tag,
            "status": status,
            "note": note,
            "stale": None,
        }


def build(store, contributed: dict[str, dict] | None = None) -> tuple[dict, dict[str, dict], dict]:
    use_contributed(contributed or {})
    store = ReadOnce(store)
    scope = scope_of(store)
    label_suites(scope)
    label_platforms(scope, store)
    off_mac = scope.gpu_ids + scope.phone_ids
    results, rmeta = results_by_tag(
        store,
        scope.a2m,
        scope.mac_ids + off_mac,
        scope.all_engines,
        scope.config.get("prefill_only"),
    )
    gpu_attempts = attempts_by_tag(store, scope.a2m, off_mac, scope.all_engines)
    gpu_keys = add_measured_off_mac(scope, results, gpu_attempts)
    scores, qmeta = quality_by_tag(store, scope.a2m)
    tags = release_tags(rmeta, qmeta)
    order = [x["id"] for x in tags]
    gpu_unsup = gpu_unsupported(
        scope.a2m, scope.gpu_ids, scope.all_engines, scope.config.get("benchmarks", [])
    )
    setup_unsup = unsupported_setups(scope, results, gpu_keys)
    grid = speed_grid(scope, gpu_keys, gpu_unsup, setup_unsup)
    sources = stack_sources(order, results, grid, run_time)
    hw_rows = shown_hardware(scope, store)
    misfits = no_fit(scope.a2m, scope.config, hw_rows, scope.engine_ids, scope.model_ids)
    misfits.update(gpu_no_fit(store, scope.a2m, hw_rows, scope.gpu_ids))
    attempts = attempts_by_tag(store, scope.a2m, scope.mac_ids, scope.engine_ids)
    for t, rs in gpu_attempts.items():
        attempts.setdefault(t, {}).update(rs)
    unsupported = unsupported_reasons(
        scope.a2m, scope.config, scope.mac_ids, scope.engine_ids, scope.model_ids
    )
    unsupported.update(gpu_unsup)
    unsupported.update({k: r for k, r in setup_unsup.items() if k not in unsupported})
    memory = {h["id"]: h.get("memory_gib") for h in hw_rows}
    empty = EmptyCells(
        misfits,
        unsupported,
        memory,
        {m["id"]: m.get("ssd_streaming") for m in scope.models},
        {key for pairs in sources.values() for key, _ in pairs},
    )
    shown_models = [m for m in scope.models if m["id"] in scope.model_ids or m.get("catalog")]
    ctx = {"models": shown_models, "suites": scope.suite_ids}
    sealed = {
        t: publish.seal(
            release_rows(t, sources.pop(t), results, grid, attempts.get(t, {}), gpu_unsup, empty),
            ctx,
        )
        for t in order[:1]
    }
    quality = quality_rows(
        order, scores, scope, MissingScores(quality_mac(scope), misfits, unsupported, memory)
    )
    parity = parity_by_tag(store, scope.a2m)
    checks = quality_checks(store, scope.a2m)
    db = {
        "updated_at": updated_at(store),
        "totals": totals(store),
        "tags": tags[:1],
        "parity": {t: parity.get(t, []) for t in order[:1]},
        "quality_parity": checks["parity"],
        "quality_kernels": checks["kernels"],
        "quality_gaps": load("support").get("quality_gaps", []),
        "speed_gaps": load("support").get("speed_gaps", []),
        "no_fit": misfits,
        "suites": scope.suite_ids,
        "hardware": hw_rows,
        "engines": engine_rows(),
        "models": shown_models,
        "workloads": workload_rows(),
        "install": install_sizes(),
        "quality_tasks": quality_tasks(),
        "quality": quality.get(order[0], []) if order else [],
    }
    return db, sealed, quality


def use_contributed(contributed: dict[str, dict]) -> None:
    CONTRIBUTED.clear()
    CONTRIBUTED.update({pid: contributed_platform(spec) for pid, spec in contributed.items()})


def scope_of(store) -> Scope:
    a2m, models = artifact_to_model()
    config = json.loads(CONFIG.read_text())
    platforms = load("platforms")["platforms"]
    phone_rows = phone_hardware(store)
    phone_ids = [h["id"] for h in phone_rows]
    suite_ids = suite_model_ids(config, a2m)
    mac_engines = [e["id"] for e in engine_rows() if "macos" in e["os"]]
    return Scope(
        a2m=a2m,
        models=models,
        config=config,
        mac_ids=mac_ids(store, config, platforms),
        gpu_ids=[p["id"] for p in platforms if p.get("os") != "macos" and p["id"] not in phone_ids],
        phone_rows=phone_rows,
        phone_ids=phone_ids,
        suite_ids=suite_ids,
        model_ids=sorted({m for ids in suite_ids.values() for m in ids}),
        mac_engines=set(mac_engines),
        engine_ids=list(mac_engines),
        all_engines=[e["id"] for e in engine_rows()],
    )


def mac_ids(store, config: dict, platforms: list[dict]) -> list[str]:
    macs = {p["id"] for p in platforms if p.get("os") == "macos"}
    seen = {
        r["platform"]
        for r in store.table().select(["platform", "status"]).to_pylist()
        if r["status"] in MEASURED
    }
    return list(config["machines"]) + sorted((seen & macs) - set(config["machines"]))


def label_suites(scope: Scope) -> None:
    targeted, full = scope.suite_ids.get("targeted", []), scope.suite_ids.get("full", [])
    for m in scope.models:
        m["suite"] = "Targeted" if m["id"] in targeted else "Full" if m["id"] in full else ""


def platform_kind(p: dict) -> str:
    if p.get("os") == "macos":
        return "Mac"
    if p.get("os") == "windows":
        return "Windows"
    if p.get("backend") == "xla":
        return "TPU"
    return "AMD" if p.get("backend") == "rocm" else "GPU"


def label_platforms(scope: Scope, store) -> None:
    kind = {
        p["id"]: platform_kind(p)
        for p in load("platforms")["platforms"]
        if p["id"] not in scope.phone_ids
    }
    seen: dict[str, set[str]] = {}
    for r in store.table().select(["artifact", "platform", "status"]).to_pylist():
        if r["status"] in MEASURED and r["artifact"] in scope.a2m and r["platform"] in kind:
            seen.setdefault(scope.a2m[r["artifact"]], set()).add(kind[r["platform"]])
    for m in scope.models:
        m["platforms"] = ", ".join(k for k in PLATFORM_KINDS if k in seen.get(m["id"], set()))


def add_measured_off_mac(scope: Scope, results: dict, gpu_attempts: dict) -> set[tuple]:
    off_mac = set(scope.gpu_ids) | set(scope.phone_ids)
    keys = {k for rs in [*results.values(), *gpu_attempts.values()] for k in rs if k[0] in off_mac}
    models = sorted({k[2] for k in keys} - set(scope.model_ids))
    scope.model_ids += models
    if "full" in scope.suite_ids:
        scope.suite_ids["full"] = scope.suite_ids["full"] + models
    scope.engine_ids += [
        e for e in scope.all_engines if e not in scope.engine_ids and any(k[1] == e for k in keys)
    ]
    return keys


def release_tags(rmeta: dict, qmeta: dict) -> list[dict]:
    meta = dict(qmeta)
    for t, m in rmeta.items():
        meta[t] = {**m, "at": max(m["at"], qmeta[t]["at"])} if t in qmeta else m
    tags = (
        {"id": t, "kind": m["kind"], "date": tag_date(t, m), "commit": m["commit"]}
        for t, m in meta.items()
        if not is_diag_tag(t)
    )
    return sorted(tags, key=lambda x: x["date"] or "", reverse=True)


def unsupported_setups(scope: Scope, results: dict, gpu_keys: set[tuple]) -> dict[tuple, str]:
    measured = {k for rs in results.values() for k in rs}
    ran = {(g[0], g[2], g[3]) for g in gpu_keys}
    return {
        k: r
        for k, r in gpu_unsupported_setups(scope.a2m, scope.gpu_ids, scope.all_engines).items()
        if k[2] in scope.model_ids
        and k[1] in scope.engine_ids
        and k not in measured
        and (k[0], k[2], k[3]) in ran
    }


def speed_grid(
    scope: Scope, gpu_keys: set[tuple], gpu_unsup: dict, setup_unsup: dict
) -> list[tuple]:
    categories = [c for c, _, _ in CATEGORIES]
    grid = [
        (hw, e, m, c)
        for e in scope.engine_ids
        for m in scope.model_ids
        for hw in scope.mac_ids
        for c in categories
        if e in scope.mac_engines
    ]
    grid += [
        (hw, e, m, c)
        for e in scope.engine_ids
        for m in scope.model_ids
        for hw in scope.gpu_ids + scope.phone_ids
        for c in categories
        if (hw, e, m, c) in gpu_keys
    ]
    grid += [k for k in setup_unsup if k not in gpu_keys]
    tpus = {p["id"] for p in load("platforms")["platforms"] if p.get("backend") == "xla"}
    measured_on = {k[0] for k in gpu_keys}
    grid += [
        (hw, e, m, "raw")
        for hw, e, m in gpu_unsup
        if m in scope.model_ids
        and (hw, e, m, "raw") not in gpu_keys
        and (hw in tpus or hw in measured_on)
    ]
    return grid


def run_time(item: tuple) -> str:
    return local(item[1]["started_at"])


def shown_hardware(scope: Scope, store) -> list[dict]:
    rows = hardware_rows(cores_by_platform(store))
    shown = [
        h
        for h in rows
        if h["id"] not in scope.phone_ids
        and (h["id"] in scope.mac_ids or h["class"] != "mac" or not h.get("runs"))
    ]
    return shown + scope.phone_rows


def release_rows(
    tag: str,
    sources: list[tuple],
    results: dict,
    grid: list[tuple],
    tried: dict,
    gpu_unsup: dict,
    empty: EmptyCells,
) -> list[dict]:
    rows = [
        {
            **as_row(results[src][key][1], key, src),
            "stale": None if src == tag else {"tag": src, "measured": run_time(results[src][key])},
        }
        for key, src in sources
    ]
    have = {(r["hardware"], r["engine"], r["model"], r["workload"]): r for r in rows}
    cut = {(r["hardware"], r["model"]) for r in rows if r.get("miniature")}
    filled = []
    for key in grid:
        row = None if key[:3] in gpu_unsup else have.get(key)
        if row is None:
            filled.append(empty.row(key, tag, tried, cut))
            continue
        if row["stale"] and key in tried:
            note = attempt_note(tried[key])
            row["note"] = f"In {tag}: {note[:1].lower()}{note[1:]}"
        filled.append(row)
    return filled


def quality_mac(scope: Scope) -> str:
    return QUALITY_MAC if QUALITY_MAC in scope.mac_ids else scope.mac_ids[-1]


def quality_rows(
    order: list[str], scores: dict, scope: Scope, missing: MissingScores
) -> dict[str, list[dict]]:
    keys = sorted({k for rows in scores.values() for k in rows})
    quality = stack(
        order,
        scores,
        keys,
        lambda item, key, src: {k: v for k, v in item.items() if k != "_at"},
        lambda item: item["date"],
    )
    for t in order[:1]:
        quality[t] = with_missing_scores(quality[t], t, scope, missing)
    return quality


def with_missing_scores(
    rows: list[dict], tag: str, scope: Scope, missing: MissingScores
) -> list[dict]:
    a2m = scope.a2m
    arms = quality_arms(scope.config)
    mismatched = mismatched_arms()
    tasks = [t["id"] for t in quality_tasks()]
    have = {(r["engine"], r["artifact"], r["task"]) for r in rows}
    rows += [
        missing.row(a2m.get(art, art), eng, art, task, tag, "not_run")
        for eng, art in arms
        for task in tasks
        if (eng, art, task) not in have
    ]
    armed = {(eng, a2m.get(art, art)) for eng, art in arms}
    rows += [
        missing.row(model, eng, "", task, tag, "no_data")
        for eng in scope.engine_ids
        for model in scope.model_ids
        if (eng, model) not in armed
        for task in tasks
    ]
    rows = [
        missing.row(r["model"], r["engine"], r["artifact"], r["task"], tag, "unsupported")
        | {"note": mismatched[r["artifact"]]}
        if r["artifact"] in mismatched
        else r
        for r in rows
    ]
    for r in rows:
        r.setdefault("status", "pass")

    def rank(xs: list[str], x: str) -> int:
        return xs.index(x) if x in xs else len(xs)

    rows.sort(
        key=lambda r: (
            rank(scope.engine_ids, r["engine"]),
            rank(scope.model_ids, r["model"]),
            r["model"],
            rank(tasks, r["task"]),
        )
    )
    return rows


def updated_at(store) -> str | None:
    stamps = [
        r["started_at"]
        for r in store.table().select(["started_at"]).to_pylist()
        if r["started_at"] is not None
    ]
    stamps += [
        datetime.fromisoformat(q["date"].replace("Z", "+00:00"))
        for q in store.quality()
        if q.get("date")
    ]
    stamps = [t if t.tzinfo else t.replace(tzinfo=ZoneInfo("UTC")) for t in stamps]
    return max(stamps).isoformat() if stamps else None


def totals(store) -> dict:
    done = [
        r
        for r in store.table().select(["status", "duration_s"]).to_pylist()
        if r["status"] in ("pass", "noisy", "fail")
    ]
    return {
        "runs": len(done) + len(store.quality()),
        "machine_s": round(sum(r["duration_s"] or 0 for r in done)),
    }
