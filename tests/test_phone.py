"""The phone app's rows (pie_evals.results.phone) and the tailnet ingest that takes them (phone_ingest)."""

from __future__ import annotations

import base64
import gzip
import json
import threading
import urllib.error
import urllib.request
from pathlib import Path

import pytest

from pie_evals.plan.matrix import Matrix
from pie_evals.results import phone
from pie_evals.results.phone_ingest import (
    allowed_address,
    import_spool,
    make_handler,
    read_token,
    serve,
    spool_dirs,
)
from pie_evals.results.store import DirStore

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def matrix():
    return Matrix.load(ROOT / "matrix")


def req(prompt=551, out=256, ttft=0.5, lat=None, ok=True):
    return {"ok": ok, "prompt_tokens": prompt, "output_tokens": out, "ttft_s": ttft,
            "latency_s": lat if lat is not None else ttft + (out - 1) / 20.0, "cached_prompt_tokens": 0}


def row(**over):
    base = {
        "schema": "pie-evals-phone/1", "run_id": "phone-test-20261106T030000-ab12", "tag": "test-phone-unit",
        "started_at": "2026-11-06T03:00:00Z", "duration_s": 120.0,
        "app": {"version": "0.1.0", "harness_commit": "7d674c49abcdef", "platform": "android"},
        "device": {"os": "android", "os_version": "16 (API 36)", "manufacturer": "samsung", "model": "SM-S938B", "soc": "SM8750",
                   "soc_vendor": "Qualcomm", "ram_gib": 11.2, "cpu_cores": 8, "abi": "arm64-v8a", "emulator": False,
                   "thermal_start": "none", "thermal_end": "light"},
        "engine": "llamacpp", "engine_version": "b11312", "engine_backend": "cpu", "engine_config": {"n_threads": 6},
        "artifact": "qwen3.5-0.8b-llamacpp",
        "checkpoint": {"repo": "unsloth/Qwen3.5-0.8B-GGUF", "file": "Qwen3.5-0.8B-Q4_K_M.gguf", "revision": "abc123"},
        "workload": "raw-512-256", "status": "pass", "load_s": 1.5,
        # decode 20, 25 and 22 tok/s: the median round is the third
        "rounds": [{"wall_s": 80.0, "peak_mem_gib": 0.9, "requests": [req(ttft=0.5, lat=0.5 + 255 / rate) for _ in range(6)]}
                   for rate in (20.0, 25.0, 22.0)],
    }
    base.update(over)
    return base


def test_raw_row_becomes_a_record_by_the_harness_definitions(matrix):
    good, bad, _ = phone.validate([row()], matrix, phone.model_ids())
    assert not bad
    r, rec = good[0]
    assert rec.status == "pass" and rec.cell.platform.id == "galaxy-s25-ultra"
    assert rec.cell.engine == "llamacpp" and rec.cell.workload.id == "raw-512-256"
    assert rec.perf.primary == "decode_tok_s"
    assert rec.perf.decode_tok_s == pytest.approx(22.0)  # the median round
    assert rec.perf.rounds == pytest.approx([20.0, 25.0, 22.0])
    assert rec.perf.prefill_tok_s == pytest.approx(551 / 0.5)  # prompt tokens over TTFT, cold
    assert rec.perf.ttft_ms_p50 == pytest.approx(500.0)
    assert rec.perf.resident_gib == pytest.approx(0.9) and rec.perf.load_s == 1.5
    assert rec.perf.counters["cold_cache_verified"] == 1.0
    assert rec.provenance.harness_commit and rec.provenance.checkpoint_revision.startswith("unsloth/Qwen3.5-0.8B-GGUF@abc123")
    assert rec.validate_for_store() == []


def test_batched_prefill_and_batching_rows(matrix):
    pf = row(workload="pf4-512", rounds=[{"wall_s": 4.0, "requests": [req(prompt=558, out=1, ttft=1.0, lat=1.0) for _ in range(16)]}] * 3)
    c4 = row(workload="c4", rounds=[{"wall_s": 16.0, "requests": [req(prompt=158, out=256, ttft=0.4, lat=16.0) for _ in range(4)]}] * 3)
    good, bad, _ = phone.validate([pf, c4], matrix, phone.model_ids())
    assert not bad
    by = {r.workload: rec for r, rec in good}
    assert by["pf4-512"].perf.primary == "prefill_tok_s" and by["pf4-512"].perf.prefill_tok_s == pytest.approx(16 * 558 / 4.0)
    assert by["c4"].perf.primary == "output_tok_s" and by["c4"].perf.output_tok_s == pytest.approx(4 * 256 / 16.0)


def test_rows_that_cannot_be_stored_are_refused(matrix):
    rows = [
        row(artifact="no-such-model"),
        row(engine="litert"),  # a GGUF is not LiteRT's format
        row(workload="c256"),
        row(device={**row()["device"], "emulator": True}, tag=None),  # an emulator outside a test tag
        row(engine="pie", artifact="qwen3.5-0.8b-mlx4", engine_version="main"),  # pie must name its commit
        {**row(), "schema": "other/2"},
    ]
    good, bad, _ = phone.validate(rows, matrix, phone.model_ids())
    assert not good and [b["line"] for b in bad] == [1, 2, 3, 4, 5, 6]


def test_short_rounds_and_other_prompts_fail_the_row(matrix):
    short = row(rounds=[{"wall_s": 1.0, "requests": [req() for _ in range(5)]}] * 3)
    other = row(rounds=[{"wall_s": 1.0, "requests": [req(prompt=300) for _ in range(6)]}] * 3)
    good, bad, _ = phone.validate([short, other], matrix, phone.model_ids())
    assert not bad
    assert [(rec.status, rec.error_class) for _, rec in good] == [("fail", "harness_invalid"), ("fail", "input_mismatch")]


def test_failed_and_unsupported_rows_keep_their_reason(matrix):
    fail = row(status="fail", error_class="oom", error="out of memory", rounds=[])
    unsup = row(status="declared_unsupported", engine="litert", artifact="gemma-4-e2b-litert", workload="c4",
                error="serves one request at a time", rounds=[])
    good, bad, _ = phone.validate([fail, unsup], matrix, phone.model_ids())
    assert not bad
    (_, f), (_, u) = good
    assert f.status == "fail" and f.error_class == "oom" and f.perf is None
    assert u.status == "declared_unsupported" and u.invalid_reason == "serves one request at a time"


def test_unknown_phone_and_emulator(matrix):
    odd = row(device={**row()["device"], "model": "XQ-DE72", "manufacturer": "Sony"})
    emu = row(device={**row()["device"], "model": "sdk_gphone64_arm64", "emulator": True})
    good, _, warnings = phone.validate([odd, emu], matrix, phone.model_ids())
    assert good[0][1].cell.platform.id == "android-xq-de72" and warnings
    assert good[1][1].cell.platform.id == "android-emulator"
    iphone = row(device={"os": "ios", "model": "iPhone17,1", "ram_gib": 7.5}, engine="mlx-swift", artifact="qwen3.5-4b-mlxlm")
    good, bad, _ = phone.validate([iphone], matrix, phone.model_ids())
    assert not bad and good[0][1].cell.platform.id == "iphone-16-pro"


def test_text_forms():
    lines = json.dumps(row()) + "\n" + json.dumps(row(workload="c4")) + "\n"
    assert len(phone.parse_text(lines)) == 2
    assert len(phone.parse_text(json.dumps({"rows": [row()]}))) == 1
    packed = base64.b64encode(gzip.compress(lines.encode())).decode()
    assert len(phone.parse_text(packed)) == 2


def test_store_rows_under_a_test_tag(tmp_path, matrix):
    store = DirStore(tmp_path / "store")
    good, _, _ = phone.validate([row(), row(workload="c4", status="fail", error="crash", rounds=[])], matrix, phone.model_ids())
    phone.store_rows(good, store)
    t = store.table()
    assert t.num_rows == 2 and set(t.column("platform").to_pylist()) == {"galaxy-s25-ultra"}
    assert phone.count_rows(store, "test-phone-unit", ["phone-test-20261106T030000-ab12"]) == {"phone-test-20261106T030000-ab12": 2}
    # a run sent again replaces itself
    phone.store_rows(good, store)
    assert store.table().num_rows == 2


def test_every_phone_artifact_maps_to_a_suite_model(matrix):
    ids = phone.model_ids()
    for a, m in [("qwen3.5-0.8b-llamacpp", "qwen3.5-0.8b"), ("gemma-4-e2b-litert", "gemma-4-e2b"), ("gemma-4-12b-litert", "gemma-4-12b"),
                 ("qwen3.5-0.8b-mlc", "qwen3.5-0.8b"), ("gemma-4-e2b-mlc", "gemma-4-e2b"), ("qwen3.5-4b-mlxlm", "qwen3.5-4b")]:
        assert ids[a] == m
    data = json.loads(phone.WORKLOADS_JSON.read_text())
    assert [w["id"] for w in data["workloads"]] == list(phone.PHONE_WORKLOADS)
    assert set(data["templates"]) == {"qwen3.5-0.8b", "qwen3.5-4b", "gemma-4-e2b", "gemma-4-e4b", "gemma-4-12b"}


def test_phone_cells_are_never_planned(matrix):
    phones = phone.load_phones(ROOT / "matrix")
    assert "galaxy-s25-ultra" in phones and not set(phones) & set(matrix.platforms)
    cells = matrix.expand(artifacts=[a for a in matrix.artifacts if a.endswith(("-litert", "-mlc")) or a.startswith("qwen3.5-0.8b-l")])
    assert all(not c.tiers for c in cells)


# ---- the ingest ---------------------------------------------------------------------------------------------------
def test_listen_addresses():
    assert allowed_address("127.0.0.1") and allowed_address("::1") and allowed_address("100.85.194.44")
    assert allowed_address("fd7a:115c:a1e0::1")
    assert not allowed_address("0.0.0.0") and not allowed_address("192.168.1.5") and not allowed_address("8.8.8.8")
    with pytest.raises(SystemExit):
        serve("0.0.0.0:8787", "x" * 20, Path("/tmp/none"), ROOT / "matrix")


def test_token_file(tmp_path):
    f = tmp_path / "t"
    tok = read_token(f, create=True)
    assert len(tok) >= 16 and (f.stat().st_mode & 0o777) == 0o600
    f.chmod(0o644)
    with pytest.raises(SystemExit):
        read_token(f)


@pytest.fixture
def ingest(tmp_path):
    from http.server import ThreadingHTTPServer

    token = "t" * 24
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(token, tmp_path / "inbox", ROOT / "matrix"))
    th = threading.Thread(target=httpd.serve_forever, daemon=True)
    th.start()
    yield f"http://127.0.0.1:{httpd.server_address[1]}", token, tmp_path / "inbox"
    httpd.shutdown()


def post(url, body: str, token: str | None):
    rq = urllib.request.Request(url + "/v1/results", data=body.encode(), method="POST",
                                headers={"Content-Type": "application/x-ndjson", **({"Authorization": f"Bearer {token}"} if token else {})})
    try:
        with urllib.request.urlopen(rq, timeout=30) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def test_ingest_end_to_end(ingest, tmp_path, matrix):
    url, token, inbox = ingest
    with urllib.request.urlopen(url + "/v1/health", timeout=10) as r:
        assert json.loads(r.read())["ok"]
    body = json.dumps(row()) + "\n" + json.dumps(row(artifact="nope")) + "\n"
    assert post(url, body, None)[0] == 401
    assert post(url, body, "wrong-token-wrong-token")[0] == 401
    code, reply = post(url, body, token)
    assert code == 200 and reply["accepted"] == 1 and [b["line"] for b in reply["rejected"]] == [2]
    pending = list((inbox / "pending").glob("*.jsonl"))
    assert len(pending) == 1 and len(pending[0].read_text().splitlines()) == 1
    assert post(url, json.dumps(row(artifact="nope")), token)[0] == 422
    store = DirStore(tmp_path / "store")
    assert import_spool(inbox, store, matrix, log=lambda *_: None) == (1, 0)
    assert store.table().num_rows == 1 and not list(spool_dirs(inbox)["pending"].glob("*.jsonl"))
