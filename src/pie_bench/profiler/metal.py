"""Metal: the GPU's work intervals on Apple silicon, from an Instruments recording of the GPU alone.

xctrace records every process; the intervals kept are those of the processes under this profiler (the engine and its
bench client), on the trace's own clock moved to Unix time by the trace's start date.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import signal
import subprocess
import threading
import xml.etree.ElementTree as ET
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from . import span

# the GPU instrument alone: the same metal-gpu-intervals as the Metal System Trace template (an M5 Max mlx-lm server's GPU
# busy time 8.65 s either way), in a trace 30 times smaller that saves in seconds, not minutes. Either way the kernel
# tracing under it costs a host-bound engine time: mlx-lm's 512-token prefill 8 to 15% (pie's 0 to 3%)
INSTRUMENT = "GPU"
TABLE = '/trace-toc/run[@number="1"]/data/table[@schema="metal-gpu-intervals"]'
LIMIT_S = 3600


def descendants(root: int) -> set[int]:
    """Every process below root."""
    out = subprocess.run(["ps", "-axo", "pid=,ppid="], capture_output=True, text=True).stdout
    kids: dict[int, list[int]] = {}
    for line in out.splitlines():
        pid, ppid = (int(x) for x in line.split())
        kids.setdefault(ppid, []).append(pid)
    seen, stack = set(), [root]
    while stack:
        for k in kids.get(stack.pop(), []):
            if k not in seen:
                seen.add(k)
                stack.append(k)
    return seen


def spool() -> set[Path]:
    """Instruments' temporary recording files, which stay behind (GBs a minute) after a trace is saved."""
    tmp = subprocess.run(["getconf", "DARWIN_USER_TEMP_DIR"], capture_output=True, text=True).stdout.strip()
    return {p for pattern in ("instruments*", "xrgpu_aps_*") for p in Path(tmp).glob(pattern)} if tmp else set()


def rows(path: Path):
    """(start ns, duration ns, pid) of each row of an exported metal-gpu-intervals table."""
    cols, ids = [], {}
    for _, el in ET.iterparse(str(path), events=("end",)):
        if el.tag == "mnemonic":
            cols.append(el.text)
        if el.tag != "row":
            continue
        for d in el.iter():
            if d is not el and "id" in d.attrib:
                ids[d.attrib["id"]] = d.text if len(d) == 0 else d.attrib.get("fmt")
        row = dict(zip(cols, (ids.get(c.attrib["ref"]) if "ref" in c.attrib else c.text if len(c) == 0 else c.attrib.get("fmt") for c in el)))
        pid = re.search(r"\((\d+)\)\s*$", str(row.get("process") or ""))
        if pid and row.get("start") and row.get("duration"):
            yield int(row["start"]), int(row["duration"]), int(pid.group(1))
        el.clear()


class Tracer:
    name = "metal"
    prefix: list[str] = []
    env: dict[str, str] = {}

    def __init__(self, out: Path):
        self.out = out

    @contextmanager
    def recording(self, out: Path):
        """Records the whole machine's GPU work while the block runs, noting the processes below this one."""
        out.mkdir(parents=True, exist_ok=True)
        trace = out / "metal.trace"
        shutil.rmtree(trace, ignore_errors=True)
        before = spool()
        proc = subprocess.Popen(["xctrace", "record", "--instrument", INSTRUMENT, "--all-processes", "--time-limit", f"{LIMIT_S}s", "--output", str(trace)],
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        started, done, pids = threading.Event(), threading.Event(), set()

        def pump():
            with open(out / "xctrace.log", "w") as log:
                for line in proc.stdout:
                    log.write(line)
                    if "Ctrl-C" in line:
                        started.set()

        def watch():
            while not done.wait(0.25):
                pids.update(descendants(os.getpid()))

        threading.Thread(target=pump, daemon=True).start()
        if not started.wait(120):
            proc.kill()
            raise RuntimeError("xctrace did not start recording within 120 s")
        threading.Thread(target=watch, daemon=True).start()
        try:
            with span(out):
                yield
        finally:
            done.set()
            proc.send_signal(signal.SIGINT)
            try:
                proc.wait(timeout=900)
            except subprocess.TimeoutExpired:
                proc.kill()
                raise RuntimeError("xctrace did not save the trace within 15 min") from None
            finally:
                for p in spool() - before:
                    shutil.rmtree(p, ignore_errors=True) if p.is_dir() else p.unlink(missing_ok=True)
            (out / "pids.json").write_text(json.dumps(sorted(pids)))

    def intervals(self, out: Path) -> list[tuple[int, int]]:
        """The GPU work intervals of the recorded processes, in Unix ns."""
        trace, pids = out / "metal.trace", set(json.loads((out / "pids.json").read_text()))
        toc = subprocess.run(["xctrace", "export", "--input", str(trace), "--toc"], capture_output=True, text=True, check=True).stdout
        t0 = round(datetime.fromisoformat(re.search(r"<start-date>([^<]+)</start-date>", toc).group(1)).timestamp() * 1e9)
        table = out / "metal-gpu-intervals.xml"
        subprocess.run(["xctrace", "export", "--input", str(trace), "--xpath", TABLE, "--output", str(table)], capture_output=True, check=True)
        return [(t0 + s, t0 + s + d) for s, d, pid in rows(table) if pid in pids]
