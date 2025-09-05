"""Simple synchronous event bus for UI components.

Provides publish/subscribe semantics. Subscribers are called in the order
registered. Handlers are executed synchronously on the calling thread.
This implementation is intentionally lightweight and only implements the
functionality required by the command palette module used in tests.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Callable, Dict, List
import threading


@dataclass
class Event:
    """Container for event data passed to subscribers."""

    name: str
    data: Dict[str, Any]
    source: str | None = None


class EventBus:
    """Minimal event bus with subscribe and publish methods."""

    def __init__(self) -> None:
        self._subscribers: Dict[str, List[Callable[[Event], None]]] = defaultdict(list)
        self._lock = threading.Lock()

    # ------------------------------------------------------------------ subscription
    def subscribe(self, event_name: str, callback: Callable[[Event], None]) -> None:
        """Register *callback* to be invoked when *event_name* is published."""
        with self._lock:
            self._subscribers[event_name].append(callback)

    def unsubscribe(self, event_name: str, callback: Callable[[Event], None]) -> None:
        """Remove a subscription if it exists."""
        with self._lock:
            if event_name in self._subscribers:
                try:
                    self._subscribers[event_name].remove(callback)
                except ValueError:
                    pass

    # ------------------------------------------------------------------ publishing
    def publish(self, event_name: str, data: Dict[str, Any] | None = None, source: str | None = None) -> None:
        """Publish an event with optional *data* and *source*.

        All registered callbacks for *event_name* are invoked sequentially. Any
        exception raised by a subscriber is swallowed so that other subscribers
        still receive the event.
        """
        event = Event(event_name, data or {}, source)
        with self._lock:
            subscribers = list(self._subscribers.get(event_name, []))
        for callback in subscribers:
            try:
                callback(event)
            except Exception:  # pragma: no cover - defensive programming
                # In production one might log the exception; here we silently
                # ignore it to keep the bus extremely lightweight.
                continue


# Shared global instance used by modules

_event_bus = EventBus()


def get_event_bus() -> EventBus:
    """Return the global :class:`EventBus` instance."""

    return _event_bus


# Backwards compatibility name expected by the command palette module.
# The module expects ``event_bus`` to be imported, so expose the instance with
# that name.

event_bus = _event_bus

__all__ = ["Event", "EventBus", "event_bus", "get_event_bus"]
