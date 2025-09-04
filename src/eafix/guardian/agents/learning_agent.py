"""Lightweight in-memory learning agent.

The real project uses a considerably more sophisticated learning subsystem
that persists events and performs statistical analysis.  For the purposes of
the tests in this kata we only require a tiny portion of this behaviour: the
ability to record events in order and make them available for later
inspection.  The :class:`LearningAgent` below therefore keeps a simple list of
events and performs basic validation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List
import copy
import time


@dataclass
class LearningAgent:
    """Collect events that may be used for off-line learning.

    The agent stores a chronological list of event dictionaries.  Each call to
    :meth:`record` accepts a mapping and stores a defensive copy augmented with
    a ``timestamp`` key if one is not already present.  The stored ``events``
    attribute can then be inspected by tests or other components.
    """

    events: List[Dict[str, object]] = field(default_factory=list)

    def record(self, event: Dict[str, object]) -> None:
        """Record *event* for later analysis.

        Parameters
        ----------
        event:
            Mapping describing what happened.  It must be a dictionary so the
            contents can be serialised and copied safely.
        """

        if not isinstance(event, dict):  # pragma: no cover - type guard
            raise TypeError("event must be a dictionary")

        # Make a defensive copy so callers cannot mutate our history after the
        # fact.  ``deepcopy`` handles nested structures gracefully.
        data = copy.deepcopy(event)

        # Ensure a timestamp exists so events are ordered even when the caller
        # forgets to add one.
        data.setdefault("timestamp", time.time())

        self.events.append(data)

__all__ = ["LearningAgent"]
