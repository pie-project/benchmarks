import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("handoff", ROOT / "infra/ci/handoff.py")
handoff = importlib.util.module_from_spec(spec)
spec.loader.exec_module(handoff)


def test_a_jobs_own_name_drops_its_caller_and_matrix_values():
    assert handoff.own_name("run / bench (weekly-h100-x1-s00, h100-x1, linux)") == "bench"
    assert handoff.own_name("collect") == "collect"
    # GitHub cuts a long matrix name short, with no closing parenthesis (weekly 42904348524's launch markers)
    assert handoff.own_name("run / launch (h200-x1-0, h200-x1, linux, run-42904348524, self-hosted, weekly-h200-x1-s0...") == "launch"
