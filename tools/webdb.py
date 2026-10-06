"""Build web/data/db.js for the new site from the measured store, with DuckDB.

    .venv/bin/python tools/webdb.py

The store holds one parquet row per run across every tier and platform. This keeps
the newest passing run per platform, engine, model, release and workload-category,
collapsing the many measured workloads into two the site shows: a single request and
a throughput (concurrency) run.
"""
from __future__ import annotations

import glob
import json
import re
from pathlib import Path

import duckdb
import yaml

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"

# Each site workload maps to measured workloads, best first.
SINGLE = ["ss-512-256", "ob-512-200", "ss-128-64", "ob-short-100", "ob-story-200"]
THROUGHPUT = ["c32", "c64", "c256", "c8", "c4"]
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


def results(a2m: dict[str, str]) -> list[dict]:
    cols = (["platform", "engine", "engine_version", "artifact", "scheme", "workload", "status", "pie_commit", "started_at"]
            + METRICS)
    files = glob.glob(str(ROOT / "store/records/**/*.parquet"), recursive=True)
    rel = duckdb.sql(f"SELECT {', '.join(cols)} FROM read_parquet({files!r}, union_by_name=true) "
                     "WHERE status IN ('pass','noisy')").fetchall()
    names = [c for c in cols]
    best: dict[tuple, tuple] = {}
    for row in rel:
        r = dict(zip(names, row))
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

    out = []
    for _, r, cat, model, release in best.values():
        out.append({
            "hardware": r["platform"], "engine": r["engine"],
            "release": release or "?", "group": "main" if r["engine"] == "pie" else (release or "?"),
            "model": model, "scheme": r["scheme"], "workload": cat,
            **{m: (round(r[m], 2) if isinstance(r[m], (int, float)) else None) for m in METRICS},
            "accuracy": None,
            "commit": (r["pie_commit"] or "")[:9] if r["engine"] == "pie" else "",
            "measured": str(r["started_at"])[:16],
        })
    return out


def quality(a2m: dict[str, str]) -> list[dict]:
    out = []
    for path in sorted((ROOT / "store/quality").glob("*.json")):
        q = json.loads(path.read_text())
        out.append({"model": a2m.get(q["model"], q["model"]), "engine": q["engine"], "artifact": q["artifact"],
                    "task": q["task"], "score": round(q["score"], 3), "ci_low": round(q["ci95"][0], 3),
                    "ci_high": round(q["ci95"][1], 3), "n": q["n"], "version": q.get("version"),
                    "minutes": q.get("minutes"), "date": q["date"][:10]})
    return out


def main() -> None:
    a2m, models = artifact_to_model()
    db = {"releases": [], "hardware": hardware(), "engines": engines(), "models": models,
          "workloads": workloads(), "results": results(a2m), "quality": quality(a2m)}
    (WEB / "data").mkdir(parents=True, exist_ok=True)
    (WEB / "data" / "db.js").write_text("const DB = " + json.dumps(db, indent=2, default=str) + ";\n")
    print({k: len(v) for k, v in db.items()})


if __name__ == "__main__":
    main()
