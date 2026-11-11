from __future__ import annotations

import gzip
import hashlib
import json
import logging
import os
import threading
import time
from contextlib import asynccontextmanager

from fastapi import Body, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, Response

from pie_bench import __version__
from server import auth, ingest, split
from server.db import Database

log = logging.getLogger("pie-bench-api")
READS = auth.RateLimit(int(os.environ.get("READ_LIMIT", "600")), 60)
WRITES = auth.RateLimit(int(os.environ.get("WRITE_LIMIT", "30")), 3600)
TOKENS = auth.RateLimit(int(os.environ.get("TOKEN_LIMIT", "5")), 3600)
LEAN = ["run_id", "cell_key", "status", "engine", "engine_version", "started_at", "duration_s", "tag", "tag_kind",
        "decode_tok_s", "prefill_tok_s", "output_tok_s", "ttft_ms_p50", "itl_ms_p50", "latency_ms_p50", "pie_commit"]


class Views:
    def __init__(self, db: Database):
        self.db = db
        self.lock = threading.Lock()
        self.dirty = threading.Event()
        self.core: dict = {}
        self.parts: dict[str, dict] = {}
        self.blobs: dict[str, tuple[bytes, str]] = {}
        self.built_at = 0.0

    def build(self) -> None:
        from server import views

        t0 = time.monotonic()
        core, parts = views.build(self.db.store)
        everything = {**core, "snapshots": {**core.get("snapshots", {}), **{t: p["snapshots"] for t, p in parts.items()}}}
        if "quality_snapshots" in core:
            everything["quality_snapshots"] = {**core["quality_snapshots"], **{t: p.get("quality_snapshots", []) for t, p in parts.items()}}
        blobs = {
            "grid": _blob(split.dumps(core).encode()),
            "db.js": _blob(("const DB = " + split.dumps(core) + ";\n").encode()),
            "export": _blob(gzip.compress(split.dumps(everything).encode())),
            "catalog": _blob(split.dumps({k: core.get(k) for k in ("hardware", "engines", "models", "workloads", "suites", "quality_tasks", "updated_at")}).encode()),
        }
        blobs.update({f"tag:{t}": _blob(split.dumps(p).encode()) for t, p in parts.items()})
        with self.lock:
            self.core, self.parts, self.blobs, self.built_at = core, parts, blobs, time.time()
        log.info("views built in %.1fs: %d tags", time.monotonic() - t0, len(parts))

    def get(self, key: str) -> tuple[bytes, str]:
        with self.lock:
            hit = self.blobs.get(key)
        if hit is None:
            if not self.built_at:
                raise HTTPException(503, "warming up, try again in a minute", headers={"Retry-After": "30"})
            raise HTTPException(404, "not found")
        return hit

    def loop(self) -> None:
        while True:
            try:
                self.build()
            except Exception:
                log.exception("views build failed")
            self.dirty.wait(timeout=float(os.environ.get("REBUILD_S", "900")))
            self.dirty.clear()


def _blob(data: bytes) -> tuple[bytes, str]:
    return data, '"' + hashlib.sha256(data).hexdigest()[:32] + '"'


def _cached(request: Request, key: str, media_type: str, *, encoding: str | None = None) -> Response:
    READS.check(auth.address(request))
    data, etag = app.state.views.get(key)
    headers = {"ETag": etag, "Cache-Control": "public, max-age=60, stale-while-revalidate=600"}
    if encoding:
        headers["Content-Encoding"] = encoding
    if request.headers.get("if-none-match") == etag:
        return Response(status_code=304, headers=headers)
    return Response(data, media_type=media_type, headers=headers)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.db = Database()
    app.state.views = Views(app.state.db)
    threading.Thread(target=app.state.views.loop, daemon=True, name="views").start()
    yield
    app.state.db.close()


app = FastAPI(title="Pie Benchmarks API", version=__version__, lifespan=lifespan, docs_url="/v1/docs", openapi_url="/v1/openapi.json")
app.add_middleware(GZipMiddleware, minimum_size=2048)
app.add_middleware(CORSMiddleware, allow_origins=[o for o in os.environ.get("CORS_ORIGINS", "*").split(",") if o],
                   allow_methods=["GET"], allow_headers=["*"], expose_headers=["ETag"])


@app.get("/")
def root():
    return {"name": "pie-bench api", "version": __version__, "docs": "/v1/docs"}


@app.get("/healthz")
def healthz():
    with app.state.db.tx() as cur:
        cur.execute("SELECT 1")
    return {"ok": True, "views_built_at": app.state.views.built_at or None}


@app.get("/v1/catalog")
def catalog(request: Request):
    return _cached(request, "catalog", "application/json")


@app.get("/v1/grid")
def grid(request: Request):
    return _cached(request, "grid", "application/json")


@app.get("/v1/grid/{tag}")
def grid_tag(tag: str, request: Request):
    return _cached(request, f"tag:{tag}", "application/json")


@app.get("/v1/db.js")
def db_js(request: Request):
    return _cached(request, "db.js", "application/javascript")


@app.get("/v1/tags/{name}")
def tag_file(name: str, request: Request):
    return _cached(request, f"tag:{name.removesuffix('.json')}", "application/json")


@app.get("/v1/trackers.json")
def trackers():
    return {}


@app.get("/v1/export.json.gz")
def export(request: Request):
    READS.check(auth.address(request))
    data, etag = app.state.views.get("export")
    if request.headers.get("if-none-match") == etag:
        return Response(status_code=304, headers={"ETag": etag})
    return Response(data, media_type="application/gzip", headers={"ETag": etag, "Cache-Control": "public, max-age=300",
                                                                   "Content-Disposition": 'attachment; filename="pie-benchmarks.json.gz"'})


@app.get("/v1/cells/{key:path}/runs")
def cell_runs(key: str, request: Request, limit: int = 100):
    READS.check(auth.address(request))
    with app.state.db.tx() as cur:
        cur.execute(f"SELECT {', '.join(LEAN)} FROM records WHERE cell_key = %s ORDER BY started_at DESC LIMIT %s", (key, max(1, min(limit, 1000))))
        rows = [dict(zip(LEAN, r)) for r in cur.fetchall()]
    return JSONResponse(json.loads(split.dumps({"cell_key": key, "runs": rows})))


@app.get("/v1/quality")
def quality(request: Request, tag: str | None = None, artifact: str | None = None):
    READS.check(auth.address(request))
    sql = "SELECT summary, tag, tag_kind, platform FROM quality WHERE (%s::text IS NULL OR tag = %s) AND (%s::text IS NULL OR artifact = %s) ORDER BY artifact, task, tag"
    with app.state.db.tx() as cur:
        cur.execute(sql, (tag, tag, artifact, artifact))
        rows = [{**s, "tag": t or None, "tag_kind": k, "platform": p or s.get("platform")} for s, t, k, p in cur.fetchall()]
    return JSONResponse(json.loads(split.dumps(rows)))


@app.get("/v1/runs/{run_id}/log")
def run_log(run_id: str, request: Request):
    READS.check(auth.address(request))
    with app.state.db.tx() as cur:
        cur.execute("SELECT log FROM run_logs WHERE run_id = %s", (run_id,))
        row = cur.fetchone()
    if not row:
        raise HTTPException(404, "no log for this run")
    return Response(split.HOME.sub("~", gzip.decompress(row[0]).decode(errors="replace")), media_type="text/plain")


@app.post("/v1/tokens")
def create_token(request: Request, body: dict = Body(default={})):
    admin = auth.is_admin(request)
    addr = auth.address(request)
    if not admin:
        TOKENS.check(addr)
    name = str(body.get("name") or "anonymous")[:80]
    quota = int(body.get("quota") or auth.DEFAULT_QUOTA) if admin else auth.DEFAULT_QUOTA
    tid = auth.new_token_id()
    with app.state.db.tx() as cur:
        cur.execute("INSERT INTO tokens (id, name, quota, admin_issued, address) VALUES (%s, %s, %s, %s, %s)", (tid, name, quota, admin, addr))
        cur.execute("INSERT INTO ingest_log (token_id, address, action, detail) VALUES (%s, %s, 'token', %s)", (tid, addr, name))
    return {"id": tid, "token": auth.issue(tid), "quota": quota}


@app.post("/v1/submissions")
async def submissions(request: Request):
    addr = auth.address(request)
    WRITES.check(addr)
    tid = auth.token_id(request)
    doc = ingest.decode(await request.body())
    records, scores = ingest.check(doc)
    with app.state.db.tx() as cur:
        out = ingest.store(cur, doc, records, scores, token_id=tid, address=addr)
    app.state.views.dirty.set()
    return out


@app.post("/v1/tokens/{tid}/quota")
def set_quota(tid: str, request: Request, body: dict = Body(...)):
    auth.require_admin(request)
    try:
        quota = int(body["quota"])
    except (KeyError, TypeError, ValueError):
        raise HTTPException(422, "body must be {\"quota\": <number>}") from None
    with app.state.db.tx() as cur:
        cur.execute("UPDATE tokens SET quota = %s WHERE id = %s RETURNING used", (quota, tid))
        row = cur.fetchone()
        if not row:
            raise HTTPException(404, "no such token")
        cur.execute("INSERT INTO ingest_log (token_id, address, action, detail) VALUES (%s, %s, 'quota', %s)", (tid, auth.address(request), str(quota)))
    return {"id": tid, "quota": quota, "used": row[0]}
