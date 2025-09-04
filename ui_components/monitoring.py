"""Real-time monitoring component placeholder."""
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class Monitoring:
    """Tracks upcoming events and countdown."""
    next_event: datetime | None = None

    def update_next_event(self, event_time: datetime) -> None:
        self.next_event = event_time

    def seconds_until(self) -> int:
        if self.next_event is None:
            return -1
        return max(0, int((self.next_event - datetime.utcnow()).total_seconds()))
