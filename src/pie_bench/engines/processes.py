from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path


def _cpu_seconds(text: str) -> float:
    days, _, rest = text.strip().rpartition("-")
    parts = [float(x) for x in rest.split(":")]
    secs = 0.0
    for x in parts:
        secs = secs * 60 + x
    return secs + (float(days) * 86400 if days else 0.0)


def win_processes() -> list[tuple[int, int, float, int]]:
    import psutil

    rows = []
    for p in psutil.process_iter(["pid", "ppid", "cpu_times", "memory_info"]):
        ct, mi = p.info.get("cpu_times"), p.info.get("memory_info")
        rows.append(
            (
                p.info["pid"],
                p.info.get("ppid") or 0,
                (ct.user + ct.system) if ct else 0.0,
                (mi.rss // 1024) if mi else 0,
            )
        )
    return rows


def process_table() -> dict[int, tuple[int, float]]:
    if sys.platform == "win32":
        return {pid: (ppid, cpu) for pid, ppid, cpu, _ in win_processes()}
    out = subprocess.run(
        ["ps", "-axo", "pid=,ppid=,time="], capture_output=True, text=True, check=False
    ).stdout
    table = {}
    for line in out.splitlines():
        parts = line.split()
        if len(parts) == 3 and parts[0].isdigit() and parts[1].isdigit():
            try:
                table[int(parts[0])] = (int(parts[1]), _cpu_seconds(parts[2]))
            except ValueError:
                continue
    return table


def tree_pids(roots: list[int], table: dict[int, tuple[int, float]]) -> set[int]:
    pids = {r for r in roots if r in table}
    grew = True
    while grew:
        more = {p for p, (pp, _) in table.items() if pp in pids and p not in pids}
        pids |= more
        grew = bool(more)
    return pids


def stall_dump(pids: list[int]) -> str:
    out = []
    if shutil.which("nvidia-smi"):
        smi = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=index,utilization.gpu,memory.used",
                "--format=csv,noheader",
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
        out.append("== nvidia-smi (index, util, mem)\n" + (smi.stdout or smi.stderr))
    gdb = shutil.which("gdb")
    for pid in pids:
        try:
            cmd = (
                Path(f"/proc/{pid}/cmdline")
                .read_bytes()
                .replace(b"\0", b" ")
                .decode(errors="replace")[:300]
            )
        except OSError:
            continue
        out.append(f"== pid {pid}: {cmd}")
        if gdb:
            bt = subprocess.run(
                [
                    gdb,
                    "-p",
                    str(pid),
                    "-batch",
                    "-nx",
                    "-ex",
                    "set pagination off",
                    "-ex",
                    "thread apply all bt 30",
                ],
                capture_output=True,
                text=True,
                check=False,
                timeout=120,
            )
            if bt.returncode == 0 and "Thread" in bt.stdout:
                out.append(bt.stdout)
                continue
            out.append(f"(gdb could not attach: {bt.stderr.strip()[-200:]})")
        for task in sorted(Path(f"/proc/{pid}/task").glob("*")):

            def read(name: str, task: Path = task) -> str:
                try:
                    return (task / name).read_text(errors="replace").strip()
                except OSError:
                    return "?"

            out.append(f"-- tid {task.name} {read('comm')} wchan={read('wchan')}\n{read('stack')}")
    return "\n".join(out)


def jit_jobs() -> str:
    jobs = os.cpu_count() or 8
    for path, per in (("/sys/fs/cgroup/cpu.max", None), ("/sys/fs/cgroup/memory.max", 4 << 30)):
        try:
            limit = open(path).read().split()
            if limit and limit[0] != "max":
                jobs = min(
                    jobs,
                    max(1, int(limit[0]) // int(limit[1]) if per is None else int(limit[0]) // per),
                )
        except (OSError, ValueError, IndexError):
            pass
    return str(jobs)


def mac_gpu_busy() -> bool:
    if sys.platform != "darwin":
        return False
    from pie_bench.runner.preflight import mac_gpu_utilization

    return (mac_gpu_utilization() or 0) > 5


def wait_with_stall_check(
    proc: subprocess.Popen,
    timeout_s: float,
    stall_s: float,
    extra_pids=lambda: [],
    poll_s: float = 5.0,
    on_stall=None,
    device_busy=mac_gpu_busy,
) -> tuple[int, bool, bool]:
    start = last_work = time.monotonic()
    last_cpu = None
    while True:
        try:
            return proc.wait(timeout=poll_s), False, False
        except subprocess.TimeoutExpired:
            pass
        now = time.monotonic()
        table = process_table()
        cpu = {p: table[p][1] for p in tree_pids([proc.pid, *extra_pids()], table)}
        if (
            last_cpu is None
            or any(c > last_cpu.get(p, 0.0) + 0.05 for p, c in cpu.items())
            or device_busy()
        ):
            last_work = now
        last_cpu = cpu
        timed_out, stalled = now - start > timeout_s, now - last_work > stall_s
        if stalled and not timed_out and on_stall is not None:
            try:
                on_stall(sorted(tree_pids([proc.pid, *extra_pids()], table)))
            except Exception:
                pass
        if timed_out or stalled:
            for p in tree_pids([proc.pid], table) - {proc.pid}:
                try:
                    os.kill(p, 9)
                except OSError:
                    pass
            proc.kill()
            proc.wait()
            return -1, timed_out, stalled and not timed_out
