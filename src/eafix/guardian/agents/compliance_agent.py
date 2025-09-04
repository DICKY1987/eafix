"""Minimal compliance agent used by tests.

The production system forwards audit logs to a central compliance service.
For our purposes we merely need a way to capture log messages so that unit
tests can assert on them.  The :class:`ComplianceAgent` stores messages in
memory with a timestamp.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List


@dataclass
class ComplianceAgent:
    """Collect compliance log messages.

    Messages are kept in the :attr:`logs` attribute.  Each entry is timestamped
    using :func:`datetime.utcnow` so callers can inspect when the message was
    recorded.
    """

    logs: List[str] = field(default_factory=list)

    def log(self, message: str) -> None:
        """Record ``message`` in the internal log list."""

        if not isinstance(message, str):  # pragma: no cover - type guard
            raise TypeError("message must be a string")

        entry = f"{datetime.utcnow().isoformat()} {message}"
        self.logs.append(entry)

__all__ = ["ComplianceAgent"]
