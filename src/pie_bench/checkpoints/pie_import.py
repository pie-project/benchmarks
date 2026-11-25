from __future__ import annotations

import os
import platform
import re
import shutil
import subprocess
import uuid
from pathlib import Path

from pie_bench.installers.bench_env import cache_root
from pie_bench.schema import ArtifactKind, ArtifactSpec, QuantScheme, SourceFormat

RELAYOUT_MARK = "would relayout a weight plane"


def needs_import(artifact: ArtifactSpec) -> bool:
    return (
        artifact.source_format in (SourceFormat.MLX, SourceFormat.GGUF)
        or (bool(artifact.pie_sku) and artifact.scheme == QuantScheme.AFFINE_U4_G64)
        or "-nvfp4a4-" in (artifact.pie_sku or "")
        or (bool(artifact.pie_sku) and artifact.kind == ArtifactKind.MINIATURE)
    )


def artifact_root(root: Path | None = None) -> Path:
    return root or cache_root() / "artifacts"


def plain_sku(artifact: ArtifactSpec) -> str | None:
    if not (artifact.pie_drafter and artifact.pie_sku):
        return None
    plain = re.sub(r"-(dflash2?|dspark)(?=-)", "", artifact.pie_sku, count=1)
    return plain if plain != artifact.pie_sku else None


def artifact_dir(
    artifact: ArtifactSpec, commit: str, root: Path | None = None, *, plain: bool = False
) -> Path:
    return artifact_root(root) / f"{artifact.id}-{commit[:8]}{'-plain' if plain else ''}"


def have_artifacts(artifact: ArtifactSpec, commit: str, root: Path | None = None) -> bool:
    return bool(find_zt(artifact_dir(artifact, commit, root))) and (
        not plain_sku(artifact) or bool(find_zt(artifact_dir(artifact, commit, root, plain=True)))
    )


def find_zt(d: Path) -> Path | None:
    zts = sorted(d.glob("*.zt")) if d.exists() else []
    return zts[-1] if zts else None


def row_flag(pie_bin: Path) -> str:
    help_ = subprocess.run(
        [str(pie_bin), "model", "import", "--help"], capture_output=True, text=True
    ).stdout
    return "--deployment" if "--deployment" in help_ else "--sku"


def ensure_artifact(
    artifact: ArtifactSpec,
    snapshot: Path,
    pie_bin: Path,
    commit: str,
    *,
    root: Path | None = None,
    timeout_s: int = 3600,
    plain: bool = False,
    log=print,
) -> Path:
    sku = plain_sku(artifact) if plain else artifact.pie_sku
    timeout_s = max(timeout_s, int(float(artifact.expected_gib or 0) * 8))
    if plain and not sku:
        raise ValueError(f"{artifact.id} has no drafter row, so no plain deployment of its own")
    d = artifact_dir(artifact, commit, root, plain=plain)
    have = find_zt(d)
    if have:
        _tokenizer_beside(snapshot, d)
        return have
    tmp = d.parent / f".tmp-{d.name}-{platform.node()}-{os.getpid()}-{uuid.uuid4().hex[:6]}"
    tmp.mkdir(parents=True, exist_ok=True)
    source = snapshot / artifact.gguf_file if artifact.gguf_file else snapshot
    if artifact.pie_drafter and not plain:
        argv = [
            str(pie_bin),
            "model",
            "import",
            artifact.base_model,
            "--drafter",
            artifact.pie_drafter,
            "--out",
            str(tmp),
            "--keep-source",
        ]
    else:
        argv = [str(pie_bin), "model", "import", str(source), "--out", str(tmp), "--keep-source"]
    if sku:
        argv += [row_flag(pie_bin), sku]
    log(f"import: {' '.join(argv)}")
    proc = subprocess.run(argv, capture_output=True, text=True, timeout=timeout_s)
    zt = find_zt(tmp)
    if proc.returncode != 0 or zt is None:
        shutil.rmtree(tmp, ignore_errors=True)
        tail = (proc.stderr or proc.stdout or "").strip().splitlines()[-12:]
        raise RuntimeError(
            f"pie model import failed for {artifact.id} (exit {proc.returncode}):\n"
            + "\n".join(tail)
        )
    if find_zt(d):
        shutil.rmtree(tmp, ignore_errors=True)
        return find_zt(d)
    d.parent.mkdir(parents=True, exist_ok=True)
    os.replace(tmp, d)
    _tokenizer_beside(snapshot, d)
    return find_zt(d)


def _tokenizer_beside(snapshot: Path, d: Path) -> None:
    if not snapshot.is_dir():
        return
    for f in snapshot.iterdir():
        if (
            f.is_file()
            and f.suffix not in (".safetensors", ".bin", ".pt", ".gguf", ".zt", ".pdf")
            and not (d / f.name).exists()
            and f.stat().st_size < 64 << 20
        ):
            shutil.copy2(f, d / f.name)
