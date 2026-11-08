#!/usr/bin/env python3
"""mlx-lm side of the parity run: greedy answers to each prompt, and the teacher-forced
top-k log-probabilities at every position of each prompt (the shape vLLM's
``prompt_logprobs`` gives: position 0 is empty, position i scores token i).

    parity_mlx.py SNAPSHOT IN.json OUT.json     # IN: {prompts, max_tokens, topk, unfused}

``unfused``: the same model with mlx's fused attention and RMSNorm kernels swapped for plain ops (``mlx_unfused.py``),
the reference's spread pass, as vLLM's runs in eager mode.
"""
from __future__ import annotations

import json
import os
import sys

import mlx.core as mx
from mlx_lm import load
from mlx_lm.generate import generate
from mlx_lm.sample_utils import make_sampler


def main() -> None:
    snapshot, inp, out = sys.argv[1:4]
    cfg = json.loads(open(inp).read())
    if cfg.get("unfused"):
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import mlx_unfused

        mlx_unfused.install()
    model, tok = load(snapshot)
    k = int(cfg["topk"])
    texts, scored = [], []
    sampler = make_sampler(temp=0.0)
    for p in cfg["prompts"]:
        ids = tok.encode(p, add_special_tokens=False)
        texts.append(generate(model, tok, prompt=ids, max_tokens=int(cfg["max_tokens"]), sampler=sampler) if cfg.get("greedy", True) else "")
        logits = model(mx.array(ids)[None])[0].astype(mx.float32)
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
