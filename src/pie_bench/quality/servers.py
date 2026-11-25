from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def get(url: str, timeout: float = 5.0) -> bytes:
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return r.read()


def post(url: str, body: dict, timeout: float = 1200.0) -> dict:
    req = urllib.request.Request(
        url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def serve(cmd: list[str], env: dict[str, str], port: int, health: str, timeout_s: float):
    url = f"http://127.0.0.1:{port}"
    log = tempfile.NamedTemporaryFile("w", prefix="quality-server-", suffix=".log", delete=False)
    proc = subprocess.Popen(
        [sys.executable, "-m", "pie_bench.engines.lifeline", *cmd],
        env={**os.environ, **env},
        stdin=subprocess.PIPE,
        stdout=log,
        stderr=subprocess.STDOUT,
    )
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            raise RuntimeError(f"{cmd[0]} exited during startup (see {log.name})")
        try:
            get(url + health, timeout=3)
            return proc, url
        except OSError:
            time.sleep(0.5)
    stop(proc)
    raise RuntimeError(f"{cmd[0]} did not answer {health} within {timeout_s:.0f}s (see {log.name})")


def _kill_lifeline_tree(proc) -> None:
    if sys.platform == "win32":
        subprocess.run(
            ["taskkill", "/T", "/F", "/PID", str(proc.pid)], capture_output=True, check=False
        )


def stop(proc) -> None:
    _kill_lifeline_tree(proc)
    proc.terminate()
    try:
        proc.wait(timeout=30)
    except subprocess.TimeoutExpired:
        proc.kill()
