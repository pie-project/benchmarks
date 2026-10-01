import json
import subprocess
import sys
from pathlib import Path

from pie_evals.plan.machines import allowed_macs, is_allowed

ROOT = Path(__file__).resolve().parents[1]


def test_only_listed_macs_are_allowed(tmp_path):
    cfg = tmp_path / "config.json"
    cfg.write_text(json.dumps({"machines": ["m5-max-128g"]}))
    allowed = allowed_macs(cfg)
    assert is_allowed("m5-max-128g", "macos", allowed) and not is_allowed("m5-max-48g", "macos", allowed)
    assert is_allowed("l40s-x1", "linux", allowed)  # the list is about Macs; rented GPUs are not on it
    assert allowed_macs(tmp_path / "none.json") is None and is_allowed("m5-max-48g", "macos", None)
    cfg.write_text(json.dumps({"machines": []}))
    assert allowed_macs(cfg) is None


def test_a_mac_outside_the_list_gets_no_job_even_when_asked_for(tmp_path):
    (tmp_path / "config.json").write_text(json.dumps({"machines": ["m5-max-128g"]}))
    out = tmp_path / "jobs"
    args = ["--tier", "targeted", "--pie-commit", "c" * 40, "--engine", "pie", "--artifact", "gemma-4-26b-a4b-mlx4", "--workload", "ob-short-100", "--out", str(out)]
    base = [sys.executable, "-m", "pie_evals.cli", "--matrix", str(ROOT / "matrix"), "--store", str(tmp_path / "store"), "jobs"]
    run = subprocess.run(base + args + ["--platform", "m5-max-48g"], cwd=tmp_path, capture_output=True, text=True, check=True)
    assert json.loads((out / "gh-matrix.json").read_text()) == {"include": []} and "not in config.json machines" in run.stderr
    subprocess.run(base + args + ["--platform", "m5-max-48g", "--platform", "m5-max-128g"], cwd=tmp_path, capture_output=True, check=True)
    assert {j["platform"] for j in json.loads((out / "gh-matrix.json").read_text())["include"]} == {"m5-max-128g"}
