"""Time-series store for currency strength values.

The class here is intentionally lightweight; it keeps a rolling window of
values per currency and exposes helpers for retrieving the latest value
or calculating simple oscillators.  Thread safety is not implemented but
hooks are provided for integration in a concurrent environment.
"""

from __future__ import annotations

from collections import deque
from typing import Deque, Dict, Iterable


class StrengthFeed:
    """Maintain rolling strength windows for currencies."""

    def __init__(self, window: int = 100):
        self.window = window
        self._data: Dict[str, Deque[float]] = {}

    def update(self, strengths: Dict[str, float]) -> None:
        for ccy, val in strengths.items():
            dq = self._data.setdefault(ccy, deque(maxlen=self.window))
            dq.append(val)

    def history(self, ccy: str) -> Iterable[float]:
        return list(self._data.get(ccy, []))

    # Oscillator getters -------------------------------------------------
    def zscore(self, ccy: str) -> float:
        """Return z-score of the latest value for *ccy*."""

        from .currency_strength import zscore

        return zscore(self.history(ccy))

