from __future__ import annotations

import json
import os
import platform
import re
import shutil
import subprocess
import tarfile
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path

from pie_bench.paths import CONFIG
from pie_bench.plan.jobs import make_jobs
from pie_bench.plan.matrix import Matrix
from pie_bench.plan.suites import all_models, load_config, suite_models
from pie_bench.schema import JobSpec, PlatformSpec, Tier

HOME = Path(os.environ.get("PIE_BENCH_HOME") or Path.home() / ".pie-bench")
PIE_REPO = "pie-project/pie"
MAC_ENGINES = ("pie", "llamacpp", "mlxlm", "splash")
WINDOWS_ENGINES = ("pie", "llamacpp", "ollama")
MLX_VLM_PIN = "0.7.11"


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
    return [ln for ln in out.splitlines() if ln.strip() and "NPU" not in ln.split(",")[0]]  # RTX Spark lists its NPU too


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
        spec = PlatformSpec(id=f"{slug}-{mem}g", os="macos", backend="metal", accelerator=chip or "Apple Silicon",
                            arch=f"apple{int(gen.group(1)) + 5}" if gen else "apple", memory_gib=mem, interconnect="uma",
                            tiers=[Tier.SMOKE, Tier.NIGHTLY, Tier.WEEKLY])
        m.platforms[spec.id] = spec
        return Machine(spec, False, fp)
    gpus = _gpus()
    fp["gpus"] = gpus
    if gpus:
        name = gpus[0].split(",")[0].strip().lower()
        for p in m.platforms.values():
            if p.os == ("windows" if platform.system() == "Windows" else "linux") and p.count == len(gpus) and (p.accelerator.lower() in name or name in p.accelerator.lower()):
                return Machine(p, True, fp)
    raise SystemExit("this machine is not in the catalog yet; pass --machine <id> (see `pie-bench machines`)")


def tier_for(machine: Machine) -> Tier:
    return Tier.TARGETED if machine.platform.os in ("macos", "windows") else Tier.NIGHTLY


def _gh(path: str) -> dict:
    req = urllib.request.Request(f"https://api.github.com/repos/{PIE_REPO}/{path}", headers={"Accept": "application/vnd.github+json"})
    if os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN"):
        req.add_header("Authorization", f"Bearer {os.environ.get('GH_TOKEN') or os.environ.get('GITHUB_TOKEN')}")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def resolve_pie(ref: str | None) -> tuple[str, str]:
    if not ref or ref == "latest":
        ref = _gh("releases/latest")["tag_name"]
    sha = _gh(f"commits/{ref}")["sha"]
    tag = ref if re.fullmatch(r"v?\d+\.\d+\.\d+.*", ref) else f"manual-{datetime.now(timezone.utc):%Y%m%d-%H%M}"
    return sha, tag.lstrip("v")


def arms(m: Matrix, models: list[str] | None, suite: str, mac: bool = True) -> list[str]:
    config = load_config(CONFIG)
    pool = (all_models(config) if models else suite_models(config, suite)) if mac else [a.id for a in m.artifacts.values()]
    match = lambda a: any(q.lower() in a.id.lower() or q.lower() in (a.base_model or "").lower() for q in models or [])
    wanted = {a for a in pool if a in m.artifacts and (not models or match(m.artifacts[a]))}
    pie = {m.artifacts[a].baseline_of for a in wanted if m.artifacts[a].baseline_of}
    return sorted({a.id for a in m.artifacts.values() if a.id in wanted or a.id in pie or (a.id not in pie and a.baseline_of in wanted)})


def plan(m: Matrix, machine: Machine, *, pie_commit: str, models: list[str] | None, engines: list[str] | None,
         workloads: list[str] | None, suite: str, tier: Tier | None = None) -> JobSpec | None:
    tier = tier or tier_for(machine)
    config = load_config(CONFIG)
    laptop = machine.platform.os in ("macos", "windows")
    ids = arms(m, models, suite, laptop) if laptop or models else None
    cells = m.expand(platforms=[machine.platform.id], artifacts=ids)
    wls = set(workloads or config.get("benchmarks") or [])
    if wls:
        cells = [c for c in cells if c.workload.id in wls or str(c.workload.kind) == "control_aa"]
    if machine.platform.os == "macos":
        engines = engines or list(MAC_ENGINES)
    elif machine.platform.os == "windows":
        engines = engines or list(WINDOWS_ENGINES)
    jobs = make_jobs(m, tier, pie_commit=pie_commit, platforms=[machine.platform.id], engines=engines, cells=cells, label="local")
    if not jobs:
        return None
    first = jobs[0]
    return first.model_copy(update={"cells": [c for j in jobs for c in j.cells], "shard": 0,
                                    "est_minutes": sum(j.est_minutes for j in jobs),
                                    "kill_s": sum(j.kill_s for j in jobs), "budget_s": sum(j.budget_s for j in jobs)})


def _venv(path: Path, packages: list[str], log) -> Path:
    py = path / "Scripts" / "python.exe" if os.name == "nt" else path / "bin" / "python"
    if not py.exists():
        log(f"installing {' '.join(packages)}")
        subprocess.run(["uv", "venv", "--quiet", "--python", "3.12", str(path)], check=True)
        subprocess.run(["uv", "pip", "install", "--quiet", "--python", str(py), *packages], check=True)
    return py


def _untar(url: str, dest: Path, log) -> None:
    log(f"downloading {url}")
    dest.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url, timeout=600) as r, tarfile.open(fileobj=BytesIO(r.read()), mode="r:gz") as t:
        for member in t.getmembers():
            parts = Path(member.name).parts[1:]
            if not parts:
                continue
            member.name = str(Path(*parts))
            t.extract(member, dest, filter="data")


def setup_engines(m: Matrix, job: JobSpec, log=print) -> dict[str, str]:
    env: dict[str, str] = {}
    want = {str(c.engine) for c in job.cells}
    base = HOME / "engines"
    if job.cells and job.cells[0].platform.os == "windows":
        return _windows_engines(m, want, base, log)
    if job.cells and job.cells[0].platform.os != "macos":
        return env
    if not shutil.which("uv"):
        raise SystemExit("pie-bench needs uv: curl -LsSf https://astral.sh/uv/install.sh | sh")
    if "mlxlm" in want:
        pin = job.baseline_versions.get("mlxlm") or m.engines["mlxlm"].pin
        env["MLX_PY"] = str(_venv(base / f"mlx-lm-{pin}", [f"mlx-lm=={pin}", "transformers"], log))
        env["LLAMACPP_PY"] = env["MLX_PY"]
        env["MLX_VLM_PY"] = str(_venv(base / f"mlx-vlm-{MLX_VLM_PIN}", [f"mlx-vlm=={MLX_VLM_PIN}"], log))
    if "llamacpp" in want:
        pin = job.baseline_versions.get("llamacpp") or m.engines["llamacpp"].pin
        d = base / f"llama-{pin}"
        if not (d / "llama-server").exists():
            _untar(f"https://github.com/ggml-org/llama.cpp/releases/download/{pin}/llama-{pin}-bin-macos-arm64.tar.gz", d, log)
        env["LLAMA_SERVER_BIN"] = str(d / "llama-server")
        env.setdefault("LLAMACPP_PY", str(_venv(base / "llamacpp-client", ["transformers"], log)))
    if "splash" in want:
        pin = job.baseline_versions.get("splash") or m.engines["splash"].pin
        d = base / f"splash-{pin}"
        launcher = d / "bin" / "splash"
        if not launcher.exists():
            _untar(f"https://github.com/incoai/splash/releases/download/{pin}/splash-{pin}-arm64-macos26.tar.gz", d, log)
            launcher.parent.mkdir(parents=True, exist_ok=True)
            launcher.write_text(f'#!/bin/sh\nexport PYTHONDONTWRITEBYTECODE=1\nexec "{d}/python/bin/python3" -u "{d}/install/launcher.py" "$@"\n')
            launcher.chmod(0o755)
        if subprocess.run([str(launcher), "--version"], capture_output=True).returncode == 0:
            env["SPLASH_BIN"] = str(launcher)
        else:
            log(f"splash {pin} needs macOS 26.4 or newer; its cells will be recorded as failed to load")
    return env


def _unzip(url: str, dest: Path, log) -> None:
    import zipfile

    log(f"downloading {url}")
    dest.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url, timeout=1800) as r, zipfile.ZipFile(BytesIO(r.read())) as z:
        z.extractall(dest)


def _windows_engines(m: Matrix, want: set[str], base: Path, log) -> dict[str, str]:
    env: dict[str, str] = {}
    if "llamacpp" in want or "ollama" in want:  # Ollama merges split GGUFs with llama.cpp's gguf-split
        pin = m.engines["llamacpp"].pin
        d = base / f"llama-{pin}-win-cuda-arm64"
        if not (d / "llama-server.exe").exists():
            rel = f"https://github.com/ggml-org/llama.cpp/releases/download/{pin}"
            cuda = re.search(r"win-cuda-([0-9.]+)-arm64", json.dumps(_gh_release("ggml-org/llama.cpp", pin)))
            if not cuda:
                raise SystemExit(f"llama.cpp {pin} ships no Windows Arm64 CUDA build")
            _unzip(f"{rel}/llama-{pin}-bin-win-cuda-{cuda.group(1)}-arm64.zip", d, log)
            _unzip(f"{rel}/cudart-llama-bin-win-cuda-{cuda.group(1)}-arm64.zip", d, log)
        env["LLAMA_SERVER_BIN"] = str(d / "llama-server.exe")
        env.setdefault("LLAMACPP_PY", str(_venv(base / "llamacpp-client", ["transformers", "psutil"], log)))
    if "ollama" in want:
        pin = m.engines["ollama"].pin
        d = base / f"ollama-{pin}"
        if not (d / "ollama.exe").exists():
            _unzip(f"https://github.com/ollama/ollama/releases/download/v{pin}/ollama-windows-arm64.zip", d, log)
        env["OLLAMA_BIN"] = str(d / "ollama.exe")
    return env


def _gh_release(repo: str, tag: str) -> dict:
    req = urllib.request.Request(f"https://api.github.com/repos/{repo}/releases/tags/{tag}", headers={"Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def prerequisites(machine: Machine) -> list[str]:
    missing = []
    if not shutil.which("git"):
        missing.append("git (xcode-select --install)" if machine.platform.os == "macos" else "git")
    if not shutil.which("cargo") and not (Path.home() / ".cargo/bin/cargo").exists():
        missing.append("Rust: curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh")
    if not shutil.which("uv") and not (Path.home() / ".local/bin/uv").exists():
        missing.append("uv: curl -LsSf https://astral.sh/uv/install.sh | sh")
    return missing
