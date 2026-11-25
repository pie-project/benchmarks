from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path

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
    import re
    import urllib.request

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


def ensure_python_headers(py: Path, log=print) -> bool:
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
    try:
        out = subprocess.run(["dpkg-query", "-W", "-f", "${Package}\n", "cuda-cudart-*"], capture_output=True, text=True, check=False, timeout=30).stdout
        m = re.search(r"cuda-cudart-(\d+)-(\d+)", out)
        if m:
            return m.group(1), m.group(2)
    except OSError:
        pass
    return None


def ensure_cuda_devkit(py: Path | None = None, log=print) -> bool:
    nvcc = Path("/usr/local/cuda/bin/nvcc")
    header = Path("/usr/local/cuda/include/cuda_runtime.h")
    devrt = Path("/usr/local/cuda/lib64/libcudadevrt.a")
    blas = Path("/usr/local/cuda/include/cublasLt.h")
    if nvcc.exists() and header.exists() and devrt.exists() and blas.exists():
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
        r = subprocess.run(apt + ["install", "-y", "-qq", "--no-install-recommends", "--allow-change-held-packages", f"libcublas-dev-{major}-{minor}"], env=env, check=False, timeout=1200, capture_output=True, text=True)
        if not blas.exists() and py is not None:
            for inc in Path(py).absolute().parent.parent.glob("lib/python3*/site-packages/nvidia/cu*/include"):
                for h in inc.glob("cublas*.h"):
                    if not (blas.parent / h.name).exists():
                        (blas.parent / h.name).symlink_to(h)
            lib = devrt.parent
            for name in ("libcublas.so", "libcublasLt.so"):
                found = sorted(lib.glob(name + ".*"))
                if not (lib / name).exists() and found:
                    (lib / name).symlink_to(found[0].name)
        log(f"baseline: cublasLt.h {blas.exists()}" + ("" if r.returncode == 0 else f" (apt: {(r.stderr or r.stdout).strip().splitlines()[-1:]})"))
    ok = nvcc.exists() and header.exists() and devrt.exists()
    log(f"baseline: nvcc {nvcc.exists()}, cuda_runtime.h {header.exists()}, libcudadevrt.a {devrt.exists()}")
    return ok


ensure_nvcc = ensure_cuda_devkit


def ensure_nvrtc_matches_toolkit(py: Path, log=print) -> None:
    import json as _json

    try:
        tk = _json.loads(Path("/usr/local/cuda/version.json").read_text())["cuda"]["version"]
    except (OSError, KeyError, ValueError):
        real = Path("/usr/local/cuda").resolve().name
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
    import ctypes.util

    if ctypes.util.find_library("mpi"):
        return True
    apt = ["apt-get"] if os.geteuid() == 0 else ["sudo", "-n", "apt-get"]
    env = dict(os.environ, DEBIAN_FRONTEND="noninteractive")
    try:
        quiet = dict(env=env, stdin=subprocess.DEVNULL, capture_output=True)
        subprocess.run(apt + ["update", "-qq"], check=False, timeout=600, **quiet)
        subprocess.run(apt + ["install", "-y", "-qq", "--no-install-recommends", "libopenmpi-dev", "openmpi-bin"], check=True, timeout=1200, **quiet)
    except (OSError, subprocess.SubprocessError) as e:
        log(f"baseline: Open MPI install failed ({e}); TensorRT-LLM cannot start")
        return False
    log("baseline: installed Open MPI for TensorRT-LLM")
    return True


def ensure_pip_nvcc_matches_cudart(py: Path, log=print) -> None:
    probe = "from importlib.metadata import version as v\nfor p in ('nvidia-cuda-runtime', 'nvidia-cuda-nvcc'):\n    try: print(v(p))\n    except Exception: print('')"
    try:
        rt, cc = subprocess.run([str(py), "-c", probe], capture_output=True, text=True, timeout=60).stdout.split("\n")[:2]
    except (OSError, subprocess.SubprocessError, ValueError):
        return
    mm = lambda s: ".".join(s.split(".")[:2])
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
    import urllib.request

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
        import shutil

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
            ensure_nvcc(py, log=log)
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
        ensure_nvcc(py, log=log)
        ensure_flashinfer_aot(py, d / ".flashinfer-aot", log=log)
        if engine == "sglang":
            ensure_pip_nvcc_matches_cudart(py, log=log)
    (d / ".ok").write_text(version + "\n")
    return py
