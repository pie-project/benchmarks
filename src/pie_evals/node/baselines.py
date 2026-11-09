"""Baseline engines on the node.

The runner image ships pie's toolchain only; vLLM and SGLang are installed
once per pinned version into a venv on the shared cache (the volume) and
reused by every pod after that. llama.cpp needs nvcc for a CUDA build and
the image has only the CUDA runtime, so it is not installed here (Linux
llama.cpp cells are declared unsupported in matrix/support.yaml).
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path

SPECS = {
    "vllm": lambda v: [f"vllm=={v}"],
    "sglang": lambda v: [f"sglang[all]=={v}"],
    # the wheels live on NVIDIA's index (PyPI holds a stub), built against the torch it pins
    "trtllm": lambda v: [f"tensorrt-llm=={v}"],
}

#: a baseline's build for another backend: vLLM's TPU build is the ``vllm-tpu`` wheel (vLLM on the
#: tpu-inference JAX backend), released in step with vllm; SGLang's is ``sglang-jax``, its own
#: project at its own pin (engines.yaml backend_pins)
BACKEND_SPECS = {
    ("vllm", "xla"): lambda v: [f"vllm-tpu=={v}"],
    # a pin "git-<sha>": that commit of sglang-jax's repository (a model its newest release does not have yet)
    # main loads Qwen3.5's video processor at startup, which Transformers builds on torch and torchvision: the CPU wheels (below)
    ("sglang", "xla"): lambda v: [f"sglang-jax[tpu] @ git+https://github.com/sgl-project/sglang-jax@{v[4:]}#subdirectory=python", "torch", "torchvision"]
                                 if v.startswith("git-") else [f"sglang-jax[tpu]=={v}"],
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
    ("sglang", "xla"): ["--torch-backend", "cpu"],
}


def _uv_flags(engine: str, backend: str | None, version: str) -> list[str]:
    if engine == "trtllm":
        # tensorrt-llm, its tensorrt and modelopt pins are on NVIDIA's index, torch and the rest on PyPI
        return ["--extra-index-url", "https://pypi.nvidia.com", "--index-strategy", "unsafe-best-match", "--prerelease", "if-necessary-or-explicit"]
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
    # FlashInfer 0.7.1's trtllm MoE JIT (SGLang 0.5.22's auto runner for bf16 experts on SM100) includes curand_kernel.h
    # ("fatal error: curand_kernel.h: No such file", GLM-5.3 mini78 on b200-x1, parity 42566505027)
    rand = Path("/usr/local/cuda/include/curand_kernel.h")
    if nvcc.exists() and header.exists() and devrt.exists() and blas.exists() and rand.exists():
        return True
    ver = cuda_toolkit_version(py)
    if ver is None:
        log("baseline: cannot tell the image's CUDA version; not installing the toolkit")
        return False
    major, minor = ver
    pkgs = [p for p, missing in ((f"cuda-nvcc-{major}-{minor}", not nvcc.exists()), (f"cuda-cudart-dev-{major}-{minor}", not (header.exists() and devrt.exists()))) if missing]
    log(f"baseline: {nvcc.name}/{header.name}/{devrt.name} missing; installing {' '.join(pkgs)}")
    apt = ["apt-get"] if os.geteuid() == 0 else ["sudo", "-n", "apt-get"]
    env = dict(os.environ, DEBIAN_FRONTEND="noninteractive")
    try:
        subprocess.run(apt + ["update", "-qq"], env=env, check=False, timeout=600, capture_output=True)
        if pkgs:
            subprocess.run(apt + ["install", "-y", "-qq", "--no-install-recommends", *pkgs], env=env, check=True, timeout=1200, capture_output=True)
    except (OSError, subprocess.SubprocessError) as e:
        log(f"baseline: CUDA toolkit install failed ({e}); engines that JIT CUDA kernels will crash")
        return False
    if not blas.exists():
        # its own step: the runtime image holds libcublas at its version, and a refused dev package must not cost nvcc
        r = subprocess.run(apt + ["install", "-y", "-qq", "--no-install-recommends", "--allow-change-held-packages", f"libcublas-dev-{major}-{minor}"], env=env, check=False, timeout=1200, capture_output=True, text=True)
        if not blas.exists() and py is not None:
            # the held runtime refuses the dev package ("held broken packages"): the venv's pip cuBLAS carries the headers
            for inc in Path(py).absolute().parent.parent.glob("lib/python3*/site-packages/nvidia/cu*/include"):
                for h in inc.glob("cublas*.h"):
                    if not (blas.parent / h.name).exists():
                        (blas.parent / h.name).symlink_to(h)
            # and the unversioned names a `-lcublasLt` link wants, which only the dev package carries
            lib = devrt.parent
            for name in ("libcublas.so", "libcublasLt.so"):
                found = sorted(lib.glob(name + ".*"))
                if not (lib / name).exists() and found:
                    (lib / name).symlink_to(found[0].name)
        log(f"baseline: cublasLt.h {blas.exists()}" + ("" if r.returncode == 0 else f" (apt: {(r.stderr or r.stdout).strip().splitlines()[-1:]})"))
    if not rand.exists():
        r = subprocess.run(apt + ["install", "-y", "-qq", "--no-install-recommends", "--allow-change-held-packages", f"libcurand-dev-{major}-{minor}"], env=env, check=False, timeout=1200, capture_output=True, text=True)
        if not rand.exists() and py is not None:
            # as cuBLAS above: the venv's pip cuRAND carries the headers
            for inc in Path(py).absolute().parent.parent.glob("lib/python3*/site-packages/nvidia/cu*/include"):
                for h in inc.glob("curand*.h"):
                    if not (rand.parent / h.name).exists():
                        (rand.parent / h.name).symlink_to(h)
        log(f"baseline: curand_kernel.h {rand.exists()}" + ("" if r.returncode == 0 else f" (apt: {(r.stderr or r.stdout).strip().splitlines()[-1:]})"))
    ok = nvcc.exists() and header.exists() and devrt.exists()
    log(f"baseline: nvcc {nvcc.exists()}, cuda_runtime.h {header.exists()}, libcudadevrt.a {devrt.exists()}")
    return ok


ensure_nvcc = ensure_cuda_devkit  # the old name


def ensure_nvrtc_matches_toolkit(py: Path, log=print) -> None:
    """TensorRT-LLM's trtllm-gen kernels JIT through the venv's pip NVRTC against the pod's CUDA headers, and
    NVRTC 13.0 refused the 13.4 headers ("identifier cudaFabricOpStatusSource is undefined", b200-x1): the pip
    NVRTC follows the toolkit's minor."""
    import json as _json

    try:
        tk = _json.loads(Path("/usr/local/cuda/version.json").read_text())["cuda"]["version"]
    except (OSError, KeyError, ValueError):
        real = Path("/usr/local/cuda").resolve().name  # cuda-13.4
        tk = real.split("-", 1)[1] if "-" in real else ""
    mm = ".".join(tk.split(".")[:2])
    if not mm:
        return
    try:
        have = subprocess.run([str(py), "-c", "from importlib.metadata import version as v; print(v('nvidia-cuda-nvrtc'))"],
                              capture_output=True, text=True, timeout=60).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return
    if not have or have.startswith(mm + "."):
        return
    log(f"baseline: pip NVRTC {have} beside the CUDA {mm} toolkit; installing nvidia-cuda-nvrtc=={mm}.*")
    subprocess.run(["uv", "pip", "install", "--quiet", "--python", str(py), f"nvidia-cuda-nvrtc=={mm}.*"], check=False, timeout=900)


def ensure_mpi(log=print) -> bool:
    """TensorRT-LLM imports mpi4py at start, even on one GPU, and mpi4py loads the system's
    libmpi; the runner image has none. Open MPI from the image's apt repo, once per pod."""
    import ctypes.util

    if ctypes.util.find_library("mpi"):
        return True
    apt = ["apt-get"] if os.geteuid() == 0 else ["sudo", "-n", "apt-get"]
    env = dict(os.environ, DEBIAN_FRONTEND="noninteractive")
    try:
        # No tty: under tmux the node leads its own process group, and apt setting up the
        # terminal stopped the whole group (SIGTTOU) for good.
        quiet = dict(env=env, stdin=subprocess.DEVNULL, capture_output=True)
        subprocess.run(apt + ["update", "-qq"], check=False, timeout=600, **quiet)
        subprocess.run(apt + ["install", "-y", "-qq", "--no-install-recommends", "libopenmpi-dev", "openmpi-bin"], check=True, timeout=1200, **quiet)
    except (OSError, subprocess.SubprocessError) as e:
        log(f"baseline: Open MPI install failed ({e}); TensorRT-LLM cannot start")
        return False
    log("baseline: installed Open MPI for TensorRT-LLM")
    return True


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


#: pins whose install already failed in this process: every later model of that engine fails at
#: once instead of holding the GPU through another install (h200 weekly 40417931828 tried twice)
def ensure_fork(engine: str, version: str, py: Path, log=print, backend: str | None = None) -> str | None:
    """Overlay the fork's fixes for this release on the installed wheel: the Python changes on branch
    ``pie-evals/v<version>`` of the fork named in the engine's recipe (``fork:``), over upstream's tag
    ``v<version>``. Returns the fork commit applied, or None when the release has no fork branch."""
    import urllib.request

    from .engines.recipes import recipe_fork

    fork = recipe_fork(engine)
    if not fork:
        return None
    # PIE_EVALS_FORK_BRANCH_<ENGINE> overlays an open fork PR branch instead (stamped with its own commit)
    branch = os.environ.get(f"PIE_EVALS_FORK_BRANCH_{engine.upper()}") or f"pie-evals/v{version}"
    try:
        head = subprocess.run(["git", "ls-remote", f"https://github.com/{fork['repo']}", f"refs/heads/{branch}"],
                              capture_output=True, text=True, check=True, timeout=60).stdout.split()
    except (OSError, subprocess.SubprocessError) as e:
        raise RuntimeError(f"{engine}: cannot read fork {fork['repo']} {branch}: {e}") from e
    if not head:
        return None
    sha = head[0]
    # the directory that holds the package: site-packages for a wheel, the source tree's python/ for the AMD image's
    # editable SGLang (/sgl-workspace/sglang/python)
    site = Path(subprocess.run([str(py), "-c", f"import importlib.util, os; print(os.path.dirname(os.path.dirname(importlib.util.find_spec('{engine}').origin)))"],
                               capture_output=True, text=True, check=True).stdout.strip())
    editable = (site.parent / ".git").exists()
    stamp = py.parent.parent / ".fork"
    if stamp.exists() and stamp.read_text().strip() == sha:
        return sha
    if stamp.exists():  # an older overlay: put the wheel's files back first; the files it added and the hunks a
        # reinstall leaves in place would make the new patch fail as "previously applied"
        import shutil

        if editable:  # the image's source tree: put its files back with git
            subprocess.run(["git", "-C", str(site.parent), "checkout", "--", "."], check=True)
            subprocess.run(["git", "-C", str(site.parent), "clean", "-fdq", "--", str(site / engine)], check=True)
        else:
            shutil.rmtree(site / engine, ignore_errors=True)
            # the backend's own build (vLLM's ROCm wheel from its index), not PyPI's CUDA one
            bkey = _backend_key(engine, backend)
            spec = (BACKEND_SPECS[bkey] if bkey else SPECS[engine])(version)
            subprocess.run(["uv", "pip", "install", "--quiet", "--python", str(py), "--reinstall", "--no-deps",
                            *_uv_flags(engine, backend, version), *spec], check=True, timeout=900,
                           env={k: v for k, v in os.environ.items() if k not in ("PIP_CONSTRAINT", "UV_CONSTRAINT", "VIRTUAL_ENV")})
    owner = fork["repo"].split("/")[0]
    url = f"https://github.com/{fork['upstream']}/compare/v{version}...{owner}:{fork['repo'].split('/')[1]}:{sha}.diff"
    diff = urllib.request.urlopen(url, timeout=120).read()
    strip = len(Path(fork.get("src", ".")).parts) + 1 if fork.get("src", ".") != "." else 1
    # a file the fork adds outlives the wheel reinstall: remove it, or patch refuses to create it again
    for m in re.finditer(rb"^--- /dev/null\n\+\+\+ b/(\S+)", diff, re.M):
        site.joinpath(*Path(m.group(1).decode()).parts[strip - 1:]).unlink(missing_ok=True)
    subprocess.run(["patch", f"-p{strip}", "--forward", "--batch", "-d", str(site)], input=diff, check=True, capture_output=True, timeout=120)
    stamp.write_text(sha + "\n")
    log(f"baseline: {engine} {version} with {fork['repo']}@{sha[:10]} ({branch})")
    return sha


_FAILED: dict[tuple[str, str, str | None], str] = {}


def ensure_baseline(engine: str, version: str, root: Path | None = None, *, backend: str | None = None, timeout_s: int = 900, log=print) -> Path:
    """Install the baseline into its venv if needed; return its python. ``backend`` picks the
    engine's build for that platform backend (``xla``: vllm-tpu) where it has one."""
    if engine not in SPECS:
        raise ValueError(f"no installer for baseline {engine}")
    if (engine, version, backend) in _FAILED:
        raise RuntimeError(f"{engine} {version} install already failed on this pod: {_FAILED[engine, version, backend]}")
    bkey = _backend_key(engine, backend)
    spec = (BACKEND_SPECS[bkey] if bkey else SPECS[engine])(version)
    uv_flags = _uv_flags(engine, backend, version)
    # the CUDA toolkit and FlashInfer kernels are for the CUDA build only
    cuda = engine in ("vllm", "sglang") and str(backend or "cuda") == "cuda"
    if engine == "trtllm":
        ensure_mpi(log=log)
    # the fork's Python fixes apply to the CUDA and the ROCm builds alike (not to vllm-tpu)
    fork = engine in ("vllm", "sglang") and str(backend or "cuda") in ("cuda", "rocm")
    d = venv_dir(engine, version, root, backend)
    py = d / "bin" / "python"
    if (d / ".ok").exists():
        ensure_python_headers(py, log=log)
        if engine == "trtllm":
            ensure_cuda_devkit(py, log=log)
            if not (d / "bin" / "pip").exists() and shutil.which("uv"):
                # DeepGEMM locates its JIT headers through `pip show tensorrt_llm`; a uv venv has no pip
                subprocess.run(["uv", "pip", "install", "--quiet", "--python", str(py), "pip"], check=False, timeout=600)
            ensure_nvrtc_matches_toolkit(py, log=log)
        if fork:
            ensure_fork(engine, version, py, log=log, backend=backend)
        if cuda:
            ensure_nvcc(py, log=log)
            ensure_flashinfer_aot(py, d / ".flashinfer-aot", log=log)
            if engine == "sglang":
                ensure_pip_nvcc_matches_cudart(py, log=log)
        return py
    if d.exists():
        shutil.rmtree(d, ignore_errors=True)  # a half-finished install
    if bkey == ("sglang", "rocm"):
        py = _image_sglang(d, version, log=log)
        ensure_fork(engine, version, py, log=log, backend=backend)
        return py
    log(f"baseline: installing {' '.join(spec)} into {d} (once per volume)")
    # the AMD SGLang image pins its own torch through PIP_CONSTRAINT and points VIRTUAL_ENV at its venv
    ienv = {k: v for k, v in os.environ.items() if k not in ("PIP_CONSTRAINT", "UV_CONSTRAINT", "VIRTUAL_ENV")}
    if shutil.which("uv"):
        subprocess.run(["uv", "venv", "--quiet", "--python", "3.12", str(d)], check=True, env=ienv)
        # a healthy pod installs from PyPI in 15 s to 3 min; a pod on a starved link took over an
        # hour and the watchdog then killed the shard's other engines (h200 weekly 40417931828).
        # One retry keeps the wheels the first try finished in the uv cache.
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
        ensure_nvcc(py, log=log)
        ensure_flashinfer_aot(py, d / ".flashinfer-aot", log=log)
        if engine == "sglang":
            ensure_pip_nvcc_matches_cudart(py, log=log)
    (d / ".ok").write_text(version + "\n")
    return py
