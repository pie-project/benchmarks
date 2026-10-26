"""pie's kernel test suites (``kernels-cuda`` / ``kernels-rocm``) on one device, as one
quality row per platform: artifact ``kernels-<backend>``, task ``kernels@<platform>``,
score = passed / (passed + failed). Test binaries print ``KERR <name> max_abs=<x>
max_rel=<y>`` under ``PIE_KERNEL_ERR=1``; those land in ``errors``."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

_RUNNING = re.compile(r"^\s*Running (?:unittests )?(\S+)")
_RESULT = re.compile(r"^test (\S+) \.\.\. ?(.*)$")
_BLOCK = re.compile(r"^---- (\S+) std(?:out|err) ----$")
_KERR = re.compile(r"KERR (\S+) max_abs=(\S+) max_rel=(\S+)")
_CRASH = re.compile(r"process didn't exit successfully: .*")


def _binary(path: str) -> str:
    p = Path(path)
    return "lib" if p.parts[:1] == ("src",) else (p.parent.name if p.stem == "main" else p.stem)


def _num(x: str) -> float | None:
    try:
        return float(x)
    except ValueError:
        return None


def parse(text: str) -> dict:
    """Counts, failing tests with their messages, and the KERR error table from ``cargo test`` output."""
    passed: list[str] = []
    failed: dict[str, str] = {}
    ignored: list[str] = []
    errors: dict[str, dict] = {}
    blocks: dict[str, list[str]] = {}
    binary, pending, block = "", None, None
    for raw in text.splitlines():
        line = raw.rstrip()
        k = _KERR.search(line)
        if k:
            name, a, r = k.group(1), _num(k.group(2)), _num(k.group(3))
            prev = errors.get(name)
            errors[name] = {"max_abs": max(a, prev["max_abs"]) if prev and a is not None and prev["max_abs"] is not None else a,
                            "max_rel": max(r, prev["max_rel"]) if prev and r is not None and prev["max_rel"] is not None else r}
            continue
        m = _RUNNING.match(line)
        if m:
            binary, pending, block = _binary(m.group(1)), None, None
            continue
        m = _CRASH.search(line)
        if m and pending:
            failed[pending] = (failed.get(pending, "") + " " + m.group(0)).strip()
            pending = None
            continue
        m = _BLOCK.match(line)
        if m:
            block = f"{binary}::{m.group(1)}"
            blocks.setdefault(block, [])
            continue
        if line in ("failures:", "successes:") or line.startswith("test result:"):
            block = None
            continue
        m = _RESULT.match(line)
        if m and block is None:
            name, res = f"{binary}::{m.group(1)}", m.group(2)
            if res == "ok":
                passed.append(name)
            elif res == "FAILED":
                failed[name] = ""
            elif res.startswith("ignored"):
                ignored.append(name)
            else:  # the binary died inside this test: no result, then cargo's exit line
                failed[name] = res
                pending = name
            continue
        if block is not None and line and not line.startswith("note: run with `RUST_BACKTRACE"):
            blocks[block].append(line)
    for name in failed:
        msg = [ln for ln in blocks.get(name, []) if not _KERR.search(ln)]
        if msg:
            failed[name] = "\n".join(msg[:20])[:2000]
    n = len(passed) + len(failed)
    out: dict = {"passed": len(passed), "failed": len(failed), "ignored": len(ignored),
                 "failures": [{"name": k, "message": v} for k, v in failed.items()],
                 "score": round(len(passed) / n, 4) if n else None, "n": n, "correct": len(passed)}
    out["ci95"] = [out["score"], out["score"]] if n else None
    if errors:
        out["errors"] = errors
        for key in ("max_abs", "max_rel"):
            have = [(v[key], k) for k, v in errors.items() if v[key] is not None]
            if have:
                v, k = max(have)
                out[f"worst_{key[4:]}"] = {"name": k, key: v}
    return out


def run_kernels(platform_id: str, *, pie_root: Path, matrix_dir: str = "matrix", store_dir: str | None = None, tag: str | None = None,
                tag_kind: str | None = None, out_dir: Path = Path("kernels-out"), log_file: Path | None = None, log=print) -> dict:
    """Run (or, with ``log_file``, only parse) the platform backend's kernel tests and store one quality row."""
    import json

    from pie_evals.plan.matrix import Matrix
    from pie_evals.results.store import Store

    plat = Matrix.load(matrix_dir).platforms[platform_id]
    backend = str(plat.backend)
    if backend not in ("cuda", "rocm"):
        raise RuntimeError(f"{platform_id}: no kernel suite for backend {backend}")
    out_dir.mkdir(parents=True, exist_ok=True)
    t0 = time.monotonic()
    rc = None
    if log_file is None:
        log_file = out_dir / f"kernels-{platform_id}.log"
        # cuda/rocm gate their tests behind the backend feature; Metal's and XLA's kernels are tested in their engine crates too
        crates = ["-p", f"kernels-{backend}", "--features", backend] if backend in ("cuda", "rocm") else ["-p", f"kernels-{backend}", "-p", f"engine-{backend}"]
        cmd = ["cargo", "test", "--release", *crates, "--tests", "--no-fail-fast", "--", "--test-threads=1", "--show-output"]
        if shutil.which("rustup"):  # the toolchain pie's rust-toolchain.toml pins
            subprocess.run(["rustup", "toolchain", "install"], cwd=pie_root, check=False)
        log(" ".join(cmd))
        with log_file.open("w") as fh:
            p = subprocess.Popen(cmd, cwd=pie_root, env={**os.environ, "PIE_KERNEL_ERR": "1"}, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
            for line in p.stdout:
                fh.write(line)
                sys.stderr.write(line)
            rc = p.wait()
    text = log_file.read_text(errors="replace")
    commit = subprocess.run(["git", "-C", str(pie_root), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    summary: dict = {"artifact": f"kernels-{backend}", "model": f"kernels-{backend}", "engine": "pie", "platform": platform_id,
                     "task": f"kernels@{platform_id}", "backend": backend, "version": commit[:12]}
    summary.update(parse(text))
    if rc not in (None, 0) and summary["n"] == 0:
        summary["error"] = "\n".join(text.splitlines()[-40:])[-4000:]
    summary["minutes"] = round((time.monotonic() - t0) / 60, 1)
    summary["date"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    (out_dir / f"kernels-{platform_id}.json").write_text(json.dumps(summary, indent=1))
    where = Store(store_dir).write_quality(summary, tag=tag, tag_kind=tag_kind)
    worst = summary.get("worst_rel") or summary.get("worst_abs")
    log(f"kernels {backend}@{platform_id}: {summary['passed']} passed, {summary['failed']} failed, {summary['ignored']} ignored"
        + (f"; worst {worst}" if worst else "") + f" -> {where}")
    return summary
