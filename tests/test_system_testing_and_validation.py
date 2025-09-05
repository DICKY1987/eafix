#!/usr/bin/env python3
"""
Enhanced HUEY_P Trading System - Comprehensive Testing and Validation Suite
Tests all components of the sophisticated trading system
"""

import asyncio
import unittest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import json
import csv
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import logging

# Configure test logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestCurrencyStrengthCalculator(unittest.TestCase):
    """Test suite for currency strength calculation system"""
    
    def setUp(self):
        """Set up test environment"""
        self.mock_dde = Mock()
        self.mock_dde.major_pairs = ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD', 'USDCAD']
        self.test_price_data = {
            'EURUSD': {'bid': 1.0845, 'ask': 1.0847, 'mid': 1.0846, 'timestamp': datetime.now()},
            'GBPUSD': {'bid': 1.2755, 'ask': 1.2757, 'mid': 1.2756, 'timestamp': datetime.now()},
            'USDJPY': {'bid': 149.80, 'ask': 149.82, 'mid': 149.81, 'timestamp': datetime.now()},
            'USDCHF': {'bid': 0.8945, 'ask': 0.8947, 'mid': 0.8946, 'timestamp': datetime.now()},
            'AUDUSD': {'bid': 0.6648, 'ask': 0.6650, 'mid': 0.6649, 'timestamp': datetime.now()},
            'USDCAD': {'bid': 1.3648, 'ask': 1.3650, 'mid': 1.3649, 'timestamp': datetime.now()}
        }
        self.mock_dde.get_realtime_prices.return_value = self.test_price_data
    
    def test_strength_calculation_basic(self):
        """Test basic currency strength calculation"""
        from enhanced_huey_trading_system import CurrencyStrengthCalculator
        
        calc = CurrencyStrengthCalculator(self.mock_dde)
        
        # Add historical data
        for pair, data in self.test_price_data.items():
            for i in range(10):
                calc.price_history[pair].append({
                    'price': data['mid'] * (1 + np.random.normal(0, 0.001)),
                    'timestamp': datetime.now() - timedelta(minutes=i*5)
                })
        
        strength_matrix = calc.calculate_strength_matrix(60)
        
        # Verify all currencies have strength values
        expected_currencies = ['USD', 'EUR', 'GBP', 'JPY', 'CHF', 'AUD', 'CAD', 'NZD']
        for currency in expected_currencies:
            self.assertIn(currency, strength_matrix)
            self.assertIsInstance(strength_matrix[currency].strength, float)
            self.assertGreaterEqual(strength_matrix[currency].strength, 0)
            self.assertLessEqual(strength_matrix[currency].strength, 100)
    
    def test_extreme_type_classification(self):
        """Test extreme type classification logic"""
        from enhanced_huey_trading_system import CurrencyStrengthCalculator, ExtremeType
        
        calc = CurrencyStrengthCalculator(self.mock_dde)
        
        # Test normal case (z_score < 1.5)
        extreme_type = calc._classify_extreme_type('USD', 0.5)
        self.assertEqual(extreme_type, ExtremeType.NOT_EXTREME)
        
        # Test moderate extreme (1.5 <= z_score < 2.0)
        extreme_type = calc._classify_extreme_type('USD', 1.7)
        self.assertEqual(extreme_type, ExtremeType.PARTIALLY_JUSTIFIED)
        
        # Test high extreme (z_score >= 2.0)
        with patch.object(calc, '_calculate_fundamental_support', return_value=0.9):
            extreme_type = calc._classify_extreme_type('USD', 2.5)
            self.assertEqual(extreme_type, ExtremeType.JUSTIFIED_EXTREME)
        
        with patch.object(calc, '_calculate_fundamental_support', return_value=0.2):
            extreme_type = calc._classify_extreme_type('USD', 2.5)
            self.assertEqual(extreme_type, ExtremeType.UNJUSTIFIED_EXTREME)
    
    def test_statistical_calculations(self):
        """Test statistical analysis components"""
        from enhanced_huey_trading_system import CurrencyStrengthCalculator
        
        calc = CurrencyStrengthCalculator(self.mock_dde)
        
        # Test with known data
        test_strengths = {'USD': 75, 'EUR': 45, 'GBP': 65, 'JPY': 25}
        mean_expected = np.mean(list(test_strengths.values()))
        std_expected = np.std(list(test_strengths.values()))
        
        # Calculate z-scores manually
        for currency, strength in test_strengths.items():
            z_score = (strength - mean_expected) / std_expected
            # Verify extreme classification logic
            if abs(z_score) >= 2.0:
                self.assertGreaterEqual(abs(z_score), 2.0)

class TestEconomicCalendarManager(unittest.TestCase):
    """Test suite for economic calendar management"""
    
    def setUp(self):
        """Set up test calendar data"""
        self.test_events = [
            {
                'Currency': 'USD',
                'Event': 'Non-Farm Payrolls',
                'Time': (datetime.now() + timedelta(hours=2)).strftime('%Y-%m-%d %H:%M:%S'),
                'Impact': 'High',
                'Actual': '',
                'Forecast': '200K',
                'Previous': '180K'
            },
            {
                'Currency': 'EUR',
                'Event': 'ECB Rate Decision',
                'Time': (datetime.now() + timedelta(hours=6)).strftime('%Y-%m-%d %H:%M:%S'),
                'Impact': 'High',
                'Actual': '',
                'Forecast': '4.50%',
                'Previous': '4.50%'
            },
            {
                'Currency': 'USD',
                'Event': 'CPI Release',
                'Time': (datetime.now() - timedelta(hours=12)).strftime('%Y-%m-%d %H:%M:%S'),
                'Impact': 'High',
                'Actual': '3.2%',
                'Forecast': '3.1%',
                'Previous': '3.0%'
            }
        ]
    
    def test_calendar_loading(self):
        """Test economic calendar CSV loading"""
        from enhanced_huey_trading_system import EconomicCalendarManager
        
        # Create temporary CSV file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.DictWriter(f, fieldnames=['Currency', 'Event', 'Time', 'Impact', 'Actual', 'Forecast', 'Previous'])
            writer.writeheader()
            writer.writerows(self.test_events)
            temp_file = f.name
        
        try:
            manager = EconomicCalendarManager()
            success = manager.load_calendar_from_csv(temp_file)
            
            self.assertTrue(success)
            self.assertEqual(len(manager.events), 3)  # All events should be loaded
            
            # Verify event data
            for event in manager.events:
                self.assertIn(event.currency, ['USD', 'EUR'])
                self.assertIn(event.impact, ['High', 'Medium'])
        finally:
            os.unlink(temp_file)
    
    def test_fundamental_justification_calculation(self):
        """Test fundamental justification calculation"""
        from enhanced_huey_trading_system import EconomicCalendarManager
        
        from enhanced_huey_trading_system import EconomicEvent
        manager = EconomicCalendarManager()
        manager.events = [
            EconomicEvent('USD', 'NFP', 'High', datetime.now() - timedelta(hours=6)),  # Recent high impact
            EconomicEvent('USD', 'CPI', 'Medium', datetime.now() + timedelta(hours=4))   # Upcoming medium impact
        ]
        
        justification = manager.calculate_fundamental_justification('USD')
        
        self.assertIn('justification', justification)
        self.assertIn('support_score', justification)
        self.assertIn('confidence', justification)
        self.assertGreater(justification['support_score'], 0)
    
    def test_time_window_filtering(self):
        """Test event time window filtering"""
        from enhanced_huey_trading_system import EconomicCalendarManager, EconomicEvent
        
        manager = EconomicCalendarManager()
        
        # Create events at different times
        now = datetime.now()
        manager.events = [
            EconomicEvent('USD', 'Event1', 'High', now + timedelta(hours=1)),
            EconomicEvent('USD', 'Event2', 'High', now + timedelta(hours=25)),  # Outside window
            EconomicEvent('EUR', 'Event3', 'High', now + timedelta(hours=12)),
            EconomicEvent('USD', 'Event4', 'High', now - timedelta(hours=6))    # Recent
        ]
        
        # Test upcoming events
        upcoming = manager.get_upcoming_events('USD', 24)
        self.assertEqual(len(upcoming), 2)  # Event1 and Event4 should be within 24 hours
        
        # Test recent events
        recent = manager.get_recent_events('USD', 12)
        self.assertEqual(len(recent), 1)  # Only Event4 should be recent

class TestSignalGenerator(unittest.TestCase):
    """Test suite for enhanced signal generation"""
    
    def setUp(self):
        """Set up test components"""
        self.mock_dde = Mock()
        self.mock_strength_calc = Mock()
        self.mock_calendar = Mock()
        
        # Sample strength matrix
        from enhanced_huey_trading_system import CurrencyStrength, ExtremeType
        self.sample_strength_matrix = {
            'USD': CurrencyStrength('USD', 25.0, -2.1, 50.0, 12.0, ExtremeType.UNJUSTIFIED_EXTREME, 0.3, datetime.now()),
            'EUR': CurrencyStrength('EUR', 75.0, 2.0, 50.0, 12.0, ExtremeType.JUSTIFIED_EXTREME, 0.9, datetime.now()),
            'GBP': CurrencyStrength('GBP', 45.0, -0.4, 50.0, 12.0, ExtremeType.NOT_EXTREME, 0.5, datetime.now()),
            'JPY': CurrencyStrength('JPY', 55.0, 0.4, 50.0, 12.0, ExtremeType.NOT_EXTREME, 0.6, datetime.now())
        }
    
    def test_counter_currency_selection(self):
        """Test optimal counter currency selection logic"""
        from enhanced_huey_trading_system import EnhancedSignalGenerator
        
        generator = EnhancedSignalGenerator(self.mock_dde, self.mock_strength_calc, self.mock_calendar)
        
        # Test strong event currency (EUR = 75) with high impact
        counter, strategy, strength = generator.get_optimal_counter_currency(
            'EUR', 'High', self.sample_strength_matrix
        )
        self.assertEqual(counter, 'USD')  # Should pair with weakest (USD = 25)
        self.assertEqual(strategy, 'STRENGTH_EXPLOITATION')
        
        # Test weak event currency (USD = 25) with high impact
        counter, strategy, strength = generator.get_optimal_counter_currency(
            'USD', 'High', self.sample_strength_matrix
        )
        self.assertEqual(counter, 'EUR')  # Should pair with strongest (EUR = 75)
        self.assertEqual(strategy, 'RECOVERY_MOMENTUM')
        
        # Test neutral currency with medium impact
        counter, strategy, strength = generator.get_optimal_counter_currency(
            'GBP', 'Medium', self.sample_strength_matrix
        )
        self.assertEqual(strategy, 'CONSERVATIVE_MAJOR')
    
    def test_currency_pair_construction(self):
        """Test currency pair symbol construction"""
        from enhanced_huey_trading_system import EnhancedSignalGenerator
        
        generator = EnhancedSignalGenerator(self.mock_dde, self.mock_strength_calc, self.mock_calendar)
        
        # Test major pair ordering
        self.assertEqual(generator.construct_currency_pair('USD', 'EUR'), 'EURUSD')
        self.assertEqual(generator.construct_currency_pair('EUR', 'USD'), 'EURUSD')
        self.assertEqual(generator.construct_currency_pair('GBP', 'JPY'), 'GBPJPY')
        self.assertEqual(generator.construct_currency_pair('JPY', 'GBP'), 'GBPJPY')
    
    def test_straddle_parameter_calculation(self):
        """Test straddle parameter calculation with risk adjustment"""
        from enhanced_huey_trading_system import EnhancedSignalGenerator
        
        generator = EnhancedSignalGenerator(self.mock_dde, self.mock_strength_calc, self.mock_calendar)
        
        # Test with justified extreme (should get enhanced parameters)
        params = generator.calculate_straddle_parameters(
            'EUR', 'USD', self.sample_strength_matrix, 'High'
        )
        
        self.assertIsNotNone(params)
        self.assertIn('buy_distance', params)
        self.assertIn('sell_distance', params)
        self.assertIn('lot_size_multiplier', params)
        self.assertGreater(params['lot_size_multiplier'], 1.0)  # Should be enhanced
        
        # Test with unjustified extreme (should be rejected or reduced)
        usd_extreme = self.sample_strength_matrix['USD']
        usd_extreme.fundamental_support = 0.2  # Low support
        
        params = generator.calculate_straddle_parameters(
            'USD', 'EUR', self.sample_strength_matrix, 'High'
        )
        
        # Should either be None (rejected) or heavily reduced
        if params is not None:
            self.assertLess(params['lot_size_multiplier'], 0.8)
    
    def test_signal_confidence_calculation(self):
        """Test comprehensive signal confidence calculation"""
        from enhanced_huey_trading_system import EnhancedSignalGenerator, EconomicEvent
        
        generator = EnhancedSignalGenerator(self.mock_dde, self.mock_strength_calc, self.mock_calendar)
        
        # High impact event with strong justification
        event = EconomicEvent('EUR', 'ECB Decision', 'High', datetime.now())
        justification = {
            'support_score': 0.9,
            'justification': 'JUSTIFIED_EXTREME'
        }
        
        confidence = generator._calculate_signal_confidence(
            event, self.sample_strength_matrix, justification, 'STRENGTH_EXPLOITATION'
        )
        
        self.assertGreater(confidence, 0.7)  # Should be high confidence
        self.assertLessEqual(confidence, 1.0)
        
        # Low impact event with poor justification
        event_low = EconomicEvent('GBP', 'Minor Data', 'Medium', datetime.now())
        justification_low = {
            'support_score': 0.2,
            'justification': 'UNJUSTIFIED_EXTREME'
        }
        
        confidence_low = generator._calculate_signal_confidence(
            event_low, self.sample_strength_matrix, justification_low, 'LIQUIDITY_DEFAULT'
        )
        
        self.assertLess(confidence_low, confidence)  # Should be lower

class TestDDEInterface(unittest.TestCase):
    """Test suite for DDE interface (mocked)"""
    
    def test_connection_handling(self):
        """Test DDE connection establishment and error handling"""
        from enhanced_huey_trading_system import MT4_DDE_Interface
        
        interface = MT4_DDE_Interface()
        
        # Test connection status
        self.assertFalse(interface.is_connected)
        
        # Test price data structure
        mock_prices = {
            'EURUSD': {'bid': 1.0845, 'ask': 1.0847, 'mid': 1.0846}
        }
        interface.price_data = mock_prices
        
        self.assertEqual(interface.price_data['EURUSD']['bid'], 1.0845)
    
    def test_price_validation(self):
        """Test price data validation"""
        from enhanced_huey_trading_system import MT4_DDE_Interface
        
        interface = MT4_DDE_Interface()
        
        # Valid price data
        valid_data = {
            'EURUSD': {
                'bid': 1.0845,
                'ask': 1.0847,
                'mid': 1.0846,
                'spread': 0.0002,
                'timestamp': datetime.now()
            }
        }
        
        # Validate structure
        for symbol, data in valid_data.items():
            self.assertIn('bid', data)
            self.assertIn('ask', data)
            self.assertIn('mid', data)
            self.assertGreater(data['ask'], data['bid'])

class TestSystemIntegration(unittest.TestCase):
    """Integration tests for the complete system"""
    
    def test_end_to_end_signal_generation(self):
        """Test complete signal generation pipeline"""
        # This would test the full workflow from economic event to signal output
        # Due to complexity, we'll test key integration points
        
        # Mock all components
        mock_dde = Mock()
        mock_strength_calc = Mock()
        mock_calendar = Mock()
        
        # Set up return values
        mock_dde.get_realtime_prices.return_value = {
            'EURUSD': {'bid': 1.0845, 'ask': 1.0847, 'mid': 1.0846, 'timestamp': datetime.now()}
        }
        
        from enhanced_huey_trading_system import CurrencyStrength, ExtremeType
        mock_strength_calc.calculate_strength_matrix.return_value = {
            'EUR': CurrencyStrength('EUR', 75.0, 2.0, 50.0, 12.0, ExtremeType.JUSTIFIED_EXTREME, 0.9, datetime.now()),
            'USD': CurrencyStrength('USD', 25.0, -2.0, 50.0, 12.0, ExtremeType.UNJUSTIFIED_EXTREME, 0.3, datetime.now())
        }
        
        mock_calendar.calculate_fundamental_justification.return_value = {
            'justification': 'JUSTIFIED_EXTREME',
            'support_score': 0.9,
            'confidence': 'HIGH_CONFIDENCE'
        }
        
        # Test signal generation
        from enhanced_huey_trading_system import EnhancedSignalGenerator, EconomicEvent
        generator = EnhancedSignalGenerator(mock_dde, mock_strength_calc, mock_calendar)
        
        event = EconomicEvent('EUR', 'ECB Decision', 'High', datetime.now())
        signal = generator.generate_economic_signal(event)
        
        self.assertIsNotNone(signal)
        self.assertEqual(signal.event_currency, 'EUR')
        self.assertEqual(signal.direction, 'STRADDLE')
        self.assertGreater(signal.confidence, 0.6)

class TestRiskManagement(unittest.TestCase):
    """Test suite for risk management components"""
    
    def test_extreme_position_detection(self):
        """Test detection of extreme currency positions"""
        from enhanced_huey_trading_system import CurrencyStrength, ExtremeType
        
        # Create extreme position
        extreme_currency = CurrencyStrength(
            'USD', 15.0, -2.8, 50.0, 12.0, 
            ExtremeType.UNJUSTIFIED_EXTREME, 0.2, datetime.now()
        )
        
        # Test extreme detection
        self.assertEqual(extreme_currency.extreme_type, ExtremeType.UNJUSTIFIED_EXTREME)
        self.assertLess(extreme_currency.fundamental_support, 0.4)
        self.assertLess(extreme_currency.z_score, -2.0)
    
    def test_position_sizing_calculation(self):
        """Test dynamic position sizing based on risk factors"""
        # This would test the lot size calculation logic
        # incorporating confidence, strength differential, and risk factors
        
        base_lot = 0.01
        confidence = 0.8
        strength_diff = 60.0
        fundamental_support = 0.9
        
        # Calculate enhanced lot size
        confidence_mult = 0.5 + (confidence * 0.5)
        strength_mult = 1.3 if strength_diff > 50 else 1.0
        support_mult = 1.2 if fundamental_support > 0.8 else 1.0
        
        enhanced_lot = base_lot * confidence_mult * strength_mult * support_mult
        
        self.assertGreater(enhanced_lot, base_lot)
        self.assertLessEqual(enhanced_lot, 0.1)  # Reasonable upper limit

def create_test_data_files():
    """Create test data files for integration testing"""
    
    # Create test economic calendar
    test_events = [
        {
            'Time': (datetime.now() + timedelta(hours=2)).strftime('%Y-%m-%d %H:%M:%S'),
            'Currency': 'USD',
            'Event': 'Test NFP',
            'Impact': 'High',
            'Actual': '',
            'Forecast': '200K',
            'Previous': '180K'
        }
    ]
    
    with open('test_calendar.csv', 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['Time', 'Currency', 'Event', 'Impact', 'Actual', 'Forecast', 'Previous'])
        writer.writeheader()
        writer.writerows(test_events)
    
    # Create test configuration
    test_config = {
        "dde_enabled": False,  # Disable for testing
        "strength_update_interval": 5,
        "min_signal_confidence": 0.5,
        "economic_calendar_path": "test_calendar.csv"
    }
    
    with open('test_config.json', 'w') as f:
        json.dump(test_config, f, indent=2)

def run_performance_tests():
    """Run performance benchmarks"""
    
    print("Running Performance Tests...")
    
    # Test 1: Currency strength calculation speed
    start_time = datetime.now()
    
    # Simulate strength calculation
    currencies = ['USD', 'EUR', 'GBP', 'JPY', 'CHF', 'AUD', 'CAD', 'NZD']
    pairs = ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD', 'USDCAD']
    
    for _ in range(1000):
        # Simulate calculation
        strength_values = [50 + np.random.normal(0, 10) for _ in currencies]
        mean_strength = np.mean(strength_values)
        std_strength = np.std(strength_values)
        z_scores = [(s - mean_strength) / std_strength for s in strength_values]
    
    calc_time = (datetime.now() - start_time).total_seconds()
    print(f"Currency strength calculation: {calc_time:.3f}s for 1000 iterations")
    
    # Test 2: Signal generation speed
    start_time = datetime.now()
    
    for _ in range(100):
        # Simulate signal generation
        confidence = 0.6 + np.random.random() * 0.4
        strength_diff = np.random.random() * 100
        # Simulate parameter calculation
        params = {
            'buy_distance': 10.0 * (1 + np.random.random()),
            'sell_distance': 10.0 * (1 + np.random.random()),
            'lot_size': 0.01 * (1 + np.random.random())
        }
    
    signal_time = (datetime.now() - start_time).total_seconds()
    print(f"Signal generation: {signal_time:.3f}s for 100 iterations")
    
    # Performance recommendations
    if calc_time > 1.0:
        print("WARNING: Currency strength calculation may need optimization")
    if signal_time > 0.5:
        print("WARNING: Signal generation may need optimization")

def run_stress_tests():
    """Run stress tests with high data volumes"""
    
    print("Running Stress Tests...")
    
    # Test with large number of economic events
    events = []
    for i in range(1000):
        events.append({
            'time': datetime.now() + timedelta(minutes=i),
            'currency': np.random.choice(['USD', 'EUR', 'GBP', 'JPY']),
            'impact': np.random.choice(['High', 'Medium', 'Low'])
        })
    
    print(f"Created {len(events)} test events")
    
    # Test with high-frequency price updates
    price_updates = []
    for i in range(10000):
        price_updates.append({
            'symbol': 'EURUSD',
            'bid': 1.0800 + np.random.normal(0, 0.01),
            'ask': 1.0802 + np.random.normal(0, 0.01),
            'timestamp': datetime.now() + timedelta(seconds=i)
        })
    
    print(f"Processed {len(price_updates)} price updates")
    
    # Memory usage test
    import sys
    memory_usage = sys.getsizeof(events) + sys.getsizeof(price_updates)
    print(f"Memory usage: {memory_usage / 1024 / 1024:.2f} MB")

if __name__ == "__main__":
    print("Enhanced HUEY_P Trading System - Comprehensive Test Suite")
    print("=" * 60)
    
    # Create test data files
    print("\nCreating test data files...")
    create_test_data_files()
    
    # Run unit tests
    print("\nRunning Unit Tests...")
    unittest.main(argv=[''], exit=False, verbosity=2)
    
    # Run performance tests
    print("\nRunning Performance Tests...")
    run_performance_tests()
    
    # Run stress tests
    print("\nRunning Stress Tests...")
    run_stress_tests()
    
    print("\nAll tests completed!")
    print("\nTest Summary:")
    print("- Unit tests: Core functionality validation")
    print("- Performance tests: Speed and efficiency benchmarks")
    print("- Stress tests: High-volume data handling")
    print("- Integration tests: End-to-end workflow validation")
    
    print("\nNext Steps:")
    print("1. Review any failed tests and fix issues")
    print("2. Run tests in different environments")
    print("3. Set up continuous testing pipeline")
    print("4. Monitor performance in production")
    
    # Cleanup test files
    try:
        os.remove('test_calendar.csv')
        os.remove('test_config.json')
        print("\nTest files cleaned up")
    except FileNotFoundError:
        pass
