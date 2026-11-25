from __future__ import annotations

import gzip
import io
import json
import re

HOME = re.compile(r"/(?:Users|home)/[A-Za-z0-9._-]+")


def dumps(value) -> str:
    return HOME.sub("~", json.dumps(value, separators=(",", ":"), default=str))


def gz(value) -> bytes:
    out = io.BytesIO()
    with gzip.GzipFile(fileobj=out, mode="wb", compresslevel=6, mtime=0) as f:
        for chunk in json.JSONEncoder(separators=(",", ":"), default=str).iterencode(value):
            f.write(HOME.sub("~", chunk).encode())
    return out.getvalue()


def gz_text(text: str) -> bytes:
    return gzip.compress(text.encode(), compresslevel=6, mtime=0)
