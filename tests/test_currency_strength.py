from eafix.currency_strength import calc_currency_strength


def test_calc_currency_strength():
    changes = {"EURUSD": 1.0, "USDJPY": -0.5}
    strength = calc_currency_strength(changes)
    assert strength["EUR"] == 1.0
    assert strength["USD"] == -1.5
    assert strength["JPY"] == 0.5
