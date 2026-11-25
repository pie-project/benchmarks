from __future__ import annotations

import numpy as np

from pie_bench.schema import AccuracyStatus

BF16_ULP = 0.125


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
    return (
        AccuracyStatus.PASS if all(bool(b) for b in benign_flags[:n_div]) else AccuracyStatus.FAIL
    )
