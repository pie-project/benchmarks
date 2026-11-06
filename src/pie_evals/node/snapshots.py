"""Checkpoints on the node.

pie's ``resolve_local_model`` refuses to touch the network, so pie-evals
fetches checkpoints itself: full artifacts through ``huggingface_hub``
(``HF_TOKEN`` honoured for gated repos), miniatures through pie's
``shrink_checkpoint.py`` (see ``miniature.py``). ``prepare`` does this for
every artifact of a tier before the bench fan-out so that N bench pods find
everything on the shared volume.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

from pie_evals.schema import ArtifactKind, ArtifactSpec, SourceFormat

WEIGHT_PATTERNS = ["*.json", "*.safetensors", "*.txt", "*.model", "*.tiktoken", "tokenizer*", "*.py", "*.jinja"]
TOKENIZER_PATTERNS = ["*.json", "*.txt", "*.model", "*.tiktoken", "tokenizer*", "*.jinja"]
#: an MLC build (WebLLM's -MLC repos): mlc-chat-config.json, the tensor cache index and its params_shard_*.bin
MLC_PATTERNS = ["*.json", "*.bin", "*.txt", "*.model", "tokenizer*"]

_SPLIT = re.compile(r"-00001-of-(\d{5})\.gguf$")


def gguf_shards(gguf_file: str) -> list[str]:
    """Every file of a GGUF arm: the one named, or each shard of a split model when it names the
    first (``...-00001-of-00004.gguf``; llama.cpp loads the rest from beside it)."""
    m = _SPLIT.search(gguf_file)
    if not m:
        return [gguf_file]
    n = int(m.group(1))
    return [gguf_file[: m.start()] + f"-{i:05d}-of-{n:05d}.gguf" for i in range(1, n + 1)]


def hf_cache_dir() -> Path:
    return Path(os.environ.get("HF_HUB_CACHE") or (Path(os.environ["HF_HOME"]) / "hub" if os.environ.get("HF_HOME") else Path.home() / ".cache/huggingface/hub"))


def snapshot_dir_if_present(artifact: ArtifactSpec, hf_cache: Path, weights: bool = True) -> Path | None:
    """The artifact's pinned revision, else the one the hub's ``main`` last
    resolved to, else any; ``weights=False`` for a row served from its
    imported .zt, which needs only the snapshot's config and tokenizer."""
    org, _, name = artifact.base_model.partition("/")
    repo = hf_cache / f"models--{org}--{name}"
    base = repo / "snapshots"
    # a GGUF repo carries no config.json, nor does an MLC build (its config is mlc-chat-config.json)
    marker = artifact.gguf_file or ("mlc-chat-config.json" if artifact.source_format == SourceFormat.MLC else "config.json")

    # a miniature is built beside its source's snapshots (`mini-l0-4-e16`, miniature.py) and
    # sorts after a hex revision: a full row must never pick it up (pie #680 was that —
    # "full" numbers on cards that had built the mini were the mini's)
    def usable(d: Path) -> bool:
        return (d / marker).exists() and not d.name.startswith("mini-") and (not weights or has_weights(d, artifact))

    main = repo / "refs" / "main"
    # hex order is no order: with several revisions cached, the last one sorted is arbitrary
    for rev in (artifact.revision, main.read_text().strip() if main.is_file() else None):
        if rev and usable(base / rev):
            return base / rev
    snaps = sorted(d for d in base.glob("*") if usable(d)) if base.exists() else []
    return snaps[-1] if snaps else None


def has_weights(snapshot: Path, artifact: ArtifactSpec) -> bool:
    """A snapshot whose weight files are gone (the blobs behind the symlinks
    reclaimed; gemma-4-E4B on the L40S pod, nightly 36099816046 s07) still
    carries its config.json and would be served: vLLM then boots into
    "Cannot find any model weights". ``exists`` follows the symlink."""
    if artifact.gguf_file:
        return all((snapshot / f).exists() for f in gguf_shards(artifact.gguf_file))
    if artifact.source_format == SourceFormat.MLC:
        return any(f.exists() for f in snapshot.glob("params_shard_*.bin"))
    index = snapshot / "model.safetensors.index.json"
    if index.exists():
        # a download the watchdog killed leaves the config and some shards (GLM-5.3-Flash on h200-x4,
        # weekly 39881122333: the next shard's pie found no deployment, SGLang no tokenizer)
        try:
            files = set(json.loads(index.read_text()).get("weight_map", {}).values())
        except (OSError, ValueError):
            files = set()
        if files:
            return all((snapshot / f).exists() for f in files)
    return any(f.exists() for f in snapshot.glob("*.safetensors"))


def with_tokenizer(artifact: ArtifactSpec, snapshot: Path, hf_cache: Path, log=print) -> Path:
    """The snapshot with its tokenizer and chat template on disk. A row pie
    imports by repository id is fetched by pie's own importer, which reads
    neither ``chat_template.jinja`` nor the tokenizer config's template; T0
    renders the reference prompt from them (Qwen3.6-27B on the 128g rendered
    14 tokens where its template writes 30)."""
    from huggingface_hub import snapshot_download

    try:
        snapshot_download(artifact.base_model, revision=snapshot.name, cache_dir=str(hf_cache),
                          allow_patterns=TOKENIZER_PATTERNS, token=os.environ.get("HF_TOKEN") or None)
    except Exception as e:  # offline, or a local-only revision: render with what is there
        log(f"tokenizer files for {artifact.base_model}@{snapshot.name} not fetched: {e}")
    return snapshot


class SnapshotMissing(FileNotFoundError):
    pass


def draft_artifact(artifact: ArtifactSpec) -> ArtifactSpec | None:
    """The draft checkpoint a baseline arm speculates with, as an artifact of its own (fetched like one)."""
    if not artifact.draft_model:
        return None
    return ArtifactSpec(id=f"{artifact.id}--draft", base_model=artifact.draft_model, family=artifact.family, scheme=artifact.scheme,
                        source_format=artifact.source_format, gguf_file=artifact.draft_gguf_file, tiers=[])


def ensure_snapshot(artifact: ArtifactSpec, hf_cache: Path, *, pie_root: Path | None = None, python: str = "python3", download: bool = True, log=print) -> Path:
    """Return the artifact's snapshot dir, with its draft checkpoint (``draft_model``) beside it in the cache."""
    path = _ensure_snapshot(artifact, hf_cache, pie_root=pie_root, python=python, download=download, log=log)
    draft = draft_artifact(artifact)
    if draft is not None:
        _ensure_snapshot(draft, hf_cache, download=download, log=log)
    return path


def _ensure_snapshot(artifact: ArtifactSpec, hf_cache: Path, *, pie_root: Path | None = None, python: str = "python3", download: bool = True, log=print) -> Path:
    """Return the artifact's snapshot dir. Miniatures are built if absent
    (atomically, see miniature.py). Full checkpoints are downloaded only when
    ``download`` is set — the bench node runs with it off, because fetching
    belongs to the ``prepare`` stage that runs once before the fan-out."""
    if artifact.kind == ArtifactKind.MINIATURE:
        from .miniature import ensure_miniature

        assert pie_root is not None
        return ensure_miniature(artifact, pie_root, hf_cache, python=python)
    have = snapshot_dir_if_present(artifact, hf_cache)
    if have:
        return _with_gguf_config(artifact, have, log)
    if not download:
        raise SnapshotMissing(f"checkpoint {artifact.base_model} not in HF cache {hf_cache} (run `pie-evals-node prepare`, or `run --download`; pie's resolve_local_model refuses network)")
    from huggingface_hub import snapshot_download

    log(f"download: {artifact.base_model}@{artifact.revision or 'main'} -> {hf_cache}")
    kw = {"revision": artifact.revision} if artifact.revision else {}
    if artifact.gguf_file:
        kw["allow_patterns"] = ["*.json", *gguf_shards(artifact.gguf_file)]
    elif artifact.source_format == SourceFormat.MLC:
        kw["allow_patterns"] = MLC_PATTERNS
    else:
        kw["allow_patterns"] = WEIGHT_PATTERNS
        # gpt-oss repos also carry original/ and metal/ copies of the weights (gpt-oss-120b: ~3x 65 GB),
        # which no engine here loads; they filled a 400 GB pod in 0.5.3-b5
        kw["ignore_patterns"] = ["original/*", "metal/*"]
    os.environ.setdefault("HF_XET_HIGH_PERFORMANCE", "1")  # more parallel Xet transfers: a cold pod's downloads bound the run
    try:
        path = snapshot_download(artifact.base_model, cache_dir=str(hf_cache), token=os.environ.get("HF_TOKEN") or None, max_workers=16, **kw)  # an empty secret must not become "Bearer "
    except Exception as e:  # noqa: BLE001
        # the pod disables Xet (runpod.py's HF_HUB_DISABLE_XET), and some repos serve their shards only through it
        # (DeepSeek-V4.1-Flash: "The file is too large to be downloaded using the regular download method")
        if "hf_xet" not in str(e):
            raise
        from huggingface_hub import constants

        log(f"download: {artifact.base_model} needs Xet; retrying with it on")
        os.environ.pop("HF_HUB_DISABLE_XET", None)
        constants.HF_HUB_DISABLE_XET = False
        path = snapshot_download(artifact.base_model, cache_dir=str(hf_cache), token=os.environ.get("HF_TOKEN") or None, max_workers=16, **kw)
    return _with_gguf_config(artifact, Path(path), log)


def _with_gguf_config(artifact: ArtifactSpec, path: Path, log=print) -> Path:
    """pie reads a snapshot's encoding from config.json ("a snapshot must carry
    the config.json its encoding is read from"); a GGUF repo ships none, so the
    base model's is copied in — also into a snapshot fetched before this existed."""
    if artifact.gguf_config_from and not (path / "config.json").exists():
        from huggingface_hub import hf_hub_download

        log(f"download: config.json of {artifact.gguf_config_from} -> {path}")
        src = hf_hub_download(artifact.gguf_config_from, "config.json", token=os.environ.get("HF_TOKEN") or None)
        (path / "config.json").write_bytes(Path(src).read_bytes())
    return path
