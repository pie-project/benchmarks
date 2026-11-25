from __future__ import annotations

import os
from pathlib import Path


def repo_cache_dirname(repo_id: str) -> str:
    return "models--" + repo_id.replace("/", "--")


def hf_cache_roots() -> list[Path]:
    roots: list[Path] = []
    if cache := os.environ.get("HF_HUB_CACHE"):
        roots.append(Path(cache).expanduser())
    if home := os.environ.get("HF_HOME"):
        roots.append(Path(home).expanduser() / "hub")
    roots.append(
        Path(os.environ.get("XDG_CACHE_HOME", "~/.cache")).expanduser() / "huggingface" / "hub"
    )
    return roots


def hf_snapshot_dir(repo_id: str, revision: str | None = None) -> Path | None:
    candidate = Path(repo_id).expanduser()
    if candidate.exists():
        return candidate.resolve()
    for root in hf_cache_roots():
        repo = root / repo_cache_dirname(repo_id)
        snapshots = repo / "snapshots"
        if not snapshots.is_dir():
            continue
        if revision and (snapshots / revision).is_dir():
            return (snapshots / revision).resolve()
        for ref_name in ("main", "master"):
            ref = repo / "refs" / ref_name
            if ref.is_file():
                rev = ref.read_text().strip()
                if (snapshots / rev).is_dir():
                    return (snapshots / rev).resolve()
        dirs = sorted(
            (d for d in snapshots.iterdir() if d.is_dir()), key=lambda d: d.stat().st_mtime_ns
        )
        if dirs:
            return dirs[-1].resolve()
    return None


def hf_snapshot_file(repo_id: str, file_name: str, revision: str | None = None) -> Path | None:
    snap = hf_snapshot_dir(repo_id, revision)
    if snap is None:
        return None
    split = "-00001-of-" in file_name
    direct = snap / file_name
    if direct.is_file():
        return direct if split else direct.resolve()
    hits = sorted(snap.rglob(Path(file_name).name))
    return (hits[0] if split else hits[0].resolve()) if hits else None


def hf_cache_dir() -> Path:
    return Path(
        os.environ.get("HF_HUB_CACHE")
        or (
            Path(os.environ["HF_HOME"]) / "hub"
            if os.environ.get("HF_HOME")
            else Path.home() / ".cache/huggingface/hub"
        )
    )
