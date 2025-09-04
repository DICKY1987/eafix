"""Utilities for fetching and displaying Forex Factory economic calendar data."""

from __future__ import annotations

import random
import re
import time
from dataclasses import dataclass
from typing import Optional, Tuple

from urllib.request import urlopen


@dataclass
class CalendarEventResult:
    """Parsed values for a single economic calendar event."""

    actual: Optional[float]
    forecast: Optional[float]
    previous: Optional[float]
    diff_forecast: Optional[float]
    diff_previous: Optional[float]


def _extract_value(html: str, cls: str) -> Optional[float]:
    """Return the numeric value contained in ``<td class=cls>``.

    Values are normalized by removing percent signs and commas.  If the class is
    not found or cannot be parsed, ``None`` is returned.
    """

    pattern = rf"<td[^>]*class=[\"']{cls}[\"'][^>]*>(.*?)</td>"
    match = re.search(pattern, html, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return None
    text = re.sub("<.*?>", "", match.group(1))
    text = text.strip().replace("%", "").replace(",", "")
    try:
        return float(text)
    except ValueError:
        return None


def parse_event_page(html: str) -> CalendarEventResult:
    """Parse *html* from a Forex Factory event page.

    The returned object contains the ``actual``, ``forecast`` and ``previous``
    values along with simple differences from ``actual``.
    """

    actual = _extract_value(html, "actual")
    forecast = _extract_value(html, "forecast")
    previous = _extract_value(html, "previous")

    diff_forecast = actual - forecast if actual is not None and forecast is not None else None
    diff_previous = actual - previous if actual is not None and previous is not None else None

    return CalendarEventResult(actual, forecast, previous, diff_forecast, diff_previous)


def fetch_event_result(
    event_url: str,
    delay_range: Tuple[int, int] = (120, 300),
    poll_interval: int = 15,
    max_attempts: int = 20,
) -> CalendarEventResult:
    """Fetch and parse a Forex Factory event page after a short delay.

    After waiting a random amount of time within ``delay_range`` (in seconds),
    the event page is polled up to ``max_attempts`` times separated by
    ``poll_interval`` seconds.  Polling stops as soon as the ``actual`` value is
    available and differs from the last seen value.  Each update emits a
    terminal bell so users are alerted when new information arrives.
    """

    wait_seconds = random.randint(*delay_range)
    time.sleep(wait_seconds)

    last_actual: Optional[float] = None
    result: CalendarEventResult | None = None

    for _ in range(max_attempts):
        with urlopen(event_url, timeout=10) as resp:  # nosec B310
            html = resp.read().decode("utf-8", errors="replace")

        result = parse_event_page(html)

        if result.actual is not None and result.actual != last_actual:
            print("\a", end="")  # alert user that new information is available
            return result

        last_actual = result.actual
        time.sleep(poll_interval)

    # If we exit the loop without returning, provide the last parsed result
    # (which may still have ``actual`` set to ``None``).
    return result if result is not None else CalendarEventResult(None, None, None, None, None)


def format_event_result(result: CalendarEventResult) -> str:
    """Return a human readable summary of *result* values."""

    actual = result.actual if result.actual is not None else "n/a"
    forecast = result.forecast if result.forecast is not None else "n/a"
    previous = result.previous if result.previous is not None else "n/a"
    diff_forecast = f"{result.diff_forecast:+}" if result.diff_forecast is not None else "n/a"
    diff_previous = f"{result.diff_previous:+}" if result.diff_previous is not None else "n/a"

    return (
        f"Actual: {actual} | Forecast: {forecast} | Previous: {previous}\n"
        f"Δ Forecast: {diff_forecast} | Δ Previous: {diff_previous}"
    )
