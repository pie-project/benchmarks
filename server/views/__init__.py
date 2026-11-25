from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

from pie_bench.paths import CONFIG
from pie_bench.plan.suites import suites
from server import encoding, publish
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


class ReadOnce:

    def __init__(self, store):
        self.store = store
        self._table = None
        self._quality = {}

    def table(self):
        if self._table is None:
            self._table = self.store.table()
        return self._table

    def quality(self, samples: bool = False):
        if samples not in self._quality:
            self._quality[samples] = self.store.quality(samples=samples)
        return [dict(q) for q in self._quality[samples]]

    def quality_answers(self):
        return self.store.quality_answers() if hasattr(self.store, "quality_answers") else self.store.quality(samples=True)

    def __getattr__(self, name):
        return getattr(self.store, name)


def build(store, contributed: dict[str, dict] | None = None) -> tuple[dict, dict[str, dict], dict]:
    CONTRIBUTED.clear()
    CONTRIBUTED.update({pid: contributed_platform(spec) for pid, spec in (contributed or {}).items()})
    import time
    t0 = time.monotonic()
    lap = lambda what: print(f"[webdb] {what}: {time.monotonic() - t0:.0f}s", file=sys.stderr, flush=True)
    store = ReadOnce(store)
    a2m, models = artifact_to_model()
    config = json.loads(CONFIG.read_text())
    macs = {p["id"] for p in load("platforms")["platforms"] if p.get("os") == "macos"}
    seen = {r["platform"] for r in store.table().select(["platform", "status"]).to_pylist() if r["status"] in ("pass", "noisy")}
    hardware_ids = list(config["machines"]) + sorted((seen & macs) - set(config["machines"]))
    mac_engines = [e for e in engine_rows() if "macos" in e["os"]]
    suite_ids = suite_model_ids(config, a2m)
    model_ids = sorted({m for ids in suite_ids.values() for m in ids})
    for m in models:
        m["suite"] = "Targeted" if m["id"] in suite_ids.get("targeted", []) else "Full" if m["id"] in suite_ids.get("full", []) else ""
    kind = {p["id"]: ("Mac" if p.get("os") == "macos" else "Windows" if p.get("os") == "windows" else "TPU" if p.get("backend") == "xla" else "AMD" if p.get("backend") == "rocm" else "GPU")
            for p in load("platforms")["platforms"]}
    kind.update({h["id"]: "Phone" for h in phone_hardware(store)})
    platforms: dict[str, set[str]] = {}
    for r in store.table().select(["artifact", "platform", "status"]).to_pylist():
        if r["status"] in ("pass", "noisy") and r["artifact"] in a2m and r["platform"] in kind:
            platforms.setdefault(a2m[r["artifact"]], set()).add(kind[r["platform"]])
    order = ["Mac", "Windows", "GPU", "TPU", "AMD", "Phone"]
    for m in models:
        m["platforms"] = ", ".join(t for t in order if t in platforms.get(m["id"], set()))
    engine_ids = [e["id"] for e in mac_engines]
    phone_rows = phone_hardware(store)
    phone_ids = [h["id"] for h in phone_rows]
    # a phone a submission contributed is among the platforms too: listed once, as a phone
    gpu_ids = [p["id"] for p in load("platforms")["platforms"] if p.get("os") != "macos" and p["id"] not in phone_ids]
    all_engines = [e["id"] for e in engine_rows()]
    results, rmeta = results_by_tag(store, a2m, hardware_ids + gpu_ids + phone_ids, all_engines, config.get("prefill_only"))
    lap("results_by_tag")
    gpu_attempts = attempts_by_tag(store, a2m, gpu_ids + phone_ids, all_engines)
    gpu_keys = {k for rs in [*results.values(), *gpu_attempts.values()] for k in rs if k[0] in gpu_ids or k[0] in phone_ids}
    gpu_models = sorted({k[2] for k in gpu_keys} - set(model_ids))
    model_ids += gpu_models
    if "full" in suite_ids:
        suite_ids["full"] = suite_ids["full"] + gpu_models
    engine_ids += [e for e in all_engines if e not in engine_ids and any(k[1] == e for k in gpu_keys)]
    scores, qmeta = quality_by_tag(store, a2m)
    lap("quality_by_tag")
    meta = dict(qmeta)
    for t, m in rmeta.items():
        meta[t] = {**m, "at": max(m["at"], qmeta[t]["at"])} if t in qmeta else m
    meta = {t: m for t, m in meta.items() if not is_diag_tag(t)}
    tags = sorted(({"id": t, "kind": m["kind"], "date": tag_date(t, m), "commit": m["commit"]} for t, m in meta.items()),
                  key=lambda x: x["date"] or "", reverse=True)
    order = [x["id"] for x in tags]
    grid = [(hw, e, m, c) for e in engine_ids for m in model_ids for hw in hardware_ids for c, _, _ in CATEGORIES if e in {x["id"] for x in mac_engines}]
    gpu_unsup = gpu_unsupported(a2m, gpu_ids, all_engines, config.get("benchmarks", []))
    grid += [(hw, e, m, c) for e in engine_ids for m in model_ids for hw in gpu_ids + phone_ids for c, _, _ in CATEGORIES if (hw, e, m, c) in gpu_keys]
    measured = {k for rs in results.values() for k in rs}
    setup_unsup = {k: r for k, r in gpu_unsupported_setups(a2m, gpu_ids, all_engines).items()
                   if k[2] in model_ids and k[1] in engine_ids and k not in measured
                   and any(g[0] == k[0] and g[2] == k[2] and g[3] == k[3] for g in gpu_keys)}
    grid += [k for k in setup_unsup if k not in gpu_keys]
    tpus = {p["id"] for p in load("platforms")["platforms"] if p.get("backend") == "xla"}
    grid += [(hw, e, m, "raw") for hw, e, m in gpu_unsup
             if m in model_ids and (hw, e, m, "raw") not in gpu_keys and (hw in tpus or any(k[0] == hw for k in gpu_keys))]
    when_run = lambda item: local(item[1]["started_at"])
    sources = stack_sources(order, results, grid, when_run)
    lap("stack")
    hw_rows = [h for h in hardware_rows(cores_by_platform(store)) if h["id"] not in phone_ids and (h["id"] in hardware_ids or h["class"] != "mac" or not h.get("runs"))] + phone_rows
    misfits = no_fit(a2m, config, hw_rows, engine_ids, model_ids)
    misfits.update(gpu_no_fit(store, a2m, hw_rows, gpu_ids))
    attempts = attempts_by_tag(store, a2m, hardware_ids, engine_ids)
    lap("attempts_by_tag")
    for t, rs in gpu_attempts.items():
        attempts.setdefault(t, {}).update(rs)
    unsupported = unsupported_reasons(a2m, config, hardware_ids, engine_ids, model_ids)
    unsupported.update(gpu_unsup)
    unsupported.update({k: r for k, r in setup_unsup.items() if k not in unsupported})
    memory = {h["id"]: h.get("memory_gib") for h in hw_rows}
    streams = {m["id"]: m.get("ssd_streaming") for m in models}
    ever = {key for pairs in sources.values() for key, _ in pairs}
    ctx = {"models": [m for m in models if m["id"] in model_ids or m.get("catalog")], "suites": suite_ids}
    sealed: dict[str, dict] = {}
    for t in order[:1]:
        rows = [{**as_row(results[src][key][1], key, src), "stale": None if src == t else {"tag": src, "measured": when_run(results[src][key])}}
                for key, src in sources.pop(t)]
        have = {(r["hardware"], r["engine"], r["model"], r["workload"]): r for r in rows}
        cut = {(r["hardware"], r["model"]) for r in rows if r.get("miniature")}
        tried = attempts.get(t, {})
        filled = []
        for key in grid:
            hw, engine, model, cat = key
            row = have.get(key)
            if row is not None and (hw, engine, model) in gpu_unsup:
                row = None
            if row is not None:
                if row["stale"] and key in tried:
                    row["note"] = f"In {t}: {attempt_note(tried[key])[:1].lower()}{attempt_note(tried[key])[1:]}"
                filled.append(row)
                continue
            gib = None if (hw, model) in cut else misfits.get(hw, {}).get(model, {}).get(engine)
            if gib:
                streaming = f" {streams[model].lower()} SSD streaming" if streams.get(model) in ("With", "Without") else ""
                where = "this Mac's GPU can use" if re.match(r"m\d", hw) else "this machine holds"
                filled.append(empty_row(key, t, "no_fit", f"Needs about {round(gib)} GB{streaming}; {where} about {gpu_note(memory.get(hw))} GB"))
            elif (hw, engine, model) in unsupported or key in unsupported:
                filled.append(empty_row(key, t, "unsupported", unsupported.get((hw, engine, model)) or unsupported[key]))
            elif key in tried:
                filled.append(empty_row(key, t, "fail" if tried[key]["status"] == "fail" else "not_run", attempt_note(tried[key])))
            else:
                filled.append(empty_row(key, t, "not_run", "Not run in this release" if key in ever else "Not run yet"))
        sealed[t] = publish.seal(filled, ctx)
        del rows, have, filled
    qkeys = sorted({k for rows in scores.values() for k in rows})
    quality = stack(order, scores, qkeys, lambda item, key, src: {k: v for k, v in item.items() if k != "_at"}, lambda item: item["date"])
    arms = quality_arms(config)
    mismatched = mismatched_arms()
    tasks =[t["id"] for t in quality_tasks()]
    qmac = "m5-max-128g" if "m5-max-128g" in hardware_ids else hardware_ids[-1]

    def why(eng: str, model: str, otherwise: str) -> tuple[str, str]:
        gib = misfits.get(qmac, {}).get(model, {}).get(eng)
        if gib:
            return "no_fit", f"Needs about {round(gib)} GB; the quality Mac's GPU can use about {gpu_note(memory.get(qmac))} GB"
        if (qmac, eng, model) in unsupported:
            return "unsupported", unsupported[(qmac, eng, model)]
        return otherwise, "Not run in this release" if otherwise == "not_run" else ""

    def missing(model: str, eng: str, art: str, task: str, t: str, otherwise: str) -> dict:
        status, note = why(eng, model, otherwise)
        return {"model": model, "engine": eng, "artifact": art, "task": task, "score": None,
                "release": t, "status": status, "note": note, "stale": None}

    for t in order[:1]:
        have = {(r["engine"], r["artifact"], r["task"]) for r in quality[t]}
        quality[t] += [missing(a2m.get(art, art), eng, art, task, t, "not_run")
                       for eng, art in arms for task in tasks if (eng, art, task) not in have]
        armed = {(eng, a2m.get(art, art)) for eng, art in arms}
        quality[t] += [missing(model, eng, "", task, t, "no_data")
                       for eng in engine_ids for model in model_ids if (eng, model) not in armed for task in tasks]
        quality[t] = [missing(r["model"], r["engine"], r["artifact"], r["task"], t, "unsupported") | {"note": mismatched[r["artifact"]]}
                      if r["artifact"] in mismatched else r for r in quality[t]]
        for r in quality[t]:
            r.setdefault("status", "pass")
        rank = lambda xs, x: xs.index(x) if x in xs else len(xs)
        quality[t].sort(key=lambda r: (rank(engine_ids, r["engine"]), rank(model_ids, r["model"]), r["model"], rank(tasks, r["task"])))
    parity = parity_by_tag(store, a2m)
    lap("parity_by_tag")
    checks = quality_checks(store, a2m)
    lap("quality_checks")
    stamps = [r["started_at"] for r in store.table().select(["started_at"]).to_pylist() if r["started_at"] is not None]
    stamps += [datetime.fromisoformat(q["date"].replace("Z", "+00:00")) for q in store.quality() if q.get("date")]
    stamps = [t if t.tzinfo else t.replace(tzinfo=ZoneInfo("UTC")) for t in stamps]
    updated_at = max(stamps).isoformat() if stamps else None
    lap("max")
    ran = sum(r["status"] in ("pass", "noisy", "fail") for r in store.table().select(["status"]).to_pylist())
    busy = sum(r["duration_s"] or 0 for r in store.table().select(["status", "duration_s"]).to_pylist() if r["status"] in ("pass", "noisy", "fail"))
    totals = {"runs": ran + len(store.quality()), "machine_s": round(busy)}
    db = {"updated_at": updated_at, "totals": totals, "tags": tags[:1], "parity": {t: parity.get(t, []) for t in order[:1]},
          "quality_parity": checks["parity"], "quality_kernels": checks["kernels"], "quality_gaps": load("support").get("quality_gaps", []),
          "speed_gaps": load("support").get("speed_gaps", []),
          "no_fit": misfits, "suites": suite_ids,
          "hardware": hw_rows,
          "engines": engine_rows(), "models": [m for m in models if m["id"] in model_ids or m.get("catalog")],
          "workloads": workload_rows(), "install": install_sizes(), "quality_tasks": quality_tasks(), "quality": quality.get(order[0], []) if order else []}
    return db, sealed, quality
