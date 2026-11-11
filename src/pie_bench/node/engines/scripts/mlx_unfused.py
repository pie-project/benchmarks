from __future__ import annotations

import mlx.core as mx

_fused_sdpa = mx.fast.scaled_dot_product_attention
_fused_rms = mx.fast.rms_norm


def sdpa(q, k, v, *, scale, mask=None, sinks=None, **_):
    hq, hk = q.shape[1], k.shape[1]
    if hq != hk:
        k = mx.repeat(k, hq // hk, axis=1)
        v = mx.repeat(v, hq // hk, axis=1)
    scores = (q.astype(mx.float32) * scale) @ k.astype(mx.float32).swapaxes(-1, -2)
    L, S = scores.shape[-2], scores.shape[-1]
    if isinstance(mask, str):
        assert mask == "causal", mask
        rows = mx.arange(S - L, S)[:, None]
        cols = mx.arange(S)[None, :]
        scores = mx.where(cols <= rows, scores, -mx.inf)
    elif mask is not None:
        scores = mx.where(mask, scores, -mx.inf) if mask.dtype == mx.bool_ else scores + mask.astype(mx.float32)
    if sinks is not None:
        sink = mx.broadcast_to(sinks.astype(mx.float32).reshape(1, -1, 1, 1), (*scores.shape[:-1], 1))
        scores = mx.concatenate([sink, scores], axis=-1)
        p = mx.softmax(scores, axis=-1, precise=True)[..., 1:]
    else:
        p = mx.softmax(scores, axis=-1, precise=True)
    return (p @ v.astype(mx.float32)).astype(q.dtype)


def rms_norm(x, weight, eps):
    y = x.astype(mx.float32) * mx.rsqrt(mx.mean(mx.square(x.astype(mx.float32)), axis=-1, keepdims=True) + eps)
    return (y * weight.astype(mx.float32)).astype(x.dtype) if weight is not None else y.astype(x.dtype)


def install() -> None:
    mx.fast.scaled_dot_product_attention = sdpa
    mx.fast.rms_norm = rms_norm
