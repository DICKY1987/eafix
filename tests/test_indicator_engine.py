from eafix.indicator_engine import IndicatorEngine, default_strength_indicators


def test_indicator_engine_updates():
    engine = IndicatorEngine()
    for ind in default_strength_indicators():
        engine.add_indicator("EURUSD", ind)
    out = engine.update("EURUSD", 1.2345)
    assert "StrengthRSIIndicator" in out
    assert isinstance(out["StrengthRSIIndicator"], float)
