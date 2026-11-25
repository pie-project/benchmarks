from __future__ import annotations

import gzip
import logging
import os
import threading
from contextlib import asynccontextmanager

from fastapi import Body, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from pie_bench import __version__
from server import auth, profiles, rate_limit, submissions
from server.db import Database
from server.hit_counter import HitCounter
from server.view_cache import ViewCache

log = logging.getLogger("pie-bench-api")
READS = rate_limit.RateLimit(int(os.environ.get("READ_LIMIT", "600")), 60)
WRITES = rate_limit.RateLimit(int(os.environ.get("WRITE_LIMIT", "30")), 3600)
TOKENS = rate_limit.RateLimit(int(os.environ.get("TOKEN_LIMIT", "5")), 3600)


def _cached(request: Request, key: str, media_type: str) -> Response:
    READS.check(auth.address(request))
    data, etag = app.state.views.get(key)
    if request.method == "GET":
        app.state.hits.add(request.url.path)
    headers = {"ETag": etag, "Cache-Control": "public, max-age=60, stale-while-revalidate=600", "Vary": "Accept-Encoding"}
    if request.headers.get("if-none-match") == etag:
        return Response(status_code=304, headers=headers)
    if "gzip" in request.headers.get("accept-encoding", ""):
        return Response(data, media_type=media_type, headers={**headers, "Content-Encoding": "gzip"})
    return Response(gzip.decompress(data), media_type=media_type, headers=headers)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.db = Database()
    app.state.views = ViewCache(app.state.db)
    app.state.views.load()
    app.state.hits = HitCounter(app.state.db)
    threading.Thread(target=app.state.views.loop, daemon=True, name="views").start()
    threading.Thread(target=app.state.hits.loop, daemon=True, name="hits").start()
    yield
    app.state.views.stop()
    app.state.hits.stop()
    app.state.db.close()


app = FastAPI(title="Pie Benchmarks API", version=__version__, lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)
app.add_middleware(CORSMiddleware, allow_origins=[o for o in os.environ.get("CORS_ORIGINS", "*").split(",") if o],
                   allow_methods=["GET"], allow_headers=["*"], expose_headers=["ETag"])


@app.api_route("/", methods=["GET", "HEAD"])
def root():
    return {"name": "pie-bench api", "version": __version__}


@app.api_route("/healthz", methods=["GET", "HEAD"])
def healthz():
    with app.state.db.tx() as cur:
        cur.execute("SELECT 1")
    return {"ok": True, "views_built_at": app.state.views.built_at or None}


@app.api_route("/v1/catalog", methods=["GET", "HEAD"])
def catalog(request: Request):
    return _cached(request, "catalog", "application/json")


@app.api_route("/v1/results", methods=["GET", "HEAD"])
def results(request: Request):
    return _cached(request, "results", "application/json")


@app.api_route("/v1/releases/latest", methods=["GET", "HEAD"])
def latest_release(request: Request):
    return _cached(request, "results", "application/json")


@app.api_route("/v1/head-to-head", methods=["GET", "HEAD"])
def head_to_head(request: Request):
    return _cached(request, "head-to-head", "application/json")


@app.api_route("/v1/footprint", methods=["GET", "HEAD"])
def download_sizes(request: Request):
    return _cached(request, "footprint", "application/json")


@app.api_route("/v1/profiles", methods=["GET", "HEAD"])
def cell_profiles(request: Request):
    return _cached(request, "profiles", "application/json")


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
async def upload_submission(request: Request):
    addr = auth.address(request)
    WRITES.check(addr)
    tid = auth.token_id(request)
    doc = submissions.decode(await request.body())
    records, scores = submissions.check(doc)
    with app.state.db.tx() as cur:
        out = submissions.store(cur, doc, records, scores, token_id=tid, address=addr)
    app.state.views.dirty.set()
    return out


@app.post("/v1/profiles")
async def upload_profiles(request: Request):
    addr = auth.address(request)
    WRITES.check(addr)
    tid = None if auth.is_admin(request) else auth.token_id(request)
    cells = profiles.check(submissions.decode(await request.body()))
    with app.state.db.tx() as cur:
        if tid:
            cur.execute("SELECT revoked FROM tokens WHERE id = %s", (tid,))
            row = cur.fetchone()
            if not row or row[0]:
                raise HTTPException(401, "token revoked or unknown: run `pie-bench login`")
        out = profiles.store(cur, cells, token_id=tid, address=addr)
        data = profiles.blob(cur)
    app.state.views.put("profiles", data)
    return out


@app.post("/v1/rebuild", status_code=202)
def rebuild(request: Request):
    auth.require_admin(request)
    with app.state.db.tx() as cur:
        cur.execute("INSERT INTO ingest_log (address, action) VALUES (%s, 'rebuild')", (auth.address(request),))
    app.state.views.dirty.set()
    return {"rebuilding": True, "views_built_at": app.state.views.built_at or None}


@app.get("/v1/stats")
def stats(request: Request, days: int = 30):
    auth.require_admin(request)
    app.state.hits.flush()
    with app.state.db.tx() as cur:
        cur.execute("SELECT day, path, count FROM hits WHERE day > current_date - %s ORDER BY day DESC, path", (max(1, min(days, 366)),))
        rows = cur.fetchall()
    by_day: dict[str, dict[str, int]] = {}
    for day, path, n in rows:
        by_day.setdefault(day.isoformat(), {})[path] = n
    return {"days": [{"day": day, "requests": requests} for day, requests in by_day.items()]}


@app.patch("/v1/tokens/{tid}")
def update_token(tid: str, request: Request, body: dict = Body(...)):
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
