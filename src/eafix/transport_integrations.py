"""Transport integrations with basic failover logic.

The production system routes messages through a hierarchy of transports
(socket → named pipe → CSV spool).  This module implements a greatly
simplified version suitable for unit testing.  Transports implement a
small common interface and the :class:`TriTransportRouter` coordinates
failover and buffering.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Protocol
import json
import os
import time


class Transport(Protocol):
    """Minimal transport interface used by :class:`TriTransportRouter`."""

    def send(self, payload: bytes) -> bool:
        ...


@dataclass
class CsvSpoolTransport:
    """Append-only CSV transport used as a last resort."""

    path: Path

    def send(self, payload: bytes) -> bool:  # pragma: no cover - trivial
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("ab") as fh:
            fh.write(payload + b"\n")
        return True


class DummyTransport:
    """In-memory transport that can be toggled to fail."""

    def __init__(self, should_fail: bool = False):
        self.should_fail = should_fail
        self.sent: List[bytes] = []

    def send(self, payload: bytes) -> bool:
        if self.should_fail:
            return False
        self.sent.append(payload)
        return True


@dataclass
class TriTransportRouter:
    """Route messages through three transports with automatic failover."""

    primary: Transport
    secondary: Transport
    emergency: CsvSpoolTransport
    buffer: List[bytes] = field(default_factory=list)

    def _encode(self, message: dict) -> bytes:
        return json.dumps(message).encode("utf-8")

    def send(self, message: dict) -> bool:
        payload = self._encode({"id": id(message), "ts": time.time(), **message})
        for transport in (self.primary, self.secondary, self.emergency):
            if transport.send(payload):
                return True
        # all failed, buffer for retry
        self.buffer.append(payload)
        return False

