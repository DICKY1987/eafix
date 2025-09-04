from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parents[1]))

from calendar_processing import (
    read_csv_calendar,
    filter_events,
    generate_all_anticipation_events,
    sort_events_chronologically,
)


def test_calendar_pipeline(tmp_path):
    path = Path("tests/data/sample_calendar.csv")
    events = read_csv_calendar(path)
    assert len(events) == 3

    filtered = filter_events(events)
    # CHF event excluded, so expect 2
    assert len(filtered) == 2

    anticipations = generate_all_anticipation_events(filtered, hours=(1, 2))
    # 2 events *2 anticipation =4
    assert len(anticipations) == 4

    combined = sort_events_chronologically(filtered + anticipations)
    times = [e.time for e in combined]
    assert times == sorted(times)
