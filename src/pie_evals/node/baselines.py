"""Baseline engines on the node.

The runner image ships pie's toolchain only; vLLM and SGLang are installed
once per pinned version into a venv on the shared cache (the volume) and
reused by every pod after that. llama.cpp needs nvcc for a CUDA build and
the image has only the CUDA runtime, so it is not installed here (Linux
llama.cpp cells are declared unsupported in matrix/support.yaml).
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

SPECS = {
    "vllm": lambda v: [f"vllm=={v}"],
    "sglang": lambda v: [f"sglang[all]=={v}"],
}

#: a baseline's build for another backend: vLLM's TPU build is the ``vllm-tpu`` wheel (vLLM on the
#: tpu-inference JAX backend), released in step with vllm; SGLang's is ``sglang-jax``, its own
#: project at its own pin (engines.yaml backend_pins)
BACKEND_SPECS = {
    ("vllm", "xla"): lambda v: [f"vllm-tpu=={v}"],
    ("sglang", "xla"): lambda v: [f"sglang-jax[tpu]=={v}"],
    # vLLM's ROCm build: the release's wheel from vLLM's own ROCm index (torch, triton and aiter for
    # the same ROCm beside it), local version `+rocmNNN` (rocm_vllm_spec reads which ROCm it is)
    ("vllm", "rocm"): lambda v: [f"vllm=={rocm_vllm_version(v)}"],
    # SGLang's ROCm build ships only as the AMD image the pod runs (lmsysorg/sglang:v<pin>-rocm*):
    # its venv sees the image's site-packages, nothing is installed (ensure_baseline checks the version)
    ("sglang", "rocm"): lambda v: [],
}

#: vLLM's ROCm wheel index: <base>/<version>/ lists one rocmNNN/ directory, the index for that release
VLLM_ROCM_INDEX = "https://wheels.vllm.ai/rocm"


def rocm_vllm_variant(version: str) -> str:
    """The ``rocmNNN`` directory vLLM published ``version``'s ROCm wheels under (0.31.0: rocm723)."""
    import re
    import urllib.request

    with urllib.request.urlopen(f"{VLLM_ROCM_INDEX}/{version}/", timeout=60) as r:
        found = re.findall(r'href="(rocm\d+)/"', r.read().decode())
    if not found:
        raise RuntimeError(f"vLLM {version} has no ROCm wheel index at {VLLM_ROCM_INDEX}/{version}/")
    return sorted(found)[-1]


def rocm_vllm_version(version: str) -> str:
    return f"{version}+{rocm_vllm_variant(version)}"

#: extra ``uv pip install`` flags per backend build: the TPU build runs torch on the host only
#: (torchax lowers it to JAX), so the CPU wheel stands in for the 3 GB CUDA one
BACKEND_UV_FLAGS = {
    ("vllm", "xla"): ["--torch-backend", "cpu"],
}


def _uv_flags(engine: str, backend: str | None, version: str) -> list[str]:
    key = _backend_key(engine, backend)
    if key == ("vllm", "rocm"):
        # the ROCm torch/triton/aiter pins come from vLLM's index, not PyPI's CUDA builds
        return ["--extra-index-url", f"{VLLM_ROCM_INDEX}/{version}/{rocm_vllm_variant(version)}", "--index-strategy", "unsafe-best-match"]
    return BACKEND_UV_FLAGS.get(key, []) if key else []


def cache_root(root: Path | None = None) -> Path:
    return root or Path(os.environ.get("PIE_EVALS_CACHE", Path.home() / ".cache/pie-evals"))


def _backend_key(engine: str, backend: str | None) -> tuple[str, str] | None:
    key = (engine, str(backend or ""))
    return key if key in BACKEND_SPECS else None


def venv_dir(engine: str, version: str, root: Path | None = None, backend: str | None = None) -> Path:
    tag = ("-tpu" if backend == "xla" else f"-{backend}") if _backend_key(engine, backend) else ""
    return cache_root(root) / f"venv-{engine}{tag}-{version}"


def baseline_python(engine: str, version: str, root: Path | None = None, backend: str | None = None) -> Path | None:
    """The interpreter for a baseline pin if it is installed, else None."""
    d = venv_dir(engine, version, root, backend)
    return d / "bin" / "python" if (d / ".ok").exists() else None


def ensure_python_headers(py: Path, log=print) -> bool:
    """triton (and torch.compile) build a small C extension at runtime against
    the interpreter's headers; a system python without ``python3-dev`` has none
    and every vLLM/SGLang engine core then dies with ``Python.h: No such file``
    (nightly 35895697621 lost all 66 vLLM cells to it). Install the headers
    for the interpreter's own minor version when they are missing."""
    try:
        out = subprocess.run(
            [str(py), "-c", "import sys, sysconfig; print(sysconfig.get_paths()['include']); print(sys.version_info[0], sys.version_info[1])"],
            capture_output=True, text=True, check=True, timeout=60,
        ).stdout.split()
        include, major, minor = Path(out[0]), out[1], out[2]
    except (OSError, subprocess.SubprocessError, IndexError) as e:
        log(f"baseline: cannot query the include dir of {py}: {e}")
        return False
    if (include / "Python.h").exists():
        return True
    pkg = f"python{major}.{minor}-dev"
    log(f"baseline: {include}/Python.h is missing; installing {pkg}")
    apt = ["apt-get"] if os.geteuid() == 0 else ["sudo", "-n", "apt-get"]
    env = dict(os.environ, DEBIAN_FRONTEND="noninteractive")
    try:
        subprocess.run(apt + ["update", "-qq"], env=env, check=False, timeout=600, capture_output=True)
        subprocess.run(apt + ["install", "-y", "-qq", pkg], env=env, check=True, timeout=900, capture_output=True)
    except (OSError, subprocess.SubprocessError) as e:
        log(f"baseline: {pkg} install failed ({e}); engines that JIT C extensions will crash")
        return False
    ok = (include / "Python.h").exists()
    log(f"baseline: {pkg} installed; Python.h present: {ok}")
    return ok


def cuda_toolkit_version(py: Path | None = None) -> tuple[str, str] | None:
    """(major, minor) of the CUDA this image was built for: torch's, when a
    baseline interpreter is given, else /usr/local/cuda/version.json."""
    if py is not None:
        try:
            cuda = subprocess.run([str(py), "-c", "import torch; print(torch.version.cuda)"], capture_output=True, text=True, check=True, timeout=300).stdout.strip()
            major, minor = cuda.split(".")[:2]
            return major, minor
        except (OSError, subprocess.SubprocessError, ValueError):
            pass
    try:
        import json

        v = json.loads(Path("/usr/local/cuda/version.json").read_text())["cuda"]["version"]
        major, minor = v.split(".")[:2]
        return major, minor
    except (OSError, KeyError, ValueError):
        pass
    # the runtime image ships no version.json (smoke 35940094146 could not
    # tell); /usr/local/cuda is a link to /usr/local/cuda-X.Y there
    import re

    try:
        m = re.search(r"cuda-(\d+)\.(\d+)", str(Path("/usr/local/cuda").resolve()))
        if m:
            return m.group(1), m.group(2)
    except OSError:
        pass
    for d in sorted(Path("/usr/local").glob("cuda-*.*"), reverse=True):
        m = re.fullmatch(r"cuda-(\d+)\.(\d+)", d.name)
        if m:
            return m.group(1), m.group(2)
    try:  # last resort: the cudart package the image installed
        out = subprocess.run(["dpkg-query", "-W", "-f", "${Package}\n", "cuda-cudart-*"], capture_output=True, text=True, check=False, timeout=30).stdout
        m = re.search(r"cuda-cudart-(\d+)-(\d+)", out)
        if m:
            return m.group(1), m.group(2)
    except OSError:
        pass
    return None


def ensure_cuda_devkit(py: Path | None = None, log=print) -> bool:
    """The runner image is ``nvidia/cuda:*-runtime``: no nvcc, no CUDA headers,
    no ``libcudadevrt.a``. vLLM/SGLang JIT kernels with nvcc (gemma's
    head_dim-512 prefill, ``sgl_kernel_jit``; nightly 35918372228), and pie's
    NVRTC path needs ``libcudadevrt.a`` for cooperative launches
    (``attention.mla_latents`` on the GLM mini, nightly 35935510089). Install
    the toolkit packages for the image's CUDA from the NVIDIA apt repo it
    already carries; once per pod (container disk)."""
    nvcc = Path("/usr/local/cuda/bin/nvcc")
    header = Path("/usr/local/cuda/include/cuda_runtime.h")
    devrt = Path("/usr/local/cuda/lib64/libcudadevrt.a")
    # FlashInfer's trtllm-gen FMHA JIT includes cublasLt.h (SGLang GLM-5.3-Flash on pro6000-x4, weekly 39890605647)
    blas = Path("/usr/local/cuda/include/cublasLt.h")
    if nvcc.exists() and header.exists() and devrt.exists() and blas.exists():
        return True
    ver = cuda_toolkit_version(py)
    if ver is None:
        log("baseline: cannot tell the image's CUDA version; not installing the toolkit")
        return False
    major, minor = ver
    pkgs = [p for p, missing in ((f"cuda-nvcc-{major}-{minor}", not nvcc.exists()), (f"cuda-cudart-dev-{major}-{minor}", not (header.exists() and devrt.exists())), (f"libcublas-dev-{major}-{minor}", not blas.exists())) if missing]
    log(f"baseline: {nvcc.name}/{header.name}/{devrt.name} missing; installing {' '.join(pkgs)}")
    apt = ["apt-get"] if os.geteuid() == 0 else ["sudo", "-n", "apt-get"]
    env = dict(os.environ, DEBIAN_FRONTEND="noninteractive")
    try:
        subprocess.run(apt + ["update", "-qq"], env=env, check=False, timeout=600, capture_output=True)
        subprocess.run(apt + ["install", "-y", "-qq", "--no-install-recommends", *pkgs], env=env, check=True, timeout=1200, capture_output=True)
    except (OSError, subprocess.SubprocessError) as e:
        log(f"baseline: CUDA toolkit install failed ({e}); engines that JIT CUDA kernels will crash")
        return False
    ok = nvcc.exists() and header.exists() and devrt.exists()
    log(f"baseline: nvcc {nvcc.exists()}, cuda_runtime.h {header.exists()}, libcudadevrt.a {devrt.exists()}")
    return ok


ensure_nvcc = ensure_cuda_devkit  # the old name


def ensure_pip_nvcc_matches_cudart(py: Path, log=print) -> None:
    """sglang[all] 0.5.22 resolves pip nvcc 13.4 beside torch's cudart 13.0, and CCCL refuses a
    compiler and headers of different minors: every tilelang JIT kernel died with "CUDA compiler
    and CUDA toolkit headers are incompatible" (GLM-5.3-Flash on pro6000-x4, weekly 39867658406)."""
    probe = "from importlib.metadata import version as v\nfor p in ('nvidia-cuda-runtime', 'nvidia-cuda-nvcc'):\n    try: print(v(p))\n    except Exception: print('')"
    try:
        rt, cc = subprocess.run([str(py), "-c", probe], capture_output=True, text=True, timeout=60).stdout.split("\n")[:2]
    except (OSError, subprocess.SubprocessError, ValueError):
        return
    mm = lambda s: ".".join(s.split(".")[:2])  # noqa: E731
    if not rt or not cc or mm(rt) == mm(cc):
        return
    pins = [f"{p}=={mm(rt)}.*" for p in ("nvidia-cuda-nvcc", "nvidia-cuda-crt", "nvidia-nvvm")]
    log(f"baseline: pip nvcc {cc} beside cudart {rt}; installing {' '.join(pins)}")
    try:
        cmd = ["uv", "pip", "install", "--quiet", "--python", str(py)] if shutil.which("uv") else [str(py), "-m", "pip", "install", "-q"]
        subprocess.run([*cmd, *pins], check=True, timeout=900)
    except (OSError, subprocess.SubprocessError) as e:
        log(f"baseline: nvcc pin failed ({e})")


def ensure_flashinfer_aot(py: Path, marker: Path, log=print) -> bool:
    """vLLM's FlashInfer backend JIT-compiles its attention kernels with nvcc,
    and the runner image ships only the CUDA runtime (nightly 35908055874 lost
    every gemma/qwen vLLM cell to ``/usr/local/cuda/bin/nvcc: not found``).
    FlashInfer publishes the compiled kernels as ``flashinfer-cubin`` and
    ``flashinfer-jit-cache`` wheels per CUDA version; install the pair that
    matches the venv's flashinfer and torch, once per venv."""
    if marker.exists():
        return True
    try:
        out = subprocess.run(
            [str(py), "-c", "import flashinfer, torch; print(flashinfer.__version__); print(torch.version.cuda)"],
            capture_output=True, text=True, check=True, timeout=300,
        ).stdout.split()
        fi, cuda = out[0], out[1]
    except (OSError, subprocess.SubprocessError, IndexError) as e:
        log(f"baseline: no flashinfer/torch to match an AOT cache to ({e})")
        return False
    cu = "cu" + cuda.replace(".", "")[:3]
    # the cubins are CUDA-agnostic and live at the index root; the JIT cache
    # (the compiled attention kernels) is per CUDA version
    plan = [
        (f"flashinfer-jit-cache=={fi}", f"https://flashinfer.ai/whl/{cu}/"),
        (f"flashinfer-cubin=={fi}", "https://flashinfer.ai/whl/"),
    ]
    ok = True
    for spec, index in plan:
        log(f"baseline: installing {spec} from {index}")
        try:
            if shutil.which("uv"):
                subprocess.run(["uv", "pip", "install", "--quiet", "--python", str(py), "--extra-index-url", index, spec], check=True, timeout=1800)
            else:
                subprocess.run([str(py), "-m", "pip", "install", "-q", "--extra-index-url", index, spec], check=True, timeout=1800)
        except (OSError, subprocess.SubprocessError) as e:
            log(f"baseline: {spec} install failed ({e}); FlashInfer may JIT and need nvcc")
            ok = False
    if ok:
        marker.write_text(fi + "\n")
    return ok


def image_python() -> str:
    """The AMD SGLang image's interpreter (the one its sglang is installed into)."""
    for c in ("/opt/venv/bin/python3", "/usr/bin/python3"):
        if Path(c).exists() and subprocess.run([c, "-c", "import sglang"], capture_output=True, timeout=300).returncode == 0:
            return c
    return shutil.which("python3") or "python3"


def _image_sglang(d: Path, version: str, log=print) -> Path:
    """SGLang on ROCm is the AMD image's own install, used as it is: ``bin/python`` here is a
    wrapper that execs the image's interpreter (a venv over it would lose the image's own venv)."""
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


def ensure_baseline(engine: str, version: str, root: Path | None = None, *, backend: str | None = None, timeout_s: int = 3600, log=print) -> Path:
    """Install the baseline into its venv if needed; return its python. ``backend`` picks the
    engine's build for that platform backend (``xla``: vllm-tpu) where it has one."""
    if engine not in SPECS:
        raise ValueError(f"no installer for baseline {engine}")
    bkey = _backend_key(engine, backend)
    spec = (BACKEND_SPECS[bkey] if bkey else SPECS[engine])(version)
    uv_flags = _uv_flags(engine, backend, version)
    # the CUDA toolkit and FlashInfer kernels are for the CUDA build only
    cuda = engine in ("vllm", "sglang") and str(backend or "cuda") == "cuda"
    d = venv_dir(engine, version, root, backend)
    py = d / "bin" / "python"
    if (d / ".ok").exists():
        ensure_python_headers(py, log=log)
        if cuda:
            ensure_nvcc(py, log=log)
            ensure_flashinfer_aot(py, d / ".flashinfer-aot", log=log)
            if engine == "sglang":
                ensure_pip_nvcc_matches_cudart(py, log=log)
        return py
    if d.exists():
        shutil.rmtree(d, ignore_errors=True)  # a half-finished install
    if bkey == ("sglang", "rocm"):
        return _image_sglang(d, version, log=log)
    log(f"baseline: installing {' '.join(spec)} into {d} (once per volume)")
    # the AMD SGLang image pins its own torch through PIP_CONSTRAINT and points VIRTUAL_ENV at its venv
    ienv = {k: v for k, v in os.environ.items() if k not in ("PIP_CONSTRAINT", "UV_CONSTRAINT", "VIRTUAL_ENV")}
    if shutil.which("uv"):
        subprocess.run(["uv", "venv", "--quiet", "--python", "3.12", str(d)], check=True, env=ienv)
        subprocess.run(["uv", "pip", "install", "--quiet", "--python", str(py), *uv_flags, *spec], check=True, timeout=timeout_s, env=ienv)
    else:
        subprocess.run(["python3", "-m", "venv", str(d)], check=True)
        subprocess.run([str(py), "-m", "pip", "install", "-q", *spec], check=True, timeout=timeout_s)
    ensure_python_headers(py, log=log)
    if cuda:
        ensure_nvcc(py, log=log)
        ensure_flashinfer_aot(py, d / ".flashinfer-aot", log=log)
        if engine == "sglang":
            ensure_pip_nvcc_matches_cudart(py, log=log)
    (d / ".ok").write_text(version + "\n")
    return py
