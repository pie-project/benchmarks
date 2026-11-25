from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from pie_bench.engines.processes import memory_table, tree_pids

ENV = "PIE_BENCH_SAMPLE_SECS"


def start(pids: list[int], out_path: Path) -> subprocess.Popen | None:
    seconds = os.environ.get(ENV, "").strip()
    if not seconds or not shutil.which("sample") or not pids:
        return None
    table = memory_table()
    tree = tree_pids(list(pids), table)
    if not tree:
        return None
    target = max(sorted(tree), key=lambda pid: table[pid][1])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    return subprocess.Popen(
        ["sample", str(target), seconds, "-file", str(out_path)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
