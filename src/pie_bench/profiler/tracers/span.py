from __future__ import annotations

import json
import time
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def span(out: Path):
    """Writes when a recording started and stopped (span.json), for the measured windows to be checked against."""
    start = time.time_ns()
    try:
        yield
    finally:
        (out / "span.json").write_text(json.dumps({"start_ns": start, "stop_ns": time.time_ns()}))
