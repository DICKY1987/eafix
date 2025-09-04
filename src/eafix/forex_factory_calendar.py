"""Forex Factory calendar importer.

This module provides a small helper to download the weekly economic
calendar from Forex Factory and return only upcoming events.  The real
calendar feed is updated daily; this helper allows users to trigger an
instant import that ignores past events.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from urllib.request import urlopen

# Public JSON feed provided by Forex Factory.
DEFAULT_CALENDAR_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"

def fetch_calendar(
    url: str = DEFAULT_CALENDAR_URL,
    now: datetime | None = None,
) -> list[dict[str, Any]]:
    """Download the Forex Factory calendar and return future events.

    Parameters
    ----------
    url:
        Endpoint returning the calendar JSON.  Defaults to the official
        Forex Factory feed.
    now:
        Reference time used to filter events.  Defaults to the current
        UTC time.

    Returns
    -------
    list[dict]
        Calendar entries occurring at or after *now*.
    """
    if now is None:
        now = datetime.now(tz=timezone.utc)

    with urlopen(url, timeout=10) as resp:  # pragma: no cover - simple I/O
        data = json.load(resp)

    upcoming: list[dict[str, Any]] = []
    for event in data:
        try:
            ts = datetime.fromtimestamp(int(event["timestamp"]), tz=timezone.utc)
        except Exception:
            continue  # skip malformed entries
        if ts >= now:
            item = dict(event)
            item["datetime"] = ts.isoformat()
            upcoming.append(item)
    return upcoming
