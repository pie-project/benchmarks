"""Build web/data/db.js for the site from the result store (Postgres at $PIE_EVALS_DB).

    PIE_EVALS_DB=postgresql://... .venv/bin/python tools/webdb.py

The store holds one row per measured cell across every tier and platform. This keeps
the newest passing run per platform, engine, model, release and workload-category,
collapsing the many measured workloads into two the site shows: a single request and
a throughput (concurrency) run.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml

from pie_evals.quality.parity import rows as parity_rows
from pie_evals.results.store import Store

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"

# Each site workload maps to measured workloads, best first.
SINGLE = ["ss-512-256", "ob-512-200", "ss-128-64", "ob-short-100", "ob-story-200"]
THROUGHPUT = ["c32", "c64", "c256", "c8", "c4"]
SITE_TZ = ZoneInfo("America/Los_Angeles")  # the team is in California: dates and times on the site are Pacific

WL_PRIORITY = {wl: (cat, i) for cat, ids in (("single", SINGLE), ("throughput", THROUGHPUT)) for i, wl in enumerate(ids)}

ENGINE_META = {
    "pie":      ("pie", "Apache-2.0", "pie-project/pie"),
    "vllm":     ("vLLM", "Apache-2.0", "vllm-project/vllm"),
    "sglang":   ("SGLang", "Apache-2.0", "sgl-project/sglang"),
    "llamacpp": ("llama.cpp", "MIT", "ggml-org/llama.cpp"),
    "mlxlm":    ("MLX", "MIT", "ml-explore/mlx-lm"),
    "splash":   ("Splash", None, "incoai/splash"),
}
METRICS = ["decode_tok_s", "prefill_tok_s", "output_tok_s", "ttft_ms_p50", "ttft_ms_p99",
           "itl_ms_p50", "itl_ms_p99", "latency_ms_p50", "latency_ms_p99", "resident_gib", "load_s"]


def load(name: str) -> dict:
    return yaml.safe_load((ROOT / "matrix" / f"{name}.yaml").read_text())


def model_name(base: str) -> str:
    drop = {"4bit", "bf16", "gguf", "mlx", "mxfp4", "q4", "q4km", "mtp", "instruct", "it", "base", "8k", "mini5", "mini8"}
    tail = base.split("/")[-1]
    return "-".join(p for p in tail.split("-") if p.lower() not in drop)


def artifact_to_model() -> tuple[dict[str, str], list[dict]]:
    by_model: dict[str, dict] = {}
    mapping = {}
    for a in load("models")["artifacts"]:
        base = a.get("base_model") or a["id"]
        mid = model_name(base).lower()
        mapping[a["id"]] = mid
        row = by_model.setdefault(mid, {"id": mid, "name": model_name(base), "family": a.get("family"),
                                        "base_model": base, "schemes": set(), "artifacts": 0})
        row["artifacts"] += 1
        row["draft"] = row.get("draft") or bool(a.get("pie_drafter"))
        if a.get("scheme"):
            row["schemes"].add(a["scheme"])
    for row in by_model.values():
        name = row["name"]
        sizes = re.findall(r"(\d+(?:\.\d+)?)b", name, re.I)
        active = re.search(r"a(\d+(?:\.\d+)?)b", name, re.I)
        row["params_b"] = float(sizes[0]) if sizes else None
        row["active_b"] = float(active.group(1)) if active else row["params_b"]
        row["architecture"] = "MoE" if active or "moe" in (row["family"] or "") else "dense"
        # one definition per model today, every expert resident: no SSD streaming. A streaming twin would fit smaller Macs.
        row["ssd_streaming"] = "Without" if row["architecture"] == "MoE" else "n/a"
        row["schemes"] = ", ".join(sorted(row["schemes"]))
        row["draft"] = "true" if row.get("draft") else "false"
        # weights only, from the parameter count and the bits each weight takes (4-bit affine with a 16-bit scale and
        # bias per 64 weights = 4.5 bits; NVFP4 4-bit with an 8-bit scale per 16 = 4.5 bits)
        row["size_gib"] = round(row["params_b"] * 1e9 * 4.5 / 8 / 2**30, 1) if row["params_b"] else None
        # what it takes to fit: the planner's own rule (weights x 1.25 must fit in the Mac's memory)
        row["needs_gib"] = round(row["size_gib"] * 1.25, 1) if row["size_gib"] else None
        row["context"] = None
        row["license"] = None
    return mapping, list(by_model.values())


def hardware() -> list[dict]:
    rows = []
    for p in load("platforms")["platforms"]:
        mac = p.get("os") == "macos"
        rows.append({
            "id": p["id"],
            "resource": "Pie self-hosted",
            "name": p["accelerator"].replace("NVIDIA ", "") + (f" ×{p['count']}" if p.get("count", 1) > 1 else ""),
            "class": "mac" if mac else "gpu", "location": "local" if mac else "cloud",
            "vendor": "Apple" if mac else "NVIDIA", "backend": p.get("backend"), "arch": p.get("arch"),
            "count": p.get("count", 1), "memory_gib": p.get("memory_gib"), "bandwidth_gbs": None, "gpu_cores": None,
            "interconnect": p.get("interconnect"), "power_w": None, "price_usd": None, "price_hr": None,
        })
    return rows


# what each engine can draft with, filled by hand from its docs and release notes
SPECULATIVE = {
    "pie": "Yes: DFlash, DFlash2, MTP drafters",
    "splash": "Yes: DFlash2",
    "llamacpp": "Yes: a separate draft model (--model-draft)",
    "mlxlm": "Yes: a separate draft model (--draft-model)",
    "vllm": "Yes: EAGLE, MTP, n-gram, draft model",
    "sglang": "Yes: EAGLE, MTP, n-gram",
}


def engines() -> list[dict]:
    rows = []
    for e in load("engines")["engines"]:
        name, lic, repo = ENGINE_META.get(e["id"], (e["id"], None, None))
        rows.append({"id": e["id"], "name": name, "version": e.get("pin") or "main", "license": lic, "repo": repo,
                     "os": ", ".join(e.get("os", [])), "formats": ", ".join(e.get("formats", [])),
                     "speculative": SPECULATIVE.get(e["id"], "No")})
    return rows


def workloads() -> list[dict]:
    params = {w["id"]: w.get("params", {}) for w in load("workloads")["workloads"]}
    out = []
    for cat, ids, label in (("single", SINGLE, "Single request"), ("throughput", THROUGHPUT, "Throughput")):
        src = next((i for i in ids if i in params), None)
        p = params.get(src, {})
        out.append({"id": cat, "label": label, "concurrency": p.get("concurrency") or (1 if cat == "single" else 32),
                    "prompt_tokens": p.get("prefill"), "output_tokens": p.get("decode"), "benchmark": ", ".join(ids)})
    return out


# the quality benchmarks: what each task asks, where its questions come from, how an answer is scored
QUALITY_TASKS = [
    ("gsm8k", "Grade-school math word problems, worked step by step", "openai/gsm8k (test)", "final number matches"),
    ("ifeval", "Following explicit instructions (length, format, keywords)", "google/IFEval", "every instruction met"),
    ("mmlu", "Multiple-choice knowledge across 57 subjects", "cais/mmlu (test)", "chosen letter matches"),
    ("arc", "Grade-school science reasoning, multiple choice", "allenai/ai2_arc (ARC-Challenge test)", "chosen letter matches"),
    ("math500", "Competition math, final answer in boxed form", "HuggingFaceH4/MATH-500", "final answer equivalent"),
]


def quality_arms(config: dict) -> list[tuple[str, str]]:
    """(engine, artifact) for each competitor arm in config.json and the pie arm it is compared with."""
    arts = {a["id"]: a for a in load("models")["artifacts"]}
    out: list[tuple[str, str]] = []
    for aid in config["models"]:
        eng = next((e for e in ("llamacpp", "mlxlm", "splash") if aid.endswith(f"-{e}") or f"-{e}-" in aid), None)
        if eng:
            out.append((eng, aid))
        pie = arts.get(aid, {}).get("baseline_of")
        if pie and ("pie", pie) not in out:
            out.append(("pie", pie))
    return out


def quality_tasks() -> list[dict]:
    from pie_evals.quality.tasks import TASKS

    return [{"id": t, "task": t, "description": d, "source": src, "scoring": sc, "max_tokens": TASKS[t][2]}
            for t, d, src, sc in QUALITY_TASKS if t in TASKS]


# runs measured before the tagged runs live on this Mac: they stay on the site as the fallback



def local(ts) -> str:
    """A run time as Pacific 'YYYY-MM-DD HH:MM' (the store keeps UTC)."""
    return ts.astimezone(SITE_TZ).strftime("%Y-%m-%d %H:%M") if ts is not None else ""


def pick(rows: list[dict], a2m: dict[str, str]) -> dict[tuple, tuple]:
    """The row to show for each (hardware, engine, model, workload category): the best-matching workload, then the newest."""
    best: dict[tuple, tuple] = {}
    for r in rows:
        cat_pri = WL_PRIORITY.get(r["workload"])
        if not cat_pri:
            continue
        cat, pri = cat_pri
        model = a2m.get(r["artifact"], r["artifact"])
        key = (r["platform"], r["engine"], model, cat)
        rank = (-pri, r["started_at"])
        if key not in best or rank > best[key][0]:
            best[key] = (rank, r)
    return best


def as_row(r: dict, key: tuple, tag: str) -> dict:
    """``release`` is the tag the run belongs to; ``version`` is what actually ran (pie commit or engine release)."""
    hw, engine, model, cat = key
    version = (r["pie_commit"] or "")[:9] if engine == "pie" else r["engine_version"]
    return {
        "hardware": hw, "engine": engine,
        "release": tag, "group": tag, "version": version or "",
        "model": model, "scheme": r["scheme"], "workload": cat,
        **{m: (round(r[m], 2) if isinstance(r[m], (int, float)) and not (m == "prefill_tok_s" and cat == "throughput") else None) for m in METRICS},
        "accuracy": None,
        "commit": (r["pie_commit"] or "")[:9] if engine == "pie" else "",
        "measured": local(r["started_at"]),
        "status": r["status"], "note": "",
    }


def empty_row(key: tuple, tag: str, status: str, note: str) -> dict:
    """A combination with no numbers in this tag: it still gets its row, with the reason."""
    hw, engine, model, cat = key
    return {"hardware": hw, "engine": engine, "release": tag, "group": tag, "version": "", "model": model, "scheme": None,
            "workload": cat, **{m: None for m in METRICS}, "accuracy": None, "commit": "", "measured": "",
            "status": status, "note": note, "stale": None}


def attempts_by_tag(store, a2m, hardware_ids, engine_ids) -> dict[str, dict[tuple, dict]]:
    """The newest attempt that left no numbers (fail, not_run) per setup under each tag: the reason a cell is empty."""
    cols = (["platform", "engine", "artifact", "workload", "status", "error_class", "error_message", "invalid_reason", "started_at", "tag"]
            + ["decode_tok_s", "prefill_tok_s", "output_tok_s"])
    rows = store.table().select(cols).to_pylist()
    # a process whose control run crashed leaves its benchmarks without numbers; their reason is that crash
    crashed: dict[tuple, dict] = {}
    for r in sorted((r for r in rows if r["workload"] == "control-aa" and r["status"] == "fail"), key=lambda r: r["started_at"]):
        crashed[(r["platform"], r["engine"], r["artifact"], r["tag"])] = r  # the newest crash wins
    out: dict[str, dict[tuple, dict]] = {}
    for r in rows:
        if measured(r) or r["platform"] not in hardware_ids or r["engine"] not in engine_ids:
            continue
        if r["status"] in ("pass", "noisy"):
            crash = crashed.get((r["platform"], r["engine"], r["artifact"], r["tag"]))
            r = {**r, "status": "fail", "error_message": f"Could not start: {first_line(crash)}" if crash else "Finished without numbers"}
        cat = WL_PRIORITY.get(r["workload"], (None,))[0]
        if not cat:
            continue
        key = (r["platform"], r["engine"], a2m.get(r["artifact"], r["artifact"]), cat)
        t = r["tag"]
        if not t:  # untagged runs are not shown
            continue
        if key not in out.setdefault(t, {}) or r["started_at"] > out[t][key]["started_at"]:
            out[t][key] = r
    return out


def first_line(r: dict) -> str:
    lines = (r.get("error_message") or r.get("invalid_reason") or r.get("error_class") or "").strip().splitlines()
    return lines[0].removeprefix("RuntimeError: ").rstrip(": ") if lines else ""


def attempt_note(r: dict) -> str:
    """One line on why an attempt left no numbers."""
    msg = (r.get("error_message") or r.get("invalid_reason") or r.get("error_class") or "").strip().splitlines()
    msg = msg[0] if msg else ""
    if r["status"] == "not_run" and "hard deadline" in msg:
        return "The job ran out of time before this setup started"
    return (msg[:1].upper() + msg[1:])[:160] if msg else ("Failed" if r["status"] == "fail" else "Not run")


def unsupported_reasons(a2m: dict[str, str], config: dict, hardware_ids: list[str], engine_ids: list[str], model_ids: list[str]) -> dict[tuple, str]:
    """{(hardware, engine, model): reason} for setups the matrix declares unsupported, or that an engine has no build of."""
    from pie_evals.plan.matrix import Matrix, selector_matches
    from pie_evals.schema import Tier

    m = Matrix.load(ROOT / "matrix")
    wanted = set(config["models"])
    pie_arts = {a.baseline_of for a in m.artifacts.values() if a.id in wanted and a.baseline_of}
    # every copy of a configured model counts, not only the configured arm: an arm left out of
    # config.json because its engine cannot load the model still carries that reason
    arms = {a.id for a in m.artifacts.values() if a.id in wanted or a.id in pie_arts or a.baseline_of in pie_arts}
    benches = set(config.get("benchmarks", []))
    seen: dict[tuple, list[str | None]] = {}
    for c in m.cells_for(Tier.TARGETED):
        if c.platform.id not in hardware_ids or str(c.engine) not in engine_ids or c.artifact.id not in arms:
            continue
        # the release runs pair pie with its own weights and every other engine with its copy, nothing else
        if (str(c.engine) == "pie") != (c.artifact.baseline_of is None):
            continue
        if benches and c.workload.id not in benches:
            continue
        model = a2m.get(c.artifact.id)
        if model not in model_ids:
            continue
        # the declared rules first: an engine that cannot load a model at all says so even where it would not fit;
        # the fit rule speaks for itself elsewhere, with the sizes
        reason = next((rule.reason for rule in m.unsupported if selector_matches(rule.when, c)), None)
        if reason is None and c.declared_unsupported_reason and not c.declared_unsupported_reason.startswith("does not fit"):
            reason = c.declared_unsupported_reason
        seen.setdefault((c.platform.id, str(c.engine), model), []).append(reason)
    out = {k: next(r for r in rs if r) for k, rs in seen.items() if rs and all(rs)}
    names = {e: ENGINE_META.get(e, (e,))[0] for e in engine_ids}
    for hw in hardware_ids:
        for e in engine_ids:
            for model in model_ids:
                if (hw, e, model) not in seen:
                    out[(hw, e, model)] = f"{names[e]} has no build of this model"
    return out


def measured(r: dict) -> bool:
    """Passed (or noisy) and carrying at least one number."""
    return r["status"] in ("pass", "noisy") and any(r.get(m) is not None for m in ("decode_tok_s", "prefill_tok_s", "output_tok_s"))


def results_by_tag(store, a2m, hardware_ids, engine_ids):
    """The picked run per setup under each tag, and each tag's kind and newest time."""
    cols = (["platform", "engine", "engine_version", "artifact", "scheme", "workload", "status", "pie_commit", "started_at", "tag", "tag_kind"]
            + METRICS)
    rows = [r for r in store.table().select(cols).to_pylist()
            if measured(r) and r["platform"] in hardware_ids and r["engine"] in engine_ids]
    by_tag: dict[str, list[dict]] = {}
    for r in rows:
        if r["tag"]:  # untagged runs are not shown: every release is a tag
            by_tag.setdefault(r["tag"], []).append(r)
    tagged = {t: pick(rs, a2m) for t, rs in by_tag.items()}
    meta = {t: {"kind": rs[0]["tag_kind"] or "manual", "at": max(r["started_at"] for r in rs),
                "commit": next((r["pie_commit"][:9] for r in rs if r["engine"] == "pie" and r["pie_commit"]), "")}
            for t, rs in by_tag.items()}
    return tagged, meta


def quality_by_tag(store, a2m):
    """The newest score per (engine, model, weights, task) under each tag, and each tag's kind and newest time."""
    from datetime import datetime

    tagged: dict[str, dict[tuple, dict]] = {}
    meta: dict[str, dict] = {}
    for q in store.quality():
        t = q.get("tag")
        if not t:
            continue
        at = datetime.fromisoformat(q["date"].replace("Z", "+00:00"))
        row = {"model": a2m.get(q["model"], q["model"]), "engine": q["engine"], "artifact": q["artifact"],
               "task": q["task"], "score": round(q["score"], 3), "ci_low": round(q["ci95"][0], 3),
               "ci_high": round(q["ci95"][1], 3), "n": q["n"], "version": q.get("version"),
               "minutes": q.get("minutes"), "date": local(at)[:10], "release": t, "_at": at}
        key = (row["engine"], row["model"], row["artifact"], row["task"])
        if key not in tagged.setdefault(t, {}) or at > tagged[t][key]["_at"]:
            tagged[t][key] = row
        m = meta.setdefault(t, {"kind": q.get("tag_kind") or "manual", "at": at, "commit": ""})
        m["at"] = max(m["at"], at)
    return tagged, meta


def parity_by_tag(store, a2m) -> dict[str, list[dict]]:
    """Per tag, the engine parity of its quality scores: one row per model and task, every engine's cell against pie."""
    arts = {a["id"]: a for a in load("models")["artifacts"]}
    by_tag: dict[str, list[dict]] = {}
    for q in store.quality(samples=True):
        t = q.get("tag")
        if not t:
            continue
        art = arts.get(q["artifact"], {})  # older summaries carry no scheme or checkpoint: the matrix has them
        row = {**q, "model": a2m.get(q["model"], q["model"]), "tag": t,
               "scheme": q.get("scheme") or art.get("scheme"), "checkpoint": q.get("checkpoint") or art.get("base_model")}
        by_tag.setdefault(t, []).append(row)
    return {t: parity_rows(rs) for t, rs in by_tag.items()}


def stack(order: list[str], tagged: dict[str, dict], keys: list[tuple], row, when) -> dict[str, list[dict]]:
    """For each tag, one row per key: the tag's own, else the newest tag not later than it (marked stale); never a later tag."""
    snaps: dict[str, list[dict]] = {}
    for i, t in enumerate(order):
        out = []
        for key in keys:
            src = next((u for u in order[i:] if key in tagged.get(u, {})), None)
            if src is None:
                continue
            item = tagged[src][key]
            out.append({**row(item, key, src), "stale": None if src == t else {"tag": src, "measured": when(item)}})
        snaps[t] = out
    return snaps


def no_fit(a2m: dict[str, str], config: dict, hw_rows: list[dict], engine_ids: list[str], model_ids: list[str]) -> dict:
    """{hardware: {model: {engine: GiB needed}}} for every setup that cannot fit, by the planner's own fit rule
    (expected_gib × fit_factor > memory_gib). An engine's weights are its configured artifact; pie runs the MLX one."""
    factor = float(load("support").get("fit_factor", 1.25))
    arts = {a["id"]: a for a in load("models")["artifacts"]}
    need: dict[tuple[str, str], float] = {}
    for model in model_ids:
        for engine in engine_ids:
            if engine == "pie":
                ids = [i for i, a in arts.items() if a2m.get(i) == model and a.get("source_format") == "mlx" and a.get("kind") != "miniature"]
            else:
                ids = [i for i in config["models"] if i.endswith(f"-{engine}") and a2m.get(i) == model]
            sizes = [arts[i]["expected_gib"] for i in ids if arts.get(i, {}).get("expected_gib")]
            if sizes:
                need[(model, engine)] = min(sizes) * factor
        # without its own artifact on record, pie needs at least what the lightest other engine needs
        if (model, "pie") not in need and "pie" in engine_ids:
            others = [gib for (m, _), gib in need.items() if m == model]
            if others:
                need[(model, "pie")] = min(others)
    out: dict[str, dict] = {}
    for hw in hw_rows:
        memory = hw.get("memory_gib")
        if not memory:
            continue
        for (model, engine), gib in need.items():
            if gib > memory:
                out.setdefault(hw["id"], {}).setdefault(model, {})[engine] = round(gib, 1)
    return out


def tag_date(tag: str, meta: dict) -> str | None:
    """A release is dated by its pie publish date; a manual run by when it ran."""
    if meta["kind"] == "release":
        for args in (["releases/tags/" + tag, "--jq", ".published_at"], ["commits/" + tag, "--jq", ".commit.committer.date"]):
            try:
                out = subprocess.run(["gh", "api", "repos/pie-project/pie/" + args[0], "--jq", args[2]],
                                     capture_output=True, text=True, timeout=30).stdout.strip()
            except (OSError, subprocess.SubprocessError):
                out = ""
            if out:
                return out[:10]
        return None
    return local(meta["at"])


def main() -> None:
    store = Store(sys.argv[1] if len(sys.argv) > 1 else None)
    a2m, models = artifact_to_model()
    # the site's grid: our Macs, the engines that run on a Mac, the models we measure there
    config = json.loads((ROOT / "config.json").read_text())
    hardware_ids = config["machines"]
    mac_engines = [e for e in engines() if "macos" in e["os"]]
    model_ids = sorted({a2m[a] for a in config["models"] if a in a2m})
    engine_ids = [e["id"] for e in mac_engines]
    results, rmeta = results_by_tag(store, a2m, hardware_ids, engine_ids)
    scores, qmeta = quality_by_tag(store, a2m)
    # one list of tags for both tables: a tag with only quality scores still gets a results table, filled from earlier tags
    meta = dict(qmeta)
    for t, m in rmeta.items():
        meta[t] = {**m, "at": max(m["at"], qmeta[t]["at"])} if t in qmeta else m
    tags = sorted(({"id": t, "kind": m["kind"], "date": tag_date(t, m), "commit": m["commit"]} for t, m in meta.items()),
                  key=lambda x: x["date"] or "", reverse=True)  # the newest tag is the default on the site
    order = [x["id"] for x in tags]
    # the site's default order: engine, then model, then hardware, then workload
    grid = [(hw, e, m, c) for e in engine_ids for m in model_ids for hw in hardware_ids for c in ("single", "throughput")]
    snaps = stack(order, results, grid, lambda item, key, src: as_row(item[1], key, src), lambda item: local(item[1]["started_at"]))
    hw_rows = [h for h in hardware() if h["id"] in hardware_ids]
    misfits = no_fit(a2m, config, hw_rows, engine_ids, model_ids)
    attempts = attempts_by_tag(store, a2m, hardware_ids, engine_ids)
    unsupported = unsupported_reasons(a2m, config, hardware_ids, engine_ids, model_ids)
    memory = {h["id"]: h.get("memory_gib") for h in hw_rows}
    streams = {m["id"]: m.get("ssd_streaming") for m in models}
    # every combination of Mac, engine, model and workload has a row in every tag, on every Mac, run there or not:
    # its numbers, or why there are none (too big, unsupported, failed, not reached)
    for t in order:
        have = {(r["hardware"], r["engine"], r["model"], r["workload"]): r for r in snaps[t]}
        tried = attempts.get(t, {})
        filled = []
        for key in grid:
            hw, engine, model, cat = key
            row = have.get(key)
            if row is not None:
                if row["stale"] and key in tried:  # the older numbers stand in; say what happened this time
                    row["note"] = f"In {t}: {attempt_note(tried[key])[:1].lower()}{attempt_note(tried[key])[1:]}"
                filled.append(row)
                continue
            gib = misfits.get(hw, {}).get(model, {}).get(engine)
            if gib:
                streaming = f" {streams[model].lower()} SSD streaming" if streams.get(model) in ("With", "Without") else ""
                filled.append(empty_row(key, t, "no_fit", f"Needs about {round(gib)} GB{streaming}; this Mac has {memory.get(hw)} GB"))
            elif (hw, engine, model) in unsupported:
                filled.append(empty_row(key, t, "unsupported", unsupported[(hw, engine, model)]))
            elif key in tried:
                filled.append(empty_row(key, t, "fail" if tried[key]["status"] == "fail" else "not_run", attempt_note(tried[key])))
            else:
                filled.append(empty_row(key, t, "not_run", "Not run in this release"))
        snaps[t] = filled
    qkeys = sorted({k for rows in scores.values() for k in rows})
    quality = stack(order, scores, qkeys, lambda item, key, src: {k: v for k, v in item.items() if k != "_at"}, lambda item: item["date"])
    # every arm the release compares, on every task, has a row like the results table: its score, or "not run"
    arms = quality_arms(config)
    tasks = [t["id"] for t in quality_tasks()]
    for t in order:
        have = {(r["engine"], r["artifact"], r["task"]) for r in quality[t]}
        quality[t] += [{"model": a2m.get(art, art), "engine": eng, "artifact": art, "task": task, "score": None,
                        "release": t, "status": "not_run", "stale": None}
                       for eng, art in arms for task in tasks if (eng, art, task) not in have]
        for r in quality[t]:
            r.setdefault("status", "pass")
        # the results page's order: engine, then model, then task
        rank = lambda xs, x: xs.index(x) if x in xs else len(xs)  # noqa: E731
        quality[t].sort(key=lambda r: (rank(engine_ids, r["engine"]), rank(model_ids, r["model"]), r["model"], rank(tasks, r["task"])))
    # parity is per tag and never stacked: a release's table holds only the scores that release measured
    parity = parity_by_tag(store, a2m)
    db = {"tags": tags, "snapshots": snaps, "quality_snapshots": quality, "parity": {t: parity.get(t, []) for t in order},
          "no_fit": misfits,
          "hardware": hw_rows,
          "engines": mac_engines, "models": [m for m in models if m["id"] in model_ids],
          "workloads": workloads(), "quality_tasks": quality_tasks(), "quality": quality.get(order[0], []) if order else []}
    (WEB / "data").mkdir(parents=True, exist_ok=True)
    (WEB / "data" / "db.js").write_text("const DB = " + json.dumps(db, indent=2, default=str) + ";\n")
    print({k: len(v) for k, v in db.items()}, {t["id"]: (len(snaps[t["id"]]), len(quality[t["id"]])) for t in tags})
    print({t: {f: sum(1 for r in parity[t] if r["flag"] == f) for f in ("ok", "mismatch", "no_pie")} for t in parity})


if __name__ == "__main__":
    main()
