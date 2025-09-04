import pytest

from eafix.currency_strength import log_return


def test_log_return_basic():
    assert log_return(110, 100) == pytest.approx(0.0953102, rel=1e-6)
    assert log_return(100, 110) == pytest.approx(-0.0953102, rel=1e-6)


def test_log_return_non_positive():
    assert log_return(0, 100) == 0.0
    assert log_return(100, 0) == 0.0
