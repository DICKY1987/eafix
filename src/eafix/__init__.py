"""Top level package for trading system scaffold.

This module exposes the most commonly used components so that callers can
simply import them from :mod:`eafix` without knowing the internal layout of
the package.
"""

from . import conditional_signals, currency_strength, indicator_engine, signals
from . import strength_feed, transport_integrations
from .indicator_loader import load_indicators_from_dir

__all__ = [
    "conditional_signals",
    "currency_strength",
    "indicator_engine",
    "signals",
    "strength_feed",
    "transport_integrations",
    "load_indicators_from_dir",
]

# Basic package metadata; the version is intentionally static for the scaffold
# and can be updated when the project adopts semantic versioning.
__version__ = "0.1.0"
