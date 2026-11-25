from __future__ import annotations

import math
from collections import defaultdict

PLATFORMS = {
    "mac": "Apple Silicon",
    "windows": "Windows PC",
    "nvidia": "NVIDIA GPU",
    "amd": "AMD GPU",
    "tpu": "Google TPU",
    "cerebras": "Cerebras",
    "web": "Browser",
    "android": "Mobile",
}
MEASURED = {"pass", "noisy"}


def platform_of(hw: dict) -> str | None:
    if hw.get("class") == "android":
        return "android"
    if hw.get("class") == "mac" or hw.get("vendor") == "Apple":
        return "mac"
    if hw.get("class") == "windows":
        return "windows"
    if hw.get("backend") == "xla":
        return "tpu"
    return {"NVIDIA": "nvidia", "AMD": "amd", "Cerebras": "cerebras"}.get(hw.get("vendor")) or (
        "web" if hw.get("class") == "web" else None
    )


def head_to_head(core: dict, workload: str = "raw", metric: str = "decode_tok_s") -> dict:
    tags = core.get("tags") or []
    snapshots = core.get("snapshots") or {}
    release = next((t["id"] for t in tags if snapshots.get(t["id"])), None)
    platform = {h["id"]: platform_of(h) for h in core.get("hardware") or []}
    names = {e["id"]: e.get("name", e["id"]) for e in core.get("engines") or []}
    best: dict[tuple[str, str], dict[str, float]] = defaultdict(dict)
    for row in snapshots.get(release) or []:
        value = row.get(metric)
        if (
            row.get("workload") != workload
            or row.get("status", "pass") not in MEASURED
            or not value
            or value <= 0
        ):
            continue
        cell = best[(row["hardware"], row["model"])]
        cell[row["engine"]] = max(cell.get(row["engine"], 0.0), float(value))
    logs: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    machines: dict[str, set] = defaultdict(set)
    for (hw, _model), engines in best.items():
        pid = platform.get(hw)
        if not pid or "pie" not in engines:
            continue
        for engine, value in engines.items():
            if engine != "pie":
                logs[pid][engine].append(math.log(engines["pie"] / value))
                machines[pid].add(hw)
    out = []
    for pid in PLATFORMS:
        if not logs.get(pid):
            continue
        rows = [
            {
                "id": e,
                "name": names.get(e, e),
                "speedup": round(math.exp(sum(v) / len(v)), 2),
                "pairs": len(v),
            }
            for e, v in logs[pid].items()
        ]
        out.append(
            {
                "id": pid,
                "name": PLATFORMS[pid],
                "machines": len(machines[pid]),
                "engines": sorted(rows, key=lambda r: r["speedup"]),
            }
        )
    return {
        "release": release,
        "updated_at": core.get("updated_at"),
        "workload": "Single Decode",
        "metric": "decode tokens per second",
        "summary": "geometric mean, over every machine and model both engines ran, of pie's speed over the engine's",
        "platforms": out,
    }
