import importlib.util
from pathlib import Path

import pytest

SHIM = Path(__file__).resolve().parents[1] / "src" / "pie_bench" / "node" / "engines" / "scripts" / "pie_xla.py"
CONFIG = '[engine]\ntype = "metal"\ntotal_pages = 4096\nmax_forward_requests = 256\n[server]\nlisten = "127.0.0.1:0"\n'


def shim():
    spec = importlib.util.spec_from_file_location("pie_xla_shim", SHIM)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_the_engine_prewarms_its_fire_ladder_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PIE_XLA_PREWARM", raising=False)
    out = shim().rewrite(CONFIG, "8123")
    assert 'type = "xla"' in out and "max_total_pages = 4096" in out
    assert out.count("prewarm = true") == 1
    assert 'listen = "127.0.0.1:8123"' in out


def test_prewarm_off_leaves_the_engine_table_as_written(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PIE_XLA_PREWARM", "0")
    out = shim().rewrite(CONFIG)
    assert "prewarm" not in out
