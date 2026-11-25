from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SCHEMES = {"affine_u4_g64": ["-q", "--q-mode", "affine", "--q-bits", "4", "--q-group-size", "64"]}


def convert_argv(python: str, src: Path, dst: Path, scheme: str) -> list[str]:
    if scheme not in SCHEMES:
        raise ValueError(f"no mlx_lm.convert flags for {scheme!r}; known: {sorted(SCHEMES)}")
    return [
        python,
        "-m",
        "mlx_lm",
        "convert",
        "--hf-path",
        str(src),
        "--mlx-path",
        str(dst),
        *SCHEMES[scheme],
        "--dtype",
        "bfloat16",
    ]


IN_PLACE = {
    "muse_spark": {
        "drop": [r"^model\.(audio_tower|vision_tower|vision_adapter|vision_projection)\."],
        "config_drop": ["vision_config", "audio_config"],
        "split": {
            r"^(.*)mlp\.experts\.gate_up_proj$": {
                "axis": 1,
                "legs": [r"\1mlp.experts.gate_proj.weight", r"\1mlp.experts.up_proj.weight"],
            }
        },
        "rename": {r"^(.*mlp\.experts\.down_proj)$": r"\1.weight"},
        "quantize": [
            r"^model\.language_model\.embed_tokens\.weight$",
            r"^model\.language_model\.layers\.\d+\.self_attn\.(q|k|v|gate|o)_proj\.weight$",
            r"^model\.language_model\.layers\.\d+\.mlp\.(pre|post)_expert_proj\.weight$",
            r"^model\.language_model\.layers\.\d+\.mlp\.experts\.(gate|up|down)_proj\.weight$",
        ],
    },
}
GROUPS = {"affine_u4_g64": (4, 64)}


def in_place_argv(python: str, src: Path, dst: Path, rules: Path) -> list[str]:
    script = Path(__file__).resolve().parent / "mlx_quantize_in_place.py"
    return [python, str(script), str(src), str(dst), str(rules)]


def mlx_quantize(cut: Path, scheme: str, family: str | None = None, timeout_s: int = 3600) -> None:
    python = os.environ.get("MLX_PY") or sys.executable
    dst = cut.with_name(cut.name + "-mlx")
    shutil.rmtree(dst, ignore_errors=True)
    with tempfile.TemporaryDirectory() as tmp:
        if family in IN_PLACE:
            if scheme not in GROUPS:
                raise ValueError(f"no bits and group width for {scheme!r}; known: {sorted(GROUPS)}")
            bits, group = GROUPS[scheme]
            rules = Path(tmp) / "rules.json"
            rules.write_text(json.dumps({"bits": bits, "group_size": group, **IN_PLACE[family]}))
            argv = in_place_argv(python, cut, dst, rules)
        else:
            argv = convert_argv(python, cut, dst, scheme)
        proc = subprocess.run(argv, capture_output=True, text=True, timeout=timeout_s, check=False)
    if proc.returncode != 0 or not (dst / "config.json").exists():
        shutil.rmtree(dst, ignore_errors=True)
        tail = (proc.stderr or proc.stdout or "").strip().splitlines()[-20:]
        raise RuntimeError(
            f"mlx quantization to {scheme} failed (exit {proc.returncode}):\n" + "\n".join(tail)
        )
    shutil.rmtree(cut)
    os.replace(dst, cut)
