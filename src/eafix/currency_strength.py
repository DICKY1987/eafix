"""Currency strength utilities.

The original project used plain percentage changes to aggregate currency
strength.  This module upgrades that logic to work with *log returns*,
which are additive across time and symmetric for up and down moves.  A
positive move in the base currency increases its strength while the quote
currency decreases.  The API mirrors what the real trading system would
expect but avoids heavy dependencies.
"""

from __future__ import annotations

from collections import defaultdict
import math
from typing import Dict, Iterable, Mapping


def log_return(price_now: float, price_then: float) -> float:
    """Return the natural log return between two prices.

    The function safely handles non-positive inputs by returning ``0.0``.
    ``price_now`` and ``price_then`` are expected to be positive floats.
    """

    if price_now <= 0 or price_then <= 0:
        return 0.0
    return math.log(price_now / price_then)


def calc_currency_strength(pair_returns: Mapping[str, float]) -> Dict[str, float]:
    """Return currency strength dictionary from pair log returns.

    Each pair contributes its log return positively to the base currency
    and negatively to the quote currency.  Contributions are averaged per
    currency so that currencies with many pairs do not dominate the final
    values.

    Parameters
    ----------
    pair_returns : mapping
        Keys are pair symbols like ``"EURUSD"`` and values are log returns
        over some window.
    """

    totals: Dict[str, float] = defaultdict(float)
    counts: Dict[str, int] = defaultdict(int)

    for pair, r in pair_returns.items():
        if len(pair) != 6:
            continue
        base, quote = pair[:3], pair[3:]
        totals[base] += r
        totals[quote] -= r
        counts[base] += 1
        counts[quote] += 1

    return {ccy: totals[ccy] / counts[ccy] for ccy in totals}


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

