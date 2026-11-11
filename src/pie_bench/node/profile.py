from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

ENV = "PIE_BENCH_SAMPLE_SECS"


def _tree(roots: list[int]) -> dict[int, int]:
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
