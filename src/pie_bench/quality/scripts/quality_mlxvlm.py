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
