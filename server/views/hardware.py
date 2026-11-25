from __future__ import annotations

import json
import re

from server.views.matrix_files import load


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
        win = p.get("os") == "windows"
        c = by_id.get(p.get("catalog")) or by_runpod.get(p.get("runpod_gpu_type")) or {}
        used.add(c.get("id"))
        base = row(c) if c else {}
        rows.append({
            **base,
            "id": p["id"],
            "resource": "Community" if p.get("contributed") else "Pie self-hosted" if mac or win else ("Google Cloud" if p.get("backend") == "xla" else "RunPod cloud"),
            "name": (p["accelerator"] if mac else c.get("short") or p["accelerator"].replace("NVIDIA ", ""))
                    + (f" ×{p['count']}" if p.get("count", 1) > 1 else ""),
            "class": "mac" if mac else "windows" if win else ("tpu" if p.get("backend") == "xla" else "web" if p.get("backend") == "webgpu" else "gpu"), "location": "local" if mac or win else "cloud",
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
