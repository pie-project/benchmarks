from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path


def ensure_python_headers(py: Path, log=print) -> bool:
    try:
        out = subprocess.run(
            [
                str(py),
                "-c",
                "import sys, sysconfig; print(sysconfig.get_paths()['include']); print(sys.version_info[0], sys.version_info[1])",
            ],
            capture_output=True,
            text=True,
            check=True,
            timeout=60,
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
        subprocess.run(
            apt + ["update", "-qq"], env=env, check=False, timeout=600, capture_output=True
        )
        subprocess.run(
            apt + ["install", "-y", "-qq", pkg],
            env=env,
            check=True,
            timeout=900,
            capture_output=True,
        )
    except (OSError, subprocess.SubprocessError) as e:
        log(f"baseline: {pkg} install failed ({e}); engines that JIT C extensions will crash")
        return False
    ok = (include / "Python.h").exists()
    log(f"baseline: {pkg} installed; Python.h present: {ok}")
    return ok


def cuda_toolkit_version(py: Path | None = None) -> tuple[str, str] | None:
    if py is not None:
        try:
            cuda = subprocess.run(
                [str(py), "-c", "import torch; print(torch.version.cuda)"],
                capture_output=True,
                text=True,
                check=True,
                timeout=300,
            ).stdout.strip()
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
        out = subprocess.run(
            ["dpkg-query", "-W", "-f", "${Package}\n", "cuda-cudart-*"],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        ).stdout
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
    pkgs = [
        p
        for p, missing in (
            (f"cuda-nvcc-{major}-{minor}", not nvcc.exists()),
            (f"cuda-cudart-dev-{major}-{minor}", not (header.exists() and devrt.exists())),
        )
        if missing
    ]
    log(f"baseline: {nvcc.name}/{header.name}/{devrt.name} missing; installing {' '.join(pkgs)}")
    apt = ["apt-get"] if os.geteuid() == 0 else ["sudo", "-n", "apt-get"]
    env = dict(os.environ, DEBIAN_FRONTEND="noninteractive")
    try:
        subprocess.run(
            apt + ["update", "-qq"], env=env, check=False, timeout=600, capture_output=True
        )
        if pkgs:
            subprocess.run(
                apt + ["install", "-y", "-qq", "--no-install-recommends", *pkgs],
                env=env,
                check=True,
                timeout=1200,
                capture_output=True,
            )
    except (OSError, subprocess.SubprocessError) as e:
        log(
            f"baseline: CUDA toolkit install failed ({e}); engines that JIT CUDA kernels will crash"
        )
        return False
    if not blas.exists():
        r = subprocess.run(
            apt
            + [
                "install",
                "-y",
                "-qq",
                "--no-install-recommends",
                "--allow-change-held-packages",
                f"libcublas-dev-{major}-{minor}",
            ],
            env=env,
            check=False,
            timeout=1200,
            capture_output=True,
            text=True,
        )
        if not blas.exists() and py is not None:
            for inc in (
                Path(py)
                .absolute()
                .parent.parent.glob("lib/python3*/site-packages/nvidia/cu*/include")
            ):
                for h in inc.glob("cublas*.h"):
                    if not (blas.parent / h.name).exists():
                        (blas.parent / h.name).symlink_to(h)
            lib = devrt.parent
            for name in ("libcublas.so", "libcublasLt.so"):
                found = sorted(lib.glob(name + ".*"))
                if not (lib / name).exists() and found:
                    (lib / name).symlink_to(found[0].name)
        log(
            f"baseline: cublasLt.h {blas.exists()}"
            + (
                ""
                if r.returncode == 0
                else f" (apt: {(r.stderr or r.stdout).strip().splitlines()[-1:]})"
            )
        )
    ok = nvcc.exists() and header.exists() and devrt.exists()
    log(
        f"baseline: nvcc {nvcc.exists()}, cuda_runtime.h {header.exists()}, libcudadevrt.a {devrt.exists()}"
    )
    return ok


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
        have = subprocess.run(
            [
                str(py),
                "-c",
                "from importlib.metadata import version as v; print(v('nvidia-cuda-nvrtc'))",
            ],
            capture_output=True,
            text=True,
            timeout=60,
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return
    if not have or have.startswith(mm + "."):
        return
    log(
        f"baseline: pip NVRTC {have} beside the CUDA {mm} toolkit; installing nvidia-cuda-nvrtc=={mm}.*"
    )
    subprocess.run(
        ["uv", "pip", "install", "--quiet", "--python", str(py), f"nvidia-cuda-nvrtc=={mm}.*"],
        check=False,
        timeout=900,
    )


def ensure_mpi(log=print) -> bool:
    import ctypes.util

    if ctypes.util.find_library("mpi"):
        return True
    apt = ["apt-get"] if os.geteuid() == 0 else ["sudo", "-n", "apt-get"]
    env = dict(os.environ, DEBIAN_FRONTEND="noninteractive")
    try:
        quiet = dict(env=env, stdin=subprocess.DEVNULL, capture_output=True)
        subprocess.run(apt + ["update", "-qq"], check=False, timeout=600, **quiet)
        subprocess.run(
            apt
            + ["install", "-y", "-qq", "--no-install-recommends", "libopenmpi-dev", "openmpi-bin"],
            check=True,
            timeout=1200,
            **quiet,
        )
    except (OSError, subprocess.SubprocessError) as e:
        log(f"baseline: Open MPI install failed ({e}); TensorRT-LLM cannot start")
        return False
    log("baseline: installed Open MPI for TensorRT-LLM")
    return True


def ensure_pip_nvcc_matches_cudart(py: Path, log=print) -> None:
    probe = "from importlib.metadata import version as v\nfor p in ('nvidia-cuda-runtime', 'nvidia-cuda-nvcc'):\n    try: print(v(p))\n    except Exception: print('')"
    try:
        rt, cc = subprocess.run(
            [str(py), "-c", probe], capture_output=True, text=True, timeout=60
        ).stdout.split("\n")[:2]
    except (OSError, subprocess.SubprocessError, ValueError):
        return
    mm = lambda s: ".".join(s.split(".")[:2])
    if not rt or not cc or mm(rt) == mm(cc):
        return
    pins = [f"{p}=={mm(rt)}.*" for p in ("nvidia-cuda-nvcc", "nvidia-cuda-crt", "nvidia-nvvm")]
    log(f"baseline: pip nvcc {cc} beside cudart {rt}; installing {' '.join(pins)}")
    try:
        cmd = (
            ["uv", "pip", "install", "--quiet", "--python", str(py)]
            if shutil.which("uv")
            else [str(py), "-m", "pip", "install", "-q"]
        )
        subprocess.run([*cmd, *pins], check=True, timeout=900)
    except (OSError, subprocess.SubprocessError) as e:
        log(f"baseline: nvcc pin failed ({e})")


def ensure_flashinfer_aot(py: Path, marker: Path, log=print) -> bool:
    if marker.exists():
        return True
    try:
        out = subprocess.run(
            [
                str(py),
                "-c",
                "import flashinfer, torch; print(flashinfer.__version__); print(torch.version.cuda)",
            ],
            capture_output=True,
            text=True,
            check=True,
            timeout=300,
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
                subprocess.run(
                    [
                        "uv",
                        "pip",
                        "install",
                        "--quiet",
                        "--python",
                        str(py),
                        "--extra-index-url",
                        index,
                        spec,
                    ],
                    check=True,
                    timeout=1800,
                )
            else:
                subprocess.run(
                    [str(py), "-m", "pip", "install", "-q", "--extra-index-url", index, spec],
                    check=True,
                    timeout=1800,
                )
        except (OSError, subprocess.SubprocessError) as e:
            log(f"baseline: {spec} install failed ({e}); FlashInfer may JIT and need nvcc")
            ok = False
    if ok:
        marker.write_text(fi + "\n")
    return ok
