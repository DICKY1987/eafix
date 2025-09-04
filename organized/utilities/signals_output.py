"""Trading signal output helpers."""
from __future__ import annotations
import csv
from typing import Iterable

from .calendar_processing import Event


def write_signals(events: Iterable[Event], path: str) -> None:
    """Write events to CSV in a simplified signal format."""
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["time", "currency", "impact", "event", "anticipation"])
        for e in events:
            writer.writerow([e.time.isoformat(), e.currency, e.impact, e.event, int(e.anticipation)])
