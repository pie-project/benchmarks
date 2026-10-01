"""One benchmark at a time on a machine.

A Mac can host more than one runner (this repo's and another's), and two of
them measuring at once share the GPU and the memory: runs come out invalid,
or do not fit. Every measuring command takes this lock first and waits its
turn. The lock is a file lock, so it is released when the process ends, however
it ends.
"""

from __future__ import annotations

import fcntl
import os
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

#: how long a job waits for its turn before it gives the run up (its cells are measured by the next run)
MAX_WAIT_S = 25 * 60


class MachineBusy(RuntimeError):
    pass


def lock_path() -> Path:
    return Path(os.environ.get("PIE_MACHINE_LOCK") or Path.home() / ".cache" / "pie-machine.lock")


@contextmanager
def machine_lock(note: str = "", *, max_wait_s: float | None = None, poll_s: float = 10.0, log=print) -> Iterator[float]:
    """Hold the machine for the body; yields the seconds spent waiting."""
    path = lock_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    limit = float(os.environ.get("PIE_MACHINE_LOCK_WAIT_S") or MAX_WAIT_S) if max_wait_s is None else max_wait_s
    t0 = time.monotonic()
    with open(path, "a+") as f:
        while True:
            try:
                fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                waited = time.monotonic() - t0
                if waited >= limit:
                    f.seek(0)
                    raise MachineBusy(f"another benchmark held this machine for {waited:.0f}s ({f.read().strip() or 'unknown'})") from None
                if waited < poll_s:
                    f.seek(0)
                    log(f"another benchmark is running on this machine ({f.read().strip() or 'unknown'}); waiting for it")
                time.sleep(poll_s)
        f.seek(0)
        f.truncate()
        f.write(f"pid {os.getpid()} {note}".strip() + "\n")
        f.flush()
        try:
            yield time.monotonic() - t0
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)
