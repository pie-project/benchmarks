"""Greedy answers from mlx-vlm, for a model mlx-lm has no code for (Qwen3.8-Flash-Next).

    python quality_mlxvlm.py <snapshot> <items.json> <out.json>

items.json is a list of {"prompt": rendered chat text, "max_tokens": n}; out.json gets the answers in order.
Runs under mlx-vlm's interpreter (MLX_VLM_PY), one prompt at a time.
"""

import json
import sys

from mlx_vlm import generate, load

snapshot, items_path, out_path = sys.argv[1:4]
model, processor = load(snapshot)
items = json.loads(open(items_path).read())
out = []
for i, item in enumerate(items):
    r = generate(model, processor, item["prompt"], max_tokens=item["max_tokens"], temperature=0.0, verbose=False)
    out.append(r.text)
    print(f"{i + 1}/{len(items)}", flush=True)
open(out_path, "w").write(json.dumps(out))
