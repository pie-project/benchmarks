from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from pie_bench.paths import CLIENTS

BENCH_DEPS = [
    "websockets",
    "msgpack",
    "blake3",
    "cryptography",
    "numpy",
    "transformers",
    "jinja2",
    "tiktoken",
]
if os.name == "nt":
    BENCH_DEPS = [d for d in BENCH_DEPS if d != "cryptography"] + ["psutil"]


def cache_root(root: Path | None = None) -> Path:
    return root or Path(os.environ.get("PIE_BENCH_CACHE", Path.home() / ".cache/pie-bench"))


def bench_python(root: Path | None = None, log=print) -> Path:
    venv = cache_root(root) / "venv-pie"
    py = venv / "Scripts" / "python.exe" if os.name == "nt" else venv / "bin" / "python"
    if not py.exists():
        log(f"venv: creating {venv}")
        if shutil.which("uv"):
            subprocess.run(["uv", "venv", "--quiet", "--python", "3.12", str(venv)], check=True)
        else:
            subprocess.run(["python3", "-m", "venv", str(venv)], check=True)
        pip_install(py, BENCH_DEPS)
    elif (
        subprocess.run(
            [str(py), "-c", "import transformers, jinja2, tiktoken"], capture_output=True
        ).returncode
        != 0
    ):
        log(f"venv: adding the bench client deps to {venv}")
        pip_install(py, BENCH_DEPS)
    return py


def pip_install(py: Path, args: list[str], timeout: float | None = None) -> None:
    if shutil.which("uv"):
        cmd = ["uv", "pip", "install", "--quiet", "--python", str(py), *args]
    else:
        cmd = [str(py), "-m", "pip", "install", "-q", *args]
    subprocess.run(cmd, check=True, timeout=timeout)


BENCH_DIR = CLIENTS


def bench_dir() -> Path:
    return Path(os.environ.get("PIE_BENCH_BENCH_DIR") or BENCH_DIR)
