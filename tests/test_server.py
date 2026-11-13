import gzip
import json
import os
import time
from datetime import datetime, timezone

import pytest

DSN = os.environ.get("PIE_BENCH_TEST_DB")
pytestmark = pytest.mark.skipif(not DSN, reason="PIE_BENCH_TEST_DB is not set")


@pytest.fixture(scope="module")
def client():
    import psycopg

    with psycopg.connect(DSN, autocommit=True) as conn:
        conn.execute("DROP SCHEMA public CASCADE; CREATE SCHEMA public")
    from server import footprint
    from tests.test_footprint import PAGES

    footprint._get = PAGES.__getitem__
    os.environ.update(DATABASE_URL=DSN, JWT_SECRET="test-secret-0123456789abcdef0123456789", ADMIN_TOKEN="admin-secret", DEFAULT_QUOTA="2", REBUILD_S="1")
    from fastapi.testclient import TestClient

    from server.app import app

    with TestClient(app) as c:
        yield c


def _record(run_id: str, value: float = 42.0) -> dict:
    from pie_bench.paths import MATRIX
    from pie_bench.plan.matrix import Matrix
    from pie_bench.schema import CellStatus, PerfMetrics, Provenance, Record, Tier

    m = Matrix.load(MATRIX)
    cell = next(c for c in m.runnable(Tier.TARGETED, m.expand(platforms=["m5-max-64g"])) if str(c.engine) == "pie" and c.workload.id == "raw-512-256")
    prov = Provenance(harness_commit="h", pie_commit="a" * 40, engine_version="0.6.0", checkpoint_revision="rev", hardware_fingerprint={"chip": "Apple M5 Max"})
    rec = Record(run_id=run_id, job_id="j", tier=Tier.TARGETED, cell_id=cell.cell_id, cell_key=cell.cell_key, cell=cell, status=CellStatus.PASS,
                 perf=PerfMetrics(primary="decode_tok_s", decode_tok_s=value, rounds=[value], cov=0.001, prompt_tokens=512, output_tokens=256),
                 provenance=prov, started_at=datetime.now(timezone.utc), duration_s=12.0)
    return json.loads(rec.model_dump_json())


def _submission(run_id: str, **over) -> bytes:
    doc = {"format": 1, "pie_bench": "0.1.0", "run_id": run_id, "tier": "targeted", "tag": "manual-test", "tag_kind": "manual",
           "pie_commit": "a" * 40, "platform": {"id": "m5-max-64g"}, "records": [_record(run_id)], "quality": [], "log": "hello from /Users/someone/run"}
    return gzip.compress(json.dumps({**doc, **over}).encode())


def test_a_contributor_uploads_and_everyone_reads(client):
    tok = client.post("/v1/tokens", json={"name": "laptop"}).json()
    auth = {"Authorization": f"Bearer {tok['token']}", "Content-Type": "application/gzip"}
    res = client.post("/v1/submissions", content=_submission("run-1"), headers=auth)
    assert res.status_code == 200, res.text
    assert res.json()["results"] == 1 and res.json()["quota_left"] == 1
    deadline = time.time() + 60
    while client.get("/v1/catalog").status_code == 503 and time.time() < deadline:
        time.sleep(0.5)
    deadline = time.time() + 60
    while not client.get("/v1/catalog").json()["totals"].get("submissions") and time.time() < deadline:
        time.sleep(0.5)
    catalog = client.get("/v1/catalog")
    assert catalog.status_code == 200 and catalog.headers["content-type"] == "application/json"
    assert catalog.json()["totals"]["submissions"] >= 1
    assert client.get("/v1/catalog", headers={"If-None-Match": catalog.headers["etag"]}).status_code == 304
    [release] = catalog.json()["releases"]
    results = client.get("/v1/results").json()
    assert results["id"] == release["id"] and results["results"]
    assert client.get("/v1/releases/latest").json() == results
    assert client.get("/v1/head-to-head").json()["platforms"] == []
    assert [e["mb"] for e in client.get("/v1/footprint").json()["engines"]] == [16111, 9738, 31]


def test_uploads_need_a_valid_token_and_stop_at_the_quota(client):
    assert client.post("/v1/submissions", content=_submission("run-x")).status_code == 401
    assert client.post("/v1/submissions", content=_submission("run-x"), headers={"Authorization": "Bearer nope"}).status_code == 401
    tok = client.post("/v1/tokens", json={}).json()
    auth = {"Authorization": f"Bearer {tok['token']}"}
    assert client.post("/v1/submissions", content=_submission("run-a"), headers=auth).status_code == 200
    assert client.post("/v1/submissions", content=_submission("run-b"), headers=auth).status_code == 200
    assert client.post("/v1/submissions", content=_submission("run-c"), headers=auth).status_code == 429
    assert client.patch(f"/v1/tokens/{tok['id']}", json={"quota": 10}, headers=auth).status_code == 403
    raised = client.patch(f"/v1/tokens/{tok['id']}", json={"quota": 10}, headers={"Authorization": "Bearer admin-secret"})
    assert raised.json() == {"id": tok["id"], "quota": 10, "used": 2}
    assert client.post("/v1/submissions", content=_submission("run-c"), headers=auth).status_code == 200


def test_trust_checks_refuse_bad_submissions(client):
    tok = client.post("/v1/tokens", json={}, headers={"Authorization": "Bearer admin-secret"}).json()
    auth = {"Authorization": f"Bearer {tok['token']}"}
    assert client.post("/v1/submissions", content=b"not gzip", headers=auth).status_code == 422
    assert client.post("/v1/submissions", content=_submission("run-d", format=99), headers=auth).status_code == 422
    assert client.post("/v1/submissions", content=_submission("run-d", pie_commit="b" * 40), headers=auth).status_code == 422
    assert client.post("/v1/submissions", content=_submission("run-d", records=[], quality=[]), headers=auth).status_code == 422
    assert client.post("/v1/submissions", content=_submission("run-1"), headers=auth).status_code == 409


def test_a_machine_new_to_the_catalog_shows_on_the_site(client):
    tok = client.post("/v1/tokens", json={}, headers={"Authorization": "Bearer admin-secret"}).json()
    rec = _record("run-new")
    rec["cell"]["platform"] = {**rec["cell"]["platform"], "id": "m9-ultra-512g", "accelerator": "Apple M9 Ultra", "memory_gib": 512}
    body = gzip.compress(json.dumps({"format": 1, "run_id": "run-new", "tier": "targeted", "tag": "manual-test", "tag_kind": "manual",
                                     "pie_commit": "a" * 40, "platform": rec["cell"]["platform"], "records": [rec]}).encode())
    assert client.post("/v1/submissions", content=body, headers={"Authorization": f"Bearer {tok['token']}"}).status_code == 200
    deadline = time.time() + 60
    while time.time() < deadline:
        hardware = {h["id"]: h for h in client.get("/v1/catalog").json()["hardware"]}
        if "m9-ultra-512g" in hardware:
            break
        time.sleep(0.5)
    assert hardware["m9-ultra-512g"]["resource"] == "Community"


def test_a_restarted_api_serves_the_saved_views_at_once(client):
    deadline = time.time() + 60
    while client.get("/v1/catalog").status_code == 503 and time.time() < deadline:
        time.sleep(0.5)
    etag = client.get("/v1/catalog").headers["etag"]
    from fastapi import HTTPException

    from server.app import Views, app

    fresh = Views(app.state.db)
    fresh.load()
    assert fresh.get("catalog")[1] == etag
    with pytest.raises(HTTPException) as missing:
        fresh.get("not-saved")
    assert missing.value.status_code == 503


def test_the_admin_can_rebuild_the_views_at_once(client):
    tok = client.post("/v1/tokens", json={}).json()
    assert client.post("/v1/rebuild").status_code == 403
    assert client.post("/v1/rebuild", headers={"Authorization": f"Bearer {tok['token']}"}).status_code == 403
    before = client.get("/healthz").json()["views_built_at"]
    res = client.post("/v1/rebuild", headers={"Authorization": "Bearer admin-secret"})
    assert res.status_code == 202 and res.json()["rebuilding"] is True
    deadline = time.time() + 60
    while client.get("/healthz").json()["views_built_at"] == before and time.time() < deadline:
        time.sleep(0.5)
    assert client.get("/healthz").json()["views_built_at"] > before


def test_the_admin_sees_reads_per_endpoint_per_day(client):
    before = client.get("/v1/stats", headers={"Authorization": "Bearer admin-secret"}).json()["days"]
    seen = before[0]["requests"] if before else {}
    client.get("/v1/results")
    client.get("/v1/results")
    client.head("/v1/catalog")
    assert client.get("/v1/stats").status_code == 403
    today = client.get("/v1/stats", headers={"Authorization": "Bearer admin-secret"}).json()["days"][0]
    assert today["day"] == datetime.now(timezone.utc).date().isoformat()
    assert today["requests"]["/v1/results"] == seen.get("/v1/results", 0) + 2
    assert today["requests"].get("/v1/catalog", 0) == seen.get("/v1/catalog", 0)


def _profile(setup: str, second_ms: float, gap_pct: float = 50) -> dict:
    stages = {"attention": 1.0, "dense_matmul": 6.0, "moe": 0.0, "norm_rope_elementwise": 1.0, "sampling": 0.0, "other_gpu": 0.0, "gpu_idle": 2.0}
    slow = {**stages, "dense_matmul": 6.0 + second_ms - 10, "gpu_idle": 2.0}
    return {"hardware": "m5-max-64g", "model": "qwen3.5-9b", "setup": setup, "gap_pct": gap_pct, "trace": "/Users/someone/trace",
            "fastest": {"engine": "pie", "unit": "ms per output token", "benchmark_step_ms": 10.0, "profiled_step_ms": 10.2, "stage_ms": stages},
            "second": {"engine": "mlxlm", "unit": "ms per output token", "benchmark_step_ms": 15.0, "profiled_step_ms": second_ms, "stage_ms": slow}}


def test_profiles_are_judged_from_their_numbers_and_served_at_once(client):
    body = lambda cells: gzip.compress(json.dumps({"format": 1, "profiles": cells}).encode())
    assert client.post("/v1/profiles", content=body([_profile("decode", 15.1)])).status_code == 401
    tok = client.post("/v1/tokens", json={}, headers={"Authorization": "Bearer admin-secret"}).json()
    auth = {"Authorization": f"Bearer {tok['token']}"}
    assert client.post("/v1/profiles", content=body([{**_profile("decode", 15.1), "gap_pct": None}]), headers=auth).status_code == 422
    missing = _profile("prefill", 15.1)
    missing["second"]["stage_ms"] = None
    res = client.post("/v1/profiles", content=body([_profile("decode", 15.1), _profile("batching", 19.0), missing]), headers=auth)
    assert res.json() == {"profiles": 3, "confirmed": 1, "bad run": 1, "not profiled": 1}, res.text
    served = client.get("/v1/profiles").json()
    assert set(served) == {"m5-max-64g|qwen3.5-9b|decode", "m5-max-64g|qwen3.5-9b|batching"}
    good = served["m5-max-64g|qwen3.5-9b|decode"]
    assert good["verdict"] == "confirmed" and good["stageKey"] == "dense_matmul" and good["second"]["engine"] == "mlxlm"
    assert good["fastest"]["stages"]["linear_attention"] == 0
    assert served["m5-max-64g|qwen3.5-9b|batching"]["verdict"] == "bad run"
    assert "Users" not in client.get("/v1/profiles").text
    linear = _profile("batching", 15.2)
    linear["second"]["stage_ms"] = {**linear["second"]["stage_ms"], "linear_attention": 4.0, "dense_matmul": 6.0}
    client.post("/v1/profiles", content=body([linear]), headers={"Authorization": "Bearer admin-secret"})
    batching = client.get("/v1/profiles").json()["m5-max-64g|qwen3.5-9b|batching"]
    assert batching["verdict"] == "confirmed" and batching["stageKey"] == "linear_attention"
    roles = _profile("batching", 15.2)
    roles["second"]["stage_ms"] = {**roles["second"]["stage_ms"], "dense_matmul": 1.0, "qkv_proj": 1.0, "o_proj": 1.0, "mlp": 4.0, "lm_head": 4.1}
    client.post("/v1/profiles", content=body([roles]), headers={"Authorization": "Bearer admin-secret"})
    batching = client.get("/v1/profiles").json()["m5-max-64g|qwen3.5-9b|batching"]
    assert batching["stageKey"] == "dense_matmul" and batching["second"]["stages"]["mlp"] == 0 and batching["second"]["stages"]["dense_matmul"] == 11.1
    roles["fastest"]["stage_ms"] = {**roles["fastest"]["stage_ms"], "dense_matmul": 1.0, "qkv_proj": 1.0, "o_proj": 1.0, "mlp": 2.0, "lm_head": 1.0}
    client.post("/v1/profiles", content=body([roles]), headers={"Authorization": "Bearer admin-secret"})
    batching = client.get("/v1/profiles").json()["m5-max-64g|qwen3.5-9b|batching"]
    assert batching["stageKey"] == "lm_head" and batching["second"]["stages"]["mlp"] == 4.0 and batching["fastest"]["stages"]["lm_head"] == 1.0


def test_monitors_can_check_health_with_head(client):
    assert client.head("/healthz").status_code == 200


def test_only_the_routes_the_site_and_cli_use_exist(client):
    for gone in ["/v1/db.js", "/v1/tags/manual-test.json", "/v1/grid", "/v1/head-to-head.json", "/v1/export.json.gz", "/v1/quality", "/v1/runs/run-1/log", "/v1/docs", "/v1/openapi.json", "/docs", "/v1/trackers.json", "/v1/releases/manual-test"]:
        assert client.get(gone).status_code == 404, gone
