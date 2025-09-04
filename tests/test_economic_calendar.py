import pytest

from eafix import economic_calendar
from eafix.economic_calendar import (
    CalendarEventResult,
    fetch_event_result,
    format_event_result,
    parse_event_page,
)

SAMPLE_HTML = """
<table>
<tr>
<td class="actual">1.5%</td>
<td class="forecast">1.2%</td>
<td class="previous">1.0%</td>
</tr>
</table>
"""

def test_parse_event_page():
    result = parse_event_page(SAMPLE_HTML)
    assert result.actual == 1.5
    assert result.forecast == 1.2
    assert result.previous == 1.0
    assert result.diff_forecast == pytest.approx(0.3)
    assert result.diff_previous == pytest.approx(0.5)


def test_format_event_result():
    result = CalendarEventResult(1.5, 1.2, 1.0, 0.3, 0.5)
    msg = format_event_result(result)
    assert "Actual: 1.5" in msg
    assert "Forecast: 1.2" in msg
    assert "Previous: 1.0" in msg
    assert "Δ Forecast: +0.3" in msg
    assert "Δ Previous: +0.5" in msg


def test_fetch_event_result_polls_until_actual(monkeypatch):
    html_no_actual = """
    <table><tr>
    <td class="actual"></td>
    <td class="forecast">1.2%</td>
    <td class="previous">1.0%</td>
    </tr></table>
    """

    html_with_actual = """
    <table><tr>
    <td class="actual">1.5%</td>
    <td class="forecast">1.2%</td>
    <td class="previous">1.0%</td>
    </tr></table>
    """

    responses = [html_no_actual, html_with_actual]

    class DummyResp:
        def __init__(self, html):
            self.html = html

        def read(self):
            return self.html.encode("utf-8")

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

    def fake_urlopen(url, timeout=10):  # noqa: D401 - signature matches real function
        return DummyResp(responses.pop(0))

    beeps = []

    monkeypatch.setattr(economic_calendar, "urlopen", fake_urlopen)
    monkeypatch.setattr(economic_calendar.random, "randint", lambda a, b: 0)
    monkeypatch.setattr(economic_calendar.time, "sleep", lambda s: None)
    monkeypatch.setattr("builtins.print", lambda msg="", end="\n": beeps.append(msg))

    result = fetch_event_result("http://example.com", delay_range=(0, 0), poll_interval=0, max_attempts=2)
    assert result.actual == 1.5
    assert "\a" in beeps
