"""Calendar CSV processing helpers."""
from __future__ import annotations
import csv
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List


@dataclass
class Event:
    time: datetime
    currency: str
    impact: str
    event: str
    anticipation: bool = False


def read_csv_calendar(path: str) -> List[Event]:
    """Read events from a CSV file with columns: time,currency,impact,event."""
    events: List[Event] = []
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            events.append(
                Event(
                    time=datetime.fromisoformat(row["time"]),
                    currency=row["currency"],
                    impact=row["impact"],
                    event=row["event"],
                )
            )
    return events


def filter_events(events: List[Event], impacts=("High", "Medium"), exclude_currency="CHF") -> List[Event]:
    """Filter events by impact and exclude a currency."""
    return [e for e in events if e.impact in impacts and e.currency != exclude_currency]


def generate_all_anticipation_events(events: List[Event], hours=(1, 2, 4, 8, 12)) -> List[Event]:
    """Create anticipation events offset by specified hours before the event."""
    anticipations: List[Event] = []
    for event in events:
        for h in hours:
            anticipations.append(
                Event(
                    time=event.time - timedelta(hours=h),
                    currency=event.currency,
                    impact=event.impact,
                    event=event.event,
                    anticipation=True,
                )
            )
    return anticipations


def sort_events_chronologically(events: List[Event]) -> List[Event]:
    """Return events sorted by time."""
    return sorted(events, key=lambda e: e.time)
