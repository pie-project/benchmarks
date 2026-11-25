from __future__ import annotations

import re

from pie_bench.plan.suites import suites
from server.views.matrix_files import load

MOE_FAMILIES = {"gpt_oss", "qwen4_exp"}
BYTES_PER_WEIGHT = {"bf16": 2, "fp8": 1, "mxfp8": 1, "mxfp4": 0.53, "int4": 0.5625, "nvfp4": 0.5625}
NODE_GB = {"GPU": 8 * 288, "AMD": 8 * 192, "TPU": 4 * 95}


def model_name(base: str) -> str:
    drop = {
        "4bit",
        "bf16",
        "gguf",
        "mlx",
        "mxfp4",
        "q4",
        "q4km",
        "mtp",
        "instruct",
        "it",
        "base",
        "8k",
        "mini5",
        "mini8",
        "litert",
        "lm",
        "mlc",
        "q4f16_1",
        "q4f32_1",
    }
    tail = re.sub(r"^[a-z-]+\.", "", base.split("/")[-1])
    return "-".join(p for p in tail.split("-") if p.lower() not in drop)


def gib_at_4_5_bits(params_b: float) -> float:
    return round(params_b * 1e9 * 4.5 / 8 / 2**30, 1)


def artifact_to_model() -> tuple[dict[str, str], list[dict]]:
    catalog = load("models")
    by_model: dict[str, dict] = {}
    mapping = {}
    for a in catalog["artifacts"]:
        mapping[a["id"]] = add_artifact(by_model, a)
    for row in by_model.values():
        derive_shape(row)
    for c in catalog.get("catalog") or []:
        add_catalog_entry(by_model, c)
    for mid, name in (catalog.get("names") or {}).items():
        if mid in by_model:
            by_model[mid]["name"] = name
    return mapping, list(by_model.values())


def add_artifact(by_model: dict[str, dict], a: dict) -> str:
    base = a.get("base_model") or a["id"]
    mid = model_name(base).lower()
    row = by_model.setdefault(
        mid,
        {
            "id": mid,
            "name": model_name(base),
            "family": a.get("family"),
            "base_model": base,
            "schemes": set(),
            "artifacts": 0,
        },
    )
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
    return mid


def derive_shape(row: dict) -> None:
    name = row["name"]
    sizes = re.findall(r"(\d+(?:\.\d+)?)b", name, re.I)
    active = re.search(r"a(\d+(?:\.\d+)?)b", name, re.I)
    row["params_b"] = row.pop("params_b_stated", None) or (float(sizes[0]) if sizes else None)
    row["active_b"] = row.pop("active_b_stated", None) or (
        float(active.group(1)) if active else row["params_b"]
    )
    moe = (
        active
        or row["active_b"] != row["params_b"]
        or "moe" in (row["family"] or "")
        or row["family"] in MOE_FAMILIES
    )
    row["architecture"] = "MoE" if moe else "dense"
    row["ssd_streaming"] = "Without" if row["architecture"] == "MoE" else "n/a"
    row["schemes"] = ", ".join(sorted(row["schemes"]))
    row["draft"] = "true" if row.get("draft") else "false"
    row["size_gib"] = gib_at_4_5_bits(row["params_b"]) if row["params_b"] else None
    row["needs_gib"] = round(row["size_gib"] * 1.25, 1) if row["size_gib"] else None
    row.setdefault("context", None)
    row["license"] = None


def add_catalog_entry(by_model: dict[str, dict], c: dict) -> None:
    mid = model_name(c["base_model"]).lower() if c.get("base_model") else c["name"].lower()
    row = by_model.get(mid)
    if row is None:
        row = by_model[mid] = {
            "id": mid,
            "name": c["name"],
            "family": c.get("family"),
            "base_model": c.get("base_model"),
            "schemes": c.get("precision") or "",
            "artifacts": 0,
            "draft": "true" if c.get("mtp") else "false",
            "catalog_only": True,
        }
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
    smaller_active = (row.get("active_b") or 0) < (row.get("params_b") or 0)
    row["architecture"] = "MoE" if smaller_active else row.get("architecture") or "dense"
    row["ssd_streaming"] = "Without" if row["architecture"] == "MoE" else "n/a"
    if row.get("params_b"):
        row["size_gib"] = gib_at_4_5_bits(row["params_b"])
        row["needs_gib"] = round(row["size_gib"] * 1.25, 1)
        need = row["params_b"] * BYTES_PER_WEIGHT.get(str(c.get("precision") or "bf16"), 2) * 1.25
        row["fits"] = ", ".join(t for t, gb in NODE_GB.items() if need <= gb)


def suite_model_ids(config: dict, a2m: dict[str, str]) -> dict[str, list[str]]:
    arts = {a["id"]: a for a in load("models")["artifacts"]}
    out = {}
    for name, arms in suites(config).items():
        ids = [a for aid in arms for a in (aid, arts.get(aid, {}).get("baseline_of")) if a in a2m]
        out[name] = sorted({a2m[a] for a in ids})
    return out
