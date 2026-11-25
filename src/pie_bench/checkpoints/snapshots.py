from __future__ import annotations

import json
import os
import re
from pathlib import Path

from pie_bench.schema import ArtifactKind, ArtifactSpec, SourceFormat

WEIGHT_PATTERNS = ["*.json", "*.safetensors", "*.txt", "*.model", "*.tiktoken", "tokenizer*", "*.py", "*.jinja"]
TOKENIZER_PATTERNS = ["*.json", "*.txt", "*.model", "*.tiktoken", "tokenizer*", "*.jinja"]
MLC_PATTERNS = ["*.json", "*.bin", "*.txt", "*.model", "tokenizer*"]

_SPLIT = re.compile(r"-00001-of-(\d{5})\.gguf$")


def gguf_shards(gguf_file: str) -> list[str]:
    m = _SPLIT.search(gguf_file)
    if not m:
        return [gguf_file]
    n = int(m.group(1))
    return [gguf_file[: m.start()] + f"-{i:05d}-of-{n:05d}.gguf" for i in range(1, n + 1)]


def snapshot_dir_if_present(artifact: ArtifactSpec, hf_cache: Path, weights: bool = True) -> Path | None:
    org, _, name = artifact.base_model.partition("/")
    repo = hf_cache / f"models--{org}--{name}"
    base = repo / "snapshots"
    marker = artifact.gguf_file or ("mlc-chat-config.json" if artifact.source_format == SourceFormat.MLC else "config.json")

    def usable(d: Path) -> bool:
        return (d / marker).exists() and not d.name.startswith("mini-") and (not weights or has_weights(d, artifact))

    main = repo / "refs" / "main"
    for rev in (artifact.revision, main.read_text().strip() if main.is_file() else None):
        if rev and usable(base / rev):
            return base / rev
    snaps = sorted(d for d in base.glob("*") if usable(d)) if base.exists() else []
    return snaps[-1] if snaps else None


def has_weights(snapshot: Path, artifact: ArtifactSpec) -> bool:
    if artifact.gguf_file:
        return all((snapshot / f).exists() for f in gguf_shards(artifact.gguf_file))
    if artifact.source_format == SourceFormat.MLC:
        return any(f.exists() for f in snapshot.glob("params_shard_*.bin"))
    index = snapshot / "model.safetensors.index.json"
    if index.exists():
        try:
            files = set(json.loads(index.read_text()).get("weight_map", {}).values())
        except (OSError, ValueError):
            files = set()
        if files:
            return all((snapshot / f).exists() for f in files)
    return any(f.exists() for f in snapshot.glob("*.safetensors"))


def with_tokenizer(artifact: ArtifactSpec, snapshot: Path, hf_cache: Path, log=print) -> Path:
    from huggingface_hub import snapshot_download

    try:
        snapshot_download(artifact.base_model, revision=snapshot.name, cache_dir=str(hf_cache),
                          allow_patterns=TOKENIZER_PATTERNS, token=os.environ.get("HF_TOKEN") or None)
    except Exception as e:
        log(f"tokenizer files for {artifact.base_model}@{snapshot.name} not fetched: {e}")
    return snapshot


class SnapshotMissing(FileNotFoundError):
    pass


def draft_artifact(artifact: ArtifactSpec) -> ArtifactSpec | None:
    if not artifact.draft_model:
        return None
    return ArtifactSpec(id=f"{artifact.id}--draft", base_model=artifact.draft_model, family=artifact.family, scheme=artifact.scheme,
                        source_format=artifact.source_format, gguf_file=artifact.draft_gguf_file, tiers=[])


def ensure_snapshot(artifact: ArtifactSpec, hf_cache: Path, *, pie_root: Path | None = None, python: str = "python3", download: bool = True, log=print) -> Path:
    path = _ensure_snapshot(artifact, hf_cache, pie_root=pie_root, python=python, download=download, log=log)
    draft = draft_artifact(artifact)
    if draft is not None:
        _ensure_snapshot(draft, hf_cache, download=download, log=log)
    return path


def _ensure_snapshot(artifact: ArtifactSpec, hf_cache: Path, *, pie_root: Path | None = None, python: str = "python3", download: bool = True, log=print) -> Path:
    if artifact.kind == ArtifactKind.MINIATURE:
        from .miniature import ensure_miniature

        assert pie_root is not None
        return ensure_miniature(artifact, pie_root, hf_cache, python=python)
    have = snapshot_dir_if_present(artifact, hf_cache)
    if have:
        return _with_gguf_config(artifact, have, log)
    if not download:
        raise SnapshotMissing(f"checkpoint {artifact.base_model} not in HF cache {hf_cache} (run `pie-bench-node prepare`, or `run --download`; pie's resolve_local_model refuses network)")
    from huggingface_hub import snapshot_download

    log(f"download: {artifact.base_model}@{artifact.revision or 'main'} -> {hf_cache}")
    kw = {"revision": artifact.revision} if artifact.revision else {}
    if artifact.gguf_file:
        kw["allow_patterns"] = ["*.json", *gguf_shards(artifact.gguf_file)]
    elif artifact.source_format == SourceFormat.MLC:
        kw["allow_patterns"] = MLC_PATTERNS
    else:
        kw["allow_patterns"] = WEIGHT_PATTERNS
        kw["ignore_patterns"] = ["original/*", "metal/*"]
    os.environ.setdefault("HF_XET_HIGH_PERFORMANCE", "1")
    try:
        path = snapshot_download(artifact.base_model, cache_dir=str(hf_cache), token=os.environ.get("HF_TOKEN") or None, max_workers=16, **kw)
    except Exception as e:
        if "hf_xet" not in str(e):
            raise
        from huggingface_hub import constants

        log(f"download: {artifact.base_model} needs Xet; retrying with it on")
        os.environ.pop("HF_HUB_DISABLE_XET", None)
        constants.HF_HUB_DISABLE_XET = False
        path = snapshot_download(artifact.base_model, cache_dir=str(hf_cache), token=os.environ.get("HF_TOKEN") or None, max_workers=16, **kw)
    return _with_gguf_config(artifact, Path(path), log)


def _with_gguf_config(artifact: ArtifactSpec, path: Path, log=print) -> Path:
    if artifact.gguf_config_from and not (path / "config.json").exists():
        from huggingface_hub import hf_hub_download

        log(f"download: config.json of {artifact.gguf_config_from} -> {path}")
        src = hf_hub_download(artifact.gguf_config_from, "config.json", token=os.environ.get("HF_TOKEN") or None)
        (path / "config.json").write_bytes(Path(src).read_bytes())
    return path
