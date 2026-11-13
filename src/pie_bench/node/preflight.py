from __future__ import annotations

import os
import platform
import re
import shutil
import signal
import subprocess
import time
from typing import Any

ENGINE_PROCESSES = ("pie", "llama-server", "mlx_lm.server", "splash")
ENGINE_ARGS = ("mlx_lm server", "mlx_lm.server")


def _run(argv: list[str], timeout: float = 20.0) -> str | None:
    if shutil.which(argv[0]) is None:
        return None
    try:
        p = subprocess.run(argv, capture_output=True, text=True, timeout=timeout, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if p.returncode != 0:
        return None
    return p.stdout


def gpu_memory_used_mib() -> list[float] | None:
    out = _run(["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"])
    if out is None:
        return None
    vals = []
    for line in out.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            vals.append(float(line))
        except ValueError:
            continue
    return vals


def await_free_gpu(threshold_mib: float = 1500, timeout_s: float = 180, poll_s: float = 2.0) -> float:
    t0 = time.monotonic()
    last: list[float] | None = None
    while True:
        last = gpu_memory_used_mib()
        if last is None or all(v <= threshold_mib for v in last):
            return time.monotonic() - t0
        if time.monotonic() - t0 >= timeout_s:
            raise TimeoutError(
                f"GPU memory still in use after {timeout_s:.0f}s: {last} MiB (threshold {threshold_mib})"
            )
        time.sleep(poll_s)


def gpu_processes() -> list[dict[str, str]]:
    out = _run(["nvidia-smi", "--query-compute-apps=pid,process_name,used_memory", "--format=csv,noheader,nounits"])
    if not out:
        return []
    procs = []
    for line in out.strip().splitlines():
        parts = [x.strip() for x in line.split(",")]
        if len(parts) >= 2:
            procs.append({"pid": parts[0], "name": parts[1], "used_mib": parts[2] if len(parts) > 2 else ""})
    return procs


def dev_nvidia_holders() -> list[dict[str, str]]:
    found: list[dict[str, str]] = []
    try:
        entries = os.listdir("/proc")
    except OSError:
        return found
    for d in entries:
        if not d.isdigit():
            continue
        pid = int(d)
        try:
            fds = os.listdir(f"/proc/{pid}/fd")
        except OSError:
            continue
        for fd in fds:
            try:
                link = os.readlink(f"/proc/{pid}/fd/{fd}")
            except OSError:
                continue
            if link.startswith("/dev/nvidia") and not link.startswith("/dev/nvidia-caps"):
                found.append({"pid": str(pid), "name": _proc_basename(pid) or "", "used_mib": ""})
                break
    return found


def _ancestors(pid: int | None = None) -> set[int]:
    protected: set[int] = set()
    cur = pid if pid is not None else os.getpid()
    try:
        protected.add(os.getpgrp())
    except (OSError, AttributeError):
        pass
    seen = 0
    while cur and cur > 0 and seen < 64:
        protected.add(cur)
        seen += 1
        try:
            with open(f"/proc/{cur}/stat") as f:
                cur = int(f.read().split(") ", 1)[1].split()[1])
        except (OSError, IndexError, ValueError):
            break
    return protected


def _proc_basename(pid: int) -> str | None:
    try:
        with open(f"/proc/{pid}/comm") as f:
            return f.read().strip()
    except OSError:
        return None


def kill_leftovers(names: list[str], threshold_mib: float = 1500, timeout_s: float = 180, any_holder: bool = False) -> dict[str, Any]:
    wanted = {n.strip() for n in names if n and n.strip()}
    protected = _ancestors()
    killed: list[dict[str, Any]] = []
    if wanted or any_holder:
        targets: list[int] = []
        holders = gpu_processes()
        listed = {p.get("pid") for p in holders}
        holders += [p for p in dev_nvidia_holders() if p["pid"] not in listed]
        for p in holders:
            try:
                pid = int(p["pid"])
            except (KeyError, ValueError):
                continue
            if pid in protected:
                continue
            base = _proc_basename(pid) or os.path.basename(p.get("name", "").replace("\\", "/")).removesuffix(".exe")
            if any_holder or base in wanted or os.path.basename(p.get("name", "")) in wanted:
                targets.append(pid)
                killed.append({"pid": pid, "name": base, "used_mib": p.get("used_mib", "")})
        for pid in targets:
            try:
                os.kill(pid, signal.SIGTERM)
            except (ProcessLookupError, PermissionError):
                pass
        if targets:
            time.sleep(5.0)
            for pid in targets:
                try:
                    os.kill(pid, getattr(signal, "SIGKILL", signal.SIGTERM))
                except (ProcessLookupError, PermissionError):
                    pass
    waited = await_free_gpu(threshold_mib=threshold_mib, timeout_s=timeout_s)
    return {"killed": killed, "gpu_drain_wait_s": round(waited, 2)}


def linux_machine_state() -> dict[str, Any]:
    state: dict[str, Any] = {"os": "linux"}
    out = _run(["nvidia-smi", "--query-gpu=name,driver_version,memory.total,memory.used,clocks.sm,clocks.mem,power.draw,power.limit,temperature.gpu,clocks_throttle_reasons.active",
                "--format=csv,noheader,nounits"])
    if out:
        gpus = []
        for line in out.strip().splitlines():
            parts = [x.strip() for x in line.split(",")]
            if len(parts) >= 4:
                g = {"name": parts[0], "driver": parts[1], "memory_total_mib": parts[2], "memory_used_mib": parts[3]}
                for k, v in zip(("sm_mhz", "mem_mhz", "power_w", "power_limit_w", "temp_c", "throttle_reasons"), parts[4:10], strict=False):
                    g[k] = v
                gpus.append(g)
        state["gpus"] = gpus
        if gpus:
            state["driver"] = gpus[0]["driver"]
    procs = [p for p in gpu_processes() if p["pid"] != str(os.getpid())]
    state["gpu_process_count"] = str(len(procs))
    state["gpu_processes"] = [p["name"] for p in procs][:20]
    state["cpu_count"] = str(len(os.sched_getaffinity(0)) if hasattr(os, "sched_getaffinity") else os.cpu_count())
    try:
        with open("/proc/cpuinfo") as f:
            state["cpu_model"] = next((ln.split(":", 1)[1].strip() for ln in f if ln.startswith("model name")), "")
    except OSError:
        pass
    if len(state.get("gpus", [])) > 1 and (topo := _run(["nvidia-smi", "topo", "-m"])):
        row = next((ln.split() for ln in topo.splitlines() if ln.split()[:1] == ["GPU0"]), [])
        if len(row) > 2:
            state["gpu_link"] = row[2]
    try:
        la = os.getloadavg()
        state["loadavg"] = ",".join(f"{x:.2f}" for x in la)
    except (OSError, AttributeError):
        pass
    return state


def engine_processes(exclude: set[int] | None = None) -> list[str]:
    out = _run(["ps", "-axo", "pid=,comm="]) or ""
    args = {ln.strip().split(None, 1)[0]: ln.strip().split(None, 1)[1] for ln in (_run(["ps", "-axo", "pid=,args="]) or "").splitlines() if len(ln.strip().split(None, 1)) == 2}
    found = []
    skip = exclude or set()
    for line in out.splitlines():
        parts = line.strip().split(None, 1)
        if len(parts) != 2 or not parts[0].isdigit() or int(parts[0]) in skip:
            continue
        if os.path.basename(parts[1]) in ENGINE_PROCESSES:
            found.append(f"{os.path.basename(parts[1])}:{parts[0]}")
        elif any(a in args.get(parts[0], "") for a in ENGINE_ARGS):
            found.append(f"mlx_lm:{parts[0]}")
    return sorted(found)


def _parse_pmset_therm(text: str | None) -> dict[str, str]:
    d: dict[str, str] = {}
    if not text:
        return d
    for line in text.splitlines():
        m = re.match(r"\s*(CPU_\w+)\s*=\s*(\d+)", line)
        if m:
            d[m.group(1).lower()] = m.group(2)
    lower = text.lower()
    if "thermal warning level" in lower:
        m = re.search(r"thermal warning level\s*[:=]?\s*(\d+)", lower)
        d["thermal_warning_level"] = m.group(1) if m else "unknown"
    limit = d.get("cpu_speed_limit")
    sched = d.get("cpu_scheduler_limit")
    warned = (
        (limit is not None and limit != "100")
        or (sched is not None and sched != "100")
        or (d.get("thermal_warning_level") not in (None, "0", "unknown"))
    )
    d["thermal_warning"] = "yes" if warned else "no"
    return d


def _parse_pmset_batt(text: str | None) -> dict[str, str]:
    d: dict[str, str] = {}
    if not text:
        return d
    lower = text.lower()
    if "ac power" in lower:
        d["power_source"] = "ac"
    elif "battery power" in lower:
        d["power_source"] = "battery"
    m = re.search(r"(\d+)%", text)
    if m:
        d["battery_pct"] = m.group(1)
    return d


def _parse_lowpowermode(text: str | None) -> str | None:
    if not text:
        return None
    m = re.search(r"lowpowermode\s+(\d)", text)
    return {"0": "off", "1": "on"}.get(m.group(1), m.group(1)) if m else None


def _parse_display_count(text: str | None) -> str | None:
    if not text:
        return None
    n = len(re.findall(r"^\s*Resolution:", text, flags=re.MULTILINE))
    return str(n) if n else None


def mac_machine_state() -> dict[str, Any]:
    state: dict[str, Any] = {"os": "macos"}
    state.update(_parse_pmset_therm(_run(["pmset", "-g", "therm"])))
    state.update(_parse_pmset_batt(_run(["pmset", "-g", "batt"])))
    lpm = _parse_lowpowermode(_run(["pmset", "-g"]))
    if lpm is not None:
        state["low_power_mode"] = lpm
    disp = _parse_display_count(_run(["system_profiler", "SPDisplaysDataType"], timeout=60))
    if disp is not None:
        state["displays"] = disp
    try:
        la = os.getloadavg()
        state["loadavg"] = ",".join(f"{x:.2f}" for x in la)
    except (OSError, AttributeError):
        pass
    state["engine_processes"] = engine_processes()
    return state


def mac_thermal_state() -> str | None:
    try:
        import ctypes
        import ctypes.util

        objc = ctypes.cdll.LoadLibrary(ctypes.util.find_library("objc"))
        ctypes.cdll.LoadLibrary("/System/Library/Frameworks/Foundation.framework/Foundation")
        objc.objc_getClass.restype = ctypes.c_void_p
        objc.objc_getClass.argtypes = [ctypes.c_char_p]
        objc.sel_registerName.restype = ctypes.c_void_p
        objc.sel_registerName.argtypes = [ctypes.c_char_p]
        obj = ctypes.CFUNCTYPE(ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p)(("objc_msgSend", objc))
        num = ctypes.CFUNCTYPE(ctypes.c_long, ctypes.c_void_p, ctypes.c_void_p)(("objc_msgSend", objc))
        info = obj(objc.objc_getClass(b"NSProcessInfo"), objc.sel_registerName(b"processInfo"))
        return ("nominal", "fair", "serious", "critical")[num(info, objc.sel_registerName(b"thermalState"))]
    except Exception:
        return None


def settle_mac(idle_s: float = 60, nominal_timeout_s: float = 600, poll_s: float = 10) -> dict[str, Any]:
    t0 = time.monotonic()
    before = mac_thermal_state()
    time.sleep(idle_s)
    state = mac_thermal_state()
    while state not in (None, "nominal") and time.monotonic() - t0 < nominal_timeout_s:
        time.sleep(poll_s)
        state = mac_thermal_state()
    return {"thermal_state_before_settle": before, "thermal_state": state, "settle_s": round(time.monotonic() - t0)}


def mac_gpu_utilization() -> int | None:
    out = _run(["ioreg", "-r", "-d", "1", "-c", "IOAccelerator"]) or ""
    m = re.search(r'"Device Utilization %"=(\d+)', out)
    return int(m.group(1)) if m else None


def await_idle_mac_gpu(max_util: int = 5, quiet_s: float = 10, timeout_s: float = 1800, poll_s: float = 1) -> dict[str, Any]:
    t0 = time.monotonic()
    first = mac_gpu_utilization()
    if first is None:
        return {}
    quiet_since = None
    while True:
        util = mac_gpu_utilization()
        now = time.monotonic()
        if util is not None and util <= max_util:
            quiet_since = quiet_since if quiet_since is not None else now
            if now - quiet_since >= quiet_s:
                return {"gpu_util_before_cell": first, "gpu_idle_wait_s": round(now - t0, 1)}
        else:
            quiet_since = None
        if now - t0 > timeout_s:
            return {"gpu_util_before_cell": first, "gpu_busy_error": f"GPU still {util}% busy after {timeout_s:.0f}s: another workload shares it"}
        time.sleep(poll_s)


def mac_thermal_changed(before: dict[str, Any], after: dict[str, Any]) -> bool:
    if before.get("thermal_warning") != after.get("thermal_warning"):
        return True
    for k in ("cpu_speed_limit", "cpu_scheduler_limit", "thermal_warning_level"):
        if before.get(k) != after.get(k):
            return True
    return False


def _is_mac(platform_os: str | None) -> bool:
    if platform_os is None:
        return platform.system() == "Darwin"
    return str(platform_os).lower() in ("macos", "darwin", "mac")


def machine_state(platform_os: str | None = None) -> dict[str, Any]:
    return mac_machine_state() if _is_mac(platform_os) else linux_machine_state()


class Preflight:

    def __init__(self, gpu_threshold_mib: float = 1500, gpu_timeout_s: float = 180):
        self.gpu_threshold_mib = gpu_threshold_mib
        self.gpu_timeout_s = gpu_timeout_s

    def before_job(self, platform_os: str | None = None) -> dict[str, Any]:
        state = machine_state(platform_os)
        if not _is_mac(platform_os):
            try:
                if os.environ.get("RUNPOD_POD_ID"):
                    state.update(kill_leftovers([], self.gpu_threshold_mib, self.gpu_timeout_s, any_holder=True))
                else:
                    state["gpu_drain_wait_s"] = round(
                        await_free_gpu(self.gpu_threshold_mib, self.gpu_timeout_s), 2
                    )
            except TimeoutError as e:
                state["gpu_drain_error"] = str(e)
        return state

    def before_cell(self, platform_os: str | None) -> dict[str, Any]:
        return await_idle_mac_gpu() if _is_mac(platform_os) and os.environ.get("PIE_BENCH_GPU_IDLE", "1") != "0" else {}

    def settle(self, platform_os: str | None) -> dict[str, Any]:
        return settle_mac() if _is_mac(platform_os) else {}

    def between_engines(self, platform_os: str | None, leftover_names: list[str]) -> dict[str, Any]:
        state: dict[str, Any] = {}
        if not _is_mac(platform_os):
            try:
                pod = bool(os.environ.get("RUNPOD_POD_ID"))
                state.update(kill_leftovers(leftover_names, self.gpu_threshold_mib, self.gpu_timeout_s, any_holder=pod))
            except TimeoutError as e:
                state["gpu_drain_error"] = str(e)
        state.update(machine_state(platform_os))
        return state

    def after_model(self, platform_os: str | None, before_state: dict[str, Any]) -> list[str]:
        reasons: list[str] = []
        after = machine_state(platform_os)
        if _is_mac(platform_os):
            if mac_thermal_changed(before_state, after):
                reasons.append(
                    f"thermal state changed during model: {before_state.get('thermal_warning')}"
                    f"->{after.get('thermal_warning')} "
                    f"(speed limit {before_state.get('cpu_speed_limit')}->{after.get('cpu_speed_limit')})"
                )
            if before_state.get("power_source") != after.get("power_source"):
                reasons.append(f"power source changed: {before_state.get('power_source')}->{after.get('power_source')}")
            if after.get("power_source") == "battery":
                reasons.append("running on battery")
            if after.get("low_power_mode") == "on":
                reasons.append("low power mode on")
            if before_state.get("displays") != after.get("displays"):
                reasons.append(f"display count changed: {before_state.get('displays')}->{after.get('displays')}")
            before = set(before_state.get("engine_processes") or [])
            new = sorted(set(after.get("engine_processes") or []) - before)
            if new:
                reasons.append(f"another inference engine started during the model: {', '.join(new)}")
            if stale := sorted(before):
                reasons.append(f"another inference engine was already running: {', '.join(stale)}")
        else:
            if before_state.get("gpu_drain_error"):
                reasons.append("GPU was not drained before the model: " + str(before_state["gpu_drain_error"]))
            b = int(before_state.get("gpu_process_count") or 0)
            a = int(after.get("gpu_process_count") or 0)
            if a > b:
                reasons.append(f"other GPU processes appeared during model: {b}->{a} ({after.get('gpu_processes')})")
        return reasons


def cuda_init() -> str | None:
    import ctypes
    import sys

    if sys.platform != "linux":
        return None
    try:
        lib = ctypes.CDLL("libcuda.so.1")
    except OSError:
        return None
    rc = lib.cuInit(0)
    if rc != 0:
        return f"cuInit answered {rc}"
    count = ctypes.c_int(0)
    rc = lib.cuDeviceGetCount(ctypes.byref(count))
    if rc != 0:
        return f"cuDeviceGetCount answered {rc}"
    if count.value < 1:
        return "cuDeviceGetCount says 0 devices"
    return None
