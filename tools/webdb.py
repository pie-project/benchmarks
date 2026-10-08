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
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml

from pie_evals.results.store import Store

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"

# Each site workload maps to measured workloads, best first.
SINGLE = ["ss-512-256", "ob-512-200", "ss-128-64", "ob-short-100", "ob-story-200"]
THROUGHPUT = ["c32", "c64", "c256", "c8", "c4"]
SITE_TZ = ZoneInfo("America/Los_Angeles")  # the team is in California: dates and times on the site are Pacific
LEGACY = "legacy"  # runs from before tags: no tag, used only as a fallback
WL_PRIORITY = {wl: (cat, i) for cat, ids in (("single", SINGLE), ("throughput", THROUGHPUT)) for i, wl in enumerate(ids)}

ENGINE_META = {
    "pie":      ("pie", "Apache-2.0", "pie-project/pie"),
    "vllm":     ("vLLM", "Apache-2.0", "vllm-project/vllm"),
    "sglang":   ("SGLang", "Apache-2.0", "sgl-project/sglang"),
    "llamacpp": ("llama.cpp", "MIT", "ggml-org/llama.cpp"),
    "mlxlm":    ("MLX", "MIT", "ml-explore/mlx-lm"),
    "ollama":   ("Ollama", "MIT", "ollama/ollama"),
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
        if a.get("scheme"):
            row["schemes"].add(a["scheme"])
    for row in by_model.values():
        name = row["name"]
        sizes = re.findall(r"(\d+(?:\.\d+)?)B", name)
        active = re.search(r"A(\d+(?:\.\d+)?)B", name)
        row["params_b"] = float(sizes[0]) if sizes else None
        row["active_b"] = float(active.group(1)) if active else row["params_b"]
        row["architecture"] = "MoE" if active or "moe" in (row["family"] or "") else "dense"
        row["schemes"] = ", ".join(sorted(row["schemes"]))
        row["size_gib"] = None
        row["context"] = None
        row["license"] = None
    return mapping, list(by_model.values())


def hardware() -> list[dict]:
    rows = []
    for p in load("platforms")["platforms"]:
        mac = p.get("os") == "macos"
        rows.append({
            "id": p["id"],
            "name": p["accelerator"].replace("NVIDIA ", "") + (f" ×{p['count']}" if p.get("count", 1) > 1 else ""),
            "class": "mac" if mac else "gpu", "location": "local" if mac else "cloud",
            "vendor": "Apple" if mac else "NVIDIA", "backend": p.get("backend"), "arch": p.get("arch"),
            "count": p.get("count", 1), "memory_gib": p.get("memory_gib"), "bandwidth_gbs": None, "gpu_cores": None,
            "interconnect": p.get("interconnect"), "power_w": None, "price_usd": None, "price_hr": None,
        })
    return rows


def engines() -> list[dict]:
    rows = []
    for e in load("engines")["engines"]:
        name, lic, repo = ENGINE_META.get(e["id"], (e["id"], None, None))
        rows.append({"id": e["id"], "name": name, "version": e.get("pin") or "main", "license": lic, "repo": repo,
                     "os": ", ".join(e.get("os", [])), "formats": ", ".join(e.get("formats", [])),
                     "continuous_batching": None, "prefix_cache": None, "speculative": None, "structured_output": None})
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


# runs measured before the tagged runs live on this Mac: they stay on the site as the fallback
LEGACY_MACS = {"m5-max-128g"}


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
        **{m: (round(r[m], 2) if isinstance(r[m], (int, float)) else None) for m in METRICS},
        "accuracy": None,
        "commit": (r["pie_commit"] or "")[:9] if engine == "pie" else "",
        "measured": local(r["started_at"]),
    }


def results_by_tag(store, a2m, hardware_ids, engine_ids):
    """The picked run per setup under each tag, and each tag's kind and newest time."""
    cols = (["platform", "engine", "engine_version", "artifact", "scheme", "workload", "status", "pie_commit", "started_at", "tag", "tag_kind"]
            + METRICS)
    rows = [r for r in store.table().select(cols).to_pylist()
            if r["status"] in ("pass", "noisy") and r["platform"] in hardware_ids and r["engine"] in engine_ids]
    by_tag: dict[str, list[dict]] = {}
    for r in rows:
        by_tag.setdefault(r["tag"] or LEGACY, []).append(r)
    tagged = {t: pick(rs, a2m) for t, rs in by_tag.items()}
    meta = {t: {"kind": rs[0]["tag_kind"] or ("legacy" if t == LEGACY else "manual"), "at": max(r["started_at"] for r in rs),
                "commit": next((r["pie_commit"][:9] for r in rs if r["engine"] == "pie" and r["pie_commit"]), "")}
            for t, rs in by_tag.items()}
    return tagged, meta


def quality_by_tag(store, a2m):
    """The newest score per (engine, model, weights, task) under each tag, and each tag's kind and newest time."""
    from datetime import datetime

    tagged: dict[str, dict[tuple, dict]] = {}
    meta: dict[str, dict] = {}
    for q in store.quality():
        t = q.get("tag") or LEGACY
        at = datetime.fromisoformat(q["date"].replace("Z", "+00:00"))
        row = {"model": a2m.get(q["model"], q["model"]), "engine": q["engine"], "artifact": q["artifact"],
               "task": q["task"], "score": round(q["score"], 3), "ci_low": round(q["ci95"][0], 3),
               "ci_high": round(q["ci95"][1], 3), "n": q["n"], "version": q.get("version"),
               "minutes": q.get("minutes"), "date": local(at)[:10], "release": t, "_at": at}
        key = (row["engine"], row["model"], row["artifact"], row["task"])
        if key not in tagged.setdefault(t, {}) or at > tagged[t][key]["_at"]:
            tagged[t][key] = row
        m = meta.setdefault(t, {"kind": q.get("tag_kind") or ("legacy" if t == LEGACY else "manual"), "at": at, "commit": ""})
        m["at"] = max(m["at"], at)
    return tagged, meta


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


def main() -> None:
    store = Store(sys.argv[1] if len(sys.argv) > 1 else None)
    a2m, models = artifact_to_model()
    # the site's grid: our Macs, the engines that run on a Mac, the models we measure there
    config = json.loads((ROOT / "config.json").read_text())
    hardware_ids = config["machines"] + sorted(LEGACY_MACS - set(config["machines"]))
    mac_engines = [e for e in engines() if "macos" in e["os"]]
    model_ids = sorted({a2m[a] for a in config["models"] if a in a2m})
    engine_ids = [e["id"] for e in mac_engines]
    results, rmeta = results_by_tag(store, a2m, hardware_ids, engine_ids)
    scores, qmeta = quality_by_tag(store, a2m)
    # one list of tags for both tables: a tag with only quality scores still gets a results table, filled from earlier tags
    meta = dict(qmeta)
    for t, m in rmeta.items():
        meta[t] = {**m, "at": max(m["at"], qmeta[t]["at"])} if t in qmeta else m
    tags = sorted(({"id": t, "kind": m["kind"], "date": local(m["at"]), "commit": m["commit"]} for t, m in meta.items()),
                  key=lambda x: x["date"], reverse=True)  # the newest tag is the default on the site
    order = [x["id"] for x in tags]
    # the site's default order: engine, then model, then hardware, then workload
    grid = [(hw, e, m, c) for e in engine_ids for m in model_ids for hw in hardware_ids for c in ("single", "throughput")]
    snaps = stack(order, results, grid, lambda item, key, src: as_row(item[1], key, src), lambda item: local(item[1]["started_at"]))
    qkeys = sorted({k for rows in scores.values() for k in rows})
    quality = stack(order, scores, qkeys, lambda item, key, src: {k: v for k, v in item.items() if k != "_at"}, lambda item: item["date"])
    hw_rows = [h for h in hardware() if h["id"] in hardware_ids]
    db = {"tags": tags, "snapshots": snaps, "quality_snapshots": quality,
          "no_fit": no_fit(a2m, config, hw_rows, engine_ids, model_ids),
          "hardware": hw_rows,
          "engines": mac_engines, "models": [m for m in models if m["id"] in model_ids],
          "workloads": workloads(), "quality": quality.get(order[0], []) if order else []}
    (WEB / "data").mkdir(parents=True, exist_ok=True)
    (WEB / "data" / "db.js").write_text("const DB = " + json.dumps(db, indent=2, default=str) + ";\n")
    print({k: len(v) for k, v in db.items()}, {t["id"]: (len(snaps[t["id"]]), len(quality[t["id"]])) for t in tags})


if __name__ == "__main__":
    main()
