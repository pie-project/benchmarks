"""Sample the serving process with macOS ``sample`` while a cell runs.

Opt-in: set ``PIE_EVALS_SAMPLE_SECS`` and every engine boot writes a call-tree
sample of its heaviest process (the one holding the most resident memory, which
is the process that runs the model) to ``<out>/profile/<engine>-<artifact>.txt``.
Sampling slows the process, so a profiled run is a diagnostic, never a measurement.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

ENV = "PIE_EVALS_SAMPLE_SECS"


def _tree(roots: list[int]) -> dict[int, int]:
    """pid -> resident KiB, for ``roots`` and everything they spawned."""
    out = subprocess.run(["ps", "-axo", "pid=,ppid=,rss="], capture_output=True, text=True, check=False).stdout
    kids: dict[int, list[int]] = {}
    rss: dict[int, int] = {}
    for line in out.splitlines():
        parts = line.split()
        if len(parts) != 3:
            continue
        pid, ppid, kib = (int(x) for x in parts)
        kids.setdefault(ppid, []).append(pid)
        rss[pid] = kib
    seen: dict[int, int] = {}
    stack = list(roots)
    while stack:
        pid = stack.pop()
        if pid in seen or pid not in rss:
            continue
        seen[pid] = rss[pid]
        stack.extend(kids.get(pid, []))
    return seen


def start(pids: list[int], out_path: Path) -> subprocess.Popen | None:
    """Start sampling the heaviest process under ``pids``; None when disabled or unavailable."""
    seconds = os.environ.get(ENV, "").strip()
    if not seconds or not shutil.which("sample") or not pids:
        return None
    tree = _tree(list(pids))
    if not tree:
        return None
    target = max(tree, key=tree.get)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    return subprocess.Popen(["sample", str(target), seconds, "-file", str(out_path)],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
