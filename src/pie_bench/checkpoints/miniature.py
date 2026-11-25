from __future__ import annotations

import json
import platform
import subprocess
import uuid
from pathlib import Path

from pie_bench.installers.bench_env import bench_dir
from pie_bench.schema import ArtifactKind, ArtifactSpec

SHRINK_SCRIPT = "shrink_checkpoint.py"


def repo_cache_dirname(repo_id: str) -> str:
    return "models--" + repo_id.replace("/", "--")


def miniature_snapshot_dir(artifact: ArtifactSpec, hf_cache: Path) -> Path:
    if artifact.miniature is None:
        raise ValueError(f"artifact {artifact.id} has no miniature recipe")
    return (
        Path(hf_cache)
        / repo_cache_dirname(artifact.base_model)
        / "snapshots"
        / artifact.miniature.tag
    )


def miniature_argv(
    artifact: ArtifactSpec, out_dir: Path, python: str, cache_dir: Path | None = None
) -> list[str]:
    r = artifact.miniature
    if r is None:
        raise ValueError(f"artifact {artifact.id} has no miniature recipe")
    argv = [
        python,
        str(bench_dir() / SHRINK_SCRIPT),
        "--repo",
        artifact.base_model,
        "--revision",
        artifact.revision or "main",
        "--out",
        str(out_dir),
        "--layers",
        r.layers,
        "--repeat",
        str(r.repeat),
        "--experts",
        str(r.experts if r.experts is not None else 0),
    ]
    if r.text_only:
        argv.append("--text-only")
    if r.engram_vocab is not None:
        argv += ["--engram-vocab", str(r.engram_vocab)]
    if r.attn_res_block_size is not None:
        argv += ["--attn-res-block-size", str(r.attn_res_block_size)]
    if r.shrink_family:
        argv += ["--family", r.shrink_family]
    if r.keep_fp8:
        argv.append("--keep-fp8")
    if cache_dir is not None:
        argv += ["--cache", str(cache_dir)]
    return argv


def _stamp(artifact: ArtifactSpec) -> dict:
    r = artifact.miniature.model_dump()
    for flag in ("widen_bf16", "mlx_quantize"):
        if not r.get(flag):
            r.pop(flag, None)
    return r


def ensure_miniature(
    artifact: ArtifactSpec, hf_cache: Path, python: str, timeout_s: int = 3600
) -> Path:
    if artifact.kind != ArtifactKind.MINIATURE:
        raise ValueError(f"artifact {artifact.id} is not a miniature")
    out = miniature_snapshot_dir(artifact, hf_cache)
    marker = Path(artifact.gguf_file).name if artifact.gguf_file else "config.json"
    if (out / marker).exists():
        stamp = out / ".miniature.json"
        if not stamp.exists():
            return out
        try:
            prev = json.loads(stamp.read_text())["recipe"]
        except (OSError, ValueError, KeyError):
            return out
        if prev == _stamp(artifact):
            return out
        import shutil

        shutil.rmtree(out, ignore_errors=True)
    import os
    import shutil
    import tempfile

    base = Path(
        os.environ.get("PIE_BENCH_SHRINK_CACHE")
        or (
            Path(os.environ["PIE_BENCH_CACHE"]) / "shrink"
            if os.environ.get("PIE_BENCH_CACHE")
            else tempfile.gettempdir()
        )
    )
    cache_dir = base / f"{platform.node()}-{os.getpid()}" / repo_cache_dirname(artifact.base_model)
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.parent / f".tmp-{out.name}-{platform.node()}-{os.getpid()}-{uuid.uuid4().hex[:6]}"
    shutil.rmtree(tmp, ignore_errors=True)
    if artifact.gguf_file:
        import sys

        r = artifact.miniature
        argv = [
            sys.executable,
            "-m",
            "pie_bench.checkpoints.gguf_slice",
            "--repo",
            artifact.base_model,
            "--revision",
            artifact.revision or "main",
            "--file",
            artifact.gguf_file,
            "--layers",
            r.layers,
            "--experts",
            str(r.experts or 0),
            "--out",
            str(tmp),
        ]
    else:
        argv = miniature_argv(artifact, tmp, python, cache_dir=cache_dir)
    proc = subprocess.run(argv, capture_output=True, text=True, timeout=timeout_s, check=False)
    if proc.returncode != 0 or not (tmp / marker).exists():
        shutil.rmtree(tmp, ignore_errors=True)
        tail = (proc.stderr or proc.stdout or "").strip().splitlines()[-20:]
        raise RuntimeError(
            f"shrink_checkpoint failed for {artifact.id} (exit {proc.returncode}):\n"
            + "\n".join(tail)
        )
    if artifact.miniature.widen_bf16:
        from pie_bench.checkpoints.widen_bf16 import widen_bf16

        widen_bf16(tmp)
    if artifact.miniature.mlx_quantize:
        from .mlx_quantize import mlx_quantize

        shutil.rmtree(cache_dir, ignore_errors=True)
        mlx_quantize(
            tmp, artifact.miniature.mlx_quantize, family=artifact.family, timeout_s=timeout_s
        )
    (tmp / ".miniature.json").write_text(
        json.dumps({"artifact": artifact.id, "recipe": _stamp(artifact), "argv": argv}, indent=2)
    )
    if (out / marker).exists():
        shutil.rmtree(tmp, ignore_errors=True)
        shutil.rmtree(cache_dir, ignore_errors=True)
        return out
    os.replace(tmp, out)
    shutil.rmtree(cache_dir, ignore_errors=True)
    return out


def num_layers_of(snapshot_dir: str | Path) -> int | None:
    cfg_path = Path(snapshot_dir) / "config.json"
    if not cfg_path.exists():
        return None
    try:
        cfg = json.loads(cfg_path.read_text())
    except (OSError, ValueError):
        return None
    n = cfg.get("num_hidden_layers")
    if n is None and isinstance(cfg.get("text_config"), dict):
        n = cfg["text_config"].get("num_hidden_layers")
    return int(n) if n is not None else None
