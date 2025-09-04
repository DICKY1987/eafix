"""Stochastic oscillator on currency strength series."""

from __future__ import annotations

from collections import deque
from typing import Deque, Tuple


class StrengthStochasticIndicator:
    """Simple stochastic %K/%D on strength differential."""

    def __init__(self, k_period: int = 14, d_period: int = 3):
        self.k_period = k_period
        self.d_period = d_period
        self.values: Deque[float] = deque(maxlen=k_period)
        self.k_history: Deque[float] = deque(maxlen=d_period)

    def update(self, value: float) -> Tuple[float, float]:
        self.values.append(value)
        if len(self.values) < 2:
            k = 0.0
        else:
            highest = max(self.values)
            lowest = min(self.values)
            if highest == lowest:
                k = 0.0
            else:
                k = (self.values[-1] - lowest) / (highest - lowest) * 100
        self.k_history.append(k)
        d = sum(self.k_history) / len(self.k_history)
        return k, d

