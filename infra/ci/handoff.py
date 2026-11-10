#!/usr/bin/env python3
"""Pass small files between the jobs of a run without GitHub's artifact storage (its quota once blocked every deploy).

  pack DIR                 DIR as one base64 line (a job output: the job specs expand hands to every bench)
  unpack DEST              that line, from stdin, unpacked into DEST
  send NAME DIR [FILE...]  DIR (or only those FILEs in it) printed into this job's log as base64 lines
  recv [--run-id ID] [--job RE] [--merge] DEST
                           those lines read back from the logs of a run's jobs (RE: a regex on the job's own name,
                           without its matrix values or caller), each NAME unpacked into DEST/NAME, or with --merge
                           all into DEST (download-artifact's merge-multiple); needs GH_TOKEN with actions: read

Job logs do not count against the storage quota. Stdlib only: it runs on pods, Macs and the laptop alike.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import os
import re
import sys
import tarfile
import time
import urllib.error
import urllib.request

TAG = "pie-evals-file"
WIDTH = 1000  # characters a log line


def _tar(root: str, files: list[str]) -> bytes:
    buf = io.BytesIO()
    try:
        import lzma  # noqa: F401  (job specs are 6x smaller as xz than as gzip)
        mode = "w:xz"
    except ImportError:
        mode = "w:gz"
    with tarfile.open(fileobj=buf, mode=mode) as t:
        for f in files or sorted(os.listdir(root)):
            p = os.path.join(root, f)
            if os.path.exists(p):
                t.add(p, arcname=f)
    return buf.getvalue()


def _untar(data: bytes, dest: str) -> int:
    os.makedirs(dest, exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:*") as t:
        members = [m for m in t.getmembers() if not (m.name.startswith("/") or ".." in m.name.split("/"))]
        if hasattr(tarfile, "data_filter"):
            t.extractall(dest, members=members, filter="data")
        else:
            t.extractall(dest, members=members)
        return sum(1 for m in members if m.isfile())


def pack(root: str) -> None:
    print(base64.b64encode(_tar(root, [])).decode())


def unpack(dest: str) -> None:
    n = _untar(base64.b64decode("".join(sys.stdin.read().split())), dest)
    print(f"{n} files -> {dest}", file=sys.stderr)


def send(name: str, root: str, files: list[str]) -> None:
    if not re.fullmatch(r"[A-Za-z0-9._-]+", name):
        sys.exit(f"bad name {name!r}")
    if not os.path.isdir(root):
        print(f"::warning::{root}: nothing to hand over")
        return
    data = base64.b64encode(_tar(root, files)).decode()
    chunks = [data[i:i + WIDTH] for i in range(0, len(data), WIDTH)]
    for i, c in enumerate(chunks):
        print(f"{TAG} {name} {i} {c}")
    print(f"{TAG}-end {name} {len(chunks)} {hashlib.sha256(data.encode()).hexdigest()}")
    sys.stdout.flush()


def _get(url: str, token: str, tries: int = 3) -> bytes:
    for i in range(tries):
        req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"})
        req.add_unredirected_header("Authorization", f"Bearer {token}")  # never sent on to the log's blob URL
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                return r.read()
        except OSError as e:
            # a job's log can lag its completion by a few seconds
            if i == tries - 1 or (isinstance(e, urllib.error.HTTPError) and e.code not in (404, 429) and e.code < 500):
                raise
            time.sleep(10 * (i + 1))
    raise AssertionError


def recv(run_id: str, job: str, merge: bool, dest: str) -> None:
    api = os.environ.get("GITHUB_API_URL", "https://api.github.com")
    repo = os.environ["GITHUB_REPOSITORY"]
    token = os.environ.get("GH_TOKEN") or os.environ["GITHUB_TOKEN"]
    jobs, page = [], 1
    while True:
        got = json.loads(_get(f"{api}/repos/{repo}/actions/runs/{run_id}/jobs?per_page=100&page={page}", token))["jobs"]
        jobs += got
        if len(got) < 100:
            break
        page += 1
    found = 0
    for j in jobs:
        # "run / bench (weekly-..., h100, ...)": the caller's job name and the matrix values aside
        own = re.sub(r" \(.*\)$", "", j["name"]).split(" / ")[-1]
        if not re.fullmatch(job, own) or j.get("status") != "completed" or j.get("conclusion") == "skipped":
            continue
        try:
            log = _get(f"{api}/repos/{repo}/actions/jobs/{j['id']}/logs", token).decode("utf-8", "replace")
        except OSError as e:
            print(f"::warning::{j['name']}: no log ({e})")
            continue
        parts: dict[str, dict[int, str]] = {}
        for line in log.splitlines():
            body = line.split(" ", 1)[1] if " " in line else ""  # each line starts with its timestamp
            f = body.split(" ")
            if f[0] == TAG and len(f) == 4:
                parts.setdefault(f[1], {})[int(f[2])] = f[3]
            elif f[0] == TAG + "-end" and len(f) == 4:
                name, n, sha = f[1], int(f[2]), f[3]
                chunks = parts.pop(name, {})
                data = "".join(chunks.get(i, "") for i in range(n))
                if len(chunks) != n or hashlib.sha256(data.encode()).hexdigest() != sha:
                    print(f"::warning::{j['name']}: {name} arrived damaged; skipped")
                    continue
                d = dest if merge else os.path.join(dest, name)
                print(f"{name}: {_untar(base64.b64decode(data), d)} files -> {d}")
                found += 1
    print(f"{found} handed over from run {run_id}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("pack"); p.add_argument("dir")
    p = sub.add_parser("unpack"); p.add_argument("dest")
    p = sub.add_parser("send"); p.add_argument("name"); p.add_argument("dir"); p.add_argument("files", nargs="*")
    p = sub.add_parser("recv"); p.add_argument("--run-id", default=os.environ.get("GITHUB_RUN_ID")); p.add_argument("--job", default=".*")
    p.add_argument("--merge", action="store_true"); p.add_argument("dest")
    a = ap.parse_args()
    if a.cmd == "pack":
        pack(a.dir)
    elif a.cmd == "unpack":
        unpack(a.dest)
    elif a.cmd == "send":
        send(a.name, a.dir, a.files)
    else:
        recv(a.run_id, a.job, a.merge, a.dest)


if __name__ == "__main__":
    main()
