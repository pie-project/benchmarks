"""Xla: a TPU's op intervals, from the engine process's own device trace (an XSpace, what jax.profiler writes).

Processes that import jax arm a trace (jax_site/sitecustomize.py, first on PYTHONPATH); pie's XLA server arms one
through xla_trace.c, preloaded by the pie_xla.py launcher. SIGUSR1 starts the trace, SIGUSR2 stops it; markers
<pid>.started and <pid>.done (pie-<pid>.* for pie) say when each step is over. The served engines (vLLM, SGLang) are
traced for the whole round; pie's bench client starts and stops its own server's trace around its measured requests.
The intervals are the ops on the TPU devices' "XLA Ops" and "Async XLA Ops" lines (compute and its copies), in
Unix ns.
"""

from __future__ import annotations

import json
import os
import shutil
import signal
import subprocess
import time
from contextlib import contextmanager
from pathlib import Path

from . import span

SITE = Path(__file__).resolve().parent / "jax_site"
SHIM = Path(__file__).resolve().parent / "xla_trace.c"


class Tracer:
    name = "xla"
    prefix: list[str] = []

    def __init__(self, out: Path):
        self.dir = out / "xla"
        self.dir.mkdir(parents=True, exist_ok=True)
        so = out / "xla_trace.so"
        subprocess.run(["cc", "-O2", "-shared", "-fPIC", "-o", str(so), str(SHIM), "-ldl", "-lpthread"], check=True)
        self.env = {"PIE_BENCH_JAX_TRACE_DIR": str(self.dir), "PIE_BENCH_PIE_PRELOAD": str(so),
                    "PYTHONPATH": os.pathsep.join([str(SITE), *filter(None, [os.environ.get("PYTHONPATH")])])}

    def _armed(self) -> list[int]:
        pids = [int(p.stem) for p in self.dir.glob("*.pid") if p.stem.isdigit()]
        return [p for p in pids if _alive(p)]

    @contextmanager
    def recording(self, out: Path):
        """Traces the round: the served engines' processes from start to end, pie's around its measured requests.
        The traces made in it move to out/xla."""
        out.mkdir(parents=True, exist_ok=True)
        since = time.time()
        pids = self._armed()
        signal_all(self.dir, [str(p) for p in pids], signal.SIGUSR1, "started", 300)
        try:
            with span(out):
                yield
        finally:
            signal_all(self.dir, [str(p) for p in pids if _alive(p)], signal.SIGUSR2, "done", 900)
            (out / "xla").mkdir(exist_ok=True)
            for done in self.dir.glob("*.done"):
                trace = self.dir / done.stem
                if done.stat().st_mtime >= since and trace.is_dir():
                    shutil.move(str(trace), str(out / "xla" / trace.name))

    def intervals(self, out: Path) -> list[tuple[int, int]]:
        """The TPU ops of the round's traces, in Unix ns; a summary of each trace goes to out/xla-summary.json."""
        found, summary = [], []
        for path in sorted((out / "xla").rglob("*.xplane.pb")):
            ops, info = device_ops(path.read_bytes())
            found += ops
            summary.append({"trace": str(path.relative_to(out)), **info})
        (out / "xla-summary.json").write_text(json.dumps(summary, indent=1))
        if not found:
            raise RuntimeError("no TPU op in the round's device traces" if summary else "no device trace was written in the round")
        return found


def signal_all(folder: Path, names: list[str], sig: int, marker: str, timeout_s: float) -> None:
    """Sends sig to each armed process (<name>.pid in folder) and waits for its <name>.<marker>; a trace that did not
    start or was not written fails the round."""
    for name in names:
        (folder / f"{name}.{marker}").unlink(missing_ok=True)
        os.kill(int(name.split("-")[-1]), sig)
    deadline = time.monotonic() + timeout_s
    for name in names:
        path = folder / f"{name}.{marker}"
        while not path.exists():
            if time.monotonic() > deadline or not _alive(int(name.split("-")[-1])):
                raise RuntimeError(f"process {name}: no trace {marker} marker after {timeout_s:.0f} s")
            time.sleep(0.2)
        text = path.read_text()
        if text.startswith("error"):
            raise RuntimeError(f"process {name}: trace {marker}: {text}")


def _varint(b: bytes, i: int) -> tuple[int, int]:
    x = s = 0
    while True:
        c = b[i]
        i += 1
        x |= (c & 0x7F) << s
        if c < 0x80:
            return x, i
        s += 7


def _fields(b: bytes, i: int = 0, end: int | None = None):
    """(field number, value) of a protobuf message: an int, or (start, end) of a length-delimited field."""
    end = len(b) if end is None else end
    while i < end:
        key, i = _varint(b, i)
        kind = key & 7
        if kind == 0:
            v, i = _varint(b, i)
        elif kind == 2:
            n, i = _varint(b, i)
            v, i = (i, i + n), i + n
        elif kind in (1, 5):
            v, i = b[i:i + (8 if kind == 1 else 4)], i + (8 if kind == 1 else 4)
        else:
            raise ValueError(f"not an XSpace: protobuf wire type {kind}")
        yield key >> 3, v


def _text(b: bytes, v) -> str:
    return b[v[0]:v[1]].decode("utf-8", errors="replace")


OP_LINES = ("XLA Ops", "Async XLA Ops")  # every op the device ran, compute and its async copies
LAUNCH, DONE = "DoEnqueueProgram", "CompleteCallbacks"  # libtpu's host events around a program run


def _plane(b: bytes, plane):
    """A plane's name, stat names and event names by id, its stats and its lines (unparsed)."""
    name, stat_names, event_names, stats, lines = "", {}, {}, [], []
    for f, v in _fields(b, *plane):
        if f == 2:
            name = _text(b, v)
        elif f == 3:
            lines.append(v)
        elif f in (4, 5):
            entry = dict(_fields(b, *v))
            meta = dict(_fields(b, *entry[2])) if 2 in entry else {}
            (event_names if f == 4 else stat_names)[entry.get(1)] = _text(b, meta[2]) if 2 in meta else ""
        elif f == 6:
            stats.append(dict(_fields(b, *v)))
    return name, stat_names, event_names, stats, lines


def _line(b: bytes, v, run_id, want) -> tuple[str, int, list]:
    """A line's name, timestamp_ns and events (metadata id, offset ps, duration ps, run_id stat when want(name))."""
    name, ts, events = "", 0, []
    for f, lv in _fields(b, *v):
        if f == 2:
            name = _text(b, lv)
        elif f == 3:
            ts = lv
        elif f == 4:
            meta = off = dur = 0
            run = None
            for ef, ev in _fields(b, *lv):
                if ef == 1:
                    meta = ev
                elif ef == 2:
                    off = ev
                elif ef == 3:
                    dur = ev
                elif ef == 4 and run_id is not None and want(name):
                    stat = dict(_fields(b, *ev))
                    if stat.get(1) == run_id:
                        run = stat.get(3, stat.get(4))
            events.append((meta, off, dur, run))
    return name, ts, events


def _launch_base(modules: dict, host: list) -> tuple[int, int]:
    """The Unix ns a device plane's offsets count from, when nothing in the trace states it: each program run starts
    after the host began enqueuing it and ends before the host ran its completion callbacks (matched by run_id)."""
    launch, done = {}, {}
    for name, run, t in host:
        (launch if name == LAUNCH else done).setdefault(run, []).append(t)
    lows = [min(t) - modules[r][0] for r, t in launch.items() if r in modules]
    highs = [min(t) - modules[r][1] for r, t in done.items() if r in modules]
    if not lows or not highs:
        raise ValueError("the device trace's clock is relative and the trace has no profile_start_time or host launches to place it")
    lo, hi = max(lows), min(highs)
    if lo > hi or hi - lo > 1_000_000:
        raise ValueError(f"the host launches place the device clock within {(hi - lo) / 1e3:.0f} us only")
    return (lo + hi) // 2, hi - lo


def device_ops(b: bytes) -> tuple[list[tuple[int, int]], dict]:
    """(start, end) Unix ns of every op on a TPU device's op lines of a serialized XSpace, and a summary. A device line
    with no timestamp counts from the device tracer's own start, which the trace does not state (it is not the
    session's profile_start_time: 1.3 ms later in a vLLM-TPU trace): the host launches and completions of its program
    runs pin it. Host lines a framework session normalized count from its profile_start_time."""
    info, start, raw, modules, host = {"bytes": len(b), "planes": {}}, None, [], {}, []
    for plane in (v for f, v in _fields(b) if f == 1):
        name, stat_names, event_names, stats, lines = _plane(b, plane)
        if name == "Task Environment":
            start = next((s.get(3, s.get(4)) for s in stats if stat_names.get(s.get(1)) == "profile_start_time"), None)
        device = name.startswith("/device:TPU:")
        if not device and name != "/host:CPU":
            continue
        run_id = next((k for k, n in stat_names.items() if n == "run_id"), None)
        counts = {}
        for v in lines:
            lname, ts, events = _line(b, v, run_id, (lambda n: n == "XLA Modules") if device else (lambda n: True))
            counts[lname] = counts.get(lname, 0) + len(events)
            if device and lname in OP_LINES:
                raw += [(ts, off, dur) for _, off, dur, _ in events]
            elif device and lname == "XLA Modules":
                modules.update({run: (ts + off // 1000, ts + (off + dur) // 1000) for _, off, dur, run in events if run is not None})
            elif not device:
                host += [(event_names.get(m), run, ts + off // 1000) for m, off, _, run in events if run is not None and event_names.get(m) in (LAUNCH, DONE)]
        if device:
            dropped = next((s.get(3, s.get(4)) for s in stats if stat_names.get(s.get(1)) == "dropped_traces"), None)
            info["planes"][name] = {**counts, **({"dropped_traces": dropped} if dropped is not None else {})}
    base = 0
    if any(ts < 10**17 for ts, _, _ in raw):
        if any(t < 10**17 for _, _, t in host) and start is None:
            raise ValueError("the trace's host lines are relative to its session and it carries no profile_start_time")
        base, width = _launch_base(modules, [(n, r, t + (start if t < 10**17 else 0)) for n, r, t in host])
        info.update(clock="host launches", clock_window_us=round(width / 1e3, 3), profile_start_ns=start)
    ops = [((base if ts < 10**17 else 0) + ts + off // 1000, (base if ts < 10**17 else 0) + ts + (off + dur) // 1000) for ts, off, dur in raw]
    info.update(ops=len(ops), base_ns=base, first_ns=min((s for s, _ in ops), default=None), last_ns=max((e for _, e in ops), default=None))
    return ops, info


def _alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False
