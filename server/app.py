from __future__ import annotations

import gzip
import hashlib
import logging
import multiprocessing
import os
import threading
import time
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import Body, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from pie_bench import __version__
from server import auth, build, footprint, ingest, split
from server.db import Database

log = logging.getLogger("pie-bench-api")
READS = auth.RateLimit(int(os.environ.get("READ_LIMIT", "600")), 60)
WRITES = auth.RateLimit(int(os.environ.get("WRITE_LIMIT", "30")), 3600)
TOKENS = auth.RateLimit(int(os.environ.get("TOKEN_LIMIT", "5")), 3600)


class Views:
    def __init__(self, db: Database):
        self.db = db
        self.lock = threading.Lock()
        self.dirty = threading.Event()
        self.stopped = threading.Event()
        self.blobs: dict[str, tuple[bytes, str]] = {}
        self.built_at = 0.0
        self.built = False

    def build(self) -> None:
        t0 = time.monotonic()
        with self.db.tx() as cur:
            cur.execute("SELECT DISTINCT ON (platform) platform, machine->'platform' FROM runs "
                        "WHERE platform IS NOT NULL AND jsonb_typeof(machine->'platform') = 'object' ORDER BY platform, submitted_at DESC")
            contributed = {pid: spec for pid, spec in cur.fetchall()}
            cur.execute("SELECT count(*) FROM runs")
            submissions = cur.fetchone()[0]
        with ProcessPoolExecutor(max_workers=1, mp_context=multiprocessing.get_context("spawn")) as pool:
            data = pool.submit(build.blobs, self.db.dsn, contributed, submissions).result()
        sizes = self.sizes()
        if sizes:
            data["footprint"] = sizes
        blobs = {k: _blob(v) for k, v in data.items()}
        with self.lock:
            self.blobs, self.built_at, self.built = blobs, time.time(), True
        self.save(data)
        log.info("views built in %.1fs: %d files, %.0f MB compressed", time.monotonic() - t0, len(blobs), sum(len(v) for v in data.values()) / 1e6)

    def sizes(self) -> bytes | None:
        try:
            return split.gz(footprint.sizes())
        except Exception:
            log.warning("download sizes not refreshed, keeping the last ones", exc_info=True)
            with self.lock:
                old = self.blobs.get("footprint")
            return old[0] if old else None

    def save(self, data: dict[str, bytes]) -> None:
        with self.db.tx() as cur:
            cur.execute("DELETE FROM views")
            with cur.copy("COPY views (key, data) FROM STDIN") as cp:
                for key, blob in data.items():
                    cp.write_row((key, blob))

    def load(self) -> None:
        with self.db.tx() as cur:
            cur.execute("SELECT key, data, extract(epoch FROM built_at) FROM views")
            rows = cur.fetchall()
        if rows:
            with self.lock:
                self.blobs, self.built_at = {k: _blob(bytes(d)) for k, d, _ in rows}, float(max(t for _, _, t in rows))
            log.info("serving %d saved views until the first build", len(rows))

    def get(self, key: str) -> tuple[bytes, str]:
        with self.lock:
            hit = self.blobs.get(key)
        if hit is None:
            if not self.built:
                raise HTTPException(503, "warming up, try again in a minute", headers={"Retry-After": "30"})
            raise HTTPException(404, "not found")
        return hit

    def stop(self) -> None:
        self.stopped.set()
        self.dirty.set()

    def loop(self) -> None:
        while not self.stopped.is_set():
            try:
                self.build()
            except Exception:
                log.exception("views build failed")
            self.dirty.wait(timeout=float(os.environ.get("REBUILD_S", "900")))
            self.dirty.clear()


class Hits:
    def __init__(self, db: Database):
        self.db = db
        self.lock = threading.Lock()
        self.counts: Counter[tuple[str, str]] = Counter()
        self.stopped = threading.Event()

    def add(self, path: str) -> None:
        with self.lock:
            self.counts[(datetime.now(timezone.utc).date().isoformat(), path)] += 1

    def flush(self) -> None:
        with self.lock:
            counts, self.counts = self.counts, Counter()
        if not counts:
            return
        try:
            with self.db.tx() as cur:
                cur.executemany("INSERT INTO hits (day, path, count) VALUES (%s, %s, %s) "
                                "ON CONFLICT (day, path) DO UPDATE SET count = hits.count + EXCLUDED.count",
                                [(day, path, n) for (day, path), n in counts.items()])
        except Exception:
            log.warning("hit counts not saved, keeping them for the next flush", exc_info=True)
            with self.lock:
                self.counts.update(counts)

    def loop(self) -> None:
        while not self.stopped.wait(timeout=60):
            self.flush()

    def stop(self) -> None:
        self.stopped.set()
        self.flush()


def _blob(data: bytes) -> tuple[bytes, str]:
    return data, '"' + hashlib.sha256(data).hexdigest()[:32] + '"'


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
    app.state.views = Views(app.state.db)
    app.state.views.load()
    app.state.hits = Hits(app.state.db)
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
