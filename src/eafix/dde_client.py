"""Simplified DDE client placeholder.

The production system connects to MetaTrader via Windows DDE.  Here we
only model the interface so unit tests can exercise configuration
parsing.  No actual DDE communication occurs.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass
class DDEConfig:
    poll_ms: int = 100
    timeout_sec: int = 30
    reconnect_sec: int = 5


class DDEClient:
    def __init__(self, cfg: DDEConfig):
        self.cfg = cfg
        self.buffers: Dict[str, list] = {}

    def subscribe(self, symbol: str) -> None:  # pragma: no cover - placeholder
        self.buffers.setdefault(symbol, [])

    def push_tick(self, symbol: str, bid: float, ask: float, ts: float) -> None:
        buf = self.buffers.setdefault(symbol, [])
        buf.append((bid, ask, ts))
        # prune to 1000 ticks
        del buf[:-1000]

