from __future__ import annotations

import functools
import json
import os
import re
import sys
import urllib.request
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml

from pie_bench.paths import CONFIG, MATRIX
from pie_bench.plan.suites import all_models, suites
from pie_bench.quality.parity import rows as parity_rows
from server import split

THROUGHPUT = ["c32", "c64", "c256", "c8", "c4", "c16", "c128", "c512", "c1024"]
RAW = ["raw-512-256"]
SPEC = ["spec-512-256"]
PREFILL_BATCH = ["pf256-512", "pf4-512", "pf8-512", "pf16-512", "pf32-512", "pf64-512", "pf128-512", "pf512-512", "pf1024-512"]
CATEGORIES = (("throughput", THROUGHPUT, "Batching"), ("raw", RAW, "Raw"), ("spec", SPEC, "Speculative"), ("prefill_batch", PREFILL_BATCH, "Batched Prefill"))
SITE_TZ = ZoneInfo("America/Los_Angeles")

WL_PRIORITY = {wl: (cat, i) for cat, ids, _ in CATEGORIES for i, wl in enumerate(ids)}

ENGINE_META = {
    "pie":      ("Pie", "Apache-2.0", "pie-project/pie"),
    "vllm":     ("vLLM", "Apache-2.0", "vllm-project/vllm"),
    "sglang":   ("SGLang", "Apache-2.0", "sgl-project/sglang"),
    "trtllm":   ("TensorRT-LLM", "Apache-2.0", "NVIDIA/TensorRT-LLM"),
    "llamacpp": ("llama.cpp", "MIT", "ggml-org/llama.cpp"),
    "mlxlm":    ("MLX", "MIT", "ml-explore/mlx-lm"),
    "vllm-metal": ("vLLM Metal", "Apache-2.0", "vllm-project/vllm-metal"),
    "webllm":   ("WebLLM", "Apache-2.0", "mlc-ai/web-llm"),
    "llamacpp-webgpu": ("llama.cpp", "MIT", "ggml-org/llama.cpp"),
    "splash":   ("Splash", None, "incoai/splash"),
    "litert":   ("LiteRT-LM", "Apache-2.0", "google-ai-edge/LiteRT-LM"),
    "mlc":      ("MLC LLM", "Apache-2.0", "mlc-ai/mlc-llm"),
    "mlx-swift": ("MLX Swift", "MIT", "ml-explore/mlx-swift-lm"),
}
ENGINE_COLOR = {"trtllm": "#a2845e", "litert": "#34a853", "mlc": "#5856d6", "mlx-swift": "#ff9500", "webllm": "#5e5ce6", "llamacpp-webgpu": "#8e8e93"}
METRICS = ["decode_tok_s", "prefill_tok_s", "output_tok_s", "ttft_ms_p50", "ttft_ms_p99",
           "itl_ms_p50", "itl_ms_p99", "latency_ms_p50", "latency_ms_p99", "resident_gib", "load_s"]


MOE_FAMILIES = {"gpt_oss", "qwen4_exp"}
BYTES_PER_WEIGHT = {"bf16": 2, "fp8": 1, "mxfp8": 1, "mxfp4": 0.53, "int4": 0.5625, "nvfp4": 0.5625}
NODE_GB = {"GPU": 8 * 288, "AMD": 8 * 192, "TPU": 4 * 95}


CONTRIBUTED: dict[str, dict] = {}


def load(name: str) -> dict:
    data = yaml.safe_load((MATRIX / f"{name}.yaml").read_text())
    if name == "platforms":
        known = {p["id"] for p in data["platforms"]}
        data["platforms"] += [p for pid, p in CONTRIBUTED.items() if pid not in known]
    return data


def contributed_platform(spec: dict) -> dict:
    return {**spec, "tiers": ["community"], "contributed": True}


def model_name(base: str) -> str:
    drop = {"4bit", "bf16", "gguf", "mlx", "mxfp4", "q4", "q4km", "mtp", "instruct", "it", "base", "8k", "mini5", "mini8",
            "litert", "lm", "mlc", "q4f16_1", "q4f32_1"}
    tail = re.sub(r"^[a-z-]+\.", "", base.split("/")[-1])
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
        for size in ("params_b", "active_b"):
            if a.get(size) is not None:
                row[size + "_stated"] = float(a[size])
        for k in ("layers", "hidden_size", "experts", "top_k", "context"):
            if a.get(k) is not None and a.get("kind", "full") == "full":
                row[k] = a[k]
        if a.get("scheme"):
            row["schemes"].add(a["scheme"])
    for row in by_model.values():
        name = row["name"]
        sizes = re.findall(r"(\d+(?:\.\d+)?)b", name, re.I)
        active = re.search(r"a(\d+(?:\.\d+)?)b", name, re.I)
        row["params_b"] = row.pop("params_b_stated", None) or (float(sizes[0]) if sizes else None)
        row["active_b"] = row.pop("active_b_stated", None) or (float(active.group(1)) if active else row["params_b"])
        row["architecture"] = "MoE" if active or row["active_b"] != row["params_b"] or "moe" in (row["family"] or "") or row["family"] in MOE_FAMILIES else "dense"
        row["ssd_streaming"] = "Without" if row["architecture"] == "MoE" else "n/a"
        row["schemes"] = ", ".join(sorted(row["schemes"]))
        row["draft"] = "true" if row.get("draft") else "false"
        row["size_gib"] = round(row["params_b"] * 1e9 * 4.5 / 8 / 2**30, 1) if row["params_b"] else None
        row["needs_gib"] = round(row["size_gib"] * 1.25, 1) if row["size_gib"] else None
        row.setdefault("context", None)
        row["license"] = None
    for c in load("models").get("catalog") or []:
        mid = model_name(c["base_model"]).lower() if c.get("base_model") else c["name"].lower()
        row = by_model.get(mid)
        if row is None:
            row = by_model[mid] = {"id": mid, "name": c["name"], "family": c.get("family"), "base_model": c.get("base_model"),
                                   "schemes": c.get("precision") or "", "artifacts": 0, "draft": "true" if c.get("mtp") else "false",
                                   "catalog_only": True}
        row["catalog"] = True
        row["name"] = c["name"]
        if c.get("mtp"):
            row["draft"] = "true"
        for key in ("params_b", "active_b"):
            if c.get(key) is not None:
                row[key] = float(c[key])
        for key in ("layers", "hidden_size", "experts", "top_k", "context", "license"):
            if c.get(key) is not None and row.get(key) is None:
                row[key] = c[key]
        row["architecture"] = "MoE" if (row.get("active_b") or 0) < (row.get("params_b") or 0) else row.get("architecture") or "dense"
        row["ssd_streaming"] = "Without" if row["architecture"] == "MoE" else "n/a"
        if row.get("params_b"):
            row["size_gib"] = round(row["params_b"] * 1e9 * 4.5 / 8 / 2**30, 1)
            row["needs_gib"] = round(row["size_gib"] * 1.25, 1)
        if row.get("params_b"):
            need = row["params_b"] * BYTES_PER_WEIGHT.get(str(c.get("precision") or "bf16"), 2) * 1.25
            row["fits"] = ", ".join(t for t, gb in NODE_GB.items() if need <= gb)
    for mid, name in (load("models").get("names") or {}).items():
        if mid in by_model:
            by_model[mid]["name"] = name
    return mapping, list(by_model.values())


def cores_by_platform(store) -> dict[str, dict]:
    rows = store.table().select(["platform", "started_at", "hardware_fingerprint_json"]).to_pylist()
    out: dict[str, dict] = {}
    for r in sorted((r for r in rows if r["started_at"] is not None), key=lambda r: r["started_at"]):
        fp = json.loads(r["hardware_fingerprint_json"] or "{}")
        cpu = re.match(r"\s*(\d+)", str(fp.get("cores") or ""))
        gpu = re.match(r"\s*(\d+)", str(fp.get("gpu_cores") or ""))
        if cpu or gpu:
            out[r["platform"]] = {"cpu_cores": int(cpu.group(1)) if cpu else None, "gpu_cores": int(gpu.group(1)) if gpu else None}
    return out


RESOURCE = {"mac": "Pie self-hosted", "tpu": "Google Cloud", "wafer": "Cerebras"}


def hardware(cores: dict[str, dict] | None = None) -> list[dict]:
    cores = cores or {}
    catalog = load("hardware")["hardware"]
    by_id = {c["id"]: c for c in catalog}
    by_runpod = {c["runpod_gpu_type"]: c for c in catalog if c.get("runpod_gpu_type")}

    def row(c: dict, **over) -> dict:
        resource = RESOURCE.get(c["class"], "RunPod cloud" if c.get("runpod_gpu_type") else "")
        return {
            "id": c["id"], "resource": resource, "name": c.get("short") or c["name"], "full_name": c["name"],
            "class": c["class"], "location": "local" if c["class"] == "mac" else "cloud",
            "vendor": c["vendor"], "backend": c.get("backend"), "arch": c.get("arch"), "count": 1,
            "memory_gib": c.get("memory_gib") or max(c.get("memory_options_gb") or [0]) or None,
            "memory_type": c.get("memory_type"), "bandwidth_gbs": c.get("bandwidth_gbs"),
            "cpu_cores": c.get("cpu_cores"), "gpu_cores": c.get("gpu_cores"), "tflops_fp16": c.get("tflops_fp16"),
            "tflops_fp8": c.get("tflops_fp8"), "tflops_mxfp8": c.get("tflops_mxfp8"),
            "ane_tflops_fp16": c.get("ane_tflops_fp16"),
            "interconnect": None, "power_w": c.get("power_w"), "year": str(c["year"]) if c.get("year") else None,
            "runs": None, "price_usd": None, "price_hr": None, **over,
        }

    rows, used = [], set()
    for p in load("platforms")["platforms"]:
        if not p.get("tiers"):
            continue
        mac = p.get("os") == "macos"
        c = by_id.get(p.get("catalog")) or by_runpod.get(p.get("runpod_gpu_type")) or {}
        used.add(c.get("id"))
        base = row(c) if c else {}
        rows.append({
            **base,
            "id": p["id"],
            "resource": "Community" if p.get("contributed") else "Pie self-hosted" if mac else ("Google Cloud" if p.get("backend") == "xla" else "RunPod cloud"),
            "name": (p["accelerator"] if mac else c.get("short") or p["accelerator"].replace("NVIDIA ", ""))
                    + (f" ×{p['count']}" if p.get("count", 1) > 1 else ""),
            "class": "mac" if mac else ("tpu" if p.get("backend") == "xla" else "web" if p.get("backend") == "webgpu" else "gpu"), "location": "local" if mac else "cloud",
            "vendor": c.get("vendor") or ("Apple" if mac else "NVIDIA"),
            "backend": p.get("backend"), "arch": p.get("arch") or c.get("arch"),
            "count": p.get("count", 1), "memory_gib": p.get("memory_gib"),
            "bandwidth_gbs": p.get("bandwidth_gbs") or c.get("bandwidth_gbs"),
            "cpu_cores": cores.get(p["id"], {}).get("cpu_cores") or c.get("cpu_cores"),
            "gpu_cores": cores.get(p["id"], {}).get("gpu_cores") or c.get("gpu_cores"),
            "interconnect": p.get("interconnect"),
            "runs": ", ".join(t.capitalize() for t in p["tiers"]),
        })
    rows += [row(c) for c in catalog if c["id"] not in used]
    for r in rows:
        if r["class"] == "web" and r.get("name"):
            r["name"] += " Chrome"
            r["vendor"] = f"Chrome ({r.get('vendor') or 'GPU'})"
            r["tflops_fp8"] = r["tflops_mxfp8"] = None
    return rows


def phone_hardware(store) -> list[dict]:
    phones = {p["id"]: p for p in load("phones")["phones"]}
    seen: dict[str, dict] = {}
    rows = store.table().select(["platform", "started_at", "hardware_fingerprint_json", "tag"]).to_pylist()
    for r in sorted((r for r in rows if r["started_at"] is not None), key=lambda r: r["started_at"]):
        pid = r["platform"] or ""
        if not (pid in phones or pid.startswith(("android-", "ios-"))) or phones.get(pid, {}).get("test") or (r["tag"] or "").startswith("test-"):
            continue
        seen[pid] = json.loads(r["hardware_fingerprint_json"] or "{}")
    out = []
    for pid, fp in seen.items():
        p = phones.get(pid, {})
        name = p.get("name") or " ".join(x for x in (fp.get("manufacturer"), fp.get("model")) if x) or pid
        chip = p.get("accelerator") or fp.get("soc")
        out.append({
            "id": pid, "resource": "Pie phone app", "name": name, "full_name": f"{name} ({chip})" if chip else name,
            "class": "android", "location": "local", "vendor": p.get("vendor") or fp.get("manufacturer") or None,
            "backend": p.get("backend") or ("metal" if fp.get("os") == "ios" else "vulkan"), "arch": p.get("arch") or fp.get("soc"),
            "count": 1, "memory_gib": p.get("memory_gib") or fp.get("ram_gib"), "memory_type": None, "bandwidth_gbs": p.get("bandwidth_gbs"),
            "cpu_cores": fp.get("cpu_cores"), "gpu_cores": None, "tflops_fp16": p.get("tflops_fp16"), "interconnect": "uma", "power_w": None,
            "year": str(p["year"]) if p.get("year") else None, "runs": "Phone app", "price_usd": None, "price_hr": None,
        })
    return out


DECODING = {"pie": (True, True), "llamacpp": (True, True), "mlxlm": (True, True), "splash": (False, True),
            "vllm": (True, True), "sglang": (True, True), "trtllm": (True, False), "vllm-metal": (True, False),
            "litert": (True, False), "mlc": (True, False), "mlx-swift": (True, False),
            "webllm": (True, False), "llamacpp-webgpu": (True, False)}


def engines() -> list[dict]:
    rows = []
    for e in load("engines")["engines"]:
        name, lic, repo = ENGINE_META.get(e["id"], (e["id"], None, None))
        rows.append({"id": e["id"], "name": name, "version": e.get("pin") or "main", "license": lic, "repo": repo,
                     "os": ", ".join(e.get("os", [])), "formats": ", ".join(e.get("formats", [])),
                     "backends": ", ".join(e.get("backends", [])),
                     **({"color": ENGINE_COLOR[e["id"]]} if e["id"] in ENGINE_COLOR else {}),
                     **dict(zip(("raw", "speculation"), ("Yes" if ok else "No" for ok in DECODING.get(e["id"], (True, False)))))})
    return rows


def install_sizes() -> list[dict]:
    data = load("install")
    known = {e["id"] for e in load("engines")["engines"]}
    rows = []
    for platform, entries in data["install"].items():
        for e in entries:
            if e["engine"] not in known:
                raise ValueError(f"matrix/install.yaml: {e['engine']} is not an engine in matrix/engines.yaml")
            rows.append({"platform": platform, "engine": e["engine"], "version": str(e["version"]), "bytes": int(e["bytes"]),
                         "method": " ".join(e["method"].split()), "source": " ".join(e["source"].split()),
                         "parts": [[str(label), int(n)] for label, n in e.get("parts") or []],
                         "measured": str(e.get("measured") or data["measured"])})
    return rows


def workloads() -> list[dict]:
    params = {w["id"]: w.get("params", {}) for w in load("workloads")["workloads"]}
    out = []
    for cat, ids, label in CATEGORIES:
        src = next((i for i in ids if i in params), None)
        p = params.get(src, {})
        shapes = {i: {"concurrency": params[i].get("concurrency") or 1, "prompt_tokens": params[i].get("prefill"),
                      "output_tokens": params[i].get("decode")} for i in ids if i in params}
        out.append({"id": cat, "label": label, "concurrency": p.get("concurrency") or (32 if cat == "throughput" else 1),
                    "prompt_tokens": p.get("prefill"), "output_tokens": p.get("decode"), "benchmark": ", ".join(ids),
                    "shapes": shapes})
    return out


QUALITY_TASKS = [
    ("gsm8k", "Grade-school math word problems, worked step by step", "openai/gsm8k (test)", "final number matches"),
    ("ifeval", "Following explicit instructions (length, format, keywords)", "google/IFEval", "every instruction met"),
    ("mmlu", "Multiple-choice knowledge across 57 subjects", "cais/mmlu (test)", "chosen letter matches"),
    ("arc", "Grade-school science reasoning, multiple choice", "allenai/ai2_arc (ARC-Challenge test)", "chosen letter matches"),
    ("math500", "Competition math, final answer in boxed form", "HuggingFaceH4/MATH-500", "final answer equivalent"),
]


def suite_model_ids(config: dict, a2m: dict[str, str]) -> dict[str, list[str]]:
    arts = {a["id"]: a for a in load("models")["artifacts"]}
    out = {}
    for name, arms in suites(config).items():
        ids = [a for aid in arms for a in (aid, arts.get(aid, {}).get("baseline_of")) if a in a2m]
        out[name] = sorted({a2m[a] for a in ids})
    return out


def quality_arms(config: dict) -> list[tuple[str, str]]:
    arts = {a["id"]: a for a in load("models")["artifacts"]}
    out: list[tuple[str, str]] = []
    for aid in all_models(config):
        eng = next((e for e in ("llamacpp", "mlxlm", "splash") if aid.endswith(f"-{e}") or f"-{e}-" in aid), None)
        if eng:
            out.append((eng, aid))
        pie = arts.get(aid, {}).get("baseline_of")
        if pie and ("pie", pie) not in out:
            out.append(("pie", pie))
    return out


def mismatched_arms() -> dict[str, str]:
    arts = {a["id"]: a for a in load("models")["artifacts"]}
    out = {}
    for a in arts.values():
        pie = arts.get(a.get("baseline_of") or "")
        if pie and a.get("scheme") != pie.get("scheme"):
            out[a["id"]] = f"Runs {a.get('scheme')} weights where pie runs {pie.get('scheme')}: not compared"
    return out


def quality_tasks() -> list[dict]:
    from pie_bench.quality.dist_run import ANSWER_TOKENS, PARITY_TASKS
    from pie_bench.quality.tasks import TASKS

    scored = [{"id": t, "task": t, "description": d, "source": src, "scoring": sc, "max_tokens": TASKS[t][2]}
              for t, d, src, sc in QUALITY_TASKS if t in TASKS]
    parity = {"id": "parity", "task": "parity",
              "description": "Pie matches vLLM on the same weights",
              "source": ", ".join(PARITY_TASKS),
              "scoring": "mean KL, top-1 agreement",
              "max_tokens": ANSWER_TOKENS}
    return scored + [parity]


def local(ts) -> str:
    return ts.astimezone(SITE_TZ).strftime("%Y-%m-%d %H:%M") if ts is not None else ""


def _cut(a: dict) -> tuple:
    m = a.get("miniature") if a.get("kind") == "miniature" else None
    return (str(m["layers"]), m.get("experts")) if m else ("full",)


CUT = {a["id"]: _cut(a) for a in load("models")["artifacts"]}


def _miniature_labels() -> dict[str, str]:
    arts = load("models")["artifacts"]
    a2m = artifact_to_model()[0]
    full = {a2m[a["id"]]: a["layers"] for a in arts if a.get("layers") and a.get("kind", "full") == "full"}
    macs = {p["id"] for p in load("platforms")["platforms"] if p.get("os") == "macos"}
    experts = {(a2m[a["id"]], CUT[a["id"]]) for a in arts if a.get("kind") == "miniature" and a.get("miniature")
               and a.get("platforms") and set(a["platforms"]) <= macs and a["miniature"].get("experts")}
    out = {}
    for a in arts:
        if a.get("kind") != "miniature" or not a.get("miniature"):
            continue
        model = a2m[a["id"]]
        kept = sum(int(x.split("-")[-1]) - int(x.split("-")[0]) + 1 for x in str(a["miniature"]["layers"]).split(","))
        out[a["id"]] = f"{kept} of {full[model]} layers" if model in full else f"{kept} layers"
        if (model, CUT[a["id"]]) in experts:
            out[a["id"]] += f", {a['miniature']['experts']} experts"
    return out


MINIATURE = _miniature_labels()


def _miniature_shapes() -> dict[str, dict]:
    arts = load("models")["artifacts"]
    full = {a["base_model"]: a for a in arts if a.get("kind", "full") == "full" and a.get("layers") and a.get("vocab")}
    out = {}
    for a in arts:
        f = full.get(a.get("base_model"))
        if a.get("kind") != "miniature" or not a.get("miniature") or not f or not f.get("params_b"):
            continue
        r = a["miniature"]
        kept = sum(int(x.split("-")[-1]) - int(x.split("-")[0]) + 1 for x in str(r["layers"]).split(","))
        share = kept / f["layers"]
        emb = 2 * f["vocab"] * f["hidden_size"] / 1e9
        body, active_body = f["params_b"] - emb, (f.get("active_b") or f["params_b"]) - emb
        n, top = f.get("experts"), f.get("top_k") or 0
        idle = min(1.0, max(0, (r.get("experts") or n) - top) / (n - top)) if n and n > top else 1.0
        out[a["id"]] = {"mini_active_b": round(emb + active_body * share, 3),
                        "mini_params_b": round(emb + (active_body + (body - active_body) * idle) * share, 3),
                        "mini_emb_b": round(emb, 3), "mini_layers": kept,
                        "mini_k": round(min(1.0, f["top_k"] / (r.get("experts") or f["experts"])), 3) if f.get("top_k") and f.get("experts") else 1.0}
    return out


MINI_SHAPE = _miniature_shapes()


def miniature_fields(artifact: str) -> dict:
    return {"miniature": MINIATURE.get(artifact, ""), **MINI_SHAPE.get(artifact, {})}


_FULL_BASES = {a["base_model"] for a in load("models")["artifacts"] if a.get("kind", "full") == "full" and (a.get("expected_gib") or 0) > 100}
SHOWN_MINIATURES = {a["id"] for a in load("models")["artifacts"] if a["id"] in MINIATURE and (a["base_model"] in _FULL_BASES or "smoke" not in a.get("tiers", []))}


def _cut_size(c: tuple) -> tuple:
    if c == ("full",):
        return (1, 0, 0)
    kept = sum(int(x.split("-")[-1]) - int(x.split("-")[0]) + 1 for x in c[0].split(","))
    return (0, kept, c[1] or 0)


def share_cut(rows: list[dict], a2m: dict[str, str]) -> list[dict]:
    arts = {a["id"]: a for a in load("models")["artifacts"]}
    macs = {p["id"] for p in load("platforms")["platforms"] if p.get("os") == "macos"}

    def counted(r):
        art = arts.get(r["artifact"], {})
        if art.get("kind") == "miniature" and r["artifact"] not in SHOWN_MINIATURES:
            return False
        return not (r["platform"] in macs and r["engine"] == "pie" and art and art.get("source_format") != "mlx")

    groups: dict[tuple, dict[str, list[dict]]] = {}
    for r in rows:
        cp = WL_PRIORITY.get(r["workload"])
        if cp and counted(r):
            groups.setdefault((r["platform"], a2m.get(r["artifact"], r["artifact"]), cp[0]), {}).setdefault(r["engine"], []).append(r)
    target = {}
    for g, by in groups.items():
        cuts = {CUT.get(r["artifact"], ("full",)) for rs in by.values() for r in rs}
        if len(cuts) < 2:
            continue
        newest = [CUT.get(max(rs, key=lambda r: r["started_at"])["artifact"], ("full",)) for rs in by.values()]
        ran = [{CUT.get(r["artifact"], ("full",)) for r in rs} for rs in by.values()]
        target[g] = max(cuts, key=lambda c: (newest.count(c), sum(c in s for s in ran), _cut_size(c)))
    out = []
    for r in rows:
        cp = WL_PRIORITY.get(r["workload"])
        t = target.get((r["platform"], a2m.get(r["artifact"], r["artifact"]), cp[0])) if cp and counted(r) else None
        if t and CUT.get(r["artifact"], ("full",)) != t:
            continue
        out.append(r)
    return out


def share_workload(rows: list[dict], a2m: dict[str, str]) -> list[dict]:
    have: dict[tuple, dict[str, set]] = {}
    for r in rows:
        cp = WL_PRIORITY.get(r["workload"])
        if cp:
            g = (r["platform"], a2m.get(r["artifact"], r["artifact"]), cp[0])
            have.setdefault(g, {}).setdefault(r["workload"], set()).add(r["engine"])
    target = {g: max(ws, key=lambda w: (len(ws[w]), -WL_PRIORITY[w][1])) for g, ws in have.items() if len(ws) > 1}
    out = []
    for r in rows:
        cp = WL_PRIORITY.get(r["workload"])
        g = cp and (r["platform"], a2m.get(r["artifact"], r["artifact"]), cp[0])
        t = target.get(g) if g else None
        if t and r["workload"] != t and r["engine"] in have[g][t]:
            continue
        out.append(r)
    return out


def pick(rows: list[dict], a2m: dict[str, str], skipped: dict | None = None) -> dict[tuple, tuple]:
    arts = {a["id"]: a for a in load("models")["artifacts"]}
    macs = {p["id"] for p in load("platforms")["platforms"] if p.get("os") == "macos"}
    best: dict[tuple, tuple] = {}
    cands: dict[tuple, list[tuple]] = {}
    for r in rows:
        cat_pri = WL_PRIORITY.get(r["workload"])
        if not cat_pri:
            continue
        art = arts.get(r["artifact"], {})
        mini = art.get("kind") == "miniature"
        if mini and r["artifact"] not in SHOWN_MINIATURES:
            if skipped is not None:
                skipped[(r.get("tag"), r["platform"], r["engine"], r["artifact"])] = "a CI fixture, never a model's number"
            continue
        if r["engine"] == "splash" and WL_PRIORITY[r["workload"]][0] in ("raw", "throughput"):
            continue
        if r["platform"] in macs and r["engine"] == "pie" and art and art.get("source_format") != "mlx":
            continue
        cat, pri = cat_pri
        model = a2m.get(r["artifact"], r["artifact"])
        key = (r["platform"], r["engine"], model, cat)
        shared = r["platform"] in macs and art.get("source_format") == "mlx"
        released = r["platform"] in macs or art.get("source_format") != "mlx"
        rank = (released, r["started_at"], not mini, -pri, shared)
        cands.setdefault(key, []).append((rank, r))
        if key not in best or rank > best[key][0]:
            best[key] = (rank, r)
    groups: dict[tuple, list[tuple]] = {}
    for key in best:
        groups.setdefault((key[0], key[2], key[3]), []).append(key)
    for keys in groups.values():
        if len({best[k][1]["workload"] for k in keys}) < 2:
            continue
        have: dict[str, int] = {}
        for k in keys:
            for w in {r["workload"] for _, r in cands[k]}:
                have[w] = have.get(w, 0) + 1
        target = max(have, key=lambda w: (have[w], -WL_PRIORITY[w][1]))
        for k in keys:
            same = [c for c in cands[k] if c[1]["workload"] == target]
            if same:
                best[k] = max(same, key=lambda c: c[0])
    return best


def as_row(r: dict, key: tuple, tag: str) -> dict:
    hw, engine, model, cat = key
    version = (r["pie_commit"] or "")[:9] if engine == "pie" else r["engine_version"]
    row = {
        "hardware": hw, "engine": engine,
        "release": tag, "group": tag, "version": version or "",
        "model": model, "scheme": r["scheme"], "workload": cat,
        **{m: (round(r[m], 2) if isinstance(r[m], (int, float)) and not (m == "prefill_tok_s" and cat == "throughput") else None) for m in METRICS},
        "accuracy": None,
        "commit": (r["pie_commit"] or "")[:9] if engine == "pie" else "",
        "measured": local(r["started_at"]),
        "benchmark": r["workload"],
        "prompt_per_request": prompt_per_request(r),
        "status": r["status"], "note": draft_note(r, engine),
        **miniature_fields(r["artifact"]),
    }
    return withhold_seat_ttft(row, r, hw, engine, cat)


SEAT_FIX, SEAT_FIX_AT = "434fc3a158dd788ac7b1f62307c6d2eda0c69642", datetime(2026, 11, 10, 19, 54, 25, tzinfo=ZoneInfo("UTC"))
SOLO_FIX, SOLO_FIX_AT = "d6163483c48bfc00ab7e82236ab5f7012ba2c6e1", datetime(2026, 11, 10, 21, 12, 19, tzinfo=ZoneInfo("UTC"))
SEAT_ENGINES = {"pie", "trtllm", "llamacpp", "mlxlm", "vllm-metal", "splash"}
BACKEND = {p["id"]: p.get("backend") for p in load("platforms")["platforms"]}
QUEUES = {w["id"] for w in load("workloads")["workloads"]
          if (w.get("params") or {}).get("num_requests", 0) > ((w.get("params") or {}).get("concurrency") or 0)}
TIMINGS = ("ttft_ms_p50", "ttft_ms_p99", "latency_ms_p50", "latency_ms_p99")


@functools.cache
def harness_has(fix: str, sha: str) -> bool | None:
    try:
        return {"ahead": True, "identical": True, "behind": False, "diverged": False}.get(_github(f"repos/pie-project/benchmarks/compare/{fix}...{sha}").get("status"))
    except Exception:
        return None


def timed_with(fix: str, at: datetime, r: dict) -> bool:
    started = r["started_at"] if r["started_at"].tzinfo else r["started_at"].replace(tzinfo=ZoneInfo("UTC"))
    if started < at:
        return False
    sha = r.get("harness_commit") or ""
    return harness_has(fix, sha) is not False if re.fullmatch(r"[0-9a-f]{7,40}", sha) else True


def withhold_seat_ttft(row: dict, r: dict, hw: str, engine: str, cat: str) -> dict:
    seat = engine in SEAT_ENGINES or (engine == "sglang" and BACKEND.get(hw) == "xla")
    if not seat or BACKEND.get(hw) == "webgpu":
        return row
    if cat in ("throughput", "prefill_batch") and r["workload"] in QUEUES and not timed_with(SEAT_FIX, SEAT_FIX_AT, r):
        note = "TTFT and latency withheld: this run started each request's clock when it took a seat, not when it was sent, so they leave out the queue (rerun pending)"
    elif cat in ("raw", "spec") and engine != "pie" and timed_with(SEAT_FIX, SEAT_FIX_AT, r) and not timed_with(SOLO_FIX, SOLO_FIX_AT, r):
        note = "Prefill, TTFT and latency withheld: this run counted each request's wait on the one before it (rerun pending)"
        row["prefill_tok_s"] = None
    else:
        return row
    for m in TIMINGS:
        row[m] = None
    row["note"] = "; ".join(n for n in (row["note"], note) if n)
    return row


def prompt_per_request(r: dict) -> float | None:
    done = int(r.get("requests") or 0) - int(r.get("failed") or 0)
    return round(r["prompt_tokens"] / done, 1) if r.get("prompt_tokens") and done > 0 else None


def draft_note(r: dict, engine: str) -> str:
    try:
        counters = json.loads(r.get("counters_json") or "{}")
    except ValueError:
        return ""
    return "Speculative: drafts with a small same-family model" if engine != "pie" and counters.get("speculative") else ""


def empty_row(key: tuple, tag: str, status: str, note: str) -> dict:
    hw, engine, model, cat = key
    return {"hardware": hw, "engine": engine, "release": tag, "group": tag, "version": "", "model": model, "scheme": None,
            "workload": cat, **{m: None for m in METRICS}, "accuracy": None, "commit": "", "measured": "",
            "status": status, "note": note, "stale": None}


def attempts_by_tag(store, a2m, hardware_ids, engine_ids) -> dict[str, dict[tuple, dict]]:
    cols = (["platform", "engine", "artifact", "workload", "status", "error_class", "error_message", "invalid_reason", "started_at", "tag"]
            + ["decode_tok_s", "prefill_tok_s", "output_tok_s"])
    rows = store.table().select(cols).to_pylist()
    crashed: dict[tuple, dict] = {}
    for r in sorted((r for r in rows if r["workload"] == "control-aa" and r["status"] == "fail"), key=lambda r: r["started_at"]):
        crashed[(r["platform"], r["engine"], r["artifact"], r["tag"])] = r
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
        if not t or t.startswith("test-"):
            continue
        if key not in out.setdefault(t, {}) or r["started_at"] > out[t][key]["started_at"]:
            out[t][key] = r
    return out


def first_line(r: dict) -> str:
    lines = (r.get("error_message") or r.get("invalid_reason") or r.get("error_class") or "").strip().splitlines()
    return lines[0].removeprefix("RuntimeError: ").rstrip(": ") if lines else ""


def attempt_note(r: dict) -> str:
    msg = (r.get("error_message") or r.get("invalid_reason") or r.get("error_class") or "").strip().splitlines()
    msg = msg[0] if msg else ""
    if r["status"] == "not_run" and "hard deadline" in msg:
        return "The job ran out of time before this setup started"
    return (msg[:1].upper() + msg[1:])[:160] if msg else ("Failed" if r["status"] == "fail" else "Not run")


@functools.cache
def matrix_cells():
    import hashlib
    import pickle

    from pie_bench.plan.matrix import Matrix

    m = Matrix.load(MATRIX)
    digest = hashlib.sha256()
    for f in sorted(MATRIX.rglob("*")):
        if f.is_file():
            digest.update(str(f.relative_to(MATRIX)).encode() + f.read_bytes())
    cache = Path(os.environ.get("PIE_BENCH_CACHE") or "/tmp/pie-bench") / f"cells-{digest.hexdigest()[:16]}.pkl"
    try:
        return m, pickle.loads(cache.read_bytes())
    except Exception:
        pass
    cells = m.expand()
    try:
        cache.parent.mkdir(parents=True, exist_ok=True)
        for old in cache.parent.glob("cells-*.pkl"):
            old.unlink(missing_ok=True)
        cache.write_bytes(pickle.dumps(cells, protocol=pickle.HIGHEST_PROTOCOL))
    except Exception:
        pass
    return m, cells


def unsupported_reasons(a2m: dict[str, str], config: dict, hardware_ids: list[str], engine_ids: list[str], model_ids: list[str]) -> dict[tuple, str]:
    from pie_bench.plan.matrix import selector_matches
    from pie_bench.schema import Tier

    m, cells = matrix_cells()
    wanted = set(all_models(config))
    pie_arts = {a.baseline_of for a in m.artifacts.values() if a.id in wanted and a.baseline_of}
    arms = {a.id for a in m.artifacts.values() if a.id in wanted or a.id in pie_arts or a.baseline_of in pie_arts}
    benches = set(config.get("benchmarks", []))
    seen: dict[tuple, list[str | None]] = {}
    for c in m.cells_for(Tier.TARGETED, cells):
        if c.platform.id not in hardware_ids or str(c.engine) not in engine_ids or c.artifact.id not in arms:
            continue
        if (str(c.engine) == "pie") != (c.artifact.baseline_of is None):
            continue
        if benches and c.workload.id not in benches:
            continue
        model = a2m.get(c.artifact.id)
        if model not in model_ids:
            continue
        reason = next((rule.reason for rule in m.unsupported if selector_matches(rule.when, c)), None)
        if reason is None and c.declared_unsupported_reason and not c.declared_unsupported_reason.startswith("does not fit"):
            reason = c.declared_unsupported_reason
        seen.setdefault((c.platform.id, str(c.engine), model), []).append(reason)
        if c.workload.id in WL_PRIORITY:
            seen.setdefault((c.platform.id, str(c.engine), model, WL_PRIORITY[c.workload.id][0]), []).append(reason)
    out = {k: next(r for r in rs if r) for k, rs in seen.items() if rs and all(rs)}
    names = {e: ENGINE_META.get(e, (e,))[0] for e in engine_ids}
    for hw in hardware_ids:
        for e in engine_ids:
            for model in model_ids:
                if (hw, e, model) not in seen:
                    out[(hw, e, model)] = f"{names[e]} has no build of this model"
    return out


def measured(r: dict) -> bool:
    return r["status"] in ("pass", "noisy") and any(r.get(m) is not None for m in ("decode_tok_s", "prefill_tok_s", "output_tok_s"))


PREFILL = ("prefill_tok_s", "ttft_ms_p50", "ttft_ms_p99", "prompt_tokens", "requests", "failed")


def keep_decode(tag_rows: list[dict], picked: dict[tuple, tuple], a2m: dict[str, str], engine: str, since: datetime) -> None:
    earlier = pick([r for r in tag_rows if r["engine"] == engine and r["started_at"] < since], a2m)
    for key, (rank, r) in picked.items():
        if key[1] == engine and key[3] == "raw" and r["started_at"] >= since and key in earlier:
            old = earlier[key][1]
            picked[key] = (rank, {**old, **{m: r[m] for m in PREFILL}})


def results_by_tag(store, a2m, hardware_ids, engine_ids, prefill_only=None):
    cols = (["platform", "engine", "engine_version", "artifact", "scheme", "workload", "status", "pie_commit", "started_at", "tag", "tag_kind", "counters_json",
             "prompt_tokens", "requests", "failed", "harness_commit"] + METRICS)
    rows = [r for r in store.table().select(cols).to_pylist()
            if measured(r) and r["platform"] in hardware_ids and r["engine"] in engine_ids]
    rows = share_workload(share_cut(rows, a2m), a2m)
    by_tag: dict[str, list[dict]] = {}
    for r in rows:
        if r["tag"] and not r["tag"].startswith("test-"):
            by_tag.setdefault(r["tag"], []).append(r)
    skipped: dict[tuple, str] = {}
    tagged = {t: pick(rs, a2m, skipped) for t, rs in by_tag.items()}
    for (t, hw, engine, art), why in sorted(skipped.items()):
        print(f"[webdb] {t}: {engine} {art} on {hw} not shown: {why}", file=sys.stderr)
    for t, p in (prefill_only or {}).items():
        if t in tagged:
            keep_decode(by_tag[t], tagged[t], a2m, p["engine"], datetime.fromisoformat(p["since"]))
    meta = {t: {"kind": rs[0]["tag_kind"] or "manual", "at": max(r["started_at"] for r in rs),
                "commit": next((r["pie_commit"][:9] for r in rs if r["engine"] == "pie" and r["pie_commit"]), "")}
            for t, rs in by_tag.items()}
    return tagged, meta


CHECKS = ("parity@", "kernels@")


def is_check(q: dict) -> bool:
    return str(q.get("task") or "").startswith(CHECKS)


def model_of(a2m: dict[str, str], model: str) -> str:
    return a2m.get(model, a2m.get(model.removesuffix("@vllm"), model.removesuffix("@vllm")))


def quality_checks(store, a2m) -> dict[str, list[dict]]:
    newest: dict[tuple, dict] = {}
    for q in store.quality():
        if not is_check(q) or is_diag_tag(q.get("tag") or ""):
            continue
        key = (q["artifact"], q["task"])
        if key not in newest or (q.get("date") or "") > (newest[key].get("date") or ""):
            newest[key] = q
    out: dict[str, list[dict]] = {"parity": [], "kernels": []}
    for (art, task), q in sorted(newest.items()):
        kind, platform = task.split("@", 1)
        row = {k: v for k, v in q.items() if k not in ("samples", "ci95", "tag_kind")}
        row.update(platform=q.get("platform") or platform, release=q.get("tag"))
        if kind == "parity":
            row["model"] = model_of(a2m, q.get("model") or art)
        else:
            errors = q.get("errors") or {}
            worst = q.get("worst") or q.get("worst_error")
            if not isinstance(worst, dict) and errors:
                name = max(errors, key=lambda n: (errors[n] or {}).get("max_abs") or 0)
                worst = {"name": name, **(errors[name] or {})}
            row["worst"] = worst if isinstance(worst, dict) else ({"max_abs": worst} if worst is not None else None)
            row.pop("errors", None)
            row["failing"] = q.get("failing") or q.get("failures") or []
        out[kind].append(row)
    return out


def quality_by_tag(store, a2m):
    from datetime import datetime

    tagged: dict[str, dict[tuple, dict]] = {}
    meta: dict[str, dict] = {}
    for q in store.quality():
        t = q.get("tag")
        if not t or is_check(q) or q.get("score") is None or not q.get("ci95") or None in q["ci95"]:
            continue
        at = datetime.fromisoformat(q["date"].replace("Z", "+00:00"))
        row = {"model": model_of(a2m, q["model"]), "engine": q["engine"], "artifact": q["artifact"],
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
    arts = {a["id"]: a for a in load("models")["artifacts"]}
    by_tag: dict[str, list[dict]] = {}
    for q in store.quality(samples=True):
        t = q.get("tag")
        if not t or is_check(q):
            continue
        art = arts.get(q["artifact"], {})
        row = {**q, "model": model_of(a2m, q["model"]), "tag": t,
               "scheme": q.get("scheme") or art.get("scheme"), "checkpoint": q.get("checkpoint") or art.get("base_model")}
        by_tag.setdefault(t, []).append(row)
    web = {p["id"] for p in load("platforms")["platforms"] if p.get("backend") == "webgpu"}
    refs = sorted((r for rs in by_tag.values() for r in rs if r["engine"] != "pie" and r.get("score") is not None and r.get("platform") not in web), key=lambda r: r.get("date") or "")
    for rs in by_tag.values():
        for r in [r for r in rs if r["engine"] == "pie" and r.get("platform") in web]:
            ref = next((x for x in reversed(refs) if (x["scheme"], x["checkpoint"], x["task"], x.get("n")) == (r["scheme"], r["checkpoint"], r["task"], r.get("n"))), None)
            if ref and not any(x["engine"] != "pie" and x.get("platform") == r["platform"] and x["model"] == r["model"] and x["task"] == r["task"] for x in rs):
                rs.append({**ref, "platform": r["platform"], "ref_platform": ref.get("platform") or "m5-max-128g"})
    return {t: parity_rows(rs) for t, rs in by_tag.items()}


def is_diag_tag(tag: str) -> bool:
    return "-diag-" in f"-{tag}-"


def stack(order: list[str], tagged: dict[str, dict], keys: list[tuple], row, when) -> dict[str, list[dict]]:
    snaps: dict[str, list[dict]] = {}
    newest: dict = {}
    for t in reversed(order):
        own = tagged.get(t, {})
        for key, item in own.items():
            if key not in newest or (when(item) or "") >= (when(tagged[newest[key]][key]) or ""):
                newest[key] = t
        out = []
        for key in keys:
            src = newest.get(key)
            if src is None:
                continue
            item = tagged[src][key]
            out.append({**row(item, key, src), "stale": None if src == t else {"tag": src, "measured": when(item)}})
        snaps[t] = out
    return snaps


def gpu_note(memory) -> str:
    from pie_bench.plan.matrix import gpu_gib

    return f"{round(gpu_gib(memory))}" if memory else "?"


def no_fit(a2m: dict[str, str], config: dict, hw_rows: list[dict], engine_ids: list[str], model_ids: list[str]) -> dict:
    factor = float(load("support").get("fit_factor", 1.25))
    arts = {a["id"]: a for a in load("models")["artifacts"]}
    need: dict[tuple[str, str], float] = {}
    for model in model_ids:
        for engine in engine_ids:
            if engine == "pie":
                ids = [i for i, a in arts.items() if a2m.get(i) == model and a.get("source_format") == "mlx" and a.get("kind") != "miniature"]
            else:
                ids = [i for i in all_models(config) if i.endswith(f"-{engine}") and a2m.get(i) == model]
            sizes = [arts[i]["expected_gib"] for i in ids if arts.get(i, {}).get("expected_gib")]
            if sizes:
                need[(model, engine)] = min(sizes) * factor
        if (model, "pie") not in need and "pie" in engine_ids:
            others = [gib for (m, _), gib in need.items() if m == model]
            if others:
                need[(model, "pie")] = min(others)
    from pie_bench.plan.matrix import gpu_gib

    out: dict[str, dict] = {}
    for hw in hw_rows:
        memory = hw.get("memory_gib")
        if not memory:
            continue
        for (model, engine), gib in need.items():
            if gib > gpu_gib(memory):
                out.setdefault(hw["id"], {}).setdefault(model, {})[engine] = round(gib, 1)
    return out


def gpu_unsupported(a2m: dict[str, str], gpu_ids: list[str], engine_ids: list[str], benches: list[str]) -> dict[tuple, str]:
    from pie_bench.plan.matrix import selector_matches

    m, cells = matrix_cells()
    out: dict[tuple, str] = {}
    for c in cells:
        if c.platform.id not in gpu_ids or str(c.engine) not in engine_ids or (benches and c.workload.id not in benches):
            continue
        if c.workload.id not in RAW:
            continue
        if any(selector_matches(sel, c) for sel in m.global_exclude):
            continue
        if c.artifact.source_format.value != "hf_safetensors" or c.artifact.kind.value != "full" or c.program.id != "text-completion-bench":
            continue
        reason = c.declared_unsupported_reason
        if reason and not reason.startswith("does not fit") and c.artifact.id in a2m:
            out.setdefault((c.platform.id, str(c.engine), a2m[c.artifact.id]), reason)
    return out


def gpu_unsupported_setups(a2m: dict[str, str], gpu_ids: list[str], engine_ids: list[str]) -> dict[tuple, str]:
    m, cells = matrix_cells()
    out: dict[tuple, str] = {}
    for c in cells:
        if c.platform.id not in gpu_ids or str(c.engine) not in engine_ids or c.workload.id not in WL_PRIORITY:
            continue
        if c.program.id != "text-completion-bench" or c.artifact.id not in a2m:
            continue
        reason = c.declared_unsupported_reason
        if reason and not reason.startswith("does not fit"):
            out.setdefault((c.platform.id, str(c.engine), a2m[c.artifact.id], WL_PRIORITY[c.workload.id][0]), reason)
    return out


def gpu_no_fit(store, a2m: dict[str, str], hw_rows: list[dict], gpu_ids: list[str]) -> dict:
    from pie_bench.plan.matrix import gpu_gib

    factor = float(load("support").get("fit_factor", 1.25))
    arts = {a["id"]: a for a in load("models")["artifacts"]}
    used: dict[str, set[str]] = {}
    engines: set[str] = set()
    for r in store.table().select(["platform", "engine", "artifact"]).to_pylist():
        a = arts.get(r["artifact"])
        if r["platform"] in gpu_ids and a and a.get("source_format", "hf_safetensors") == "hf_safetensors" and a.get("kind", "full") == "full" and r["artifact"] in a2m:
            used.setdefault(a2m[r["artifact"]], set()).add(r["artifact"])
            engines.add(r["engine"])
    weights = {m: min(arts[i]["expected_gib"] for i in ids if arts[i].get("expected_gib"))
               for m, ids in used.items() if any(arts[i].get("expected_gib") for i in ids)}
    factors = {p["id"]: p.get("fit_factor") or factor for p in load("platforms")["platforms"]}
    web = {p["id"] for p in load("platforms")["platforms"] if p.get("backend") == "webgpu"}
    out: dict[str, dict] = {}
    for hw in hw_rows:
        if hw["id"] not in gpu_ids or hw["id"] in web or not hw.get("memory_gib"):
            continue
        cap = gpu_gib(hw["memory_gib"], hw.get("interconnect") or "pcie")
        for model, w in weights.items():
            gib = w * factors.get(hw["id"], factor)
            if gib > cap:
                out.setdefault(hw["id"], {})[model] = {e: round(gib, 1) for e in engines}
    return out


def tag_date(tag: str, meta: dict) -> str | None:
    if meta["kind"] == "release":
        for path, key in ((f"releases/tags/{tag}", ("published_at",)), (f"commits/{tag}", ("commit", "committer", "date"))):
            try:
                v = _github(f"repos/pie-project/pie/{path}")
                for k in key:
                    v = v[k]
                return str(v)[:10]
            except Exception:
                continue
        return None
    return local(meta["at"])


@functools.cache
def _github(path: str) -> dict:
    req = urllib.request.Request(f"https://api.github.com/{path}", headers={"Accept": "application/vnd.github+json", "User-Agent": "pie-bench-api"})
    if os.environ.get("GITHUB_TOKEN"):
        req.add_header("Authorization", f"Bearer {os.environ['GITHUB_TOKEN']}")
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read())


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

    def __getattr__(self, name):
        return getattr(self.store, name)


def build(store, contributed: dict[str, dict] | None = None) -> tuple[dict, dict[str, dict]]:
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
    mac_engines = [e for e in engines() if "macos" in e["os"]]
    suite_ids = suite_model_ids(config, a2m)
    model_ids = sorted({m for ids in suite_ids.values() for m in ids})
    for m in models:
        m["suite"] = "Targeted" if m["id"] in suite_ids.get("targeted", []) else "Full" if m["id"] in suite_ids.get("full", []) else ""
    kind = {p["id"]: ("Mac" if p.get("os") == "macos" else "TPU" if p.get("backend") == "xla" else "AMD" if p.get("backend") == "rocm" else "GPU")
            for p in load("platforms")["platforms"]}
    kind.update({h["id"]: "Phone" for h in phone_hardware(store)})
    platforms: dict[str, set[str]] = {}
    for r in store.table().select(["artifact", "platform", "status"]).to_pylist():
        if r["status"] in ("pass", "noisy") and r["artifact"] in a2m and r["platform"] in kind:
            platforms.setdefault(a2m[r["artifact"]], set()).add(kind[r["platform"]])
    order = ["Mac", "GPU", "TPU", "AMD", "Phone"]
    for m in models:
        m["platforms"] = ", ".join(t for t in order if t in platforms.get(m["id"], set()))
    engine_ids = [e["id"] for e in mac_engines]
    gpu_ids = [p["id"] for p in load("platforms")["platforms"] if p.get("os") != "macos"]
    phone_rows = phone_hardware(store)
    phone_ids = [h["id"] for h in phone_rows]
    all_engines = [e["id"] for e in engines()]
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
    snaps = stack(order, results, grid, lambda item, key, src: as_row(item[1], key, src), lambda item: local(item[1]["started_at"]))
    lap("stack")
    hw_rows = [h for h in hardware(cores_by_platform(store)) if h["id"] in hardware_ids or h["class"] != "mac" or not h.get("runs")] + phone_rows
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
    ever = {(r["hardware"], r["engine"], r["model"], r["workload"]) for rows in snaps.values() for r in rows}
    for t in order:
        have = {(r["hardware"], r["engine"], r["model"], r["workload"]): r for r in snaps[t]}
        cut = {(r["hardware"], r["model"]) for r in snaps[t] if r.get("miniature")}
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
        snaps[t] = filled
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

    for t in order:
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
    db = {"updated_at": updated_at, "totals": totals, "tags": tags, "snapshots": snaps, "quality_snapshots": quality, "parity": {t: parity.get(t, []) for t in order},
          "quality_parity": checks["parity"], "quality_kernels": checks["kernels"], "quality_gaps": load("support").get("quality_gaps", []),
          "speed_gaps": load("support").get("speed_gaps", []),
          "no_fit": misfits, "suites": suite_ids,
          "hardware": hw_rows,
          "engines": engines(), "models": [m for m in models if m["id"] in model_ids or m.get("catalog")],
          "workloads": workloads(), "install": install_sizes(), "quality_tasks": quality_tasks(), "quality": quality.get(order[0], []) if order else []}
    return split.split(db)
