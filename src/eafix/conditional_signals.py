"""Conditional probability signal scanner and runtime helper.

This module provides a lightweight scaffold around the much larger
conditional probability system described in the project notes.  The
actual historical scanning and ranking logic is outside the scope of
this kata; however the interfaces are defined so that production code
can drop in later without changing call sites.

The implementation here favours clarity and idempotency.  All heavy
lifting functions contain TODO markers for future work.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional, Tuple

import csv
import math

# ---------------------------------------------------------------------------
# Data containers
# ---------------------------------------------------------------------------

@dataclass
class ConditionalRow:
    """Represents a single trigger/outcome row.

    Attributes
    ----------
    trigger: str
        Description of the trigger e.g. "burst_10_15".
    outcome: str
        Outcome bucket identifier.
    direction: str
        Trade direction associated with the row.
    state: str
        Additional state information; derived from helpers like
        :func:`state_rsi_bucket`.
    succ: int
        Success count.
    tot: int
        Total count.
    p: float
        Probability of success ``succ / tot`` after smoothing.
    """

    trigger: str
    outcome: str
    direction: str
    state: str
    succ: int
    tot: int
    p: float


# ---------------------------------------------------------------------------
# State helpers
# ---------------------------------------------------------------------------

def state_rsi_bucket(rsi: float, buckets: Iterable[Tuple[int, int]] = ((0, 30), (30, 70), (70, 100))) -> str:
    """Bucketise an RSI value.

    Parameters
    ----------
    rsi : float
        Relative Strength Index value.
    buckets : iterable of (low, high)
        Ranges that map to string buckets.
    """
    for low, high in buckets:
        if low <= rsi < high:
            return f"RSI_{low}_{high}"
    return "RSI_OUT_OF_RANGE"


def state_none(*_: object, **__: object) -> str:
    """Fallback state helper used when no state is required."""

    return "NONE"


# ---------------------------------------------------------------------------
# Scanner skeleton
# ---------------------------------------------------------------------------

@dataclass
class ScanConfig:
    months_back: int = 6
    min_samples: int = 200


class ConditionalScanner:
    """Offline M1 scanner for conditional probabilities.

    In production this class would read historical one minute bars and
    compute the trigger/outcome table.  The `scan` method currently only
    writes a CSV header so unit tests can exercise the filesystem paths
    without the heavy lifting.
    """

    def __init__(self, cfg: ScanConfig):
        self.cfg = cfg

    def scan(self, symbol: str, dest: Path) -> Path:
        """Run a historical scan for *symbol*.

        Parameters
        ----------
        symbol : str
            Instrument identifier.
        dest : Path
            Destination directory where CSVs will be written.
        """
        dest.mkdir(parents=True, exist_ok=True)
        table_path = dest / f"{symbol}_conditional_table.csv"
        top_path = dest / f"{symbol}_conditional_top.csv"
        with table_path.open("w", newline="") as fh:
            writer = csv.writer(fh)
            writer.writerow(["symbol","trigger","outcome","dir","state","succ","tot","p"])
        with top_path.open("w", newline="") as fh:
            writer = csv.writer(fh)
            writer.writerow(["symbol","trigger","outcome","dir","state","succ","tot","p"])
        return table_path

    # ------------------------------------------------------------------
    # Ranking helpers
    # ------------------------------------------------------------------
    @staticmethod
    def laplace_smoothing(success: int, total: int, alpha: float = 1.0) -> float:
        """Return smoothed probability using Laplace estimator."""
        return (success + alpha) / (total + 2 * alpha)

    @staticmethod
    def wilson_score_interval(p: float, n: int, z: float = 1.96) -> Tuple[float, float]:
        """Wilson score confidence interval for a Bernoulli process."""
        if n == 0:
            return 0.0, 0.0
        centre = p + z**2/(2*n)
        margin = z * math.sqrt((p*(1-p) + z**2/(4*n))/n)
        denom = 1 + z**2/n
        return (centre - margin)/denom, (centre + margin)/denom

    def best_match(self, rows: List[ConditionalRow]) -> Optional[ConditionalRow]:
        """Return the row with the highest probability *p*.

        This helper is used at runtime when the current trigger/state are
        known and a quick best match is required.
        """
        if not rows:
            return None
        return max(rows, key=lambda r: (r.p, r.tot))


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def pips(value: float, decimals: int = 5) -> float:
    """Convert raw price change into pips given decimal places."""
    return round(value * (10 ** decimals), 1)

