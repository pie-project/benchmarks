"""The phone app's rows (pie_bench.phone) made into Records and API submissions (`pie-bench import-phone`)."""

from __future__ import annotations

import base64
import gzip
import json

import pytest
from click.testing import CliRunner

from pie_bench import phone
from pie_bench.cli import main
from pie_bench.paths import MATRIX
from pie_bench.plan.matrix import Matrix
from pie_bench.schema import Record


@pytest.fixture(scope="module")
def matrix():
    return Matrix.load(MATRIX)


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
    good, bad, _ = phone.validate([row()], matrix, phone.model_ids(matrix))
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
    good, bad, _ = phone.validate([pf, c4], matrix, phone.model_ids(matrix))
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
    good, bad, _ = phone.validate(rows, matrix, phone.model_ids(matrix))
    assert not good and [b["line"] for b in bad] == [1, 2, 3, 4, 5, 6]


def test_short_rounds_and_other_prompts_fail_the_row(matrix):
    short = row(rounds=[{"wall_s": 1.0, "requests": [req() for _ in range(5)]}] * 3)
    other = row(rounds=[{"wall_s": 1.0, "requests": [req(prompt=300) for _ in range(6)]}] * 3)
    good, bad, _ = phone.validate([short, other], matrix, phone.model_ids(matrix))
    assert not bad
    assert [(rec.status, rec.error_class) for _, rec in good] == [("fail", "harness_invalid"), ("fail", "input_mismatch")]


def test_failed_and_unsupported_rows_keep_their_reason(matrix):
    fail = row(status="fail", error_class="oom", error="out of memory", rounds=[])
    unsup = row(status="declared_unsupported", engine="litert", artifact="gemma-4-e2b-litert", workload="c4",
                error="serves one request at a time", rounds=[])
    good, bad, _ = phone.validate([fail, unsup], matrix, phone.model_ids(matrix))
    assert not bad
    (_, f), (_, u) = good
    assert f.status == "fail" and f.error_class == "oom" and f.perf is None
    assert u.status == "declared_unsupported" and u.invalid_reason == "serves one request at a time"


def test_unknown_phone_and_emulator(matrix):
    odd = row(device={**row()["device"], "model": "XQ-DE72", "manufacturer": "Sony"})
    emu = row(device={**row()["device"], "model": "sdk_gphone64_arm64", "emulator": True})
    good, _, warnings = phone.validate([odd, emu], matrix, phone.model_ids(matrix))
    assert good[0][1].cell.platform.id == "android-xq-de72" and warnings
    assert good[1][1].cell.platform.id == "android-emulator"
    iphone = row(device={"os": "ios", "model": "iPhone17,1", "ram_gib": 7.5}, engine="mlx-swift", artifact="qwen3.5-4b-mlxlm")
    good, bad, _ = phone.validate([iphone], matrix, phone.model_ids(matrix))
    assert not bad and good[0][1].cell.platform.id == "iphone-16-pro"


def test_text_forms():
    lines = json.dumps(row()) + "\n" + json.dumps(row(workload="c4")) + "\n"
    assert len(phone.parse_text(lines)) == 2
    assert len(phone.parse_text(json.dumps({"rows": [row()]}))) == 1
    packed = base64.b64encode(gzip.compress(lines.encode())).decode()
    assert len(phone.parse_text(packed)) == 2


def test_every_phone_artifact_maps_to_a_suite_model(matrix):
    ids = phone.model_ids(matrix)
    for a, m in [("qwen3.5-0.8b-llamacpp", "qwen3.5-0.8b"), ("gemma-4-e2b-litert", "gemma-4-e2b"), ("gemma-4-12b-litert", "gemma-4-12b"),
                 ("qwen3.5-0.8b-mlc", "qwen3.5-0.8b"), ("gemma-4-e2b-mlc", "gemma-4-e2b"), ("qwen3.5-4b-mlxlm", "qwen3.5-4b")]:
        assert ids[a] == m
    data = json.loads(phone.WORKLOADS_JSON.read_text())
    assert [w["id"] for w in data["workloads"]] == list(phone.PHONE_WORKLOADS)
    assert set(data["templates"]) == {"qwen3.5-0.8b", "qwen3.5-4b", "gemma-4-e2b", "gemma-4-e4b", "gemma-4-12b"}


def test_phone_cells_are_never_planned(matrix):
    phones = phone.load_phones(matrix.root)
    assert "galaxy-s25-ultra" in phones and not set(phones) & set(matrix.platforms)
    cells = matrix.expand(artifacts=[a for a in matrix.artifacts if a.endswith(("-litert", "-mlc")) or a.startswith("qwen3.5-0.8b-l")])
    assert all(not c.tiers for c in cells)



def test_pack_writes_one_submission_per_run(tmp_path, matrix):
    rows = [row(), row(workload="c4", status="fail", error="crash", rounds=[]), row(run_id="phone-test-20261106T040000-cd34")]
    good, bad, _ = phone.validate(rows, matrix, phone.model_ids(matrix), tag="test-phone-unit")
    assert not bad
    folders = phone.pack(good, tmp_path, tag="test-phone-unit")
    assert [d.name for d in folders] == ["phone-test-20261106T030000-ab12", "phone-test-20261106T040000-cd34"]
    doc = json.loads(gzip.decompress((folders[0] / "submission.json.gz").read_bytes()))
    assert doc["format"] == 1 and doc["run_id"] == folders[0].name and doc["tag"] == "test-phone-unit" and doc["tag_kind"] == "manual"
    assert len(doc["records"]) == 2 and doc["pie_commit"] is None
    assert all(Record.model_validate(r).validate_for_store() == [] for r in doc["records"])


def test_pie_row_names_its_commit_in_the_submission(tmp_path, matrix):
    sha = "fdc91d79742b7d28814d8009c136fecc14d1301c"
    r = row(engine="pie", engine_version=sha, engine_backend="metal", artifact="qwen3.5-0.8b-mlx4",
            device={"os": "ios", "model": "iPhone18,3", "ram_gib": 7.5, "emulator": False}, app={"version": "1.0", "harness_commit": "7d674c49abcdef", "platform": "ios"})
    good, bad, _ = phone.validate([r], matrix, phone.model_ids(matrix), tag="main-f03640150")
    assert not bad and good[0][1].cell.platform.id == "iphone-17" and good[0][1].provenance.pie_commit == sha
    (d,) = phone.pack(good, tmp_path, tag="main-f03640150")
    doc = json.loads(gzip.decompress((d / "submission.json.gz").read_bytes()))
    assert doc["pie_commit"] == sha and doc["tag_kind"] == "release" and doc["platform"]["id"] == "iphone-17"


def test_import_phone_cli(tmp_path):
    f = tmp_path / "records.jsonl"
    f.write_text(json.dumps(row()) + "\n" + json.dumps({"schema": "other/2"}) + "\n")
    res = CliRunner().invoke(main, ["import-phone", str(f), "--tag", "test-phone-unit", "--dry-run"])
    assert res.exit_code == 1 and "1 rows ok, 1 refused" in res.output and not (tmp_path / "out").exists()
    f.write_text(json.dumps(row()) + "\n")
    res = CliRunner().invoke(main, ["import-phone", str(f), "--tag", "test-phone-unit", "--out", str(tmp_path / "out")])
    assert res.exit_code == 0, res.output
    assert (tmp_path / "out" / "phone-test-20261106T030000-ab12" / "submission.json.gz").exists()
