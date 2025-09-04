"""Minimal indicator engine used in tests and documentation.

The real project utilises a much more feature rich engine.  This module
implements only the pieces required for unit testing the new strength
indicators.  Indicators are simple objects exposing an ``update`` method.
"""

from __future__ import annotations

from typing import Callable, Dict, List
import time

from .indicators import (
    StrengthRSIIndicator,
    StrengthStochasticIndicator,
    StrengthZScoreIndicator,
    StrengthMACDIndicator,
)

MAX_INDICATORS_PER_SYMBOL = 50


class IndicatorEngine:
    def __init__(self, ui_refresh_ms: int = 500):
        self.ui_refresh_ms = ui_refresh_ms
        self._registry: Dict[str, List[object]] = {}
        self._last_perf_check = time.time()
        # Track how many updates have occurred between performance checks and
        # store a small history of update rates (updates/second).  These values
        # are primarily useful for unit tests and lightweight diagnostics.
        self._updates_since_check = 0
        self.perf_history: List[float] = []

    def add_indicator(self, symbol: str, indicator: object) -> None:
        lst = self._registry.setdefault(symbol, [])
        if len(lst) >= MAX_INDICATORS_PER_SYMBOL:
            raise ValueError("indicator cap exceeded")
        lst.append(indicator)

    def update(self, symbol: str, value: float) -> Dict[str, float]:
        outputs: Dict[str, float] = {}
        for ind in self._registry.get(symbol, []):
            try:
                out = ind.update(value)
            except Exception:
                out = None
            outputs[ind.__class__.__name__] = out if out is not None else float("nan")
        self._updates_since_check += 1
        self._maybe_perf_check()
        return outputs

    # ------------------------------------------------------------------
    def _maybe_perf_check(self) -> None:
        now = time.time()
        elapsed = now - self._last_perf_check
        if elapsed * 1000 >= self.ui_refresh_ms:
            # Compute updates per second since the last check.  This is a very
            # lightweight metric but provides a useful signal for tests or
            # diagnostic tools.
            if elapsed > 0:
                rate = self._updates_since_check / elapsed
                self.perf_history.append(rate)

            self._updates_since_check = 0
            self._last_perf_check = now


# Factory convenience ----------------------------------------------------------

def default_strength_indicators() -> List[object]:
    return [
        StrengthRSIIndicator(),
        StrengthStochasticIndicator(),
        StrengthZScoreIndicator(),
        StrengthMACDIndicator(),
    ]

