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
    key = _record("x")["cell_key"]
    runs = client.get(f"/v1/cells/{key}/runs").json()["runs"]
    assert [r["decode_tok_s"] for r in runs] == [42.0]
    assert client.get("/v1/runs/run-1/log").text == "hello from ~/run"
    deadline = time.time() + 60
    while client.get("/v1/grid").status_code == 503 and time.time() < deadline:
        time.sleep(0.5)
    grid = client.get("/v1/grid")
    assert grid.status_code == 200 and "tags" in grid.json()
    assert client.get("/v1/grid", headers={"If-None-Match": grid.headers["etag"]}).status_code == 304
    assert client.get("/v1/db.js").text.startswith("const DB = ")


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
