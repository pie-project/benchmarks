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

import yaml

from pie_evals.results.store import Store

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"

# Each site workload maps to measured workloads, best first.
SINGLE = ["ss-512-256", "ob-512-200", "ss-128-64", "ob-short-100", "ob-story-200"]
THROUGHPUT = ["c32", "c64", "c256", "c8", "c4"]
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


def fleet() -> set[str]:
    """Only the Macs we operate are shown; every other platform stays in the database."""
    return set(json.loads((ROOT / "config.json").read_text())["machines"])


def best_per_key(rows: list[dict], a2m: dict[str, str]) -> dict[tuple, dict]:
    """One row per (hardware, engine, model, workload category, release) among these runs."""
    best: dict[tuple, tuple] = {}
    for r in rows:
        cat_pri = WL_PRIORITY.get(r["workload"])
        if not cat_pri:
            continue
        cat, pri = cat_pri
        model = a2m.get(r["artifact"], r["artifact"])
        release = (r["pie_commit"] or "")[:9] if r["engine"] == "pie" else r["engine_version"]
        key = (r["platform"], r["engine"], model, cat, release or "")
        rank = (-pri, r["started_at"])  # higher-priority workload, then newest
        if key not in best or rank > best[key][0]:
            best[key] = (rank, r, cat, model, release)
    return {k: v for k, v in best.items()}


def as_row(r: dict, cat: str, model: str, release: str | None) -> dict:
    return {
        "hardware": r["platform"], "engine": r["engine"],
        "release": release or "?", "group": "main" if r["engine"] == "pie" else (release or "?"),
        "model": model, "scheme": r["scheme"], "workload": cat,
        **{m: (round(r[m], 2) if isinstance(r[m], (int, float)) else None) for m in METRICS},
        "accuracy": None,
        "commit": (r["pie_commit"] or "")[:9] if r["engine"] == "pie" else "",
        "measured": str(r["started_at"])[:16],
    }


def snapshots(store, a2m: dict[str, str]):
    """Tags newest first, and for each tag a complete table of every combination the store has measured.

    A combination with no run under a tag is filled from its most recent run under another tag,
    and marked ``stale`` with that tag and date, so the site always has something to show.
    """
    cols = (["platform", "engine", "engine_version", "artifact", "scheme", "workload", "status", "pie_commit", "started_at", "tag", "tag_kind"]
            + METRICS)
    allowed = fleet()
    rows = [r for r in store.table().select(cols).to_pylist()
            if r["status"] in ("pass", "noisy") and r["platform"] in allowed]
    by_tag: dict[str, list[dict]] = {}
    kinds: dict[str, str] = {}
    for r in rows:
        tag = r["tag"] or LEGACY
        by_tag.setdefault(tag, []).append(r)
        kinds[tag] = r["tag_kind"] or ("legacy" if tag == LEGACY else "manual")

    tagged = {t: best_per_key(rs, a2m) for t, rs in by_tag.items()}
    # the most recent measurement of each combination, and the tag it came from
    combo = lambda key: key[:4]  # noqa: E731 - hardware, engine, model, workload category
    latest: dict[tuple, tuple] = {}
    for t, best in tagged.items():
        for key, entry in best.items():
            measured = entry[1]["started_at"]
            if combo(key) not in latest or measured > latest[combo(key)][0]:
                latest[combo(key)] = (measured, t)
    combos = {combo(k) for best in tagged.values() for k in best}

    info = []
    for t, rs in by_tag.items():
        info.append({"id": t, "kind": kinds[t], "date": str(max(r["started_at"] for r in rs))[:16],
                     "commit": next((r["pie_commit"][:9] for r in rs if r["engine"] == "pie" and r["pie_commit"]), "")})
    info.sort(key=lambda x: x["date"], reverse=True)
    info.sort(key=lambda x: x["kind"] == "legacy")  # newest first; legacy last

    snaps: dict[str, list[dict]] = {}
    for t in (x["id"] for x in info):
        out = []
        for c in combos:
            here = [entry for k, entry in tagged[t].items() if combo(k) == c]
            if here:
                out += [{**as_row(r, cat, model, release), "stale": None} for _, r, cat, model, release in (e for e in here)]
                continue
            src = latest[c][1]
            for k, (_, r, cat, model, release) in tagged[src].items():
                if combo(k) == c:
                    out.append({**as_row(r, cat, model, release), "stale": {"tag": src, "measured": str(r["started_at"])[:16]}})
        snaps[t] = out
    return info, snaps


def quality(store, a2m: dict[str, str]) -> list[dict]:
    out = []
    for q in store.quality():
        out.append({"model": a2m.get(q["model"], q["model"]), "engine": q["engine"], "artifact": q["artifact"],
                    "task": q["task"], "score": round(q["score"], 3), "ci_low": round(q["ci95"][0], 3),
                    "ci_high": round(q["ci95"][1], 3), "n": q["n"], "version": q.get("version"),
                    "minutes": q.get("minutes"), "date": q["date"][:10]})
    return out


def main() -> None:
    store = Store(sys.argv[1] if len(sys.argv) > 1 else None)
    a2m, models = artifact_to_model()
    tags, snaps = snapshots(store, a2m)
    allowed = fleet()
    db = {"tags": tags, "snapshots": snaps, "hardware": [h for h in hardware() if h["id"] in allowed],
          "engines": engines(), "models": models, "workloads": workloads(), "quality": quality(store, a2m)}
    (WEB / "data").mkdir(parents=True, exist_ok=True)
    (WEB / "data" / "db.js").write_text("const DB = " + json.dumps(db, indent=2, default=str) + ";\n")
    print({k: len(v) for k, v in db.items()}, {t["id"]: len(snaps[t["id"]]) for t in tags})


if __name__ == "__main__":
    main()
