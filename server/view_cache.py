from __future__ import annotations

import hashlib
import logging
import multiprocessing
import os
import threading
import time
from concurrent.futures import ProcessPoolExecutor

from fastapi import HTTPException

from server import encoding, footprint, profiles, publish
from server.db import Database

log = logging.getLogger("pie-bench-api")


class ViewCache:
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
            cur.execute(
                "SELECT DISTINCT ON (platform) platform, machine->'platform' FROM runs "
                "WHERE platform IS NOT NULL AND jsonb_typeof(machine->'platform') = 'object' ORDER BY platform, submitted_at DESC"
            )
            contributed = {pid: spec for pid, spec in cur.fetchall()}
            cur.execute("SELECT count(*) FROM runs")
            submissions = cur.fetchone()[0]
        with ProcessPoolExecutor(
            max_workers=1, mp_context=multiprocessing.get_context("spawn")
        ) as pool:
            data = pool.submit(publish.blobs, self.db.dsn, contributed, submissions).result()
        sizes = self.sizes()
        if sizes:
            data["footprint"] = sizes
        with self.lock, self.db.tx() as cur:
            data["profiles"] = profiles.blob(cur)
            blobs = {k: _blob(v) for k, v in data.items()}
            self.blobs, self.built_at, self.built = blobs, time.time(), True
        self.save(data)
        log.info(
            "views built in %.1fs: %d files, %.0f MB compressed",
            time.monotonic() - t0,
            len(blobs),
            sum(len(v) for v in data.values()) / 1e6,
        )

    def sizes(self) -> bytes | None:
        try:
            return encoding.gz(footprint.sizes())
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

    def put(self, key: str, data: bytes) -> None:
        with self.lock:
            self.blobs = {**self.blobs, key: _blob(data)}
        with self.db.tx() as cur:
            cur.execute(
                "INSERT INTO views (key, data) VALUES (%s, %s) ON CONFLICT (key) DO UPDATE SET data = EXCLUDED.data, built_at = now()",
                (key, data),
            )

    def load(self) -> None:
        with self.db.tx() as cur:
            cur.execute("SELECT key, data, extract(epoch FROM built_at) FROM views")
            rows = cur.fetchall()
        if rows:
            with self.lock:
                self.blobs, self.built_at = (
                    {k: _blob(bytes(d)) for k, d, _ in rows},
                    float(max(t for _, _, t in rows)),
                )
            log.info("serving %d saved views until the first build", len(rows))

    def get(self, key: str) -> tuple[bytes, str]:
        with self.lock:
            hit = self.blobs.get(key)
        if hit is None:
            if not self.built:
                raise HTTPException(
                    503, "warming up, try again in a minute", headers={"Retry-After": "30"}
                )
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


def _blob(data: bytes) -> tuple[bytes, str]:
    return data, '"' + hashlib.sha256(data).hexdigest()[:32] + '"'
