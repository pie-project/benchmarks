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

from pie_bench.engines.processes import process_table, tree_pids
from pie_bench.profiler.tracers.span import span

INSTRUMENT = "GPU"
TABLE = '/trace-toc/run[@number="1"]/data/table[@schema="metal-gpu-intervals"]'
LIMIT_S = 3600


def spool() -> set[Path]:
    tmp = subprocess.run(
        ["getconf", "DARWIN_USER_TEMP_DIR"], capture_output=True, text=True
    ).stdout.strip()
    return (
        {p for pattern in ("instruments*", "xrgpu_aps_*") for p in Path(tmp).glob(pattern)}
        if tmp
        else set()
    )


def rows(path: Path):
    cols, ids = [], {}
    for _, el in ET.iterparse(str(path), events=("end",)):
        if el.tag == "mnemonic":
            cols.append(el.text)
        if el.tag != "row":
            continue
        for d in el.iter():
            if d is not el and "id" in d.attrib:
                ids[d.attrib["id"]] = d.text if len(d) == 0 else d.attrib.get("fmt")
        row = dict(
            zip(
                cols,
                (
                    ids.get(c.attrib["ref"])
                    if "ref" in c.attrib
                    else c.text
                    if len(c) == 0
                    else c.attrib.get("fmt")
                    for c in el
                ),
            )
        )
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
        out.mkdir(parents=True, exist_ok=True)
        trace = out / "metal.trace"
        shutil.rmtree(trace, ignore_errors=True)
        before = spool()
        proc = subprocess.Popen(
            [
                "xctrace",
                "record",
                "--instrument",
                INSTRUMENT,
                "--all-processes",
                "--time-limit",
                f"{LIMIT_S}s",
                "--output",
                str(trace),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        started, done, pids = threading.Event(), threading.Event(), set()

        def pump():
            with open(out / "xctrace.log", "w") as log:
                for line in proc.stdout:
                    log.write(line)
                    if "Ctrl-C" in line:
                        started.set()

        def watch():
            while not done.wait(0.25):
                pids.update(tree_pids([os.getpid()], process_table()) - {os.getpid()})

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
                    shutil.rmtree(p, ignore_errors=True) if p.is_dir() else p.unlink(
                        missing_ok=True
                    )
            (out / "pids.json").write_text(json.dumps(sorted(pids)))

    def intervals(self, out: Path) -> list[tuple[int, int]]:
        trace, pids = out / "metal.trace", set(json.loads((out / "pids.json").read_text()))
        toc = subprocess.run(
            ["xctrace", "export", "--input", str(trace), "--toc"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        t0 = round(
            datetime.fromisoformat(
                re.search(r"<start-date>([^<]+)</start-date>", toc).group(1)
            ).timestamp()
            * 1e9
        )
        table = out / "metal-gpu-intervals.xml"
        subprocess.run(
            ["xctrace", "export", "--input", str(trace), "--xpath", TABLE, "--output", str(table)],
            capture_output=True,
            check=True,
        )
        return [(t0 + s, t0 + s + d) for s, d, pid in rows(table) if pid in pids]
