from datetime import datetime, timezone
import json
from io import BytesIO

from eafix.forex_factory_calendar import fetch_calendar


class DummyResponse(BytesIO):
    def __enter__(self):  # pragma: no cover - trivial
        return self

    def __exit__(self, *exc):  # pragma: no cover - trivial
        self.close()


def test_fetch_calendar_filters_past_events(monkeypatch):
    data = [
        {"title": "Old", "timestamp": 1000},
        {"title": "Upcoming", "timestamp": 3000},
    ]

    def fake_urlopen(url, *_, **__):
        return DummyResponse(json.dumps(data).encode("utf-8"))

    monkeypatch.setattr("eafix.forex_factory_calendar.urlopen", fake_urlopen)
    now = datetime.fromtimestamp(2000, tz=timezone.utc)

    events = fetch_calendar(url="http://example.com", now=now)
    assert len(events) == 1
    assert events[0]["title"] == "Upcoming"
    # ensure the helper adds ISO formatted datetime
    assert events[0]["datetime"].endswith("+00:00")
