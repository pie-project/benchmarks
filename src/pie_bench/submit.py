from __future__ import annotations

import gzip
import json
import os
import platform
import urllib.error
import urllib.request
from pathlib import Path

from pie_bench import __version__

API = os.environ.get("PIE_BENCH_API") or "https://bench-api.pie-project.org"
TOKEN_FILE = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config") / "pie-bench" / "token"
SUBMISSION = "submission.json.gz"
FORMAT = 1


class ApiError(RuntimeError):
    pass


def request(method: str, path: str, body: bytes | None = None, *, token: str | None = None, content_type: str = "application/json") -> dict:
    req = urllib.request.Request(f"{API.rstrip('/')}{path}", data=body, method=method,
                                 headers={"User-Agent": f"pie-bench/{__version__}", "Accept": "application/json"})
    if body is not None:
        req.add_header("Content-Type", content_type)
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            return json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        try:
            detail = json.loads(e.read()).get("detail")
        except ValueError:
            detail = e.reason
        raise ApiError(f"{e.code}: {detail}") from None
    except urllib.error.URLError as e:
        raise ApiError(f"cannot reach {API}: {e.reason}") from None


def saved_token() -> str | None:
    if os.environ.get("PIE_BENCH_TOKEN"):
        return os.environ["PIE_BENCH_TOKEN"]
    return TOKEN_FILE.read_text().strip() if TOKEN_FILE.exists() else None


def login(name: str | None = None) -> dict:
    out = request("POST", "/v1/tokens", json.dumps({"name": name or platform.node()}).encode())
    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_FILE.write_text(out["token"] + "\n")
    TOKEN_FILE.chmod(0o600)
    return out


def token() -> str:
    return saved_token() or login()["token"]


def _jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text().splitlines():
        try:
            rows.append(json.loads(line))
        except ValueError:
            continue
    return rows


def pack(out: Path, meta: dict) -> Path:
    log = out / "run.log"
    quality = [json.loads(p.read_text()) for p in sorted((out / "quality").glob("*.json"))] if (out / "quality").is_dir() else []
    doc = {
        "format": FORMAT,
        "pie_bench": __version__,
        **meta,
        "records": _jsonl(out / "records.jsonl"),
        "quality": quality,
        "log": log.read_text(errors="replace") if log.exists() else "",
    }
    path = out / SUBMISSION
    path.write_bytes(gzip.compress(json.dumps(doc, default=str).encode()))
    return path


def merge(outs: list[Path], path: Path) -> Path:
    """One submission of several runs' folders on one machine (the quota counts submissions, not runs). Each record
    keeps its run; the submission names a pie commit only when every run measured that one."""
    docs = [json.loads(gzip.decompress((o / SUBMISSION).read_bytes())) for o in outs]
    machines = {(d.get("platform") or {}).get("id") for d in docs}
    tags = {d.get("tag") for d in docs}
    if len(machines) > 1 or len(tags) > 1:
        raise ApiError(f"one submission holds one machine's runs for one release: {sorted(map(str, machines))}, tags {sorted(map(str, tags))}")
    commits = {d.get("pie_commit") for d in docs}
    doc = {**docs[0], "pie_commit": commits.pop() if len(commits) == 1 else None, "records": [r for d in docs for r in d["records"]],
           "quality": [q for d in docs for q in d.get("quality") or []], "log": "\n".join(d.get("log") or "" for d in docs)}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(gzip.compress(json.dumps(doc, default=str).encode()))
    return path


def upload(path: Path) -> dict:
    return request("POST", "/v1/submissions", path.read_bytes(), token=token(), content_type="application/gzip")


def upload_profiles(cells: list[dict]) -> dict:
    """Posts profiled cells to /v1/profiles, which judges each one (no quota); a cell with an engine not measured stays out."""
    cells = [c for c in cells if c.get("gap_pct") is not None and not any("why" in c[s] for s in ("fastest", "second"))]
    if not cells:
        return {"profiles": 0}
    body = gzip.compress(json.dumps({"format": 1, "profiles": cells}).encode())
    return request("POST", "/v1/profiles", body, token=token(), content_type="application/gzip")
