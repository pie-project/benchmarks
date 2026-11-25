import json
import sys
from pathlib import Path

from mlx_vlm import generate, load


def main() -> None:
    snapshot, items_path, out_path = sys.argv[1:4]
    model, processor = load(snapshot)
    items = json.loads(Path(items_path).read_text())
    out = []
    for i, item in enumerate(items):
        r = generate(
            model,
            processor,
            item["prompt"],
            max_tokens=item["max_tokens"],
            temperature=0.0,
            verbose=False,
        )
        out.append(r.text)
        print(f"{i + 1}/{len(items)}", flush=True)
    Path(out_path).write_text(json.dumps(out))


if __name__ == "__main__":
    main()
