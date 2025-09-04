"""Minimal indicator engine used in tests and documentation.

The real project utilises a much more feature rich engine.  This module
implements only the pieces required for unit testing the new strength
indicators.  Indicators are simple objects exposing an ``update`` method.
"""

from __future__ import annotations

from typing import Dict, List
from pathlib import Path
import time

from .indicator_loader import load_indicators_from_dir

MAX_INDICATORS_PER_SYMBOL = 50


class IndicatorEngine:
    def __init__(self, ui_refresh_ms: int = 500):
        self.ui_refresh_ms = ui_refresh_ms
        self._registry: Dict[str, List[object]] = {}
        self._last_perf_check = time.time()

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
        self._maybe_perf_check()
        return outputs

    # ------------------------------------------------------------------
    def _maybe_perf_check(self) -> None:
        now = time.time()
        if (now - self._last_perf_check) * 1000 >= self.ui_refresh_ms:
            self._last_perf_check = now
            # Placeholder for future performance metrics
            pass


# Factory convenience ----------------------------------------------------------

def default_strength_indicators() -> List[object]:
    cfg_dir = Path(__file__).resolve().parent / "indicator_configs"
    return load_indicators_from_dir(cfg_dir, category="strength")

