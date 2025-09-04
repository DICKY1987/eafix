"""Currency strength calculator.

This module provides a simple implementation that aggregates percentage
changes per currency.  A positive move in the base currency increases its
strength while the quote currency decreases.  The API mirrors what the
real trading system would expect but avoids heavy dependencies.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, Iterable, Mapping


def calc_currency_strength(pair_changes: Mapping[str, float]) -> Dict[str, float]:
    """Return currency strength dictionary from pair percentage changes.

    Parameters
    ----------
    pair_changes : mapping
        Keys are pair symbols like ``"EURUSD"`` and values are percentage
        changes over some window.
    """
    strength: Dict[str, float] = defaultdict(float)
    for pair, pct in pair_changes.items():
        if len(pair) != 6:
            continue
        base, quote = pair[:3], pair[3:]
        strength[base] += pct
        strength[quote] -= pct
    return dict(strength)


# Oscillator helpers -----------------------------------------------------------

def zscore(values: Iterable[float]) -> float:
    vals = list(values)
    if not vals:
        return 0.0
    mean = sum(vals) / len(vals)
    var = sum((v - mean) ** 2 for v in vals) / len(vals)
    std = var ** 0.5
    if std == 0:
        return 0.0
    return (vals[-1] - mean) / std

