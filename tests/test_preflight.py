import os
import platform

from pie_bench.node import preflight as pf

THERM_OK = """Note: No thermal warning level has been recorded
Note: No performance warning level has been recorded
2026-09-28 10:00:00 +0000 CPU Power notify
\tCPU_Scheduler_Limit \t= 100
\tCPU_Available_CPUs \t= 12
\tCPU_Speed_Limit \t= 100
"""

THERM_HOT = """2026-09-28 10:00:00 +0000 Thermal Warning Level: 2
\tCPU_Scheduler_Limit \t= 100
\tCPU_Available_CPUs \t= 12
\tCPU_Speed_Limit \t= 70
"""


def test_ancestors_include_self_and_group():
    anc = pf._ancestors()
    assert os.getpid() in anc
    assert os.getpgrp() in anc
    assert len(anc) >= 2


def test_kill_leftovers_never_kills_ancestors(monkeypatch):
    my = os.getpid()
    base = pf._proc_basename(my)
    monkeypatch.setattr(pf, "gpu_processes", lambda: [{"pid": str(my), "name": f"/usr/bin/{base}", "used_mib": "40000"}])
    monkeypatch.setattr(pf, "await_free_gpu", lambda **k: 0.0)
    killed = []
    monkeypatch.setattr(pf.os, "kill", lambda pid, sig: killed.append((pid, sig)))
    r = pf.kill_leftovers([base])
    assert killed == [], "must not kill a process in our ancestor set"
    assert r["killed"] == []


def test_kill_leftovers_targets_matching_orphan(monkeypatch):
    fake_pid = 999999
    monkeypatch.setattr(pf, "gpu_processes", lambda: [{"pid": str(fake_pid), "name": "/opt/pie/target/release/pie", "used_mib": "41000"}])
    monkeypatch.setattr(pf, "_proc_basename", lambda pid: "pie" if pid == fake_pid else None)
    monkeypatch.setattr(pf, "await_free_gpu", lambda **k: 0.0)
    monkeypatch.setattr(pf, "time", type("T", (), {"sleep": staticmethod(lambda s: None)}))
    sent = []
    monkeypatch.setattr(pf.os, "kill", lambda pid, sig: sent.append((pid, sig)))
    r = pf.kill_leftovers(["pie"])
    assert (fake_pid, pf.signal.SIGTERM) in sent
    assert r["killed"] and r["killed"][0]["pid"] == fake_pid


def test_kill_leftovers_ignores_unmatched_names(monkeypatch):
    monkeypatch.setattr(pf, "gpu_processes", lambda: [{"pid": "999998", "name": "/usr/bin/python3", "used_mib": "40000"}])
    monkeypatch.setattr(pf, "_proc_basename", lambda pid: "python3")
    monkeypatch.setattr(pf, "await_free_gpu", lambda **k: 0.0)
    sent = []
    monkeypatch.setattr(pf.os, "kill", lambda pid, sig: sent.append((pid, sig)))
    r = pf.kill_leftovers(["pie", "EngineCore"])
    assert sent == [] and r["killed"] == []


def test_no_pkill_invocation():
    with open(pf.__file__) as f:
        for line in f:
            code = line.split("#", 1)[0]
            if "```" in line or line.lstrip().startswith('"'):
                continue
            assert '"pkill"' not in code and "'pkill'" not in code, f"pkill invoked: {line!r}"


def test_any_holder_kills_an_orphan_of_any_name_but_never_us(monkeypatch):
    me, orphan = os.getpid(), 999997
    monkeypatch.setattr(pf, "gpu_processes", lambda: [
        {"pid": str(orphan), "name": "/usr/bin/python3", "used_mib": "73409"},
        {"pid": str(me), "name": "/usr/bin/python3", "used_mib": "10"},
    ])
    monkeypatch.setattr(pf, "_proc_basename", lambda pid: "python3")
    monkeypatch.setattr(pf, "await_free_gpu", lambda **k: 0.0)
    monkeypatch.setattr(pf, "time", type("T", (), {"sleep": staticmethod(lambda s: None)}))
    sent = []
    monkeypatch.setattr(pf.os, "kill", lambda pid, sig: sent.append((pid, sig)))
    r = pf.kill_leftovers([], any_holder=True)
    assert (orphan, pf.signal.SIGTERM) in sent and all(pid != me for pid, _ in sent)
    assert [k["pid"] for k in r["killed"]] == [orphan]


def test_before_job_on_a_pod_clears_the_card_first(monkeypatch):
    monkeypatch.setenv("RUNPOD_POD_ID", "abc")
    monkeypatch.setattr(pf, "machine_state", lambda os_: {"os": "linux"})
    calls = []
    monkeypatch.setattr(pf, "kill_leftovers", lambda names, thr, to, any_holder=False: calls.append(any_holder) or {"killed": [], "gpu_drain_wait_s": 0.0})
    pf.Preflight().before_job("linux")
    assert calls == [True]


def test_any_holder_finds_a_holder_nvidia_smi_cannot_list(monkeypatch):
    me, orphan = os.getpid(), 999996
    monkeypatch.setattr(pf, "gpu_processes", lambda: [])
    monkeypatch.setattr(pf, "dev_nvidia_holders", lambda: [{"pid": str(orphan), "name": "python3", "used_mib": ""}, {"pid": str(me), "name": "python3", "used_mib": ""}])
    monkeypatch.setattr(pf, "_proc_basename", lambda pid: "python3")
    monkeypatch.setattr(pf, "await_free_gpu", lambda **k: 0.0)
    monkeypatch.setattr(pf, "time", type("T", (), {"sleep": staticmethod(lambda s: None)}))
    sent = []
    monkeypatch.setattr(pf.os, "kill", lambda pid, sig: sent.append((pid, sig)))
    r = pf.kill_leftovers([], any_holder=True)
    assert (orphan, pf.signal.SIGKILL) in sent and all(pid != me for pid, _ in sent)
    assert [k["pid"] for k in r["killed"]] == [orphan]


def test_dev_nvidia_holders_reads_proc(tmp_path, monkeypatch):
    for pid, target in ((4242, "/dev/nvidia0"), (4243, "socket:[1]")):
        fd = tmp_path / str(pid) / "fd"
        fd.mkdir(parents=True)
        os.symlink(target, fd / "7")
    (tmp_path / "self").mkdir()
    real_listdir, real_readlink = os.listdir, os.readlink
    monkeypatch.setattr(pf.os, "listdir", lambda p: real_listdir(str(p).replace("/proc", str(tmp_path), 1)))
    monkeypatch.setattr(pf.os, "readlink", lambda p: real_readlink(str(p).replace("/proc", str(tmp_path), 1)))
    monkeypatch.setattr(pf, "_proc_basename", lambda pid: "python3")
    assert [h["pid"] for h in pf.dev_nvidia_holders()] == ["4242"]


def test_pmset_therm():
    ok = pf._parse_pmset_therm(THERM_OK)
    assert ok["cpu_speed_limit"] == "100" and ok["cpu_available_cpus"] == "12"
    assert ok["thermal_warning"] == "no"
    hot = pf._parse_pmset_therm(THERM_HOT)
    assert hot["thermal_warning_level"] == "2" and hot["thermal_warning"] == "yes"
    assert pf._parse_pmset_therm(None) == {}


def test_pmset_batt_lowpower_and_displays():
    assert pf._parse_pmset_batt("Now drawing from 'AC Power'\n -InternalBattery-0 (id=1)\t100%; charged;") == {"power_source": "ac", "battery_pct": "100"}
    assert pf._parse_pmset_batt("Now drawing from 'Battery Power'\n -InternalBattery-0\t81%; discharging;")["power_source"] == "battery"
    assert pf._parse_lowpowermode("System-wide power settings:\n lowpowermode         1\n") == "on"
    assert pf._parse_lowpowermode(" lowpowermode         0") == "off"
    assert pf._parse_lowpowermode("") is None
    two = "Displays:\n  Color LCD:\n    Resolution: 3456 x 2234\n  DELL:\n    Resolution: 2560 x 1440\n"
    assert pf._parse_display_count(two) == "2"
    assert pf._parse_display_count("Displays:\n") is None


def test_engine_processes_skips_our_own_children(monkeypatch):
    ps = "  101 /opt/homebrew/bin/llama-server\n  102 /Users/x/pie/target/release/pie\n  103 /usr/bin/python3\n  104 llama-server\n"
    monkeypatch.setattr(pf, "_run", lambda argv, timeout=20.0: ps)
    assert pf.engine_processes() == ["llama-server:101", "llama-server:104", "pie:102"]
    assert pf.engine_processes(exclude={104}) == ["llama-server:101", "pie:102"]


def _state(**over):
    base = {"os": "macos", "thermal_warning": "no", "cpu_speed_limit": "100", "power_source": "ac",
            "displays": "1", "engine_processes": []}
    return {**base, **over}


def test_after_model_reads_a_steady_machine_as_clean(monkeypatch):
    monkeypatch.setattr(pf, "machine_state", lambda os_=None: _state())
    assert pf.Preflight().after_model("macos", _state()) == []


def test_after_model_reads_an_engine_left_running_as_unclean(monkeypatch):
    before = _state(engine_processes=["pie:48330"])
    monkeypatch.setattr(pf, "machine_state", lambda os_=None: before)
    reasons = " | ".join(pf.Preflight().after_model("macos", before))
    assert "pie:48330" in reasons


def test_after_model_names_every_change(monkeypatch):
    after = _state(thermal_warning="yes", cpu_speed_limit="70", power_source="battery", low_power_mode="on",
                   displays="2", engine_processes=["pie:555"])
    monkeypatch.setattr(pf, "machine_state", lambda os_=None: after)
    reasons = " | ".join(pf.Preflight().after_model("macos", _state()))
    for want in ("thermal state changed", "power source changed", "running on battery", "low power mode on",
                 "display count changed", "pie:555"):
        assert want in reasons, want


def test_the_runner_holding_the_gpu_is_no_other_process(monkeypatch):
    import os

    import pie_bench.node.preflight as pf

    monkeypatch.setattr(pf, "_run", lambda cmd, *a, **k: "")
    monkeypatch.setattr(pf, "gpu_processes", lambda: [
        {"pid": str(os.getpid()), "name": "/venv/bin/python3", "used_mib": "1800"},
        {"pid": "999997", "name": "/usr/bin/other", "used_mib": "900"},
    ])
    state = pf.linux_machine_state()
    assert state["gpu_process_count"] == "1"
    assert state["gpu_processes"] == ["/usr/bin/other"]


def test_a_mac_reads_its_thermal_state_and_settles(monkeypatch):
    if platform.system() != "Darwin":
        return
    assert pf.mac_thermal_state() in ("nominal", "fair", "serious", "critical")
    settled = pf.settle_mac(idle_s=0, nominal_timeout_s=0)
    assert settled["thermal_state"] in ("nominal", "fair", "serious", "critical") and "settle_s" in settled
    monkeypatch.setattr(pf, "settle_mac", lambda: {"settle_s": 0})
    assert pf.Preflight().settle("macos") == {"settle_s": 0}
    assert pf.Preflight().settle("linux") == {}


def test_a_cell_waits_for_an_idle_gpu_and_gives_up_on_a_shared_one(monkeypatch):
    seq = iter([80, 80, 3, 2, 1, 0, 0, 0])
    monkeypatch.setattr(pf, "mac_gpu_utilization", lambda: next(seq, 0))
    idle = pf.await_idle_mac_gpu(quiet_s=0.02, timeout_s=5, poll_s=0.01)
    assert idle["gpu_util_before_cell"] == 80 and "gpu_busy_error" not in idle
    monkeypatch.setattr(pf, "mac_gpu_utilization", lambda: 90)
    busy = pf.await_idle_mac_gpu(quiet_s=0.02, timeout_s=0.05, poll_s=0.01)
    assert "another workload shares it" in busy["gpu_busy_error"]
