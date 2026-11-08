#!/usr/bin/env python3
"""mlx-lm side of the parity run: greedy answers to each prompt, and the teacher-forced
top-k log-probabilities at every position of each prompt (the shape vLLM's
``prompt_logprobs`` gives: position 0 is empty, position i scores token i).

    parity_mlx.py SNAPSHOT IN.json OUT.json     # IN: {prompts, max_tokens, topk, split}

``split``: each prompt read in two pieces through a prompt cache, the same model with only its kernels' shapes changed
(the reference's spread against its one-piece read).
"""
from __future__ import annotations

import json
import sys

import mlx.core as mx
from mlx_lm import load
from mlx_lm.generate import generate
from mlx_lm.models.cache import make_prompt_cache
from mlx_lm.sample_utils import make_sampler


def main() -> None:
    snapshot, inp, out = sys.argv[1:4]
    cfg = json.loads(open(inp).read())
    model, tok = load(snapshot)
    k = int(cfg["topk"])
    texts, scored = [], []
    sampler = make_sampler(temp=0.0)
    for p in cfg["prompts"]:
        ids = tok.encode(p, add_special_tokens=False)
        texts.append(generate(model, tok, prompt=ids, max_tokens=int(cfg["max_tokens"]), sampler=sampler) if cfg.get("greedy", True) else "")
        start = 0
        if cfg.get("split") and len(ids) > 2:
            # rows h.. of the one-piece read, from the second piece over the first's cache; the rows before stay unscored
            start = len(ids) // 2
            cache = make_prompt_cache(model)
            mx.eval(model(mx.array(ids[:start])[None], cache=cache))
            logits = model(mx.array(ids[start:])[None], cache=cache)[0].astype(mx.float32)
        else:
            logits = model(mx.array(ids)[None])[0].astype(mx.float32)
        lp = logits - mx.logsumexp(logits, axis=-1, keepdims=True)
        top = mx.argpartition(-lp, kth=k - 1, axis=-1)[:, :k]
        vals = mx.take_along_axis(lp, top, axis=-1)
        mx.eval(top, vals)
        top, vals = top.tolist(), vals.tolist()
        # logits row i (of the whole prompt; ``start`` rows in, of a split read) predicts token i+1
        scored.append([{}] + [{}] * start + [dict(zip(map(str, top[j]), vals[j])) for j in range(len(ids) - 1 - start)])
        print(f"{len(texts)}/{len(cfg['prompts'])}", flush=True)
    open(out, "w").write(json.dumps({"texts": texts, "scored": scored}))


if __name__ == "__main__":
    main()
