from eafix.currency_strength import calc_currency_strength


def test_calc_currency_strength():
    returns = {"EURUSD": 1.0, "USDJPY": -0.5}
    strength = calc_currency_strength(returns)
    assert strength["EUR"] == 1.0
    assert strength["USD"] == -0.75
    assert strength["JPY"] == 0.5
