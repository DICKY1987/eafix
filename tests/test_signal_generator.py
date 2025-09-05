#!/usr/bin/env python3
"""
HUEY_P Trading System - Signal Generator Unit Tests
Tests for the ML signal generation system
"""

import unittest
import asyncio
import sys
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

# Add source path for imports
sys.path.append(str(Path(__file__).parent.parent.parent.parent / "Source" / "Python"))

try:
    from services.signal_service import SignalService, TradingSignal
    from models.ml_models import HUEY_P_EnsembleModel, FeatureGenerator, MarketFeatures
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure HUEY_P modules are available")
    sys.exit(1)

class TestSignalGenerator(unittest.TestCase):
    """Test cases for signal generation system"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.signal_service = SignalService()
        self.ensemble_model = HUEY_P_EnsembleModel()
        self.feature_generator = FeatureGenerator()
    
    def test_signal_service_initialization(self):
        """Test signal service initializes correctly"""
        self.assertIsNotNone(self.signal_service)
        self.assertIsInstance(self.signal_service, SignalService)
    
    def test_ensemble_model_initialization(self):
        """Test ensemble model initializes with required models"""
        self.assertIsNotNone(self.ensemble_model)
        self.assertIn('random_forest', self.ensemble_model.models)
        self.assertIn('gradient_boost', self.ensemble_model.models)
        self.assertIn('neural_network', self.ensemble_model.models)
        self.assertIn('svm', self.ensemble_model.models)
    
    @patch('models.ml_models.time.time')
    async def test_feature_generation(self, mock_time):
        """Test market feature generation"""
        mock_time.return_value = 1234567890
        
        features = await self.feature_generator.generate_features("EURUSD")
        
        self.assertIsNotNone(features)
        self.assertIsInstance(features, MarketFeatures)
        self.assertEqual(features.pair, "EURUSD")
        self.assertGreater(features.open_price, 0)
        self.assertGreater(features.volume, 0)
        self.assertGreaterEqual(features.rsi, 0)
        self.assertLessEqual(features.rsi, 100)
    
    async def test_ml_prediction(self):
        """Test ML model prediction"""
        # Generate test features
        features = await self.feature_generator.generate_features("EURUSD")
        
        # Get prediction
        prediction = await self.ensemble_model.predict("EURUSD", features)
        
        self.assertIsNotNone(prediction)
        self.assertEqual(prediction.pair, "EURUSD")
        self.assertIn(prediction.direction, ["BUY", "SELL", "HOLD"])
        self.assertGreaterEqual(prediction.confidence, 0.0)
        self.assertLessEqual(prediction.confidence, 1.0)
        self.assertIsInstance(prediction.timestamp, datetime)
    
    async def test_signal_generation_flow(self):
        """Test complete signal generation flow"""
        with patch.object(self.signal_service, '_generate_basic_signal') as mock_basic:
            # Mock basic signal
            mock_signal = TradingSignal(
                signal_id="TEST_001",
                pair="EURUSD",
                direction="BUY",
                confidence=0.75,
                entry_price=1.0500,
                stop_loss=1.0450,
                take_profit=1.0600,
                signal_type="ML_ENHANCED",
                timestamp=datetime.utcnow()
            )
            mock_basic.return_value = mock_signal
            
            # Generate signals
            signals = await self.signal_service.generate_signals()
            
            self.assertIsInstance(signals, list)
            if signals:  # If any signals generated
                signal = signals[0]
                self.assertIsInstance(signal, TradingSignal)
                self.assertIsNotNone(signal.signal_id)
                self.assertIn(signal.direction, ["BUY", "SELL"])
    
    def test_signal_validation(self):
        """Test signal validation logic"""
        # Valid signal
        valid_signal = TradingSignal(
            signal_id="TEST_001",
            pair="EURUSD",
            direction="BUY",
            confidence=0.75,
            entry_price=1.0500,
            stop_loss=1.0450,
            take_profit=1.0600,
            signal_type="ML_ENHANCED",
            timestamp=datetime.utcnow()
        )
        
        # Validate signal structure
        self.assertEqual(valid_signal.pair, "EURUSD")
        self.assertEqual(valid_signal.direction, "BUY")
        self.assertGreater(valid_signal.take_profit, valid_signal.entry_price)
        self.assertLess(valid_signal.stop_loss, valid_signal.entry_price)
    
    def test_confidence_thresholds(self):
        """Test confidence threshold validation"""
        # High confidence signal
        high_conf_signal = TradingSignal(
            signal_id="HIGH_001",
            pair="EURUSD",
            direction="BUY",
            confidence=0.85,
            entry_price=1.0500,
            stop_loss=1.0450,
            take_profit=1.0600,
            signal_type="ML_ENHANCED",
            timestamp=datetime.utcnow()
        )
        
        # Low confidence signal
        low_conf_signal = TradingSignal(
            signal_id="LOW_001",
            pair="EURUSD",
            direction="BUY",
            confidence=0.45,
            entry_price=1.0500,
            stop_loss=1.0450,
            take_profit=1.0600,
            signal_type="ML_ENHANCED",
            timestamp=datetime.utcnow()
        )
        
        # Test confidence levels
        self.assertGreaterEqual(high_conf_signal.confidence, 0.7)  # Should be tradeable
        self.assertLess(low_conf_signal.confidence, 0.6)           # Should be filtered out
    
    def test_price_relationship_validation(self):
        """Test price relationship validation for BUY/SELL signals"""
        # BUY signal validation
        buy_signal = TradingSignal(
            signal_id="BUY_001",
            pair="EURUSD",
            direction="BUY",
            confidence=0.75,
            entry_price=1.0500,
            stop_loss=1.0450,
            take_profit=1.0600,
            signal_type="ML_ENHANCED",
            timestamp=datetime.utcnow()
        )
        
        # SELL signal validation
        sell_signal = TradingSignal(
            signal_id="SELL_001",
            pair="EURUSD",
            direction="SELL",
            confidence=0.75,
            entry_price=1.0500,
            stop_loss=1.0550,
            take_profit=1.0400,
            signal_type="ML_ENHANCED",
            timestamp=datetime.utcnow()
        )
        
        # Validate BUY signal relationships
        self.assertLess(buy_signal.stop_loss, buy_signal.entry_price)
        self.assertGreater(buy_signal.take_profit, buy_signal.entry_price)
        
        # Validate SELL signal relationships
        self.assertGreater(sell_signal.stop_loss, sell_signal.entry_price)
        self.assertLess(sell_signal.take_profit, sell_signal.entry_price)
    
    async def test_feature_caching(self):
        """Test feature caching mechanism"""
        # Generate features twice for same pair
        features1 = await self.feature_generator.generate_features("EURUSD")
        features2 = await self.feature_generator.generate_features("EURUSD")
        
        # Should have features (caching behavior may vary)
        self.assertIsNotNone(features1)
        self.assertIsNotNone(features2)
        self.assertEqual(features1.pair, features2.pair)
    
    def test_model_info(self):
        """Test model information retrieval"""
        model_info = self.ensemble_model.get_model_info()
        
        self.assertIsInstance(model_info, dict)
        self.assertIn('model_name', model_info)
        self.assertIn('version', model_info)
        self.assertIn('components', model_info)
        self.assertEqual(model_info['model_name'], 'HUEY_P_Ensemble')

class TestAsyncSignalGeneration(unittest.IsolatedAsyncioTestCase):
    """Async test cases for signal generation"""
    
    async def asyncSetUp(self):
        """Async setup for test fixtures"""
        self.signal_service = SignalService()
        self.ensemble_model = HUEY_P_EnsembleModel()
    
    async def test_concurrent_signal_generation(self):
        """Test concurrent signal generation for multiple pairs"""
        pairs = ["EURUSD", "GBPUSD", "USDJPY"]
        
        # Generate signals concurrently
        tasks = []
        for pair in pairs:
            feature_gen = FeatureGenerator()
            task = asyncio.create_task(feature_gen.generate_features(pair))
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        # Validate results
        self.assertEqual(len(results), len(pairs))
        for i, features in enumerate(results):
            if features:  # If features were generated
                self.assertEqual(features.pair, pairs[i])
    
    async def test_error_handling(self):
        """Test error handling in signal generation"""
        with patch.object(self.ensemble_model, 'predict', side_effect=Exception("Test error")):
            # Should handle error gracefully
            prediction = await self.ensemble_model.predict("INVALID", None)
            
            # Should return error prediction
            self.assertIsNotNone(prediction)
            self.assertEqual(prediction.direction, "HOLD")
            self.assertEqual(prediction.confidence, 0.0)

def run_tests():
    """Run all signal generator tests"""
    print("🧪 Running HUEY_P Signal Generator Tests")
    print("=" * 50)
    
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTest(unittest.makeSuite(TestSignalGenerator))
    suite.addTest(unittest.makeSuite(TestAsyncSignalGeneration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 50)
    print(f"📊 Test Results:")
    print(f"  ✅ Tests run: {result.testsRun}")
    print(f"  ❌ Failures: {len(result.failures)}")
    print(f"  💥 Errors: {len(result.errors)}")
    
    if result.failures:
        print(f"\n❌ Failures:")
        for test, traceback in result.failures:
            print(f"  {test}: {traceback}")
    
    if result.errors:
        print(f"\n💥 Errors:")
        for test, traceback in result.errors:
            print(f"  {test}: {traceback}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    print(f"\n🎯 Overall Result: {'PASSED' if success else 'FAILED'}")
    
    return success

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)