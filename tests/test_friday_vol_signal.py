from datetime import datetime
import pathlib
import sys

# Allow running tests without installing the package  
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

try:
    from zoneinfo import ZoneInfo
    UTC = ZoneInfo("UTC")
except ImportError:
    # Fallback for older Python versions
    from datetime import timezone
    UTC = timezone.utc

try:
    from eafix.signals import FridayVolSignal, FridayVolSignalConfig
except ImportError:
    # Fallback to direct import for development
    from signals.friday_vol_signal import FridayVolSignal, FridayVolSignalConfig

# Freeze to a known Friday after 14:00 Chicago: 2025-08-29 20:10:00 UTC
FRI_UTC = datetime(2025, 8, 29, 20, 10, 0, tzinfo=UTC)

def mock_prices_factory(p_start: float, p_end: float):
    def _get_price_at(_dt):
        # Simple stub: return start before 14:00 and end at/after 14:00
        # We don't distinguish timestamps in this simple mock
        # First call -> start, second call -> end
        if not hasattr(_get_price_at, "_count"):
            _get_price_at._count = 0
        _get_price_at._count += 1
        return p_start if _get_price_at._count == 1 else p_end
    return _get_price_at

def test_triggers_once():
    """Test that signal triggers once and guards against re-firing"""
    cfg = FridayVolSignalConfig(percent_threshold=1.0)
    sig = FridayVolSignal(cfg)

    # 1.2% up move
    get_price = mock_prices_factory(1.0000, 1.0120)
    msg1 = sig.evaluate("EURUSD", get_price_at=get_price, now_utc=FRI_UTC)
    assert msg1 and msg1["type"] == "EXECUTE"
    # Guard prevents re-fire
    msg2 = sig.evaluate("EURUSD", get_price_at=get_price, now_utc=FRI_UTC)
    assert msg2 is None

def test_below_threshold_no_trigger():
    """Test that signal doesn't trigger below threshold"""
    cfg = FridayVolSignalConfig(percent_threshold=2.0)
    sig = FridayVolSignal(cfg)

    # 1.2% up move but threshold is 2%
    get_price = mock_prices_factory(1.0000, 1.0120)
    msg = sig.evaluate("EURUSD", get_price_at=get_price, now_utc=FRI_UTC)
    assert msg is None

def test_friday_vol_signal_triggers():
    """Test APF-style Friday vol signal triggering"""
    cfg = FridayVolSignalConfig(percent_threshold=0.5)
    signal = FridayVolSignal(cfg)
    start_utc = datetime(2023, 9, 1, 12, 30, tzinfo=UTC)
    end_utc = datetime(2023, 9, 1, 19, 0, tzinfo=UTC)

    def get_price_at(dt):
        return 100.0 if dt == start_utc else 101.0

    now_utc = datetime(2023, 9, 1, 20, 0, tzinfo=UTC)
    result = signal.evaluate("EURUSD", get_price_at, now_utc)
    assert result and result["type"] == "EXECUTE"


def test_naive_datetime_supported():
    """Evaluate should accept naive UTC datetimes without error."""
    cfg = FridayVolSignalConfig(percent_threshold=1.0)
    sig = FridayVolSignal(cfg)
    get_price = mock_prices_factory(1.0, 1.02)
    now_naive = datetime(2025, 8, 29, 20, 10, 0)  # same moment as FRI_UTC but naive
    msg = sig.evaluate("EURUSD", get_price_at=get_price, now_utc=now_naive)
    assert msg and msg["type"] == "EXECUTE"
