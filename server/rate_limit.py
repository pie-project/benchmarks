from __future__ import annotations

import threading
import time
from collections import defaultdict, deque

from fastapi import HTTPException


class RateLimit:
    def __init__(self, limit: int, window_s: float):
        self.limit = limit
        self.window_s = window_s
        self.hits: dict[str, deque] = defaultdict(deque)
        self.lock = threading.Lock()

    def check(self, key: str) -> None:
        now = time.monotonic()
        with self.lock:
            q = self.hits[key]
            while q and now - q[0] > self.window_s:
                q.popleft()
            if len(q) >= self.limit:
                raise HTTPException(
                    429,
                    "too many requests, try again later",
                    headers={"Retry-After": str(int(self.window_s))},
                )
            q.append(now)
