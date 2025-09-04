import pytest

from eafix.strength_feed import StrengthFeed


def test_strength_feed_window_and_history():
    feed = StrengthFeed(window=3)
    feed.update({'USD': 1.0})
    feed.update({'USD': 2.0})
    feed.update({'USD': 3.0})
    feed.update({'USD': 4.0})
    assert feed.history('USD') == [2.0, 3.0, 4.0]


def test_strength_feed_zscore():
    feed = StrengthFeed(window=10)
    for val in [1.0, 2.0, 3.0, 4.0]:
        feed.update({'EUR': val})
    z = feed.zscore('EUR')
    assert z > 0
    assert pytest.approx(z, rel=1e-3) == 1.3416
