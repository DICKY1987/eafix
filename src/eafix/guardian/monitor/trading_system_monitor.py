"""Monitor placeholder for trading system health."""

from __future__ import annotations

from typing import Dict


def collect() -> Dict[str, float]:
    """Return dummy metrics."""
    return {"latency_ms": 0.0}

