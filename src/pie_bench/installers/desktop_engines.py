from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tarfile
import urllib.request
from io import BytesIO
from pathlib import Path

from pie_bench.paths import HOME
from pie_bench.plan.matrix import Matrix
from pie_bench.schema import JobSpec

MAC_ENGINES = ("pie", "llamacpp", "mlxlm", "splash")
WINDOWS_ENGINES = ("pie", "llamacpp", "ollama")
MLX_VLM_PIN = "0.7.11"


def _venv(path: Path, packages: list[str], log) -> Path:
    py = path / "Scripts" / "python.exe" if os.name == "nt" else path / "bin" / "python"
    if not py.exists():
        log(f"installing {' '.join(packages)}")
        subprocess.run(["uv", "venv", "--quiet", "--python", "3.12", str(path)], check=True)
        subprocess.run(
            ["uv", "pip", "install", "--quiet", "--python", str(py), *packages], check=True
        )
    return py


def _untar(url: str, dest: Path, log) -> None:
    log(f"downloading {url}")
    dest.mkdir(parents=True, exist_ok=True)
    with (
        urllib.request.urlopen(url, timeout=600) as r,
        tarfile.open(fileobj=BytesIO(r.read()), mode="r:gz") as t,
    ):
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
        env["MLX_VLM_PY"] = str(
            _venv(base / f"mlx-vlm-{MLX_VLM_PIN}", [f"mlx-vlm=={MLX_VLM_PIN}"], log)
        )
    if "llamacpp" in want:
        pin = job.baseline_versions.get("llamacpp") or m.engines["llamacpp"].pin
        d = base / f"llama-{pin}"
        if not (d / "llama-server").exists():
            _untar(
                f"https://github.com/ggml-org/llama.cpp/releases/download/{pin}/llama-{pin}-bin-macos-arm64.tar.gz",
                d,
                log,
            )
        env["LLAMA_SERVER_BIN"] = str(d / "llama-server")
        env.setdefault("LLAMACPP_PY", str(_venv(base / "llamacpp-client", ["transformers"], log)))
    if "splash" in want:
        pin = job.baseline_versions.get("splash") or m.engines["splash"].pin
        d = base / f"splash-{pin}"
        launcher = d / "bin" / "splash"
        if not launcher.exists():
            _untar(
                f"https://github.com/incoai/splash/releases/download/{pin}/splash-{pin}-arm64-macos26.tar.gz",
                d,
                log,
            )
            launcher.parent.mkdir(parents=True, exist_ok=True)
            launcher.write_text(
                f'#!/bin/sh\nexport PYTHONDONTWRITEBYTECODE=1\nexec "{d}/python/bin/python3" -u "{d}/install/launcher.py" "$@"\n'
            )
            launcher.chmod(0o755)
        if subprocess.run([str(launcher), "--version"], capture_output=True).returncode == 0:
            env["SPLASH_BIN"] = str(launcher)
        else:
            log(
                f"splash {pin} needs macOS 26.4 or newer; its cells will be recorded as failed to load"
            )
    return env


def _unzip(url: str, dest: Path, log) -> None:
    import zipfile

    log(f"downloading {url}")
    dest.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url, timeout=1800) as r, zipfile.ZipFile(BytesIO(r.read())) as z:
        z.extractall(dest)


def _windows_engines(m: Matrix, want: set[str], base: Path, log) -> dict[str, str]:
    env: dict[str, str] = {}
    if "llamacpp" in want or "ollama" in want:
        pin = m.engines["llamacpp"].pin
        d = base / f"llama-{pin}-win-cuda-arm64"
        if not (d / "llama-server.exe").exists():
            rel = f"https://github.com/ggml-org/llama.cpp/releases/download/{pin}"
            cuda = re.search(
                r"win-cuda-([0-9.]+)-arm64", json.dumps(_gh_release("ggml-org/llama.cpp", pin))
            )
            if not cuda:
                raise SystemExit(f"llama.cpp {pin} ships no Windows Arm64 CUDA build")
            _unzip(f"{rel}/llama-{pin}-bin-win-cuda-{cuda.group(1)}-arm64.zip", d, log)
            _unzip(f"{rel}/cudart-llama-bin-win-cuda-{cuda.group(1)}-arm64.zip", d, log)
        env["LLAMA_SERVER_BIN"] = str(d / "llama-server.exe")
        env.setdefault(
            "LLAMACPP_PY", str(_venv(base / "llamacpp-client", ["transformers", "psutil"], log))
        )
    if "ollama" in want:
        pin = m.engines["ollama"].pin
        d = base / f"ollama-{pin}"
        if not (d / "ollama.exe").exists():
            _unzip(
                f"https://github.com/ollama/ollama/releases/download/v{pin}/ollama-windows-arm64.zip",
                d,
                log,
            )
        env["OLLAMA_BIN"] = str(d / "ollama.exe")
    return env


def _gh_release(repo: str, tag: str) -> dict:
    req = urllib.request.Request(
        f"https://api.github.com/repos/{repo}/releases/tags/{tag}",
        headers={"Accept": "application/vnd.github+json"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())
