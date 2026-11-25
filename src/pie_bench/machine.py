from __future__ import annotations

import platform
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from pie_bench.plan.matrix import Matrix
from pie_bench.schema import PlatformSpec, Tier


@dataclass
class Machine:
    platform: PlatformSpec
    known: bool
    fingerprint: dict


def _run(cmd: list[str]) -> str:
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=60).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def _mac() -> tuple[str, float]:
    chip = ""
    for line in _run(["system_profiler", "SPHardwareDataType"]).splitlines():
        if line.strip().startswith("Chip:"):
            chip = line.split(":", 1)[1].strip()
    mem = _run(["sysctl", "-n", "hw.memsize"])
    return chip, round(int(mem) / 1024**3) if mem.isdigit() else 0


def _gpus() -> list[str]:
    out = _run(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"])
    return [ln for ln in out.splitlines() if ln.strip() and not _is_npu(ln)]


def _is_npu(gpu_line: str) -> bool:
    return "NPU" in gpu_line.split(",")[0]


def detect(m: Matrix, platform_id: str | None = None) -> Machine:
    fp = {"system": platform.system(), "machine": platform.machine(), "hostname": platform.node()}
    if platform_id:
        if platform_id not in m.platforms:
            raise SystemExit(f"unknown machine id {platform_id!r}; see `pie-bench machines`")
        return Machine(m.platforms[platform_id], True, fp)
    if platform.system() == "Darwin" and platform.machine() == "arm64":
        chip, mem = _mac()
        fp.update(chip=chip, memory_gib=mem)
        for p in m.platforms.values():
            if p.os == "macos" and p.accelerator == chip and round(p.memory_gib) == mem:
                return Machine(p, True, fp)
        slug = re.sub(r"[^a-z0-9]+", "-", chip.lower().replace("apple ", "")).strip("-") or "mac"
        gen = re.search(r"m(\d+)", slug)
        spec = PlatformSpec(
            id=f"{slug}-{mem}g",
            os="macos",
            backend="metal",
            accelerator=chip or "Apple Silicon",
            arch=f"apple{int(gen.group(1)) + 5}" if gen else "apple",
            memory_gib=mem,
            interconnect="uma",
            tiers=[Tier.SMOKE, Tier.NIGHTLY, Tier.WEEKLY],
        )
        m.platforms[spec.id] = spec
        return Machine(spec, False, fp)
    gpus = _gpus()
    fp["gpus"] = gpus
    if gpus:
        name = gpus[0].split(",")[0].strip().lower()
        for p in m.platforms.values():
            if (
                p.os == ("windows" if platform.system() == "Windows" else "linux")
                and p.count == len(gpus)
                and (p.accelerator.lower() in name or name in p.accelerator.lower())
            ):
                return Machine(p, True, fp)
    raise SystemExit(
        "this machine is not in the catalog yet; pass --machine <id> (see `pie-bench machines`)"
    )


def tier_for(machine: Machine) -> Tier:
    return Tier.TARGETED if machine.platform.os in ("macos", "windows") else Tier.NIGHTLY


def prerequisites(machine: Machine) -> list[str]:
    missing = []
    if not shutil.which("git"):
        missing.append("git (xcode-select --install)" if machine.platform.os == "macos" else "git")
    if not shutil.which("cargo") and not (Path.home() / ".cargo/bin/cargo").exists():
        missing.append("Rust: curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh")
    if not shutil.which("uv") and not (Path.home() / ".local/bin/uv").exists():
        missing.append("uv: curl -LsSf https://astral.sh/uv/install.sh | sh")
    return missing
