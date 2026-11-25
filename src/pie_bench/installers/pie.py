from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tarfile
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from pie_bench.installers.bench_env import _cache_root, _pip_install, bench_python

PIE_UPSTREAM = "https://github.com/pie-project/pie.git"
PIE_EXE = "pie.exe" if os.name == "nt" else "pie"


def python_dir(pie_root: Path) -> Path:
    return pie_root / "packages/python" if (pie_root / "packages/python").is_dir() else pie_root / "python"


def cache_key(commit: str, features: list[str]) -> str:
    return f"{commit[:12]}-{'+'.join(features) or 'none'}"


def cache_dir(commit: str, features: list[str], root: Path | None = None) -> Path:
    return _cache_root(root) / "builds" / cache_key(commit, features)


def is_cached(commit: str, features: list[str], root: Path | None = None) -> bool:
    d = cache_dir(commit, features, root)
    wheel = any(d.glob("pie_server-*.whl")) or not ({"cuda", "rocm"} & set(features))
    return (d / PIE_EXE).exists() and (d / "wasm").is_dir() and any((d / "wasm").glob("*.wasm")) and wheel


def _git(args: list[str], cwd: Path | None = None, retries: int = 3, timeout_s: int = 1800) -> None:
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


def build(pie_root: Path, commit: str, features: list[str], *, cache_root: Path | None = None, target_dir: Path | None = None, timeout_s: int = 3600, log=print) -> Path:
    out = cache_dir(commit, features, cache_root)
    out.mkdir(parents=True, exist_ok=True)
    env = {**os.environ}
    if target_dir:
        env["CARGO_TARGET_DIR"] = str(target_dir)
    feats = ",".join(features)
    if "wgpu" in features and not env.get("PIE_SLANGC") and not shutil.which("slangc"):
        env["PIE_SLANGC"] = str(ensure_slangc(pie_root, _cache_root(cache_root), log=log))
    log(f"build: pie {commit[:12]} features={feats} target={env.get('CARGO_TARGET_DIR', 'in-tree')}")
    subprocess.run(["cargo", "build", "--release", "-p", "pie", "--bin", "pie", "--features", feats], cwd=pie_root, env=env, check=True, timeout=timeout_s)
    tdir = Path(env.get("CARGO_TARGET_DIR", pie_root / "target"))
    shutil.copy2(tdir / "release" / PIE_EXE, out / PIE_EXE)
    if {"cuda", "rocm"} & set(features):
        py = bench_python(cache_root, log=log)
        log("build: embedded engine wheel (maturin)")
        if shutil.which("uv"):
            maturin = ["uv", "tool", "run", "maturin"]
        else:
            _pip_install(py, ["maturin"])
            maturin = [str(py), "-m", "maturin"]
        nodef = [] if "cuda" in features else ["--no-default-features"]
        subprocess.run([*maturin, "build", "--release", "-o", str(out), *nodef, "--features", feats, "-i", str(py)], cwd=python_dir(pie_root) / "server", env=env, check=True, timeout=timeout_s)
    if "wgpu" in features:
        log("build: @pie-project/server-web (wasm32-unknown-unknown + wasm-bindgen)")
        if not shutil.which("wasm-bindgen"):
            lock = (pie_root / "Cargo.lock").read_text()
            ver = re.search(r'name = "wasm-bindgen"\nversion = "([^"]+)"', lock).group(1)
            subprocess.run(["cargo", "install", "wasm-bindgen-cli", "--locked", "--version", ver], cwd=pie_root, env=env, check=True, timeout=timeout_s)
        if shutil.which("rustup"):
            subprocess.run(["rustup", "target", "add", "wasm32-unknown-unknown"], cwd=pie_root, env=env, check=False, timeout=timeout_s)
        wenv = {k: v for k, v in env.items() if k != "CARGO_TARGET_DIR"}
        subprocess.run(["bash", "packages/javascript/server-web/build.sh", "release"], cwd=pie_root, env=wenv, check=True, timeout=timeout_s)
        dist = pie_root / "packages/javascript/server-web/dist"
        if (out / "web").exists():
            shutil.rmtree(out / "web")
        shutil.copytree(dist, out / "web")
    target = wasm_target(pie_root)
    log(f"build: every inferlet in examples/ ({target})")
    genv = {k: v for k, v in env.items() if k != "CARGO_TARGET_DIR"}
    if shutil.which("rustup"):
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
    action = pie_root / ".github/actions/toolchain/action.yml"
    m = re.search(r"SLANG_VERSION:\s*'?([0-9.]+)", action.read_text()) if action.exists() else None
    ver = m.group(1) if m else "2026.17"
    d = cache / f"slang-{ver}"
    slangc = d / "bin" / "slangc"
    if not slangc.exists():
        log(f"build: fetching slangc {ver}")
        d.mkdir(parents=True, exist_ok=True)
        tgz = d / "slang.tar.gz"
        url = f"https://github.com/shader-slang/slang/releases/download/v{ver}/slang-{ver}-linux-x86_64.tar.gz"
        for attempt in range(3):
            try:
                urllib.request.urlretrieve(url, tgz)
                break
            except OSError as e:
                if attempt == 2:
                    raise
                log(f"build: slangc download failed ({e}), retrying")
                time.sleep(10 * (attempt + 1))
        with tarfile.open(tgz) as t:
            t.extractall(d)
        tgz.unlink()
    return slangc


def wasm_target(pie_root: Path) -> str:
    pinned = pie_root / "examples" / "rust-toolchain.toml"
    return "wasm32-wasip3" if pinned.exists() and "wasm32-wasip3" in pinned.read_text() else "wasm32-wasip2"


def restore(pie_root: Path, commit: str, features: list[str], *, cache_root: Path | None = None, set_env: bool = True, log=print) -> bool:
    d = cache_dir(commit, features, cache_root)
    if not is_cached(commit, features, cache_root):
        return False
    binary = pie_root / "target/release" / PIE_EXE
    binary.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(d / PIE_EXE, binary)
    wdir = pie_root / f"examples/target/{wasm_target(pie_root)}/release"
    wdir.mkdir(parents=True, exist_ok=True)
    for w in (d / "wasm").glob("*.wasm"):
        shutil.copy(w, wdir / w.name)
        os.utime(wdir / w.name, None)
    whl = sorted(d.glob("pie_server-*.whl"))
    if whl:
        py = bench_python(cache_root, log=log)
        _pip_install(py, ["--force-reinstall", "--no-deps", str(whl[-1])])
        so = subprocess.run([str(py), "-c", "import pie._engine as e; print(e.__file__)"], capture_output=True, text=True).stdout.strip()
        if so:
            dst = python_dir(pie_root) / "server/python/pie" / Path(so).name
            shutil.copy(so, dst)
            os.utime(dst, None)
    if set_env:
        os.environ.setdefault("PIE_PY", str(bench_python(cache_root, log=log)))
    log(f"restore: {d} -> {pie_root}")
    return True


def ensure(pie_root: Path, commit: str, features: list[str], *, cache_root: Path | None = None, target_dir: Path | None = None, log=print) -> None:
    if restore(pie_root, commit, features, cache_root=cache_root, log=log):
        return
    build(pie_root, commit, features, cache_root=cache_root, target_dir=target_dir, log=log)
    restore(pie_root, commit, features, cache_root=cache_root, log=log)


PIE_REPO = "pie-project/pie"


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
