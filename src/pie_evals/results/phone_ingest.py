"""The phone ingest: a small HTTP service the benchmark app POSTs its records.jsonl to, on the tailnet only.

    pie-evals phone-ingest --listen 100.85.194.44:8787 --token-file ~/.config/pie-evals/phone-ingest.token

It binds only to a loopback or Tailscale address (100.64.0.0/10, fd7a:115c:a1e0::/48) and answers only peers
from those ranges, so nothing outside the tailnet can reach it. Every request needs the bearer token. A POST is
checked row by row with the store's own conversion (pie_evals.results.phone) and the good rows are written to
the inbox (``<spool>/pending``), where the pages build on the site laptop imports them into the database
(``pie-evals import-phone --spool``) within a few minutes. With ``--direct`` and $PIE_EVALS_DB set it stores
them at once instead.
"""

from __future__ import annotations

import hmac
import ipaddress
import json
import os
import secrets
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from pie_evals.results import phone

MAX_BODY = 8 * 2**20
TAILNET = [ipaddress.ip_network("100.64.0.0/10"), ipaddress.ip_network("fd7a:115c:a1e0::/48")]


def allowed_address(host: str) -> bool:
    """Loopback or Tailscale: the only addresses the service binds to or answers."""
    try:
        ip = ipaddress.ip_address(host.split("%")[0])
    except ValueError:
        return False
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
        ip = ip.ipv4_mapped
    return ip.is_loopback or any(ip in net for net in TAILNET)


def read_token(path: Path, create: bool = False) -> str:
    if not path.exists():
        if not create:
            raise SystemExit(f"{path}: no token file (run with --init-token to make one)")
        path.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w") as f:
            f.write(secrets.token_urlsafe(24) + "\n")
    if path.stat().st_mode & 0o077:
        raise SystemExit(f"{path}: the token file must be readable by its owner only (chmod 600)")
    token = path.read_text().strip()
    if len(token) < 16:
        raise SystemExit(f"{path}: the token is shorter than 16 characters")
    return token


def spool_dirs(spool: Path) -> dict[str, Path]:
    d = {k: spool / k for k in ("pending", "done", "failed")}
    for p in d.values():
        p.mkdir(parents=True, exist_ok=True)
    return d


def spool_write(spool: Path, run_ids: set[str], rows: list[dict]) -> Path:
    """The good rows, as one file in pending/ (written whole, then renamed in, so an import never reads half a file)."""
    name = f"{time.strftime('%Y%m%dT%H%M%S')}-{'_'.join(sorted(run_ids))[:120]}-{secrets.token_hex(3)}.jsonl"
    pending = spool_dirs(spool)["pending"]
    tmp = pending / f".{name}.tmp"
    tmp.write_text("".join(json.dumps(r, separators=(",", ":")) + "\n" for r in rows))
    final = pending / name
    tmp.rename(final)
    return final


def import_spool(spool: Path, store, matrix, *, tag: str | None = None, log=print) -> tuple[int, int]:
    """Store every pending inbox file; a stored file moves to done/, one that cannot be stored to failed/ with its reason."""
    d = spool_dirs(spool)
    ok = failed = 0
    for f in sorted(d["pending"].glob("*.jsonl")):
        try:
            good, bad, warnings = phone.validate(phone.read_file(f), matrix, phone.model_ids())
            if not good:
                raise phone.PhoneRowError(f"no storable rows: {bad[:3]}")
            for msg in phone.store_rows(good, store, tag=tag):
                log(f"{f.name}: {msg}")
            for w in warnings + [f"line {b['line']}: {b['error']}" for b in bad]:
                log(f"{f.name}: {w}")
            f.rename(d["done"] / f.name)
            ok += 1
        except Exception as e:  # noqa: BLE001 - one bad file never holds the others back
            (d["failed"] / f"{f.name}.err").write_text(f"{type(e).__name__}: {e}\n")
            f.rename(d["failed"] / f.name)
            log(f"{f.name}: failed: {type(e).__name__}: {str(e)[:300]}")
            failed += 1
    return ok, failed


def make_handler(token: str, spool: Path, matrix_root: Path, direct_store=None):
    from pie_evals.plan.matrix import Matrix

    class Handler(BaseHTTPRequestHandler):
        server_version = "pie-evals-phone-ingest/1"

        def log_message(self, fmt, *args):  # one line per request, never a header or a body
            sys.stderr.write(f"[phone-ingest] {self.client_address[0]} {fmt % args}\n")

        def _reply(self, code: int, body: dict) -> None:
            data = json.dumps(body).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _gate(self) -> bool:
            if not allowed_address(self.client_address[0]):
                self._reply(403, {"error": "tailnet only"})
                return False
            return True

        def _authorized(self) -> bool:
            auth = self.headers.get("Authorization", "")
            given = auth[7:].strip() if auth.lower().startswith("bearer ") else ""
            if not given or not hmac.compare_digest(given.encode(), token.encode()):
                self._reply(401, {"error": "missing or wrong bearer token"})
                return False
            return True

        def do_GET(self):  # noqa: N802
            if not self._gate():
                return
            if self.path.rstrip("/") in ("/v1/health", "/health"):
                self._reply(200, {"ok": True, "schema": phone.SCHEMA, "workloads": list(phone.PHONE_WORKLOADS)})
            else:
                self._reply(404, {"error": "POST /v1/results"})

        def do_POST(self):  # noqa: N802
            if not self._gate() or not self._authorized():
                return
            if self.path.rstrip("/") != "/v1/results":
                self._reply(404, {"error": "POST /v1/results"})
                return
            n = int(self.headers.get("Content-Length") or 0)
            if n <= 0 or n > MAX_BODY:
                self._reply(413 if n > MAX_BODY else 400, {"error": f"body must be 1 byte to {MAX_BODY} bytes"})
                return
            try:
                raw = phone.parse_text(self.rfile.read(n).decode())
            except (ValueError, UnicodeDecodeError) as e:
                self._reply(400, {"error": f"unreadable body: {str(e)[:200]}"})
                return
            good, bad, warnings = phone.validate(raw, Matrix.load(matrix_root), phone.model_ids())
            body = {"accepted": len(good), "rejected": bad, "warnings": warnings}
            if good:
                path = spool_write(spool, {row.run_id for row, _ in good}, [obj for obj in raw if _ok(obj, good)])
                body["spooled"] = path.name
                if direct_store is not None:
                    try:
                        body["stored"] = phone.store_rows(good, direct_store)
                        path.rename(spool_dirs(spool)["done"] / path.name)
                    except Exception as e:  # noqa: BLE001 - the inbox still holds the rows for the next import
                        body["stored"] = None
                        body["store_error"] = f"{type(e).__name__}: {str(e)[:200]}"
                else:
                    body["note"] = "in the inbox; the site laptop's pages build stores it within about 5 minutes"
            self._reply(200 if good else 422, body)

    return Handler


def _ok(obj: dict, good) -> bool:
    """Whether this sent object is one of the good rows (matched by run, engine, artifact and workload)."""
    keys = {(row.run_id, row.engine, row.artifact, row.workload) for row, _ in good}
    return isinstance(obj, dict) and (obj.get("run_id"), obj.get("engine"), obj.get("artifact"), obj.get("workload")) in keys


def serve(listen: str, token: str, spool: Path, matrix_root: Path, direct_store=None) -> None:
    host, _, port = listen.rpartition(":")
    host = host.strip("[]")
    if not allowed_address(host):
        raise SystemExit(f"{host}: the ingest listens only on a loopback or Tailscale address (100.64.0.0/10), never a public one")
    spool_dirs(spool)
    httpd = ThreadingHTTPServer((host, int(port)), make_handler(token, spool, matrix_root, direct_store))
    print(f"[phone-ingest] listening on http://{listen} (tailnet only), inbox {spool}", file=sys.stderr, flush=True)
    httpd.serve_forever()
