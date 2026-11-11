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


def _db(text: str) -> dict:
    return json.loads(text.removeprefix("const DB = ").rstrip().removesuffix(";"))


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
    while client.get("/v1/db.js").status_code == 503 and time.time() < deadline:
        time.sleep(0.5)
    db = client.get("/v1/db.js")
    assert db.status_code == 200 and "tags" in _db(db.text)
    assert client.get("/v1/db.js", headers={"If-None-Match": db.headers["etag"]}).status_code == 304


def test_uploads_need_a_valid_token_and_stop_at_the_quota(client):
    assert client.post("/v1/submissions", content=_submission("run-x")).status_code == 401
    assert client.post("/v1/submissions", content=_submission("run-x"), headers={"Authorization": "Bearer nope"}).status_code == 401
    tok = client.post("/v1/tokens", json={}).json()
    auth = {"Authorization": f"Bearer {tok['token']}"}
    assert client.post("/v1/submissions", content=_submission("run-a"), headers=auth).status_code == 200
    assert client.post("/v1/submissions", content=_submission("run-b"), headers=auth).status_code == 200
    assert client.post("/v1/submissions", content=_submission("run-c"), headers=auth).status_code == 429
    assert client.post(f"/v1/tokens/{tok['id']}/quota", json={"quota": 10}, headers=auth).status_code == 403
    raised = client.post(f"/v1/tokens/{tok['id']}/quota", json={"quota": 10}, headers={"Authorization": "Bearer admin-secret"})
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
        hardware = {h["id"]: h for h in _db(client.get("/v1/db.js").text)["hardware"]}
        if "m9-ultra-512g" in hardware:
            break
        time.sleep(0.5)
    assert hardware["m9-ultra-512g"]["resource"] == "Community"


def test_a_restarted_api_serves_the_saved_views_at_once(client):
    deadline = time.time() + 60
    while client.get("/v1/db.js").status_code == 503 and time.time() < deadline:
        time.sleep(0.5)
    etag = client.get("/v1/db.js").headers["etag"]
    from server.app import Views, app

    fresh = Views(app.state.db)
    fresh.load()
    assert fresh.get("db.js")[1] == etag


def test_monitors_can_check_health_with_head(client):
    assert client.head("/healthz").status_code == 200


def test_only_the_routes_the_site_and_cli_use_exist(client):
    for gone in ["/v1/catalog", "/v1/grid", "/v1/export.json.gz", "/v1/quality", "/v1/runs/run-1/log"]:
        assert client.get(gone).status_code == 404, gone
