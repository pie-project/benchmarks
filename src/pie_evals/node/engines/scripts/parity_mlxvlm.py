#!/usr/bin/env python3
"""parity_mlx.py on mlx-vlm, for a model mlx-lm has no code for (Qwen3.8-Flash-Next): greedy answers to
each prompt, and the teacher-forced top-k log-probabilities at every position of each prompt.

    parity_mlxvlm.py SNAPSHOT IN.json OUT.json     # IN: {prompts, max_tokens, topk, greedy}
"""
from __future__ import annotations

import json
import sys

import mlx.core as mx
from mlx_vlm import generate, load


def main() -> None:
    snapshot, inp, out = sys.argv[1:4]
    cfg = json.loads(open(inp).read())
    model, processor = load(snapshot)
    tok = getattr(processor, "tokenizer", processor)
    k = int(cfg["topk"])
    texts, scored = [], []
    for p in cfg["prompts"]:
        ids = tok.encode(p, add_special_tokens=False)
        texts.append(generate(model, processor, p, max_tokens=int(cfg["max_tokens"]), temperature=0.0).text if cfg.get("greedy", True) else "")
        res = model.language_model(mx.array(ids)[None])
        logits = (res.logits if hasattr(res, "logits") else res)[0].astype(mx.float32)
        lp = logits - mx.logsumexp(logits, axis=-1, keepdims=True)
        top = mx.argpartition(-lp, kth=k - 1, axis=-1)[:, :k]
        vals = mx.take_along_axis(lp, top, axis=-1)
        mx.eval(top, vals)
        top, vals = top.tolist(), vals.tolist()
        # logits row i predicts token i+1
        scored.append([{}] + [dict(zip(map(str, top[i]), vals[i])) for i in range(len(ids) - 1)])
        print(f"{len(texts)}/{len(cfg['prompts'])}", flush=True)
    open(out, "w").write(json.dumps({"texts": texts, "scored": scored}))


if __name__ == "__main__":
    main()
