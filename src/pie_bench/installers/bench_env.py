from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from pie_bench.paths import CLIENTS

BENCH_DEPS = ["websockets", "msgpack", "blake3", "cryptography", "numpy", "transformers", "jinja2", "tiktoken"]


if os.name == "nt":  # cryptography has no Windows Arm64 wheel and nothing in the bench imports it
    BENCH_DEPS = [d for d in BENCH_DEPS if d != "cryptography"] + ["psutil"]


DEFAULT_CACHE = Path.home() / ".cache/pie-bench"


def _cache_root(root: Path | None) -> Path:
    return root or Path(os.environ.get("PIE_BENCH_CACHE", DEFAULT_CACHE))


def bench_python(cache_root: Path | None = None, log=print) -> Path:
    venv = _cache_root(cache_root) / "venv-pie"
    py = venv / "Scripts" / "python.exe" if os.name == "nt" else venv / "bin" / "python"
    if not py.exists():
        log(f"venv: creating {venv}")
        if shutil.which("uv"):
            subprocess.run(["uv", "venv", "--quiet", "--python", "3.12", str(venv)], check=True)
        else:
            subprocess.run(["python3", "-m", "venv", str(venv)], check=True)
        _pip_install(py, BENCH_DEPS)
    elif subprocess.run([str(py), "-c", "import transformers, jinja2, tiktoken"], capture_output=True).returncode != 0:
        log(f"venv: adding the bench client deps to {venv}")
        _pip_install(py, BENCH_DEPS)
    return py


def _pip_install(py: Path, args: list[str]) -> None:
    if shutil.which("uv"):
        subprocess.run(["uv", "pip", "install", "--quiet", "--python", str(py), *args], check=True)
    else:
        subprocess.run([str(py), "-m", "pip", "install", "-q", *args], check=True)


BENCH_DIR = CLIENTS


def bench_dir() -> Path:
    return Path(os.environ.get("PIE_BENCH_BENCH_DIR") or BENCH_DIR)
