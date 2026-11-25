from __future__ import annotations

import argparse
import os
import re
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(os.environ.get("PIE_ROOT") or Path.home() / "pie").resolve()


def resolve_local_model(model: str) -> str:
    candidate = Path(model).expanduser()
    if candidate.exists():
        return str(candidate.resolve())
    pie_home = Path(os.environ.get("PIE_HOME", "~/.pie")).expanduser()
    for slug in (model, model.replace("/", "--")):
        art_dir = pie_home / "artifacts" / slug
        if art_dir.is_dir() and any(art_dir.glob("*.zt")):
            return model
    encoded = f"models--{model.replace('/', '--')}"
    roots = []
    if cache := os.environ.get("HF_HUB_CACHE"):
        roots.append(Path(cache).expanduser())
    if home := os.environ.get("HF_HOME"):
        roots.append(Path(home).expanduser() / "hub")
    roots.extend(
        (
            Path(os.environ.get("XDG_CACHE_HOME", "~/.cache")).expanduser()
            / "huggingface"
            / "hub",
            Path("~/.pie/programs").expanduser(),
        )
    )
    for root in roots:
        repository = root / encoded
        revision = None
        for ref_name in ("main", "master"):
            ref = repository / "refs" / ref_name
            if ref.is_file():
                revision = ref.read_text().strip()
                break
        if revision:
            snapshot = repository / "snapshots" / revision
            if snapshot.is_dir():
                return str(snapshot.resolve())
    raise FileNotFoundError(
        f"no local snapshot for {model!r}; download it before benchmarking"
    )


def gpu_clock_state() -> list[dict[str, Any]]:
    try:
        out = subprocess.run(
            ["nvidia-smi",
             "--query-gpu=index,clocks.sm,clocks.max.sm,utilization.gpu",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5, check=True).stdout
    except Exception:
        return []
    state = []
    for line in out.strip().splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) != 4:
            continue
        try:
            state.append({
                "index": int(parts[0]),
                "sm_mhz": int(parts[1]),
                "sm_max_mhz": int(parts[2]),
                "util_pct": int(parts[3]),
            })
        except ValueError:
            continue
    return state


def _parse_cpu_list(spec: str) -> set[int]:
    cpus: set[int] = set()
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            lo, hi = part.split("-", 1)
            cpus.update(range(int(lo), int(hi) + 1))
        else:
            cpus.add(int(part))
    return cpus


def _format_cpu_list(cpus: set[int]) -> str:
    if not cpus:
        return ""
    xs = sorted(cpus)
    ranges: list[str] = []
    start = prev = xs[0]
    for x in xs[1:]:
        if x == prev + 1:
            prev = x
            continue
        ranges.append(f"{start}-{prev}" if start != prev else str(start))
        start = prev = x
    ranges.append(f"{start}-{prev}" if start != prev else str(start))
    return ",".join(ranges)


def _numa_node_cpus(node: int) -> set[int]:
    try:
        text = Path(
            f"/sys/devices/system/node/node{node}/cpulist").read_text()
    except OSError:
        return set()
    return _parse_cpu_list(text.strip())


def gpu_local_cpu_affinity(gpu_ids: list[int]) -> set[int]:
    if not gpu_ids:
        return set()
    try:
        topo = subprocess.check_output(
            ["nvidia-smi", "topo", "-m"],
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        return set()
    ansi = re.compile(r"\x1b\[[0-9;]*m")
    lines = [ansi.sub("", line).strip() for line in topo.splitlines() if line.strip()]
    if not lines:
        return set()
    header = lines[0].split()
    gpu_cols = sum(1 for tok in header if re.fullmatch(r"(?:GPU|NIC)\d+", tok))
    affinity_by_gpu: dict[int, set[int]] = {}
    numa_by_gpu: dict[int, int] = {}
    for line in lines[1:]:
        toks = line.split()
        if len(toks) <= gpu_cols + 1 or not re.fullmatch(r"GPU\d+", toks[0]):
            continue
        gpu = int(toks[0][3:])
        affinity_by_gpu[gpu] = _parse_cpu_list(toks[1 + gpu_cols])
        if len(toks) > gpu_cols + 2:
            try:
                numa_by_gpu[gpu] = int(toks[2 + gpu_cols])
            except ValueError:
                pass
    cpus: set[int] = set()
    for gpu in gpu_ids:
        node = numa_by_gpu.get(gpu)
        node_cpus = _numa_node_cpus(node) if node is not None else set()
        cpus.update(node_cpus or affinity_by_gpu.get(gpu, set()))
    if hasattr(os, "sched_getaffinity"):
        cpus &= set(os.sched_getaffinity(0))
    return cpus


def visible_cuda_devices(tp_size: int, dp_size: int = 1) -> list[int]:
    world = max(1, tp_size) * max(1, dp_size)
    visible = os.environ.get("CUDA_VISIBLE_DEVICES")
    if visible:
        ids: list[int] = []
        for item in visible.split(","):
            item = item.strip()
            if item.isdigit():
                ids.append(int(item))
        if ids:
            return ids[:world]
    return list(range(world))


def maybe_set_cpu_affinity(args: argparse.Namespace, gpu_ids: list[int]) -> str | None:
    mode = getattr(args, "cpu_affinity", "auto")
    if mode in (None, "", "none") or not hasattr(os, "sched_setaffinity"):
        return None
    cpus = gpu_local_cpu_affinity(gpu_ids) if mode == "auto" else _parse_cpu_list(mode)
    if not cpus or not hasattr(os, "sched_setaffinity"):
        return None
    os.sched_setaffinity(0, cpus)
    return _format_cpu_list(cpus)
