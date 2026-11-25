from __future__ import annotations

import os
import re
import shutil
import subprocess
import urllib.request
from pathlib import Path

from pie_bench.installers.cuda_toolkit import (
    ensure_cuda_devkit,
    ensure_flashinfer_aot,
    ensure_mpi,
    ensure_nvrtc_matches_toolkit,
    ensure_pip_nvcc_matches_cudart,
    ensure_python_headers,
)

SPECS = {
    "vllm": lambda v: [f"vllm=={v}"],
    "sglang": lambda v: [f"sglang[all]=={v}"],
    "trtllm": lambda v: [f"tensorrt-llm=={v}"],
}

BACKEND_SPECS = {
    ("vllm", "xla"): lambda v: [f"vllm-tpu=={v}"],
    ("sglang", "xla"): lambda v: [f"sglang-jax[tpu] @ git+https://github.com/sgl-project/sglang-jax@{v[4:]}#subdirectory=python", "torch", "torchvision"]
                                 if v.startswith("git-") else [f"sglang-jax[tpu]=={v}"],
    ("vllm", "rocm"): lambda v: [f"vllm=={rocm_vllm_version(v)}"],
    ("sglang", "rocm"): lambda v: [],
}

VLLM_ROCM_INDEX = "https://wheels.vllm.ai/rocm"


def rocm_vllm_variant(version: str) -> str:
    with urllib.request.urlopen(f"{VLLM_ROCM_INDEX}/{version}/", timeout=60) as r:
        found = re.findall(r'href="(rocm\d+)/"', r.read().decode())
    if not found:
        raise RuntimeError(f"vLLM {version} has no ROCm wheel index at {VLLM_ROCM_INDEX}/{version}/")
    return sorted(found)[-1]


def rocm_vllm_version(version: str) -> str:
    return f"{version}+{rocm_vllm_variant(version)}"


BACKEND_UV_FLAGS = {
    ("vllm", "xla"): ["--torch-backend", "cpu"],
    ("sglang", "xla"): ["--torch-backend", "cpu"],
}


def _uv_flags(engine: str, backend: str | None, version: str) -> list[str]:
    if engine == "trtllm":
        return ["--extra-index-url", "https://pypi.nvidia.com", "--index-strategy", "unsafe-best-match", "--prerelease", "if-necessary-or-explicit"]
    key = _backend_key(engine, backend)
    if key == ("vllm", "rocm"):
        return ["--extra-index-url", f"{VLLM_ROCM_INDEX}/{version}/{rocm_vllm_variant(version)}", "--index-strategy", "unsafe-best-match"]
    return BACKEND_UV_FLAGS.get(key, []) if key else []


def cache_root(root: Path | None = None) -> Path:
    return root or Path(os.environ.get("PIE_BENCH_CACHE", Path.home() / ".cache/pie-bench"))


def _backend_key(engine: str, backend: str | None) -> tuple[str, str] | None:
    key = (engine, str(backend or ""))
    return key if key in BACKEND_SPECS else None


def venv_dir(engine: str, version: str, root: Path | None = None, backend: str | None = None) -> Path:
    tag = ("-tpu" if backend == "xla" else f"-{backend}") if _backend_key(engine, backend) else ""
    return cache_root(root) / f"venv-{engine}{tag}-{version}"


def baseline_python(engine: str, version: str, root: Path | None = None, backend: str | None = None) -> Path | None:
    d = venv_dir(engine, version, root, backend)
    return d / "bin" / "python" if (d / ".ok").exists() else None


def image_python() -> str:
    for c in ("/opt/venv/bin/python3", "/usr/bin/python3"):
        if Path(c).exists() and subprocess.run([c, "-c", "import sglang"], capture_output=True, timeout=300).returncode == 0:
            return c
    return shutil.which("python3") or "python3"


def _image_sglang(d: Path, version: str, log=print) -> Path:
    base = image_python()
    have = subprocess.run([base, "-c", "import sglang; print(sglang.__version__)"], capture_output=True, text=True, timeout=300).stdout.strip()
    if have.lstrip("v") != version.lstrip("v"):
        raise RuntimeError(f"the pod image carries sglang {have or 'none'}, the run pins {version}: launch the pod on lmsysorg/sglang:v{version}-rocm*")
    log(f"baseline: sglang {have} from the pod image ({base})")
    (d / "bin").mkdir(parents=True, exist_ok=True)
    py = d / "bin" / "python"
    py.write_text(f'#!/bin/sh\nexec {base} "$@"\n')
    py.chmod(0o755)
    (d / ".ok").write_text(version + "\n")
    return py


def ensure_fork(engine: str, version: str, py: Path, log=print, backend: str | None = None) -> str | None:
    from pie_bench.engines.recipes import recipe_fork

    fork = recipe_fork(engine)
    if not fork:
        return None
    branch = os.environ.get(f"PIE_BENCH_FORK_BRANCH_{engine.upper()}") or f"pie-bench/v{version}"
    try:
        head = subprocess.run(["git", "ls-remote", f"https://github.com/{fork['repo']}", f"refs/heads/{branch}"],
                              capture_output=True, text=True, check=True, timeout=60).stdout.split()
    except (OSError, subprocess.SubprocessError) as e:
        raise RuntimeError(f"{engine}: cannot read fork {fork['repo']} {branch}: {e}") from e
    if not head:
        return None
    sha = head[0]
    site = Path(subprocess.run([str(py), "-c", f"import importlib.util, os; print(os.path.dirname(os.path.dirname(importlib.util.find_spec('{engine}').origin)))"],
                               capture_output=True, text=True, check=True).stdout.strip())
    editable = (site.parent / ".git").exists()
    stamp = py.parent.parent / ".fork"
    if stamp.exists() and stamp.read_text().strip() == sha:
        return sha
    if stamp.exists():
        if editable:
            subprocess.run(["git", "-C", str(site.parent), "checkout", "--", "."], check=True)
            subprocess.run(["git", "-C", str(site.parent), "clean", "-fdq", "--", str(site / engine)], check=True)
        else:
            shutil.rmtree(site / engine, ignore_errors=True)
            bkey = _backend_key(engine, backend)
            spec = (BACKEND_SPECS[bkey] if bkey else SPECS[engine])(version)
            subprocess.run(["uv", "pip", "install", "--quiet", "--python", str(py), "--reinstall", "--no-deps",
                            *_uv_flags(engine, backend, version), *spec], check=True, timeout=900,
                           env={k: v for k, v in os.environ.items() if k not in ("PIP_CONSTRAINT", "UV_CONSTRAINT", "VIRTUAL_ENV")})
    owner = fork["repo"].split("/")[0]
    url = f"https://github.com/{fork['upstream']}/compare/v{version}...{owner}:{fork['repo'].split('/')[1]}:{sha}.diff"
    diff = urllib.request.urlopen(url, timeout=120).read()
    strip = len(Path(fork.get("src", ".")).parts) + 1 if fork.get("src", ".") != "." else 1
    for m in re.finditer(rb"^--- /dev/null\n\+\+\+ b/(\S+)", diff, re.M):
        site.joinpath(*Path(m.group(1).decode()).parts[strip - 1:]).unlink(missing_ok=True)
    subprocess.run(["patch", f"-p{strip}", "--forward", "--batch", "-d", str(site)], input=diff, check=True, capture_output=True, timeout=120)
    stamp.write_text(sha + "\n")
    log(f"baseline: {engine} {version} with {fork['repo']}@{sha[:10]} ({branch})")
    return sha


_FAILED: dict[tuple[str, str, str | None], str] = {}


def ensure_baseline(engine: str, version: str, root: Path | None = None, *, backend: str | None = None, timeout_s: int = 900, log=print) -> Path:
    if engine not in SPECS:
        raise ValueError(f"no installer for baseline {engine}")
    if (engine, version, backend) in _FAILED:
        raise RuntimeError(f"{engine} {version} install already failed on this pod: {_FAILED[engine, version, backend]}")
    bkey = _backend_key(engine, backend)
    spec = (BACKEND_SPECS[bkey] if bkey else SPECS[engine])(version)
    uv_flags = _uv_flags(engine, backend, version)
    cuda = engine in ("vllm", "sglang") and str(backend or "cuda") == "cuda"
    if engine == "trtllm":
        ensure_mpi(log=log)
    fork = engine in ("vllm", "sglang") and str(backend or "cuda") in ("cuda", "rocm")
    d = venv_dir(engine, version, root, backend)
    py = d / "bin" / "python"
    if (d / ".ok").exists():
        ensure_python_headers(py, log=log)
        if engine == "trtllm":
            ensure_cuda_devkit(py, log=log)
            if not (d / "bin" / "pip").exists() and shutil.which("uv"):
                subprocess.run(["uv", "pip", "install", "--quiet", "--python", str(py), "pip"], check=False, timeout=600)
            ensure_nvrtc_matches_toolkit(py, log=log)
        if fork:
            ensure_fork(engine, version, py, log=log, backend=backend)
        if cuda:
            ensure_cuda_devkit(py, log=log)
            ensure_flashinfer_aot(py, d / ".flashinfer-aot", log=log)
            if engine == "sglang":
                ensure_pip_nvcc_matches_cudart(py, log=log)
        return py
    if d.exists():
        shutil.rmtree(d, ignore_errors=True)
    if bkey == ("sglang", "rocm"):
        py = _image_sglang(d, version, log=log)
        ensure_fork(engine, version, py, log=log, backend=backend)
        return py
    log(f"baseline: installing {' '.join(spec)} into {d} (once per volume)")
    ienv = {k: v for k, v in os.environ.items() if k not in ("PIP_CONSTRAINT", "UV_CONSTRAINT", "VIRTUAL_ENV")}
    if shutil.which("uv"):
        subprocess.run(["uv", "venv", "--quiet", "--python", "3.12", str(d)], check=True, env=ienv)
        for attempt in (1, 2):
            try:
                subprocess.run(["uv", "pip", "install", "--quiet", "--python", str(py), *uv_flags, *spec], check=True, timeout=timeout_s, env=ienv)
                break
            except subprocess.SubprocessError as e:
                if attempt == 2:
                    _FAILED[engine, version, backend] = str(e)[:300]
                    raise
                log(f"baseline: {' '.join(spec)} install failed ({str(e)[:200]}); retrying once")
    else:
        subprocess.run(["python3", "-m", "venv", str(d)], check=True)
        subprocess.run([str(py), "-m", "pip", "install", "-q", *spec], check=True, timeout=timeout_s)
    ensure_python_headers(py, log=log)
    if engine == "trtllm":
        ensure_cuda_devkit(py, log=log)
        subprocess.run(["uv", "pip", "install", "--quiet", "--python", str(py), "pip"], check=False, timeout=600)
        ensure_nvrtc_matches_toolkit(py, log=log)
    if fork:
        ensure_fork(engine, version, py, log=log, backend=backend)
    if cuda:
        ensure_cuda_devkit(py, log=log)
        ensure_flashinfer_aot(py, d / ".flashinfer-aot", log=log)
        if engine == "sglang":
            ensure_pip_nvcc_matches_cudart(py, log=log)
    (d / ".ok").write_text(version + "\n")
    return py
