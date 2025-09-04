from datetime import datetime
from zoneinfo import ZoneInfo

from eafix.signals import FridayVolSignal, FridayVolSignalConfig

UTC = ZoneInfo("UTC")


def test_friday_vol_signal_triggers():
    cfg = FridayVolSignalConfig(percent_threshold=0.5)
    signal = FridayVolSignal(cfg)
    start_utc = datetime(2023, 9, 1, 12, 30, tzinfo=UTC)
    end_utc = datetime(2023, 9, 1, 19, 0, tzinfo=UTC)

    def get_price_at(dt):
        return 100.0 if dt == start_utc else 101.0

    now_utc = datetime(2023, 9, 1, 20, 0, tzinfo=UTC)
    result = signal.evaluate("EURUSD", get_price_at, now_utc)
    assert result and result["type"] == "EXECUTE"
