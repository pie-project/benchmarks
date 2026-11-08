"""A bf16 cut quantized where it is built: ``mlx_lm.convert`` in mlx-lm's own interpreter (``MLX_PY``), so a 16 GB
Mac builds the 4-bit slice of a model whose bf16 cut does not fit it, and pie and mlx-lm read the very same files.
Nemotron-3-Ultra at 16 of 512 experts: an 11.4 GiB bf16 cut, 3.3 GiB at 4 bits in 64-wide groups."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

#: the schemes a cut quantizes to, as mlx_lm.convert's flags
SCHEMES = {"affine_u4_g64": ["-q", "--q-mode", "affine", "--q-bits", "4", "--q-group-size", "64"]}


def convert_argv(python: str, src: Path, dst: Path, scheme: str) -> list[str]:
    """The exact ``mlx_lm.convert`` invocation (pure): the scheme's flags, the unquantized planes kept bf16."""
    if scheme not in SCHEMES:
        raise ValueError(f"no mlx_lm.convert flags for {scheme!r}; known: {sorted(SCHEMES)}")
    return [python, "-m", "mlx_lm", "convert", "--hf-path", str(src), "--mlx-path", str(dst), *SCHEMES[scheme], "--dtype", "bfloat16"]


#: families whose cut mlx quantizes in place under the release's names (``scripts/mlx_quantize_in_place.py``) rather
#: than through ``mlx_lm.convert``. Muse Spark: mlx-lm's recipe quantizes only the middle layers' experts (a two-layer
#: cut stays bf16), and its conversion stores what pie reads rewritten (gate coefficients for the residual gates, norm
#: gains, q/k/v/gate fused with their rows re-paired); mlx-lm loads the release's names as it loads a release. The
#: towers a text cut leaves out are dropped, with their configs, so mlx-lm builds none. The head stays bf16: mlx-lm casts
#: its input to the head weight's dtype (`out.astype(self.lm_head.weight.dtype)`), a quantized head's uint32 codes.
IN_PLACE = {
    "muse_spark": {
        "drop": [r"^model\.(audio_tower|vision_tower|vision_adapter|vision_projection)\."],
        "config_drop": ["vision_config", "audio_config"],
        "split": {r"^(.*)mlp\.experts\.gate_up_proj$": {"axis": 1, "legs": [r"\1mlp.experts.gate_proj.weight", r"\1mlp.experts.up_proj.weight"]}},
        "rename": {r"^(.*mlp\.experts\.down_proj)$": r"\1.weight"},
        "quantize": [
            r"^model\.language_model\.embed_tokens\.weight$",
            r"^model\.language_model\.layers\.\d+\.self_attn\.(q|k|v|gate|o)_proj\.weight$",
            r"^model\.language_model\.layers\.\d+\.mlp\.(pre|post)_expert_proj\.weight$",
            r"^model\.language_model\.layers\.\d+\.mlp\.experts\.(gate|up|down)_proj\.weight$",
        ],
    },
}
#: a scheme's bits and group width, for the in-place quantizer
GROUPS = {"affine_u4_g64": (4, 64)}


def in_place_argv(python: str, src: Path, dst: Path, rules: Path) -> list[str]:
    script = Path(__file__).resolve().parent / "engines" / "scripts" / "mlx_quantize_in_place.py"
    return [python, str(script), str(src), str(dst), str(rules)]


def mlx_quantize(cut: Path, scheme: str, family: str | None = None, timeout_s: int = 3600) -> None:
    """Replace the bf16 cut in ``cut`` by its ``scheme`` quantization, in place."""
    python = os.environ.get("MLX_PY") or sys.executable
    dst = cut.with_name(cut.name + "-mlx")
    shutil.rmtree(dst, ignore_errors=True)  # mlx_lm.convert refuses an existing directory
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
        raise RuntimeError(f"mlx quantization to {scheme} failed (exit {proc.returncode}):\n" + "\n".join(tail))
    shutil.rmtree(cut)
    os.replace(dst, cut)
