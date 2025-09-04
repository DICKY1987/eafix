"""Z-score indicator for currency strength series."""

from __future__ import annotations

from collections import deque
from typing import Deque


class StrengthZScoreIndicator:
    def __init__(self, period: int = 20):
        self.period = period
        self.values: Deque[float] = deque(maxlen=period)

    def update(self, value: float) -> float:
        self.values.append(value)
        vals = list(self.values)
        if not vals:
            return 0.0
        mean = sum(vals) / len(vals)
        var = sum((v - mean) ** 2 for v in vals) / len(vals)
        std = var ** 0.5
        if std == 0:
            return 0.0
        return (vals[-1] - mean) / std

