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
        # Track how many indicator updates occur between performance checks
        self._updates_since_perf = 0
        # Most recent performance metrics captured by :meth:`_maybe_perf_check`
        # Consumers can inspect this dictionary for lightweight telemetry.
        self.performance: Dict[str, float] = {}

    def add_indicator(self, symbol: str, indicator: object) -> None:
        lst = self._registry.setdefault(symbol, [])
        if len(lst) >= MAX_INDICATORS_PER_SYMBOL:
            raise ValueError("indicator cap exceeded")
        lst.append(indicator)

    def update(self, symbol: str, value: float) -> Dict[str, float]:
        outputs: Dict[str, float] = {}
        self._updates_since_perf += 1
        for ind in self._registry.get(symbol, []):
            try:
                out = ind.update(value)
            except Exception:
                out = None
            outputs[ind.__class__.__name__] = out if out is not None else float("nan")
        self._maybe_perf_check()
        return outputs

    # ------------------------------------------------------------------
    def _maybe_perf_check(self) -> None:
        now = time.time()
        elapsed_ms = (now - self._last_perf_check) * 1000
        if elapsed_ms >= self.ui_refresh_ms:
            # Record simple throughput metrics.  This deliberately avoids
            # expensive operations to keep the engine lightweight.
            if elapsed_ms:
                rate = self._updates_since_perf / (elapsed_ms / 1000.0)
            else:
                rate = float("nan")
            self.performance = {
                "updates": self._updates_since_perf,
                "elapsed_ms": elapsed_ms,
                "updates_per_sec": rate,
            }
            self._updates_since_perf = 0
            self._last_perf_check = now


# Factory convenience ----------------------------------------------------------

def default_strength_indicators() -> List[object]:
    return [
        StrengthRSIIndicator(),
        StrengthStochasticIndicator(),
        StrengthZScoreIndicator(),
        StrengthMACDIndicator(),
    ]

