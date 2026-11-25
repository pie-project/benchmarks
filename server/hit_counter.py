from __future__ import annotations

import logging
import threading
from collections import Counter
from datetime import datetime, timezone

from server.db import Database

log = logging.getLogger("pie-bench-api")


class HitCounter:
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
