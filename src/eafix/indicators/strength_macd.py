"""MACD indicator for strength differential series."""

from __future__ import annotations

class StrengthMACDIndicator:
    """Compute MACD using exponential moving averages."""

    def __init__(self, fast: int = 12, slow: int = 26, signal: int = 9):
        self.fast = fast
        self.slow = slow
        self.signal = signal
        self.ema_fast = None
        self.ema_slow = None
        self.ema_signal = None
        self.value = 0.0

    def _ema(self, prev: float, value: float, period: int) -> float:
        k = 2 / (period + 1)
        return value * k + prev * (1 - k) if prev is not None else value

    def update(self, value: float) -> tuple:
        self.ema_fast = self._ema(self.ema_fast, value, self.fast)
        self.ema_slow = self._ema(self.ema_slow, value, self.slow)
        macd = (self.ema_fast - self.ema_slow) if (self.ema_fast and self.ema_slow) else 0.0
        self.ema_signal = self._ema(self.ema_signal, macd, self.signal)
        self.value = macd - (self.ema_signal or 0.0)
        return macd, self.ema_signal or 0.0, self.value

