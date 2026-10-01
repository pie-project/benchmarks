"""Which pie commits are worth measuring: one that only touches docs or CI
files cannot change a benchmark number."""

from __future__ import annotations

from collections.abc import Iterable

DOC_DIRS = ("docs/", ".github/")
DOC_NAMES = ("LICENSE", "NOTICE", ".gitignore")
DOC_SUFFIXES = (".md",)


def is_doc(path: str) -> bool:
    return path.startswith(DOC_DIRS) or path in DOC_NAMES or path.endswith(DOC_SUFFIXES)


def docs_only(paths: Iterable[str]) -> bool:
    paths = [p.strip() for p in paths if p.strip()]
    return bool(paths) and all(is_doc(p) for p in paths)
