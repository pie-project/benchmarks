"""Build web/data/db.js for the site from the result store (Postgres at $PIE_EVALS_DB).

    PIE_EVALS_DB=postgresql://... .venv/bin/python tools/webdb.py

The store holds one row per measured cell across every tier and platform. This keeps
the newest passing run per platform, engine, model, release and workload-category,
collapsing the many measured workloads into the two the site shows: the raw single request and
a throughput (concurrency) run.
"""
from __future__ import annotations

import functools
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import split_db  # tools/split_db.py, beside this script
import yaml

from pie_evals.plan.suites import all_models, suites
from pie_evals.quality.parity import rows as parity_rows
from pie_evals.results.store import Store

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"

# Each site workload maps to measured workloads, best first.
# a device evaluation measures throughput at the concurrency that saturates its GPU (c<N>, pf<N>-512, N a power of two):
# every N is listed, after the fixed counts the Macs use, so each cell shows whichever N it was measured at
THROUGHPUT = ["c32", "c64", "c256", "c8", "c4", "c16", "c128", "c512", "c1024"]
RAW = ["raw-512-256"]  # the single request with speculation off: what the hardware limit is measured against
SPEC = ["spec-512-256"]  # the same request with speculation on: every engine drafts with its own drafter
PREFILL_BATCH = ["pf256-512", "pf4-512", "pf8-512", "pf16-512", "pf32-512", "pf64-512", "pf128-512", "pf512-512", "pf1024-512"]  # 256 cold prompts at once, one token each: the batch's prompt tokens over the wall
CATEGORIES = (("throughput", THROUGHPUT, "Batching"), ("raw", RAW, "Raw"), ("spec", SPEC, "Speculative"), ("prefill_batch", PREFILL_BATCH, "Batched Prefill"))
SITE_TZ = ZoneInfo("America/Los_Angeles")  # the team is in California: dates and times on the site are Pacific

WL_PRIORITY = {wl: (cat, i) for cat, ids, _ in CATEGORIES for i, wl in enumerate(ids)}

ENGINE_META = {
    "pie":      ("Pie", "Apache-2.0", "pie-project/pie"),
    "vllm":     ("vLLM", "Apache-2.0", "vllm-project/vllm"),
    "sglang":   ("SGLang", "Apache-2.0", "sgl-project/sglang"),
    "trtllm":   ("TensorRT-LLM", "Apache-2.0", "NVIDIA/TensorRT-LLM"),
    "llamacpp": ("llama.cpp", "MIT", "ggml-org/llama.cpp"),
    "mlxlm":    ("MLX", "MIT", "ml-explore/mlx-lm"),
    "vllm-metal": ("vLLM Metal", "Apache-2.0", "vllm-project/vllm-metal"),
    "webllm":   ("MLC", "Apache-2.0", "mlc-ai/web-llm"),  # MLC's browser engine (WebLLM), named for its project
    "llamacpp-webgpu": ("llama.cpp", "MIT", "ggml-org/llama.cpp"),  # its browser build, named as the engine: a browser runs only the WebGPU one
    "splash":   ("Splash", None, "incoai/splash"),
    "litert":   ("LiteRT-LM", "Apache-2.0", "google-ai-edge/LiteRT-LM"),
    "mlc":      ("MLC LLM", "Apache-2.0", "mlc-ai/mlc-llm"),
    "mlx-swift": ("MLX Swift", "MIT", "ml-explore/mlx-swift-lm"),
}
# an engine the site's own palette (tokens.css) has no color for brings its own
ENGINE_COLOR = {"trtllm": "#a2845e", "litert": "#34a853", "mlc": "#5856d6", "mlx-swift": "#ff9500", "webllm": "#5e5ce6", "llamacpp-webgpu": "#8e8e93"}
METRICS = ["decode_tok_s", "prefill_tok_s", "output_tok_s", "ttft_ms_p50", "ttft_ms_p99",
           "itl_ms_p50", "itl_ms_p99", "latency_ms_p50", "latency_ms_p99", "resident_gib", "load_s"]


# families whose name does not say they route experts
MOE_FAMILIES = {"gpt_oss", "qwen4_exp"}
# a catalog-only model's fit: bytes per weight at its release precision, and the largest node CI rents on each platform
# (RunPod: 8 x B300 288 GB, 8 x MI300X 192 GB; Google Cloud: a v5p-8, 4 chips x 95 GB; TPU7x has no quota)
BYTES_PER_WEIGHT = {"bf16": 2, "fp8": 1, "mxfp8": 1, "mxfp4": 0.53, "int4": 0.5625, "nvfp4": 0.5625}
NODE_GB = {"GPU": 8 * 288, "AMD": 8 * 192, "TPU": 4 * 95}


def load(name: str) -> dict:
    return yaml.safe_load((ROOT / "matrix" / f"{name}.yaml").read_text())


def model_name(base: str) -> str:
    drop = {"4bit", "bf16", "gguf", "mlx", "mxfp4", "q4", "q4km", "mtp", "instruct", "it", "base", "8k", "mini5", "mini8",
            "litert", "lm", "mlc", "q4f16_1", "q4f32_1"}  # the phones' LiteRT-LM and MLC releases (pie_evals.results.phone.model_ids)
    # a mirror that names its files after the source org (DevQuasar's "meta-models.Muse-Spark-...") is the same model
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
        # sizes stated in the catalog win over the ones read from the name (gpt-oss-20b says neither its experts nor 21B)
        for size in ("params_b", "active_b"):
            if a.get(size) is not None:
                row[size + "_stated"] = float(a[size])
        # the shape as the model's config.json states it (a full checkpoint's, never a miniature's)
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
        # one definition per model today, every expert resident: no SSD streaming. A streaming twin would fit smaller Macs.
        row["ssd_streaming"] = "Without" if row["architecture"] == "MoE" else "n/a"
        row["schemes"] = ", ".join(sorted(row["schemes"]))
        row["draft"] = "true" if row.get("draft") else "false"
        # weights only, from the parameter count and the bits each weight takes (4-bit affine with a 16-bit scale and
        # bias per 64 weights = 4.5 bits; NVFP4 4-bit with an 8-bit scale per 16 = 4.5 bits)
        row["size_gib"] = round(row["params_b"] * 1e9 * 4.5 / 8 / 2**30, 1) if row["params_b"] else None
        # what it takes to fit: the planner's own rule (weights x 1.25 must fit in the Mac's memory)
        row["needs_gib"] = round(row["size_gib"] * 1.25, 1) if row["size_gib"] else None
        row.setdefault("context", None)
        row["license"] = None
    # the catalog's models (matrix/models.yaml `catalog:`): every model the site lists, run or not. A model CI runs takes
    # the stated sizes and layer count it lacks; one it does not run becomes a catalog-only row (no results, no grid)
    for c in load("models").get("catalog") or []:
        # the same id CI gives the model's runs (from its repo name), so the catalog row and its results meet
        mid = model_name(c["base_model"]).lower() if c.get("base_model") else c["name"].lower()
        row = by_model.get(mid)
        if row is None:
            row = by_model[mid] = {"id": mid, "name": c["name"], "family": c.get("family"), "base_model": c.get("base_model"),
                                   "schemes": c.get("precision") or "", "artifacts": 0, "draft": "true" if c.get("mtp") else "false",
                                   "catalog_only": True}
        row["catalog"] = True
        row["name"] = c["name"]  # the catalog's short name, not the repo's ("Nemotron-3-Ultra", not "...-550B-A55B")
        if c.get("mtp"):
            row["draft"] = "true"  # ships its own draft head: speculative decoding works out of the box
        # the card's sizes win over the ones read from a name; the rest only fill what is missing
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
            # where it would fit (shown faded wherever it is not yet measured): its weights at the precision it is released in, x1.25, against the
            # largest node CI can rent on each platform
            need = row["params_b"] * BYTES_PER_WEIGHT.get(str(c.get("precision") or "bf16"), 2) * 1.25
            row["fits"] = ", ".join(t for t, gb in NODE_GB.items() if need <= gb)
    # the site's names, one pattern for every model: Family-Version-Size, the total size (matrix/models.yaml `names:`)
    for mid, name in (load("models").get("names") or {}).items():
        if mid in by_model:
            by_model[mid]["name"] = name
    return mapping, list(by_model.values())


def cores_by_platform(store) -> dict[str, dict]:
    """Each machine's CPU and GPU core counts, read from the newest run that recorded them."""
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
    """The CI's machines (tagged with the runs that use them) first, then every other catalog accelerator.
    Specs come from matrix/hardware.yaml (datasheet values only); a CI machine links to its entry by
    `catalog:` (Macs, TPU) or by its RunPod GPU type, and keeps its own memory and device count."""
    cores = cores or {}
    catalog = load("hardware")["hardware"]
    by_id = {c["id"]: c for c in catalog}
    by_runpod = {c["runpod_gpu_type"]: c for c in catalog if c.get("runpod_gpu_type")}
    spec_keys = ("bandwidth_gbs", "tflops_fp16", "tflops_fp8", "tflops_mxfp8", "ane_tflops_fp16", "power_w", "cpu_cores", "gpu_cores", "year", "memory_type")

    def row(c: dict, **over) -> dict:
        resource = RESOURCE.get(c["class"], "RunPod cloud" if c.get("runpod_gpu_type") else "")
        return {
            # a short name everywhere a machine is named (grids, menus, the table); the full one beside it in the catalog
            "id": c["id"], "resource": resource, "name": c.get("short") or c["name"], "full_name": c["name"],
            "class": c["class"], "location": "local" if c["class"] == "mac" else "cloud",
            "vendor": c["vendor"], "backend": c.get("backend"), "arch": c.get("arch"), "count": 1,
            "memory_gib": c.get("memory_gib") or max(c.get("memory_options_gb") or [0]) or None,
            "memory_type": c.get("memory_type"), "bandwidth_gbs": c.get("bandwidth_gbs"),
            "cpu_cores": c.get("cpu_cores"), "gpu_cores": c.get("gpu_cores"), "tflops_fp16": c.get("tflops_fp16"),
            # the narrower tensor peaks the limits use for FP8 and MXFP4 builds, where the chip has them
            "tflops_fp8": c.get("tflops_fp8"), "tflops_mxfp8": c.get("tflops_mxfp8"),
            # the Neural Engine beside an Apple GPU: only an engine that runs prompt matmuls on it has it in its limit
            "ane_tflops_fp16": c.get("ane_tflops_fp16"),
            "interconnect": None, "power_w": c.get("power_w"), "year": str(c["year"]) if c.get("year") else None,
            "runs": None, "price_usd": None, "price_hr": None, **over,
        }

    rows, used = [], set()
    for p in load("platforms")["platforms"]:
        # a platform no CI run uses is only known through its catalog entry below
        if not p.get("tiers"):
            continue
        mac = p.get("os") == "macos"
        c = by_id.get(p.get("catalog")) or by_runpod.get(p.get("runpod_gpu_type")) or {}
        used.add(c.get("id"))
        base = row(c) if c else {}
        rows.append({
            **base,
            "id": p["id"],
            "resource": "Pie self-hosted" if mac else ("Google Cloud" if p.get("backend") == "xla" else "RunPod cloud"),
            # grids show short names: the chip for a Mac, RunPod's short name for a GPU; the catalog keeps the full one
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
    # an accelerator keeps the name its maker writes, words apart (H100 SXM, RTX PRO 6000, TPU v6e), as a Mac keeps Apple's
    for r in rows:
        # a browser row is the same card as a native one, seen through Chrome's WebGPU: its name says so, and its
        # vendor names the browser beside the card's maker (the site files a machine whose vendor is "NVIDIA" under NVIDIA)
        if r["class"] == "web" and r.get("name"):
            r["name"] += " Chrome"
            r["vendor"] = f"Chrome ({r.get('vendor') or 'GPU'})"
            # WebGPU has no FP8 or block-scaled matrix math, so the card's narrower peaks are out of a browser's reach
            r["tflops_fp8"] = r["tflops_mxfp8"] = None
    return rows


def phone_hardware(store) -> list[dict]:
    """The phones the benchmark app (mobile/) has sent rows from, as machines of the site's Mobile platform: named by
    matrix/phones.yaml, or by what the phone reported when it is not listed there. A test device never shows."""
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
            # the site's Mobile platform (Pie.platformOf): every phone, Android or iPhone
            "class": "android", "location": "local", "vendor": p.get("vendor") or fp.get("manufacturer") or None,
            "backend": p.get("backend") or ("metal" if fp.get("os") == "ios" else "vulkan"), "arch": p.get("arch") or fp.get("soc"),
            "count": 1, "memory_gib": p.get("memory_gib") or fp.get("ram_gib"), "memory_type": None, "bandwidth_gbs": p.get("bandwidth_gbs"),
            "cpu_cores": fp.get("cpu_cores"), "gpu_cores": None, "tflops_fp16": p.get("tflops_fp16"), "interconnect": "uma", "power_w": None,
            "year": str(p["year"]) if p.get("year") else None, "runs": "Phone app", "price_usd": None, "price_hr": None,
        })
    return out


# what each engine can decode with: plain (speculation off, the Raw rows) and speculative (with a drafter).
# Splash pairs every model with its DFlash2 draft and has no flag to turn it off (support.yaml)
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
                     "backends": ", ".join(e.get("backends", [])),  # where it can run at all, for Platform Support
                     **({"color": ENGINE_COLOR[e["id"]]} if e["id"] in ENGINE_COLOR else {}),
                     **dict(zip(("raw", "speculation"), ("Yes" if ok else "No" for ok in DECODING.get(e["id"], (True, False)))))})
    return rows


def install_sizes() -> list[dict]:
    """matrix/install.yaml as the site's `install` table: one row per platform and engine, its bytes and how they were
    counted, for the Overview's Install Size cards and the Methodology's chapter."""
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
        # each benchmark's own shape: a row measured at c1024 or pf16-512 (its `benchmark`) is held to the limit of its
        # own requests at once, prompt and answer, not to the category's first benchmark's
        shapes = {i: {"concurrency": params[i].get("concurrency") or 1, "prompt_tokens": params[i].get("prefill"),
                      "output_tokens": params[i].get("decode")} for i in ids if i in params}
        out.append({"id": cat, "label": label, "concurrency": p.get("concurrency") or (32 if cat == "throughput" else 1),
                    "prompt_tokens": p.get("prefill"), "output_tokens": p.get("decode"), "benchmark": ", ".join(ids),
                    "shapes": shapes})
    return out


# the quality benchmarks: what each task asks, where its questions come from, how an answer is scored
# the tasks the site lists and expects a score on: MATH-500 only now; the others are no longer run
QUALITY_TASKS = [
    ("gsm8k", "Grade-school math word problems, worked step by step", "openai/gsm8k (test)", "final number matches"),
    ("ifeval", "Following explicit instructions (length, format, keywords)", "google/IFEval", "every instruction met"),
    ("mmlu", "Multiple-choice knowledge across 57 subjects", "cais/mmlu (test)", "chosen letter matches"),
    ("arc", "Grade-school science reasoning, multiple choice", "allenai/ai2_arc (ARC-Challenge test)", "chosen letter matches"),
    ("math500", "Competition math, final answer in boxed form", "HuggingFaceH4/MATH-500", "final answer equivalent"),
]


def suite_model_ids(config: dict, a2m: dict[str, str]) -> dict[str, list[str]]:
    """{suite: [model ids]}: the models each suite's arms (and the pie arms they stand beside) carry."""
    arts = {a["id"]: a for a in load("models")["artifacts"]}
    out = {}
    for name, arms in suites(config).items():
        ids = [a for aid in arms for a in (aid, arts.get(aid, {}).get("baseline_of")) if a in a2m]
        out[name] = sorted({a2m[a] for a in ids})
    return out


def quality_arms(config: dict) -> list[tuple[str, str]]:
    """(engine, artifact) for each competitor arm of any suite in config.json and the pie arm it is compared with."""
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
    """{competitor artifact: why}: arms quantized unlike the pie arm they stand beside. Their
    scores measure the quantization, not the engine, so the quality table shows none of them."""
    arts = {a["id"]: a for a in load("models")["artifacts"]}
    out = {}
    for a in arts.values():
        pie = arts.get(a.get("baseline_of") or "")
        if pie and a.get("scheme") != pie.get("scheme"):
            out[a["id"]] = f"Runs {a.get('scheme')} weights where pie runs {pie.get('scheme')}: not compared"
    return out


def quality_tasks() -> list[dict]:
    from pie_evals.quality.dist_run import ANSWER_TOKENS, PARITY_TASKS
    from pie_evals.quality.tasks import TASKS

    scored = [{"id": t, "task": t, "description": d, "source": src, "scoring": sc, "max_tokens": TASKS[t][2]}
              for t, d, src, sc in QUALITY_TASKS if t in TASKS]
    # the parity check beside the scores (quality/dist_run.py): one row per model and machine
    parity = {"id": "parity", "task": "parity",
              "description": "Pie matches vLLM on the same weights",
              "source": ", ".join(PARITY_TASKS),
              "scoring": "mean KL, top-1 agreement",
              "max_tokens": ANSWER_TOKENS}
    return scored + [parity]


# runs measured before the tagged runs live on this Mac: they stay on the site as the fallback



def local(ts) -> str:
    """A run time as Pacific 'YYYY-MM-DD HH:MM' (the store keeps UTC)."""
    return ts.astimezone(SITE_TZ).strftime("%Y-%m-%d %H:%M") if ts is not None else ""


# a miniature row's label: how much of the model it keeps ("8 of 78 layers")
def _miniature_labels() -> dict[str, str]:
    arts = load("models")["artifacts"]
    full = {a["base_model"]: a["layers"] for a in arts if a.get("layers") and a.get("kind", "full") == "full"}
    macs = {p["id"] for p in load("platforms")["platforms"] if p.get("os") == "macos"}
    out = {}
    for a in arts:
        if a.get("kind") != "miniature" or not a.get("miniature"):
            continue
        kept = sum(int(x.split("-")[-1]) - int(x.split("-")[0]) + 1 for x in str(a["miniature"]["layers"]).split(","))
        out[a["id"]] = f"{kept} of {full[a['base_model']]} layers" if a["base_model"] in full else f"{kept} layers"
        if a.get("platforms") and set(a["platforms"]) <= macs and a["miniature"].get("experts"):
            out[a["id"]] += f", {a['miniature']['experts']} experts"  # a Mac slice may keep every layer and cut only experts
    return out


MINIATURE = _miniature_labels()


def _miniature_shapes() -> dict[str, dict]:
    """A miniature's own size, for its roofline: the embedding and LM head whole, the kept share of the body's layers,
    and in them the routed experts it keeps (a token still runs through top-k of them). An estimate from the full
    model's stated sizes: the body is taken as even across layers."""
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
        # body - active_body is the E - top_k experts a layer a token does not run; the cut keeps kept - top_k of them,
        # its top-k being in the active body already (GLM-5.3 at 8 of 256 experts, its top-8: every kept one runs)
        n, top = f.get("experts"), f.get("top_k") or 0
        idle = min(1.0, max(0, (r.get("experts") or n) - top) / (n - top)) if n and n > top else 1.0
        out[a["id"]] = {"mini_active_b": round(emb + active_body * share, 3),
                        "mini_params_b": round(emb + (active_body + (body - active_body) * idle) * share, 3),
                        "mini_emb_b": round(emb, 3), "mini_layers": kept,
                        # the share of its kept experts a token runs through
                        "mini_k": round(min(1.0, f["top_k"] / (r.get("experts") or f["experts"])), 3) if f.get("top_k") and f.get("experts") else 1.0}
    return out


MINI_SHAPE = _miniature_shapes()


def miniature_fields(artifact: str) -> dict:
    """What a row of this artifact says of its cut: its label, and its size for the limits (methodology.js miniArch)."""
    return {"miniature": MINIATURE.get(artifact, ""), **MINI_SHAPE.get(artifact, {})}


# the miniatures of a datacenter model (over 100 GiB as released): those stand in for it, the CI fixtures never do
_FULL_BASES = {a["base_model"] for a in load("models")["artifacts"] if a.get("kind", "full") == "full" and (a.get("expected_gib") or 0) > 100}
# a model that does not fit a device is shown as its miniature there, whatever its size; only the CI's smoke fixtures
# (tiny cuts in the smoke tier) are never a model's number
SHOWN_MINIATURES = {a["id"] for a in load("models")["artifacts"] if a["id"] in MINIATURE and (a["base_model"] in _FULL_BASES or "smoke" not in a.get("tiers", []))}


def pick(rows: list[dict], a2m: dict[str, str]) -> dict[tuple, tuple]:
    """The row to show for each (hardware, engine, model, workload category): the newest run, then the best-matching
    workload, then on a Mac the MLX weights every Mac engine shares. A miniature (a few layers of the real shape) stands in only
    where the model has no full-checkpoint row, and its row says so (``miniature``)."""
    arts = {a["id"]: a for a in load("models")["artifacts"]}
    macs = {p["id"] for p in load("platforms")["platforms"] if p.get("os") == "macos"}
    best: dict[tuple, tuple] = {}
    for r in rows:
        cat_pri = WL_PRIORITY.get(r["workload"])
        if not cat_pri:
            continue
        art = arts.get(r["artifact"], {})
        mini = art.get("kind") == "miniature"
        # a CI fixture is never a model's number; a datacenter model cut to fit one device is, marked as such
        if mini and r["artifact"] not in SHOWN_MINIATURES:
            continue
        # Splash always drafts; its Raw and Batched rows (older runs among them) were never plain decoding
        if r["engine"] == "splash" and WL_PRIORITY[r["workload"]][0] in ("raw", "throughput"):
            continue
        # on a Mac every engine runs the same 4-bit MLX weights; a pie run of another precision (a bf16 import) is not
        # the comparison, so it never stands in for the model's number
        if r["platform"] in macs and r["engine"] == "pie" and art and art.get("source_format") != "mlx":
            continue
        cat, pri = cat_pri
        model = a2m.get(r["artifact"], r["artifact"])
        key = (r["platform"], r["engine"], model, cat)
        shared = r["platform"] in macs and art.get("source_format") == "mlx"
        # the newest run wins: a cell measured again (a fix, a fairer workload, a new saturating N) shows its latest number
        rank = (r["started_at"], not mini, -pri, shared)
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
        "benchmark": r["workload"],  # the workload the number came from (c512, pf16-512, raw-512-256): engines compare at the same N
        "prompt_per_request": prompt_per_request(r),
        "status": r["status"], "note": draft_note(r, engine),
        **miniature_fields(r["artifact"]),
    }


def prompt_per_request(r: dict) -> float | None:
    """The prompt tokens the engine processed per request, its chat template and cold-cache tag included (about 554 for
    raw-512-256 on Qwen): the count a row's prefill tok/s divides by, so its limit is held to the same prompt. As
    report.prompt_length_mismatches counts it: the row's prompt tokens over its completed requests."""
    done = int(r.get("requests") or 0) - int(r.get("failed") or 0)
    return round(r["prompt_tokens"] / done, 1) if r.get("prompt_tokens") and done > 0 else None


def draft_note(r: dict, engine: str) -> str:
    """A baseline that drafted with a separate small model on this row says so (pie's drafting shows as the model's Draft)."""
    try:
        counters = json.loads(r.get("counters_json") or "{}")
    except ValueError:
        return ""
    return "Speculative: drafts with a small same-family model" if engine != "pie" and counters.get("speculative") else ""


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
        if not t or t.startswith("test-"):  # untagged runs are not shown, nor a test of the phone app (pie_evals.results.phone)
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


@functools.cache
def matrix_cells():
    """The matrix and every cell it expands to, once per build: expanding takes minutes, and three tables read it."""
    import hashlib
    import pickle

    from pie_evals.plan.matrix import Matrix

    m = Matrix.load(ROOT / "matrix")
    # kept on the site laptop between builds, keyed by the matrix files: most builds only bring new results, and
    # expanding the matrix again would cost five minutes each time
    digest = hashlib.sha256()
    for f in sorted((ROOT / "matrix").rglob("*")):
        if f.is_file():
            digest.update(str(f.relative_to(ROOT)).encode() + f.read_bytes())
    cache = Path.home() / ".cache" / "pie-evals" / f"webdb-cells-{digest.hexdigest()[:16]}.pkl"
    try:
        return m, pickle.loads(cache.read_bytes())
    except Exception:
        pass
    cells = m.expand()
    try:
        cache.parent.mkdir(parents=True, exist_ok=True)
        for old in cache.parent.glob("webdb-cells-*.pkl"):
            old.unlink(missing_ok=True)
        cache.write_bytes(pickle.dumps(cells, protocol=pickle.HIGHEST_PROTOCOL))
    except Exception:
        pass
    return m, cells


def unsupported_reasons(a2m: dict[str, str], config: dict, hardware_ids: list[str], engine_ids: list[str], model_ids: list[str]) -> dict[tuple, str]:
    """{(hardware, engine, model): reason} for setups the matrix declares unsupported, or that an engine has no build of."""
    from pie_evals.plan.matrix import selector_matches
    from pie_evals.schema import Tier

    m, cells = matrix_cells()
    wanted = set(all_models(config))
    pie_arts = {a.baseline_of for a in m.artifacts.values() if a.id in wanted and a.baseline_of}
    # every copy of a configured model counts, not only the configured arm: an arm left out of
    # config.json because its engine cannot load the model still carries that reason
    arms = {a.id for a in m.artifacts.values() if a.id in wanted or a.id in pie_arts or a.baseline_of in pie_arts}
    benches = set(config.get("benchmarks", []))
    seen: dict[tuple, list[str | None]] = {}
    for c in m.cells_for(Tier.TARGETED, cells):
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
        # a rule on one workload (Splash has no Raw row) speaks for that tab alone
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
    """Passed (or noisy) and carrying at least one number."""
    return r["status"] in ("pass", "noisy") and any(r.get(m) is not None for m in ("decode_tok_s", "prefill_tok_s", "output_tok_s"))


# the prompt counts go with the prefill numbers: a prefill rate is the prompt tokens the engine processed over its TTFT
PREFILL = ("prefill_tok_s", "ttft_ms_p50", "ttft_ms_p99", "prompt_tokens", "requests", "failed")


def keep_decode(tag_rows: list[dict], picked: dict[tuple, tuple], a2m: dict[str, str], engine: str, since: datetime) -> None:
    """A prefill-only rerun: its single-request rows give the prefill numbers, every other number stays the earlier run's."""
    earlier = pick([r for r in tag_rows if r["engine"] == engine and r["started_at"] < since], a2m)
    for key, (rank, r) in picked.items():
        if key[1] == engine and key[3] == "raw" and r["started_at"] >= since and key in earlier:
            old = earlier[key][1]
            picked[key] = (rank, {**old, **{m: r[m] for m in PREFILL}})


def results_by_tag(store, a2m, hardware_ids, engine_ids, prefill_only=None):
    """The picked run per setup under each tag, and each tag's kind and newest time."""
    cols = (["platform", "engine", "engine_version", "artifact", "scheme", "workload", "status", "pie_commit", "started_at", "tag", "tag_kind", "counters_json",
             "prompt_tokens", "requests", "failed"] + METRICS)
    rows = [r for r in store.table().select(cols).to_pylist()
            if measured(r) and r["platform"] in hardware_ids and r["engine"] in engine_ids]
    by_tag: dict[str, list[dict]] = {}
    for r in rows:
        if r["tag"] and not r["tag"].startswith("test-"):  # untagged runs are not shown: every release is a tag; a test-* tag never shows
            by_tag.setdefault(r["tag"], []).append(r)
    tagged = {t: pick(rs, a2m) for t, rs in by_tag.items()}
    # config.json "prefill_only": {tag: {"engine": e, "since": ISO time}} reruns that may change only prefill
    for t, p in (prefill_only or {}).items():
        if t in tagged:
            keep_decode(by_tag[t], tagged[t], a2m, p["engine"], datetime.fromisoformat(p["since"]))
    meta = {t: {"kind": rs[0]["tag_kind"] or "manual", "at": max(r["started_at"] for r in rs),
                "commit": next((r["pie_commit"][:9] for r in rs if r["engine"] == "pie" and r["pie_commit"]), "")}
            for t, rs in by_tag.items()}
    return tagged, meta


#: tasks that are not accuracy scores: distribution parity (``parity@<platform>``) and kernel tests (``kernels@<platform>``)
CHECKS = ("parity@", "kernels@")


def is_check(q: dict) -> bool:
    return str(q.get("task") or "").startswith(CHECKS)


def model_of(a2m: dict[str, str], model: str) -> str:
    """The site's model id of a quality row; a vLLM arm's artifact ends in ``@vllm``."""
    return a2m.get(model, a2m.get(model.removesuffix("@vllm"), model.removesuffix("@vllm")))


def quality_checks(store, a2m) -> dict[str, list[dict]]:
    """The newest parity and kernel row per (artifact, platform), across tags: {"parity": [...], "kernels": [...]}."""
    newest: dict[tuple, dict] = {}
    for q in store.quality():
        # a diagnostic run's check (a quality-mac-diag kernel swap, say) is not the engine's verdict: never the newest
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
    """The newest score per (engine, model, weights, task) under each tag, and each tag's kind and newest time."""
    from datetime import datetime

    tagged: dict[str, dict[tuple, dict]] = {}
    meta: dict[str, dict] = {}
    for q in store.quality():
        t = q.get("tag")
        if not t or is_check(q) or q.get("score") is None or not q.get("ci95") or None in q["ci95"]:
            continue  # a run that ended without a score is not a result
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
    """Per tag, the engine parity of its quality scores: one row per model and task, every engine's cell against pie."""
    arts = {a["id"]: a for a in load("models")["artifacts"]}
    by_tag: dict[str, list[dict]] = {}
    for q in store.quality(samples=True):
        t = q.get("tag")
        if not t or is_check(q):
            continue
        art = arts.get(q["artifact"], {})  # older summaries carry no scheme or checkpoint: the matrix has them
        row = {**q, "model": model_of(a2m, q["model"]), "tag": t,
               "scheme": q.get("scheme") or art.get("scheme"), "checkpoint": q.get("checkpoint") or art.get("base_model")}
        by_tag.setdefault(t, []).append(row)
    # a browser tab (webgpu) runs pie alone: its reference is the newest engine row on the same weights and questions
    # from another machine (the Mac's mlx-lm on the MLX checkpoint), as its slices take the Mac's first-token reference
    web = {p["id"] for p in load("platforms")["platforms"] if p.get("backend") == "webgpu"}
    refs = sorted((r for rs in by_tag.values() for r in rs if r["engine"] != "pie" and r.get("score") is not None and r.get("platform") not in web), key=lambda r: r.get("date") or "")
    for rs in by_tag.values():
        for r in [r for r in rs if r["engine"] == "pie" and r.get("platform") in web]:
            ref = next((x for x in reversed(refs) if (x["scheme"], x["checkpoint"], x["task"], x.get("n")) == (r["scheme"], r["checkpoint"], r["task"], r.get("n"))), None)
            if ref and not any(x["engine"] != "pie" and x.get("platform") == r["platform"] and x["model"] == r["model"] and x["task"] == r["task"] for x in rs):
                rs.append({**ref, "platform": r["platform"], "ref_platform": ref.get("platform") or "m5-max-128g"})
    return {t: parity_rows(rs) for t, rs in by_tag.items()}


def is_diag_tag(tag: str) -> bool:
    """A tag of diagnostic runs (tpu-diag-fwd8k, tpu-diag-c256prof, ...): profilers and timing A/Bs, kept off the site."""
    return "-diag-" in f"-{tag}-"


def stack(order: list[str], tagged: dict[str, dict], keys: list[tuple], row, when) -> dict[str, list[dict]]:
    """For each tag, one row per key: the tag's own, else the newest run among the tags not later than it (marked
    stale); never a later tag."""
    # one pass from the oldest tag to the newest, carrying each key's newest run so far, instead of searching back
    # through every older tag for every key (66 tags made that the build's slowest step). A gap takes the newest run,
    # not the newest tag's: a tag's date moves with every import, so an old tag imported into again would otherwise
    # cover a later tag's runs with its older ones
    snaps: dict[str, list[dict]] = {}
    newest: dict = {}
    for t in reversed(order):
        own = tagged.get(t, {})
        for key, item in own.items():
            if key not in newest or (when(item) or "") >= (when(tagged[newest[key]][key]) or ""):
                newest[key] = t
        out = []
        for key in keys:
            src = t if key in own else newest.get(key)
            if src is None:
                continue
            item = tagged[src][key]
            out.append({**row(item, key, src), "stale": None if src == t else {"tag": src, "measured": when(item)}})
        snaps[t] = out
    return snaps


def gpu_note(memory) -> str:
    from pie_evals.plan.matrix import gpu_gib

    return f"{round(gpu_gib(memory))}" if memory else "?"


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
                ids = [i for i in all_models(config) if i.endswith(f"-{engine}") and a2m.get(i) == model]
            sizes = [arts[i]["expected_gib"] for i in ids if arts.get(i, {}).get("expected_gib")]
            if sizes:
                need[(model, engine)] = min(sizes) * factor
        # without its own artifact on record, pie needs at least what the lightest other engine needs
        if (model, "pie") not in need and "pie" in engine_ids:
            others = [gib for (m, _), gib in need.items() if m == model]
            if others:
                need[(model, "pie")] = min(others)
    from pie_evals.plan.matrix import gpu_gib

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
    """{(gpu, engine, model): reason} for GPU setups a support rule declares unsupported (not the fit rule)."""
    from pie_evals.plan.matrix import selector_matches

    m, cells = matrix_cells()
    out: dict[tuple, str] = {}
    for c in cells:
        if c.platform.id not in gpu_ids or str(c.engine) not in engine_ids or (benches and c.workload.id not in benches):
            continue
        # the key has no workload, so only the Raw request decides it: speculation's own gaps (no drafter) must not
        # blank a model's Raw and Batching numbers
        if c.workload.id not in RAW:
            continue
        # a setup no tier ever schedules (the TPU runs pie and vLLM only) is not an engine gap
        if any(selector_matches(sel, c) for sel in m.global_exclude):
            continue
        if c.artifact.source_format.value != "hf_safetensors" or c.artifact.kind.value != "full" or c.program.id != "text-completion-bench":
            continue
        reason = c.declared_unsupported_reason
        if reason and not reason.startswith("does not fit") and c.artifact.id in a2m:
            out.setdefault((c.platform.id, str(c.engine), a2m[c.artifact.id]), reason)
    return out


def gpu_unsupported_setups(a2m: dict[str, str], gpu_ids: list[str], engine_ids: list[str]) -> dict[tuple, str]:
    """{(gpu, engine, model, category): reason} for any GPU setup (a miniature's too) a support rule declares
    unsupported. Unlike gpu_unsupported it never blanks a measured row: it only explains a cell no run filled."""
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
    """{gpu: {model: {engine: GiB needed}}}: the planner's fit rule over the weights the GPU runs used."""
    from pie_evals.plan.matrix import gpu_gib

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
    # a browser tab (webgpu) runs the Mac's 4-bit weights, or their slice where those do not fit, never these
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


class ReadOnce:
    """The store read once: the build asks for the records and quality tables many times, each a full fetch over the tailnet."""

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
        # fresh dicts each call: callers fill in fields of their own
        return [dict(q) for q in self._quality[samples]]

    def __getattr__(self, name):
        return getattr(self.store, name)


def main() -> None:
    import time
    t0 = time.monotonic()
    lap = lambda what: print(f"[webdb] {what}: {time.monotonic() - t0:.0f}s", file=sys.stderr, flush=True)  # where a slow build spends its time
    store = ReadOnce(Store(sys.argv[1] if len(sys.argv) > 1 else None))
    a2m, models = artifact_to_model()
    # the site's grid: our Macs, the engines that run on a Mac, the models we measure there
    config = json.loads((ROOT / "config.json").read_text())
    hardware_ids = config["machines"]
    mac_engines = [e for e in engines() if "macos" in e["os"]]
    # every model of every suite has its rows; the site's suite picker narrows them to one suite's
    suite_ids = suite_model_ids(config, a2m)
    model_ids = sorted({m for ids in suite_ids.values() for m in ids})
    # the CI suite each model runs in: Targeted ones run in both, the rest only in Full
    for m in models:
        m["suite"] = "Targeted" if m["id"] in suite_ids.get("targeted", []) else "Full" if m["id"] in suite_ids.get("full", []) else ""
    # the platforms each model has actually been measured on: any CI result with a number, on a Mac, an NVIDIA GPU
    # ("GPU"), an AMD GPU or a TPU
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
    # the RunPod GPUs join the grids with every engine that ran there (pie, vLLM, SGLang): one row per setup a tag measured or tried
    gpu_ids = [p["id"] for p in load("platforms")["platforms"] if p.get("os") != "macos"]
    # the phones the app has measured: their rows join the grids as the GPUs' do, every engine that ran there
    phone_rows = phone_hardware(store)
    phone_ids = [h["id"] for h in phone_rows]
    all_engines = [e["id"] for e in engines()]
    results, rmeta = results_by_tag(store, a2m, hardware_ids + gpu_ids + phone_ids, all_engines, config.get("prefill_only"))
    lap("results_by_tag")
    gpu_attempts = attempts_by_tag(store, a2m, gpu_ids + phone_ids, all_engines)
    gpu_keys = {k for rs in [*results.values(), *gpu_attempts.values()] for k in rs if k[0] in gpu_ids or k[0] in phone_ids}
    gpu_models = sorted({k[2] for k in gpu_keys} - set(model_ids))
    model_ids += gpu_models
    if "full" in suite_ids:  # Full is every model: the GPU-only ones too
        suite_ids["full"] = suite_ids["full"] + gpu_models
    engine_ids += [e for e in all_engines if e not in engine_ids and any(k[1] == e for k in gpu_keys)]
    scores, qmeta = quality_by_tag(store, a2m)
    lap("quality_by_tag")
    # one list of tags for both tables: a tag with only quality scores still gets a results table, filled from earlier tags
    meta = dict(qmeta)
    for t, m in rmeta.items():
        meta[t] = {**m, "at": max(m["at"], qmeta[t]["at"])} if t in qmeta else m
    # a diagnostic run's tag (tpu-diag-*, a profiler or a timing A/B: its tok/s slowed on purpose) never reaches the
    # site: not as a release, and not as a fill for another tag's cells, where the newest run would otherwise win
    meta = {t: m for t, m in meta.items() if not is_diag_tag(t)}
    tags = sorted(({"id": t, "kind": m["kind"], "date": tag_date(t, m), "commit": m["commit"]} for t, m in meta.items()),
                  key=lambda x: x["date"] or "", reverse=True)  # the newest tag is the default on the site
    order = [x["id"] for x in tags]
    # the site's default order: engine, then model, then hardware, then workload
    grid = [(hw, e, m, c) for e in engine_ids for m in model_ids for hw in hardware_ids for c, _, _ in CATEGORIES if e in {x["id"] for x in mac_engines}]
    # a GPU setup the matrix declares unsupported (an engine's own bug or gap) reads unsupported with its reason,
    # even where an older engine release once measured it: one release of each engine per tag
    gpu_unsup = gpu_unsupported(a2m, gpu_ids, all_engines, config.get("benchmarks", []))
    grid += [(hw, e, m, c) for e in engine_ids for m in model_ids for hw in gpu_ids + phone_ids for c, _, _ in CATEGORIES if (hw, e, m, c) in gpu_keys]
    # only a number stands against a declared gap: an attempt that failed or never ran reads as unsupported
    measured = {k for rs in results.values() for k in rs}
    # a setup another engine measured on this GPU that the matrix declares unsupported for this one (a miniature's
    # engine gap too): its reason, not a blank
    setup_unsup = {k: r for k, r in gpu_unsupported_setups(a2m, gpu_ids, all_engines).items()
                   if k[2] in model_ids and k[1] in engine_ids and k not in measured
                   and any(g[0] == k[0] and g[2] == k[2] and g[3] == k[3] for g in gpu_keys)}
    grid += [k for k in setup_unsup if k not in gpu_keys]
    # a TPU the project cannot get at all (support.yaml: no access, no quota) has no runs, only its reasons
    tpus = {p["id"] for p in load("platforms")["platforms"] if p.get("backend") == "xla"}
    grid += [(hw, e, m, "raw") for hw, e, m in gpu_unsup
             if m in model_ids and (hw, e, m, "raw") not in gpu_keys and (hw in tpus or any(k[0] == hw for k in gpu_keys))]
    snaps = stack(order, results, grid, lambda item, key, src: as_row(item[1], key, src), lambda item: local(item[1]["started_at"]))
    lap("stack")
    # the Macs the site's grids measure, and every GPU or TPU setup a scheduled CI run launches (tagged with its runs)
    # the Macs the grids measure, every CI GPU and TPU, and every catalog accelerator; a CI Mac without a runner stays out
    hw_rows = [h for h in hardware(cores_by_platform(store)) if h["id"] in hardware_ids or h["class"] != "mac" or not h.get("runs")] + phone_rows
    misfits = no_fit(a2m, config, hw_rows, engine_ids, model_ids)
    # a GPU runs every engine on the same Hugging Face weights (bf16, MXFP4), not the Mac's 4-bit ones: its fit is
    # sized by the artifact the GPU runs actually loaded, so a 54 GB bf16 model reads "doesn't fit" on a 48 GB card
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
    # every combination of Mac, engine, model and workload has a row in every tag, on every Mac, run there or not:
    # its numbers, or why there are none (too big, unsupported, failed, not reached)
    # a setup no release has measured, earlier or later, has simply not been run yet
    ever = {(r["hardware"], r["engine"], r["model"], r["workload"]) for rows in snaps.values() for r in rows}
    for t in order:
        have = {(r["hardware"], r["engine"], r["model"], r["workload"]): r for r in snaps[t]}
        # a model run cut down to fit (a miniature) on a machine is never "does not fit" there for the other engines
        cut = {(r["hardware"], r["model"]) for r in snaps[t] if r.get("miniature")}
        tried = attempts.get(t, {})
        filled = []
        for key in grid:
            hw, engine, model, cat = key
            row = have.get(key)
            if row is not None and (hw, engine, model) in gpu_unsup:
                row = None  # an engine that cannot run this setup in this release: no older number stands in
            if row is not None:
                if row["stale"] and key in tried:  # the older numbers stand in; say what happened this time
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
    # every arm the release compares, on every task, has a row like the results table: its score, or "not run"
    arms = quality_arms(config)
    mismatched = mismatched_arms()
    tasks =[t["id"] for t in quality_tasks()]
    # quality runs on the big Mac: a missing score is explained the way the results table explains a missing number
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
        # an engine with no arm for a model still has its rows: too big, unsupported, or no data
        armed = {(eng, a2m.get(art, art)) for eng, art in arms}
        quality[t] += [missing(model, eng, "", task, t, "no_data")
                       for eng in engine_ids for model in model_ids if (eng, model) not in armed for task in tasks]
        # apples to apples: a competitor on other weights keeps its row, without a score
        quality[t] = [missing(r["model"], r["engine"], r["artifact"], r["task"], t, "unsupported") | {"note": mismatched[r["artifact"]]}
                      if r["artifact"] in mismatched else r for r in quality[t]]
        for r in quality[t]:
            r.setdefault("status", "pass")
        # the results page's order: engine, then model, then task
        rank = lambda xs, x: xs.index(x) if x in xs else len(xs)  # noqa: E731
        quality[t].sort(key=lambda r: (rank(engine_ids, r["engine"]), rank(model_ids, r["model"]), r["model"], rank(tasks, r["task"])))
    # parity is per tag and never stacked: a release's table holds only the scores that release measured
    parity = parity_by_tag(store, a2m)
    lap("parity_by_tag")
    checks = quality_checks(store, a2m)
    lap("quality_checks")
    # when the newest measurement or score was taken: the site's "Updated" line
    stamps = [r["started_at"] for r in store.table().select(["started_at"]).to_pylist() if r["started_at"] is not None]
    stamps += [datetime.fromisoformat(q["date"].replace("Z", "+00:00")) for q in store.quality() if q.get("date")]
    stamps = [t if t.tzinfo else t.replace(tzinfo=ZoneInfo("UTC")) for t in stamps]
    updated_at = max(stamps).isoformat() if stamps else None
    lap("max")
    # the welcome band's number: every benchmark run that ran, in every tag (a failed one too), and every quality eval
    ran = sum(r["status"] in ("pass", "noisy", "fail") for r in store.table().select(["status"]).to_pylist())
    # the machine time behind every measured cell, each run's own measured duration summed: the site's "days of compute"
    busy = sum(r["duration_s"] or 0 for r in store.table().select(["status", "duration_s"]).to_pylist() if r["status"] in ("pass", "noisy", "fail"))
    totals = {"runs": ran + len(store.quality()), "machine_s": round(busy)}
    db = {"updated_at": updated_at, "totals": totals, "tags": tags, "snapshots": snaps, "quality_snapshots": quality, "parity": {t: parity.get(t, []) for t in order},
          "quality_parity": checks["parity"], "quality_kernels": checks["kernels"], "quality_gaps": load("support").get("quality_gaps", []),
          "speed_gaps": load("support").get("speed_gaps", []),
          "no_fit": misfits, "suites": suite_ids,
          "hardware": hw_rows,
          # the Engines table lists every engine CI runs, the GPU-only ones (vLLM, SGLang) too; the grids keep to the Mac engines
          "engines": engines(), "models": [m for m in models if m["id"] in model_ids or m.get("catalog")],
          "workloads": workloads(), "install": install_sizes(), "quality_tasks": quality_tasks(), "quality": quality.get(order[0], []) if order else []}
    (WEB / "data").mkdir(parents=True, exist_ok=True)
    # db.js holds what the site draws first; every other tag is a file of its own, fetched when a page asks for it
    split_db.write(db, WEB / "data")
    print({k: len(v) for k, v in db.items() if hasattr(v, "__len__")}, {t["id"]: (len(snaps.get(t["id"]) or []), len(quality.get(t["id"]) or [])) for t in tags})
    print({t: {f: sum(1 for r in parity[t] if r["flag"] == f) for f in ("ok", "mismatch", "no_pie")} for t in parity})


if __name__ == "__main__":
    main()
