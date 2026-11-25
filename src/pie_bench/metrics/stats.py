from __future__ import annotations

from dataclasses import dataclass

import numpy as np


def median(xs: list[float]) -> float:
    return float(np.median(np.asarray(xs, dtype=float)))


def cov(xs: list[float]) -> float:
    if len(xs) < 2:
        return 0.0
    a = np.asarray(xs, dtype=float)
    m = a.mean()
    return float(a.std(ddof=1) / m) if m else 0.0


@dataclass
class AdaptiveDecision:
    more_rounds: int
    reason: str


def decide_repetition(
    first: float,
    history: list[float],
    *,
    sigma: float,
    confirm_rounds: int,
    min_history: int = 3,
    floor_rel: float = 0.01,
) -> AdaptiveDecision:
    if len(history) < min_history:
        return AdaptiveDecision(confirm_rounds, f"history has {len(history)} < {min_history} points")
    h = np.asarray(history, dtype=float)
    center = float(np.median(h))
    spread = max(float(np.std(h, ddof=1)), floor_rel * center)
    z = abs(first - center) / spread if spread else 0.0
    if z <= sigma:
        return AdaptiveDecision(0, f"within band (z={z:.2f} ≤ {sigma})")
    return AdaptiveDecision(confirm_rounds, f"outside band (z={z:.2f} > {sigma}); confirming")

