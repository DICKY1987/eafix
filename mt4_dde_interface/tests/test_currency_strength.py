"""Tests for Currency Strength indicator and price feed integration."""

import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'indicators'))

from price_manager import PriceManager
from indicator_engine import IndicatorEngine
import currency_strength  # noqa: F401 ensures registration


class TestPriceFeedIntegration(unittest.TestCase):
    """Ensure price ticks feed both standard and currency strength indicators."""

    def setUp(self):
        self.pm = PriceManager()
        self.engine = IndicatorEngine(self.pm)

        # Simple SMA for each pair
        self.engine.add_indicator('EURUSD', 'SMA', 'sma_eur', {'period': 2})
        self.engine.add_indicator('GBPUSD', 'SMA', 'sma_gbp', {'period': 2})

        # Currency strength indicator uses both pairs
        csi_config = {
            'price_manager': self.pm,
            'symbols': ['EURUSD', 'GBPUSD'],
            'window': 2,
        }
        self.engine.add_indicator('GBPUSD', 'CurrencyStrength', 'csi', csi_config)

    def test_price_updates_feed_indicators(self):
        # First ticks
        self.pm.add_price_tick('EURUSD', {'bid': 1.0, 'ask': 1.001})
        self.pm.add_price_tick('GBPUSD', {'bid': 1.5, 'ask': 1.501})

        # Second ticks to trigger SMA calculations
        self.pm.add_price_tick('EURUSD', {'bid': 1.01, 'ask': 1.011})
        self.pm.add_price_tick('GBPUSD', {'bid': 1.52, 'ask': 1.521})

        # SMA values should be available
        self.assertIsNotNone(self.engine.get_indicator_value('EURUSD', 'sma_eur'))
        self.assertIsNotNone(self.engine.get_indicator_value('GBPUSD', 'sma_gbp'))

        # Currency strength should reflect both pairs
        csi = self.engine.get_indicator_value('GBPUSD', 'csi')
        self.assertIn('EUR', csi)
        self.assertIn('GBP', csi)
        self.assertIn('USD', csi)

        # Verify approximate values
        eur_change = (1.0105 - 1.0005) / 1.0005
        gbp_change = (1.5205 - 1.5005) / 1.5005
        usd_change = -(eur_change + gbp_change)

        self.assertAlmostEqual(csi['EUR'], eur_change, places=6)
        self.assertAlmostEqual(csi['GBP'], gbp_change, places=6)
        self.assertAlmostEqual(csi['USD'], usd_change, places=6)


def run_currency_strength_tests():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPriceFeedIntegration)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return result.wasSuccessful()


if __name__ == '__main__':
    run_currency_strength_tests()

