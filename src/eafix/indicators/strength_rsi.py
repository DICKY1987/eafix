"""RSI indicator operating on currency strength series."""

from __future__ import annotations

from collections import deque
from typing import Deque, Optional


class StrengthRSIIndicator:
    """Compute RSI over a rolling window of strength values."""

    def __init__(self, period: int = 14):
        self.period = period
        self.values: Deque[float] = deque(maxlen=period + 1)
        self.rsi: Optional[float] = None

    def update(self, value: float) -> float:
        self.values.append(value)
        if len(self.values) <= 1:
            self.rsi = 0.0
        elif len(self.values) >= self.period + 1:
            gains = [max(0.0, self.values[i+1]-self.values[i]) for i in range(self.period)]
            losses = [max(0.0, self.values[i]-self.values[i+1]) for i in range(self.period)]
            avg_gain = sum(gains)/self.period
            avg_loss = sum(losses)/self.period
            if avg_loss == 0:
                self.rsi = 100.0
            else:
                rs = avg_gain/avg_loss
                self.rsi = 100 - (100/(1+rs))
        return self.rsi or 0.0

