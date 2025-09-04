"""Top level package for trading system scaffold.

This module exposes the most commonly used components so that callers can
simply import them from :mod:`eafix` without knowing the internal layout of
the package.
"""

from . import conditional_signals, currency_strength, indicator_engine, signals
from . import economic_calendar, strength_feed, transport_integrations

__all__ = [
    "conditional_signals",
    "currency_strength",
    "economic_calendar",
    "indicator_engine",
    "signals",
    "strength_feed",
    "transport_integrations",
]

# Basic package metadata; the version is intentionally static for the scaffold
# and can be updated when the project adopts semantic versioning.
__version__ = "0.1.0"
