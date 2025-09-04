"""
Test suite for Technical Indicators
"""
import unittest
import sys
import os
from datetime import datetime
import pytest

# The indicator implementations rely on numpy for calculations.
np = pytest.importorskip("numpy")

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'indicators'))

from base_indicator import BaseIndicator, IndicatorConfig, IndicatorFactory
from moving_averages import *
from oscillators import *
from volatility import *


class TestBaseIndicator(unittest.TestCase):
    """Test cases for BaseIndicator base class"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create a simple test indicator
        class TestIndicator(BaseIndicator):
            def get_required_periods(self):
                return 10
            
            def calculate(self, price_data):
                if len(price_data) < 10:
                    return None
                return sum(price_data[-10:]) / 10
        
        self.test_indicator_class = TestIndicator
        config = IndicatorConfig(period=10)
        self.indicator = TestIndicator("test_sma", config)
    
    def test_indicator_initialization(self):
        """Test indicator initialization"""
        self.assertEqual(self.indicator.name, "test_sma")
        self.assertFalse(self.indicator.is_initialized)
        self.assertIsNone(self.indicator.last_value)
        self.assertEqual(self.indicator.calculation_count, 0)
    
    def test_indicator_update_insufficient_data(self):
        """Test indicator update with insufficient data"""
        # Add less data than required
        for i in range(5):
            result = self.indicator.update(100.0 + i)
            self.assertIsNone(result)
        
        self.assertFalse(self.indicator.is_initialized)
    
    def test_indicator_update_sufficient_data(self):
        """Test indicator update with sufficient data"""
        # Add sufficient data
        prices = [100.0 + i for i in range(15)]
        
        for i, price in enumerate(prices):
            result = self.indicator.update(price)
            
            if i >= 9:  # After 10 data points
                self.assertIsNotNone(result)
                self.assertTrue(self.indicator.is_initialized)
                self.assertGreater(self.indicator.calculation_count, 0)
            else:
                self.assertIsNone(result)
    
    def test_indicator_reset(self):
        """Test indicator reset functionality"""
        # Add data and update
        for i in range(15):
            self.indicator.update(100.0 + i)
        
        # Verify indicator has state
        self.assertTrue(self.indicator.is_initialized)
        self.assertIsNotNone(self.indicator.last_value)
        
        # Reset
        self.indicator.reset()
        
        # Verify reset state
        self.assertFalse(self.indicator.is_initialized)
        self.assertIsNone(self.indicator.last_value)
        self.assertEqual(self.indicator.calculation_count, 0)
    
    def test_performance_tracking(self):
        """Test performance metrics tracking"""
        # Update indicator multiple times
        for i in range(20):
            self.indicator.update(100.0 + i)
        
        # Get performance stats
        stats = self.indicator.get_performance_stats()
        
        # Verify stats structure
        expected_keys = [
            'calculation_count', 'avg_calculation_time_ms',
            'min_calculation_time_ms', 'max_calculation_time_ms',
            'total_calculation_time_ms'
        ]
        
        for key in expected_keys:
            self.assertIn(key, stats)
        
        # Verify reasonable values
        self.assertGreater(stats['calculation_count'], 0)
        self.assertGreaterEqual(stats['avg_calculation_time_ms'], 0)


class TestMovingAverages(unittest.TestCase):
    """Test cases for Moving Average indicators"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_prices = [100.0, 101.0, 102.0, 99.0, 98.0, 103.0, 105.0, 104.0, 102.0, 101.0,
                           100.0, 99.0, 101.0, 103.0, 102.0, 104.0, 106.0, 105.0, 107.0, 108.0]
    
    def test_sma_calculation(self):
        """Test Simple Moving Average calculation"""
        sma = create_moving_average('SMA', 'test_sma', 5)
        
        results = []
        for price in self.test_prices:
            result = sma.update(price)
            if result is not None:
                results.append(result)
        
        # Verify we got results
        self.assertGreater(len(results), 0)
        
        # Verify last calculation manually
        last_sma = sum(self.test_prices[-5:]) / 5
        self.assertAlmostEqual(results[-1], last_sma, places=5)
    
    def test_ema_calculation(self):
        """Test Exponential Moving Average calculation"""
        ema = create_moving_average('EMA', 'test_ema', 5)
        
        results = []
        for price in self.test_prices:
            result = ema.update(price)
            if result is not None:
                results.append(result)
        
        # Verify we got results
        self.assertGreater(len(results), 0)
        
        # EMA should be different from SMA
        sma_value = sum(self.test_prices[-5:]) / 5
        self.assertNotEqual(results[-1], sma_value)
    
    def test_wma_calculation(self):
        """Test Weighted Moving Average calculation"""
        wma = create_moving_average('WMA', 'test_wma', 5)
        
        results = []
        for price in self.test_prices:
            result = wma.update(price)
            if result is not None:
                results.append(result)
        
        # Verify we got results
        self.assertGreater(len(results), 0)
        
        # Verify last calculation manually
        weights = [1, 2, 3, 4, 5]
        weighted_sum = sum(p * w for p, w in zip(self.test_prices[-5:], weights))
        weight_sum = sum(weights)
        last_wma = weighted_sum / weight_sum
        
        self.assertAlmostEqual(results[-1], last_wma, places=5)
    
    def test_moving_average_comparison(self):
        """Test that different MA types give different results"""
        sma = create_moving_average('SMA', 'sma', 10)
        ema = create_moving_average('EMA', 'ema', 10)
        wma = create_moving_average('WMA', 'wma', 10)
        
        # Update all with same data
        for price in self.test_prices:
            sma.update(price)
            ema.update(price)
            wma.update(price)
        
        # Get final values
        sma_value = sma.get_current_value()
        ema_value = ema.get_current_value()
        wma_value = wma.get_current_value()
        
        # All should have values
        self.assertIsNotNone(sma_value)
        self.assertIsNotNone(ema_value)
        self.assertIsNotNone(wma_value)
        
        # Values should be different (with trending data)
        self.assertNotEqual(sma_value, ema_value)
        self.assertNotEqual(sma_value, wma_value)


class TestOscillators(unittest.TestCase):
    """Test cases for Oscillator indicators"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create trending price data for better oscillator testing
        self.test_prices = []
        base_price = 100.0
        for i in range(50):
            # Add some trend and volatility
            trend = i * 0.1
            noise = np.sin(i * 0.3) * 2
            price = base_price + trend + noise
            self.test_prices.append(price)
    
    def test_rsi_calculation(self):
        """Test RSI calculation"""
        rsi = create_rsi('test_rsi', 14)
        
        results = []
        for price in self.test_prices:
            result = rsi.update(price)
            if result is not None:
                results.append(result)
        
        # Verify we got results
        self.assertGreater(len(results), 0)
        
        # RSI should be between 0 and 100
        for value in results:
            self.assertGreaterEqual(value, 0)
            self.assertLessEqual(value, 100)
        
        # Test overbought/oversold detection
        final_rsi = results[-1]
        if final_rsi > 70:
            self.assertTrue(rsi.is_overbought())
        elif final_rsi < 30:
            self.assertTrue(rsi.is_oversold())
    
    def test_macd_calculation(self):
        """Test MACD calculation"""
        macd = create_macd('test_macd')
        
        results = []
        for price in self.test_prices:
            result = macd.update(price)
            if result is not None:
                results.append(result)
        
        # Verify we got results
        self.assertGreater(len(results), 0)
        
        # Check structure of last result
        last_result = results[-1]
        expected_keys = ['MACD', 'Signal', 'Histogram']
        for key in expected_keys:
            self.assertIn(key, last_result)
        
        # Histogram should equal MACD - Signal
        histogram_calc = last_result['MACD'] - last_result['Signal']
        self.assertAlmostEqual(last_result['Histogram'], histogram_calc, places=5)
    
    def test_stochastic_calculation(self):
        """Test Stochastic oscillator calculation"""
        stoch = create_stochastic('test_stoch', 14, 3)
        
        results = []
        for price in self.test_prices:
            result = stoch.update(price)
            if result is not None:
                results.append(result)
        
        # Verify we got results
        self.assertGreater(len(results), 0)
        
        # Check structure
        last_result = results[-1]
        expected_keys = ['K', 'D']
        for key in expected_keys:
            self.assertIn(key, last_result)
        
        # %K and %D should be between 0 and 100
        self.assertGreaterEqual(last_result['K'], 0)
        self.assertLessEqual(last_result['K'], 100)
        self.assertGreaterEqual(last_result['D'], 0)
        self.assertLessEqual(last_result['D'], 100)
    
    def test_williams_r_calculation(self):
        """Test Williams %R calculation"""
        williams_r = create_williams_r('test_wr', 14)
        
        results = []
        for price in self.test_prices:
            result = williams_r.update(price)
            if result is not None:
                results.append(result)
        
        # Verify we got results
        self.assertGreater(len(results), 0)
        
        # Williams %R should be between -100 and 0
        for value in results:
            self.assertGreaterEqual(value, -100)
            self.assertLessEqual(value, 0)
    
    def test_cci_calculation(self):
        """Test CCI calculation"""
        cci = create_cci('test_cci', 20)
        
        results = []
        for price in self.test_prices:
            result = cci.update(price)
            if result is not None:
                results.append(result)
        
        # Verify we got results
        self.assertGreater(len(results), 0)
        
        # CCI can have wide range, just check it's reasonable
        for value in results:
            self.assertGreater(value, -500)  # Reasonable bounds
            self.assertLess(value, 500)


class TestVolatilityIndicators(unittest.TestCase):
    """Test cases for Volatility indicators"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create price data with varying volatility
        self.test_prices = []
        base_price = 100.0
        volatility = 1.0
        
        for i in range(50):
            # Vary volatility over time
            if i % 10 == 0:
                volatility = np.random.uniform(0.5, 3.0)
            
            # Generate price with current volatility
            change = np.random.normal(0, volatility)
            base_price += change
            self.test_prices.append(base_price)
    
    def test_bollinger_bands_calculation(self):
        """Test Bollinger Bands calculation"""
        bb = create_bollinger_bands('test_bb', 20, 2.0)
        
        results = []
        for price in self.test_prices:
            result = bb.update(price)
            if result is not None:
                results.append(result)
        
        # Verify we got results
        self.assertGreater(len(results), 0)
        
        # Check structure
        last_result = results[-1]
        expected_keys = ['Upper', 'Middle', 'Lower', 'PercentB', 'Bandwidth']
        for key in expected_keys:
            self.assertIn(key, last_result)
        
        # Upper > Middle > Lower
        self.assertGreater(last_result['Upper'], last_result['Middle'])
        self.assertGreater(last_result['Middle'], last_result['Lower'])
        
        # %B should be reasonable (can be outside 0-100 for breakouts)
        self.assertGreater(last_result['PercentB'], -50)
        self.assertLess(last_result['PercentB'], 150)
        
        # Bandwidth should be positive
        self.assertGreater(last_result['Bandwidth'], 0)
    
    def test_atr_calculation(self):
        """Test ATR calculation"""
        atr = create_atr('test_atr', 14)
        
        results = []
        for price in self.test_prices:
            result = atr.update(price)
            if result is not None:
                results.append(result)
        
        # Verify we got results
        self.assertGreater(len(results), 0)
        
        # ATR should be positive
        for value in results:
            self.assertGreater(value, 0)
        
        # Test volatility classification
        last_atr = results[-1]
        last_price = self.test_prices[-1]
        volatility_level = classify_volatility(last_atr, last_price)
        
        expected_levels = ["Very Low", "Low", "Medium", "High", "Very High"]
        self.assertIn(volatility_level, expected_levels)
    
    def test_standard_deviation_calculation(self):
        """Test Standard Deviation calculation"""
        std_dev = create_standard_deviation('test_std', 20)
        
        results = []
        for price in self.test_prices:
            result = std_dev.update(price)
            if result is not None:
                results.append(result)
        
        # Verify we got results
        self.assertGreater(len(results), 0)
        
        # Standard deviation should be positive
        for value in results:
            self.assertGreaterEqual(value, 0)
        
        # Verify last calculation manually
        last_20_prices = self.test_prices[-20:]
        manual_std = np.std(last_20_prices, ddof=1)
        self.assertAlmostEqual(results[-1], manual_std, places=5)
    
    def test_volatility_index_calculation(self):
        """Test Volatility Index calculation"""
        vol_index = create_volatility_index('test_vol', 14)
        
        results = []
        for price in self.test_prices:
            result = vol_index.update(price)
            if result is not None:
                results.append(result)
        
        # Verify we got results
        self.assertGreater(len(results), 0)
        
        # Volatility index should be non-negative
        for value in results:
            self.assertGreaterEqual(value, 0)


class TestIndicatorFactory(unittest.TestCase):
    """Test cases for IndicatorFactory"""
    
    def test_factory_registration(self):
        """Test indicator factory registration"""
        available_types = IndicatorFactory.get_available_types()
        
        # Check that common indicators are registered
        expected_types = ['SMA', 'EMA', 'RSI', 'MACD', 'BollingerBands', 'ATR']
        for indicator_type in expected_types:
            self.assertIn(indicator_type, available_types)
    
    def test_factory_creation(self):
        """Test indicator creation through factory"""
        # Test SMA creation
        sma = IndicatorFactory.create('SMA', 'test_sma', {'period': 20})
        self.assertIsInstance(sma, SimpleMovingAverage)
        self.assertEqual(sma.name, 'test_sma')
        
        # Test RSI creation
        rsi = IndicatorFactory.create('RSI', 'test_rsi', {'period': 14})
        self.assertIsInstance(rsi, RelativeStrengthIndex)
        self.assertEqual(rsi.name, 'test_rsi')
        
        # Test invalid type
        with self.assertRaises(ValueError):
            IndicatorFactory.create('INVALID', 'test', {})
    
    def test_indicator_export_import(self):
        """Test indicator configuration export/import"""
        # Create indicator
        original = IndicatorFactory.create('SMA', 'test_sma', {'period': 20})
        
        # Export configuration
        config = original.export_config()
        
        # Verify config structure
        expected_keys = ['name', 'type', 'config']
        for key in expected_keys:
            self.assertIn(key, config)
        
        # Create new indicator from config
        recreated = IndicatorFactory.create(
            config['type'], 
            config['name'], 
            config['config']
        )
        
        # Verify they're equivalent
        self.assertEqual(original.name, recreated.name)
        self.assertEqual(original.__class__, recreated.__class__)


class TestIndicatorAccuracy(unittest.TestCase):
    """Test indicator calculation accuracy against known values"""
    
    def test_sma_accuracy(self):
        """Test SMA accuracy against manual calculation"""
        test_data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        period = 5
        
        sma = create_moving_average('SMA', 'test', period)
        
        results = []
        for price in test_data:
            result = sma.update(price)
            if result is not None:
                results.append(result)
        
        # Manual calculations
        expected_results = [
            3.0,  # (1+2+3+4+5)/5
            4.0,  # (2+3+4+5+6)/5
            5.0,  # (3+4+5+6+7)/5
            6.0,  # (4+5+6+7+8)/5
            7.0,  # (5+6+7+8+9)/5
            8.0   # (6+7+8+9+10)/5
        ]
        
        self.assertEqual(len(results), len(expected_results))
        for actual, expected in zip(results, expected_results):
            self.assertAlmostEqual(actual, expected, places=10)
    
    def test_rsi_boundary_conditions(self):
        """Test RSI with boundary conditions"""
        rsi = create_rsi('test_rsi', 14)
        
        # All increasing prices (should approach RSI 100)
        for i in range(30):
            rsi.update(100.0 + i)
        
        high_rsi = rsi.get_current_value()
        self.assertGreater(high_rsi, 80)  # Should be high
        
        # Reset and test decreasing prices
        rsi.reset()
        for i in range(30):
            rsi.update(100.0 - i)
        
        low_rsi = rsi.get_current_value()
        self.assertLess(low_rsi, 20)  # Should be low


def run_indicator_tests():
    """Run all indicator tests"""
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_classes = [
        TestBaseIndicator,
        TestMovingAverages,
        TestOscillators,
        TestVolatilityIndicators,
        TestIndicatorFactory,
        TestIndicatorAccuracy
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    print("Running Technical Indicator Tests...")
    print("=" * 50)
    
    success = run_indicator_tests()
    
    if success:
        print("\n" + "=" * 50)
        print("All indicator tests passed successfully!")
    else:
        print("\n" + "=" * 50)
        print("Some tests failed. Check output above for details.")
        
    exit(0 if success else 1)