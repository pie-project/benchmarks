"""A bf16 cut quantized where it is built: ``mlx_lm.convert`` in mlx-lm's own interpreter (``MLX_PY``), so a 16 GB
Mac builds the 4-bit slice of a model whose bf16 cut does not fit it, and pie and mlx-lm read the very same files.
Nemotron-3-Ultra at 16 of 512 experts: an 11.4 GiB bf16 cut, 3.3 GiB at 4 bits in 64-wide groups."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

#: the schemes a cut quantizes to, as mlx_lm.convert's flags
SCHEMES = {"affine_u4_g64": ["-q", "--q-mode", "affine", "--q-bits", "4", "--q-group-size", "64"]}


def convert_argv(python: str, src: Path, dst: Path, scheme: str) -> list[str]:
    """The exact ``mlx_lm.convert`` invocation (pure): the scheme's flags, the unquantized planes kept bf16."""
    if scheme not in SCHEMES:
        raise ValueError(f"no mlx_lm.convert flags for {scheme!r}; known: {sorted(SCHEMES)}")
    return [python, "-m", "mlx_lm", "convert", "--hf-path", str(src), "--mlx-path", str(dst), *SCHEMES[scheme], "--dtype", "bfloat16"]


def mlx_quantize(cut: Path, scheme: str, timeout_s: int = 3600) -> None:
    """Replace the bf16 cut in ``cut`` by its ``scheme`` quantization, in place."""
    python = os.environ.get("MLX_PY") or sys.executable
    dst = cut.with_name(cut.name + "-mlx")
    shutil.rmtree(dst, ignore_errors=True)  # mlx_lm.convert refuses an existing directory
    proc = subprocess.run(convert_argv(python, cut, dst, scheme), capture_output=True, text=True, timeout=timeout_s, check=False)
    if proc.returncode != 0 or not (dst / "config.json").exists():
        shutil.rmtree(dst, ignore_errors=True)
        tail = (proc.stderr or proc.stdout or "").strip().splitlines()[-20:]
        raise RuntimeError(f"mlx_lm.convert to {scheme} failed (exit {proc.returncode}):\n" + "\n".join(tail))
    shutil.rmtree(cut)
    os.replace(dst, cut)
