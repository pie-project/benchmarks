from __future__ import annotations

import hmac
import os
import secrets
import time

import jwt
from fastapi import HTTPException, Request

ALGORITHM = "HS256"
DEFAULT_QUOTA = int(os.environ.get("DEFAULT_QUOTA", "20"))


def signing_key() -> str:
    key = os.environ.get("JWT_SECRET")
    if not key:
        raise RuntimeError("JWT_SECRET is not set")
    return key


def new_token_id() -> str:
    return "tk_" + secrets.token_hex(8)


def issue(token_id: str) -> str:
    return jwt.encode({"sub": token_id, "iat": int(time.time()), "iss": "pie-bench"}, signing_key(), algorithm=ALGORITHM)


def bearer(request: Request) -> str:
    header = request.headers.get("authorization", "")
    if not header.lower().startswith("bearer "):
        raise HTTPException(401, "missing token: run `pie-bench login`")
    return header[7:].strip()


def token_id(request: Request) -> str:
    try:
        claims = jwt.decode(bearer(request), signing_key(), algorithms=[ALGORITHM], issuer="pie-bench")
    except jwt.PyJWTError:
        raise HTTPException(401, "invalid token: run `pie-bench login` again") from None
    return claims["sub"]


def is_admin(request: Request) -> bool:
    expected = os.environ.get("ADMIN_TOKEN")
    header = request.headers.get("authorization", "")
    return bool(expected) and header.lower().startswith("bearer ") and hmac.compare_digest(header[7:].strip(), expected)


def require_admin(request: Request) -> None:
    if not is_admin(request):
        raise HTTPException(403, "admin token required")


def address(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "")
    return forwarded.split(",")[0].strip() or (request.client.host if request.client else "unknown")
