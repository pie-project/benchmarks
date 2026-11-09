"""Build pie once per (commit, features) and cache the artifacts on the
shared volume, so a fan-out of N pods builds 0 times, not N.

Artifacts per build: the ``pie`` CLI binary, the embedded-engine wheel
(``pie_server-*.whl``, maturin) with its ``_engine`` .so, and the
``text-completion-bench`` guest (wasm). ``restore`` puts them where the bench
scripts look; ``build`` produces them in a pod-local checkout so concurrent
pods never touch the same work tree or cargo target dir.

pie compiles its CUDA kernels with NVRTC at runtime (cudarc ``nvrtc``), so a
CUDA build is GPU-generation independent and one cache entry serves every
NVIDIA platform. The ROCm build (``--features rocm``) is the same engine over
HIP: hiprtc compiles its kernels at runtime for the card's gfx target, so one
entry serves every AMD Instinct platform too.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import time
from pathlib import Path

PIE_UPSTREAM = "https://github.com/pie-project/pie.git"  # public; pods have no SSH key
BENCH_DEPS = ["websockets", "msgpack", "blake3", "cryptography", "numpy", "transformers", "jinja2", "tiktoken"]  # pie_client + scripts/bench/common.py (pie_client itself rides on PYTHONPATH); transformers renders chat templates


DEFAULT_CACHE = Path.home() / ".cache/pie-evals"
DEFAULT_PIE_ROOT = Path("/root/pie")


def _cache_root(root: Path | None) -> Path:
    return root or Path(os.environ.get("PIE_EVALS_CACHE", DEFAULT_CACHE))


def bench_python(cache_root: Path | None = None, log=print) -> Path:
    """A venv on the shared cache that runs pie's bench scripts (and this repo's
    clients, which share their prompt construction): the client deps,
    transformers for the chat template, plus the embedded-engine wheel.
    Created with uv when present (the runner image ships uv but no pip), else
    python3 -m venv."""
    venv = _cache_root(cache_root) / "venv-pie"
    py = venv / "bin" / "python"
    if not py.exists():
        log(f"venv: creating {venv}")
        if shutil.which("uv"):
            subprocess.run(["uv", "venv", "--quiet", "--python", "3.12", str(venv)], check=True)
        else:
            subprocess.run(["python3", "-m", "venv", str(venv)], check=True)
        _pip_install(py, BENCH_DEPS)
    elif subprocess.run([str(py), "-c", "import transformers, jinja2, tiktoken"], capture_output=True).returncode != 0:
        # a venv made before the baseline clients needed the chat template renderer
        log(f"venv: adding the bench client deps to {venv}")
        _pip_install(py, BENCH_DEPS)
    return py


def _pip_install(py: Path, args: list[str]) -> None:
    if shutil.which("uv"):
        subprocess.run(["uv", "pip", "install", "--quiet", "--python", str(py), *args], check=True)
    else:
        subprocess.run([str(py), "-m", "pip", "install", "-q", *args], check=True)


def python_dir(pie_root: Path) -> Path:
    """pie's python packages: `packages/python` since pie #838, `python` before."""
    return pie_root / "packages/python" if (pie_root / "packages/python").is_dir() else pie_root / "python"


def cache_key(commit: str, features: list[str]) -> str:
    return f"{commit[:12]}-{'+'.join(features) or 'none'}"


def cache_dir(commit: str, features: list[str], root: Path | None = None) -> Path:
    return _cache_root(root) / "builds" / cache_key(commit, features)


def is_cached(commit: str, features: list[str], root: Path | None = None) -> bool:
    d = cache_dir(commit, features, root)
    wheel = any(d.glob("pie_server-*.whl")) or not ({"cuda", "rocm"} & set(features))
    return (d / "pie").exists() and (d / "wasm").is_dir() and any((d / "wasm").glob("*.wasm")) and wheel


def _git(args: list[str], cwd: Path | None = None, retries: int = 3, timeout_s: int = 1800) -> None:
    """git with HTTP/1.1 (RunPod hosts cancel HTTP/2 streams on long transfers) and retries."""
    last: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            subprocess.run(["git", "-c", "http.version=HTTP/1.1", "-c", "http.lowSpeedLimit=1000", "-c", "http.lowSpeedTime=120", *args], cwd=cwd, check=True, timeout=timeout_s)
            return
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            last = e
            if attempt < retries:
                time.sleep(15 * attempt)
    assert last is not None
    raise last


def ensure_checkout(pie_root: Path, commit: str, mirror: Path | None = None, upstream: str = PIE_UPSTREAM) -> None:
    """A pod-local checkout at ``pie_root`` pinned to ``commit``.

    With a bare mirror on the shared volume it is the clone source (fast, no
    network). Without one — a cold pod — only the pinned commit is fetched
    (shallow): a full-history clone over a flaky host link took 33 minutes and
    then died mid-transfer."""
    if not (pie_root / ".git").exists():
        if mirror and mirror.exists():
            _git(["clone", "--quiet", str(mirror), str(pie_root)])
            subprocess.run(["git", "-C", str(pie_root), "remote", "set-url", "origin", upstream], check=False)
        else:
            pie_root.mkdir(parents=True, exist_ok=True)
            subprocess.run(["git", "init", "--quiet", str(pie_root)], check=True)
            subprocess.run(["git", "-C", str(pie_root), "remote", "add", "origin", upstream], check=True)
            _git(["-C", str(pie_root), "fetch", "--quiet", "--depth", "1", "origin", commit])
            subprocess.run(["git", "-C", str(pie_root), "checkout", "--quiet", "FETCH_HEAD"], check=True)
            return
    head = subprocess.run(["git", "-C", str(pie_root), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    if not head.startswith(commit) and not commit.startswith(head):
        r = subprocess.run(["git", "-C", str(pie_root), "checkout", "--quiet", "--force", commit], capture_output=True, text=True)
        if r.returncode != 0:
            _git(["-C", str(pie_root), "fetch", "--quiet", "--depth", "1", "origin", commit])
            subprocess.run(["git", "-C", str(pie_root), "checkout", "--quiet", "--force", "FETCH_HEAD"], check=True)


def update_mirror(mirror: Path, upstream: str = PIE_UPSTREAM) -> None:
    """Maintain the bare mirror on the shared volume. Skipped when there is no
    volume (``PIE_EVALS_VOLUME`` unset): a cold pod must not spend half an hour
    mirroring history it will throw away."""
    if not os.environ.get("PIE_EVALS_VOLUME") and not mirror.exists():
        return
    if not mirror.exists():
        _git(["clone", "--quiet", "--mirror", upstream, str(mirror)], timeout_s=3600)
    else:
        subprocess.run(["git", "-C", str(mirror), "fetch", "--quiet", "--prune"], check=False, timeout=1800)


def build(pie_root: Path, commit: str, features: list[str], *, cache_root: Path | None = None, target_dir: Path | None = None, python: str = "python3", timeout_s: int = 3600, log=print) -> Path:
    """Build the three artifacts and store them under the cache dir."""
    out = cache_dir(commit, features, cache_root)
    out.mkdir(parents=True, exist_ok=True)
    env = {**os.environ}
    if target_dir:
        env["CARGO_TARGET_DIR"] = str(target_dir)  # pod-local: never a shared cargo target
    feats = ",".join(features)
    if "wgpu" in features and not env.get("PIE_SLANGC") and not shutil.which("slangc"):
        env["PIE_SLANGC"] = str(ensure_slangc(pie_root, _cache_root(cache_root), log=log))
    log(f"build: pie {commit[:12]} features={feats} target={env.get('CARGO_TARGET_DIR', 'in-tree')}")
    subprocess.run(["cargo", "build", "--release", "-p", "pie", "--bin", "pie", "--features", feats], cwd=pie_root, env=env, check=True, timeout=timeout_s)
    tdir = Path(env.get("CARGO_TARGET_DIR", pie_root / "target"))
    shutil.copy2(tdir / "release" / "pie", out / "pie")
    # embedded engine wheel (the python bench path on CUDA, and on ROCm: the same engine over HIP),
    # built against the bench venv's interpreter
    if {"cuda", "rocm"} & set(features):
        py = bench_python(cache_root, log=log)
        log("build: embedded engine wheel (maturin)")
        if shutil.which("uv"):
            maturin = ["uv", "tool", "run", "maturin"]
        else:
            _pip_install(py, ["maturin"])
            maturin = [str(py), "-m", "maturin"]
        # the server crate defaults to `cuda`, and `cuda` beside `rocm` is a compile error ("a build carries one")
        nodef = [] if "cuda" in features else ["--no-default-features"]
        subprocess.run([*maturin, "build", "--release", "-o", str(out), *nodef, "--features", feats, "-i", str(py)], cwd=python_dir(pie_root) / "server", env=env, check=True, timeout=timeout_s)
    if "wgpu" in features:
        # pie in a browser tab (the webgpu platforms): the runtime and its WebGPU engine as wasm, @pie-project/server-web
        log("build: @pie-project/server-web (wasm32-unknown-unknown + wasm-bindgen)")
        if not shutil.which("wasm-bindgen"):
            lock = (pie_root / "Cargo.lock").read_text()
            import re as _re

            ver = _re.search(r'name = "wasm-bindgen"\nversion = "([^"]+)"', lock).group(1)
            # from pie's checkout, so its rust-toolchain pins the cargo: a pod's rustup may have no default ("rustup could
            # not choose a version of cargo to run", parity 42562757717 on web-rtx4090)
            subprocess.run(["cargo", "install", "wasm-bindgen-cli", "--locked", "--version", ver], cwd=pie_root, env=env, check=True, timeout=timeout_s)
        if shutil.which("rustup"):
            subprocess.run(["rustup", "target", "add", "wasm32-unknown-unknown"], cwd=pie_root, env=env, check=False, timeout=timeout_s)
        wenv = {k: v for k, v in env.items() if k != "CARGO_TARGET_DIR"}
        subprocess.run(["bash", "packages/javascript/server-web/build.sh", "release"], cwd=pie_root, env=wenv, check=True, timeout=timeout_s)
        dist = pie_root / "packages/javascript/server-web/dist"
        if (out / "web").exists():
            shutil.rmtree(out / "web")
        shutil.copytree(dist, out / "web")
    # guest programs: the whole examples/ workspace (every inferlet the matrix can name), built
    # in-tree because bench_inferlet_paths walks up to examples/target; all .wasm are cached
    target = wasm_target(pie_root)
    log(f"build: every inferlet in examples/ ({target})")
    genv = {k: v for k, v in env.items() if k != "CARGO_TARGET_DIR"}
    # the target comes with the toolchain examples/ pins (pie #1010 moved the inferlets to WASI 0.3 on a nightly);
    # added explicitly, since a toolchain file that does not list it leaves cargo with "can't find crate for `core`"
    if shutil.which("rustup"):
        # `rustup toolchain install` with no name installs what the directory's toolchain file pins
        subprocess.run(["rustup", "toolchain", "install"], cwd=pie_root / "examples", env=genv, check=False, timeout=timeout_s)
        subprocess.run(["rustup", "target", "add", target], cwd=pie_root / "examples", env=genv, check=False, timeout=timeout_s)
    subprocess.run(["cargo", "build", "--release", "--target", target, "--workspace"], cwd=pie_root / "examples", env=genv, check=True, timeout=timeout_s)
    (out / "wasm").mkdir(exist_ok=True)
    n = 0
    for w in (pie_root / f"examples/target/{target}/release").glob("*.wasm"):
        shutil.copy2(w, out / "wasm" / w.name)
        n += 1
    log(f"build: {n} guest programs cached")
    (out / "COMMIT").write_text(commit + "\n")
    log(f"build: cached at {out}")
    return out


def ensure_slangc(pie_root: Path, cache: Path, log=print) -> Path:
    """The Slang compiler pie's kernels-slang needs to build the wgpu engine, at the version pie's own CI pins
    (.github/actions/toolchain: SLANG_VERSION), unpacked once on the cache."""
    import re
    import tarfile
    import urllib.request

    action = pie_root / ".github/actions/toolchain/action.yml"
    m = re.search(r"SLANG_VERSION:\s*'?([0-9.]+)", action.read_text()) if action.exists() else None
    ver = m.group(1) if m else "2026.17"
    d = cache / f"slang-{ver}"
    slangc = d / "bin" / "slangc"
    if not slangc.exists():
        log(f"build: fetching slangc {ver}")
        d.mkdir(parents=True, exist_ok=True)
        tgz = d / "slang.tar.gz"
        urllib.request.urlretrieve(f"https://github.com/shader-slang/slang/releases/download/v{ver}/slang-{ver}-linux-x86_64.tar.gz", tgz)
        with tarfile.open(tgz) as t:
            t.extractall(d)
        tgz.unlink()
    return slangc


def wasm_target(pie_root: Path) -> str:
    """The wasm target pie's inferlets build for: WASI 0.3 since pie #1010 (examples/rust-toolchain.toml), 0.2 before."""
    pinned = pie_root / "examples" / "rust-toolchain.toml"
    return "wasm32-wasip3" if pinned.exists() and "wasm32-wasip3" in pinned.read_text() else "wasm32-wasip2"


def restore(pie_root: Path, commit: str, features: list[str], *, cache_root: Path | None = None, python: str = "python3", set_env: bool = True, log=print) -> bool:
    """Put cached artifacts where the bench scripts look. Returns False on a cache miss."""
    d = cache_dir(commit, features, cache_root)
    if not is_cached(commit, features, cache_root):
        return False
    binary = pie_root / "target/release/pie"
    binary.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(d / "pie", binary)
    wdir = pie_root / f"examples/target/{wasm_target(pie_root)}/release"
    wdir.mkdir(parents=True, exist_ok=True)
    for w in (d / "wasm").glob("*.wasm"):
        shutil.copy(w, wdir / w.name)
        os.utime(wdir / w.name, None)  # newer than the freshly cloned sources (bench_inferlet_paths' staleness check)
    whl = sorted(d.glob("pie_server-*.whl"))
    if whl:
        py = bench_python(cache_root, log=log)
        _pip_install(py, ["--force-reinstall", "--no-deps", str(whl[-1])])
        # pie_bench.py puts python/server/python first on sys.path, which shadows the
        # installed package; the compiled module must sit in the source dir (maturin develop layout).
        # Its mtime must also be newer than every source under crates/ and python/server/src —
        # pie_bench's staleness guard — and a fresh clone's sources are newer than a cached .so.
        so = subprocess.run([str(py), "-c", "import pie._engine as e; print(e.__file__)"], capture_output=True, text=True).stdout.strip()
        if so:
            dst = python_dir(pie_root) / "server/python/pie" / Path(so).name
            shutil.copy(so, dst)
            os.utime(dst, None)
    if set_env:
        os.environ.setdefault("PIE_PY", str(bench_python(cache_root, log=log)))  # the pie adapter's interpreter
    log(f"restore: {d} -> {pie_root}")
    return True


def ensure(pie_root: Path, commit: str, features: list[str], *, cache_root: Path | None = None, target_dir: Path | None = None, python: str = "python3", log=print) -> None:
    if restore(pie_root, commit, features, cache_root=cache_root, python=python, log=log):
        return
    build(pie_root, commit, features, cache_root=cache_root, target_dir=target_dir, python=python, log=log)
    restore(pie_root, commit, features, cache_root=cache_root, python=python, log=log)
