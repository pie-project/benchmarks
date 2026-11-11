from __future__ import annotations

import math

import numpy as np

from pie_bench.schema import AccuracyStatus

BF16_ULP = 0.125

COSINE_GATE = 0.9999


def first_divergence(a: list[int], b: list[int]) -> int | None:
    n = min(len(a), len(b))
    for i in range(n):
        if a[i] != b[i]:
            return i
    if len(a) != len(b):
        return n
    return None


def adjudicate_divergence(
    logits_at_pos: np.ndarray, tok_a: int, tok_b: int, ulp: float = BF16_ULP
) -> tuple[float, bool]:
    v = np.asarray(logits_at_pos, dtype=np.float64).reshape(-1)
    if not (0 <= tok_a < v.shape[0] and 0 <= tok_b < v.shape[0]):
        raise IndexError(f"token id out of vocab range {v.shape[0]}: {tok_a}, {tok_b}")
    gap = float(abs(v[tok_a] - v[tok_b]))
    if tok_a == tok_b:
        return gap, True
    if v.shape[0] < 2:
        return gap, False
    top2 = {int(i) for i in np.argpartition(-v, 1)[:2]}
    benign = gap <= ulp and tok_a in top2 and tok_b in top2
    return gap, bool(benign)


def t0_verdict(
    divergences: list[int | None], gaps: list[float], benign_flags: list[bool]
) -> AccuracyStatus:
    n_div = sum(1 for d in divergences if d is not None)
    if n_div == 0:
        return AccuracyStatus.PASS
    if len(benign_flags) < n_div:
        return AccuracyStatus.FAIL
    if len(gaps) != len(benign_flags):
        raise ValueError("gaps and benign_flags must be aligned")
    return AccuracyStatus.PASS if all(bool(b) for b in benign_flags[:n_div]) else AccuracyStatus.FAIL


def _log_softmax(logits: np.ndarray) -> np.ndarray:
    x = np.asarray(logits, dtype=np.float64)
    if x.ndim == 1:
        x = x[None, :]
    m = x.max(axis=-1, keepdims=True)
    z = x - m
    return z - np.log(np.exp(z).sum(axis=-1, keepdims=True))


def kl_divergence(p_logits: np.ndarray, q_logits: np.ndarray) -> float:
    lp = _log_softmax(p_logits)
    lq = _log_softmax(q_logits)
    if lp.shape != lq.shape:
        raise ValueError(f"shape mismatch {lp.shape} vs {lq.shape}")
    p = np.exp(lp)
    kl = (p * (lp - lq)).sum(axis=-1)
    return float(kl.mean())


def topk_agreement(p_logits: np.ndarray, q_logits: np.ndarray, k: int = 1) -> float:
    p = np.asarray(p_logits, dtype=np.float64)
    q = np.asarray(q_logits, dtype=np.float64)
    if p.ndim == 1:
        p, q = p[None, :], q[None, :]
    if p.shape != q.shape:
        raise ValueError(f"shape mismatch {p.shape} vs {q.shape}")
    if k < 1 or k > p.shape[-1]:
        raise ValueError(f"k={k} out of range for vocab {p.shape[-1]}")
    if k == 1:
        return float(np.mean(p.argmax(-1) == q.argmax(-1)))
    tp = np.argpartition(-p, k - 1, axis=-1)[:, :k]
    tq = np.argpartition(-q, k - 1, axis=-1)[:, :k]
    agree = [set(a.tolist()) == set(b.tolist()) for a, b in zip(tp, tq)]
    return float(np.mean(agree))


def perplexity_from_logits(logits: np.ndarray, target_ids: list[int]) -> float:
    lp = _log_softmax(logits)
    t = np.asarray(target_ids, dtype=np.int64)
    if t.shape[0] != lp.shape[0]:
        raise ValueError(f"{lp.shape[0]} logit rows vs {t.shape[0]} targets")
    nll = -lp[np.arange(lp.shape[0]), t]
    return float(np.exp(nll.mean()))


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    x = np.asarray(a, dtype=np.float64).reshape(-1)
    y = np.asarray(b, dtype=np.float64).reshape(-1)
    if x.shape != y.shape:
        raise ValueError(f"shape mismatch {x.shape} vs {y.shape}")
    nx, ny = np.linalg.norm(x), np.linalg.norm(y)
    if nx == 0.0 or ny == 0.0:
        return 1.0 if nx == ny else 0.0
    return float(np.dot(x, y) / (nx * ny))


def psnr(a: np.ndarray, b: np.ndarray, peak: float | None = None) -> float:
    x = np.asarray(a, dtype=np.float64).reshape(-1)
    y = np.asarray(b, dtype=np.float64).reshape(-1)
    if x.shape != y.shape:
        raise ValueError(f"shape mismatch {x.shape} vs {y.shape}")
    mse = float(np.mean((x - y) ** 2))
    if mse == 0.0:
        return math.inf
    if peak is None:
        peak = float(x.max() - x.min()) or 1.0
    return float(20.0 * math.log10(peak) - 10.0 * math.log10(mse))


def bootstrap_ci(
    scores: list[float], iters: int = 2000, seed: int = 0, alpha: float = 0.05
) -> tuple[float, float]:
    s = np.asarray(scores, dtype=np.float64)
    if s.size == 0:
        raise ValueError("no scores")
    if s.size == 1:
        return float(s[0]), float(s[0])
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, s.size, size=(iters, s.size))
    means = s[idx].mean(axis=1)
    lo, hi = np.percentile(means, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return float(lo), float(hi)


def scores_differ(
    a: list[float], b: list[float], iters: int = 2000, seed: int = 0, alpha: float = 0.05
) -> bool:
    x = np.asarray(a, dtype=np.float64)
    y = np.asarray(b, dtype=np.float64)
    if x.size == 0 or y.size == 0:
        raise ValueError("no scores")
    rng = np.random.default_rng(seed)
    if x.size == y.size:
        d = x - y
        if np.all(d == 0.0):
            return False
        idx = rng.integers(0, d.size, size=(iters, d.size))
        diffs = d[idx].mean(axis=1)
    else:
        ix = rng.integers(0, x.size, size=(iters, x.size))
        iy = rng.integers(0, y.size, size=(iters, y.size))
        diffs = x[ix].mean(axis=1) - y[iy].mean(axis=1)
    lo, hi = np.percentile(diffs, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return bool(lo > 0.0 or hi < 0.0)
