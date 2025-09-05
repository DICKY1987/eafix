#!/usr/bin/env python3
"""
HUEY_P Trading System - Integration Test for Signal Flow
End-to-end testing of signal generation, communication, and processing
"""

import unittest
import asyncio
import sys
import time
import json
import socket
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

# Add source path for imports
sys.path.append(str(Path(__file__).parent.parent.parent / "Source" / "Python"))

try:
    from services.signal_service import SignalService, TradingSignal
    from communication_bridge import HUEY_P_CommunicationBridge, SignalBroadcaster
    from models.ml_models import HUEY_P_EnsembleModel, FeatureGenerator
    from database_manager import DatabaseManager
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure HUEY_P modules are available")
    sys.exit(1)

class TestSignalFlow(unittest.IsolatedAsyncioTestCase):
    """Integration tests for complete signal flow"""
    
    async def asyncSetUp(self):
        """Set up test fixtures"""
        self.signal_service = SignalService()
        self.comm_bridge = HUEY_P_CommunicationBridge()
        self.ensemble_model = HUEY_P_EnsembleModel()
        self.db_manager = DatabaseManager(":memory:")  # In-memory database for testing
        
        # Initialize test database
        await self.db_manager.initialize()
    
    async def test_complete_signal_flow(self):
        """Test signal generation -> bridge -> EA execution"""
        print("🔄 Testing complete signal flow...")
        
        # Mock socket connection for testing
        with patch('socket.socket') as mock_socket:
            mock_socket_instance = Mock()
            mock_socket.return_value = mock_socket_instance
            mock_socket_instance.connect.return_value = None
            mock_socket_instance.sendall.return_value = None
            
            # Step 1: Generate ML signal
            feature_gen = FeatureGenerator()
            features = await feature_gen.generate_features("EURUSD")
            self.assertIsNotNone(features)
            
            prediction = await self.ensemble_model.predict("EURUSD", features)
            self.assertIsNotNone(prediction)
            
            # Step 2: Create trading signal
            if prediction.direction != "HOLD" and prediction.confidence > 0.6:
                signal = TradingSignal(
                    signal_id=f"TEST_{int(time.time())}",
                    pair="EURUSD",
                    direction=prediction.direction,
                    confidence=prediction.confidence,
                    entry_price=features.close_price,
                    stop_loss=features.close_price * (0.99 if prediction.direction == "BUY" else 1.01),
                    take_profit=features.close_price * (1.02 if prediction.direction == "BUY" else 0.98),
                    signal_type="ML_ENHANCED",
                    timestamp=datetime.utcnow()
                )
                
                # Step 3: Send through communication bridge
                await self.comm_bridge.connect()
                result = await self.comm_bridge.send_signal(signal)
                
                # Verify signal was sent
                self.assertTrue(result)
                mock_socket_instance.sendall.assert_called()
                
                # Verify message format (should be CSV)
                sent_data = mock_socket_instance.sendall.call_args[0][0]
                self.assertIsInstance(sent_data, bytes)
                
                # Decode and verify CSV format
                message_content = sent_data[4:].decode('utf-8')  # Skip length header
                csv_parts = message_content.split(',')
                self.assertGreaterEqual(len(csv_parts), 8)  # Expected CSV fields
                self.assertEqual(csv_parts[0], "EURUSD")  # Pair
                self.assertIn(csv_parts[1], ["BUY", "SELL"])  # Direction
    
    async def test_error_recovery(self):
        """Test system recovery from failures"""
        print("🛠️ Testing error recovery...")
        
        # Test communication failure recovery
        with patch('socket.socket') as mock_socket:
            mock_socket_instance = Mock()
            mock_socket.return_value = mock_socket_instance
            mock_socket_instance.connect.side_effect = ConnectionRefusedError("Connection refused")
            
            # Should handle connection failure gracefully
            result = await self.comm_bridge.connect_with_retry()
            self.assertFalse(result)
            
            # Check circuit breaker activation
            self.assertGreater(self.comm_bridge.circuit_breaker_failures, 0)
            self.assertTrue(self.comm_bridge.is_circuit_breaker_open())
    
    async def test_database_integration(self):
        """Test database integration in signal flow"""
        print("💾 Testing database integration...")
        
        # Create test signal data
        signal_data = {
            'signal_id': 'TEST_DB_001',
            'pair': 'EURUSD',
            'direction': 'BUY',
            'confidence': 0.75,
            'entry_price': 1.0500,
            'stop_loss': 1.0450,
            'take_profit': 1.0600,
            'signal_type': 'ML_ENHANCED',
            'ml_enhanced': True,
            'model_name': 'HUEY_P_Ensemble',
            'features_used': ['rsi', 'macd', 'sentiment']
        }
        
        # Insert signal into database
        signal_id = await self.db_manager.insert_trading_signal(signal_data)
        self.assertEqual(signal_id, 'TEST_DB_001')
        
        # Retrieve and verify
        active_signals = await self.db_manager.get_active_signals('EURUSD')
        self.assertGreater(len(active_signals), 0)
        
        retrieved_signal = active_signals[0]
        self.assertEqual(retrieved_signal['signal_id'], 'TEST_DB_001')
        self.assertEqual(retrieved_signal['pair'], 'EURUSD')
    
    async def test_concurrent_signal_processing(self):
        """Test concurrent processing of multiple signals"""
        print("⚡ Testing concurrent signal processing...")
        
        pairs = ["EURUSD", "GBPUSD", "USDJPY"]
        
        with patch('socket.socket') as mock_socket:
            mock_socket_instance = Mock()
            mock_socket.return_value = mock_socket_instance
            mock_socket_instance.connect.return_value = None
            mock_socket_instance.sendall.return_value = None
            
            await self.comm_bridge.connect()
            
            # Create test signals
            signals = []
            for i, pair in enumerate(pairs):
                signal = TradingSignal(
                    signal_id=f"CONCURRENT_{i:03d}",
                    pair=pair,
                    direction="BUY",
                    confidence=0.75,
                    entry_price=1.0000 + i * 0.0100,
                    stop_loss=0.9950 + i * 0.0100,
                    take_profit=1.0200 + i * 0.0100,
                    signal_type="ML_ENHANCED",
                    timestamp=datetime.utcnow()
                )
                signals.append(signal)
            
            # Send signals concurrently
            tasks = [self.comm_bridge.send_signal(signal) for signal in signals]
            results = await asyncio.gather(*tasks)
            
            # Verify all signals were sent
            self.assertEqual(len(results), len(pairs))
            self.assertTrue(all(results))
            
            # Verify send_all was called for each signal
            self.assertEqual(mock_socket_instance.sendall.call_count, len(pairs))
    
    async def test_signal_validation_flow(self):
        """Test signal validation throughout the flow"""
        print("✅ Testing signal validation flow...")
        
        # Test invalid signal (missing required fields)
        invalid_signal_data = {
            'signal_id': 'INVALID_001',
            'pair': '',  # Empty pair
            'direction': 'INVALID_DIRECTION',
            'confidence': 1.5,  # Invalid confidence > 1.0
            'entry_price': -1.0,  # Invalid negative price
            'stop_loss': 1.0450,
            'take_profit': 1.0600,
        }
        
        # Should fail database insertion due to validation
        with self.assertRaises(Exception):
            await self.db_manager.insert_trading_signal(invalid_signal_data)
        
        # Test valid signal passes validation
        valid_signal_data = {
            'signal_id': 'VALID_001',
            'pair': 'EURUSD',
            'direction': 'BUY',
            'confidence': 0.75,
            'entry_price': 1.0500,
            'stop_loss': 1.0450,
            'take_profit': 1.0600,
            'signal_type': 'ML_ENHANCED',
            'ml_enhanced': True,
            'model_name': 'HUEY_P_Ensemble',
            'features_used': ['rsi', 'macd']
        }
        
        # Should succeed
        signal_id = await self.db_manager.insert_trading_signal(valid_signal_data)
        self.assertEqual(signal_id, 'VALID_001')
    
    async def test_communication_protocol_compliance(self):
        """Test CSV communication protocol compliance"""
        print("📋 Testing CSV protocol compliance...")
        
        with patch('socket.socket') as mock_socket:
            mock_socket_instance = Mock()
            mock_socket.return_value = mock_socket_instance
            mock_socket_instance.connect.return_value = None
            mock_socket_instance.sendall.return_value = None
            
            await self.comm_bridge.connect()
            
            # Create test signal
            signal = TradingSignal(
                signal_id="CSV_TEST_001",
                pair="EURUSD",
                direction="BUY",
                confidence=0.75,
                entry_price=1.0500,
                stop_loss=1.0450,
                take_profit=1.0600,
                signal_type="ML_ENHANCED",
                timestamp=datetime.utcnow()
            )
            
            # Send signal
            await self.comm_bridge.send_signal(signal)
            
            # Verify CSV format
            sent_data = mock_socket_instance.sendall.call_args[0][0]
            
            # Should have 4-byte length header + CSV data
            self.assertGreaterEqual(len(sent_data), 4)
            
            # Extract CSV content
            csv_content = sent_data[4:].decode('utf-8')
            csv_fields = csv_content.split(',')
            
            # Verify CSV structure: PAIR,DIRECTION,CONFIDENCE,ENTRY,SL,TP,TYPE,TIMESTAMP
            self.assertGreaterEqual(len(csv_fields), 8)
            self.assertEqual(csv_fields[0], "EURUSD")  # Pair
            self.assertEqual(csv_fields[1], "BUY")     # Direction
            self.assertEqual(float(csv_fields[2]), 0.75)  # Confidence
            self.assertEqual(float(csv_fields[3]), 1.0500)  # Entry price
    
    async def test_system_health_during_signal_flow(self):
        """Test system health monitoring during signal processing"""
        print("🏥 Testing system health monitoring...")
        
        # This would integrate with the health monitor
        # For now, test basic health metrics
        
        start_time = time.time()
        
        # Generate multiple signals to test system load
        signals = []
        for i in range(10):
            feature_gen = FeatureGenerator()
            features = await feature_gen.generate_features("EURUSD")
            
            if features:
                prediction = await self.ensemble_model.predict("EURUSD", features)
                signals.append(prediction)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Verify reasonable processing time (should be < 10 seconds for 10 signals)
        self.assertLess(processing_time, 10.0)
        
        # Verify signals were generated
        self.assertGreater(len(signals), 0)
        
        print(f"  Processed {len(signals)} signals in {processing_time:.2f}s")

def run_integration_tests():
    """Run all integration tests"""
    print("🔧 Running HUEY_P Signal Flow Integration Tests")
    print("=" * 60)
    
    # Run the test suite
    unittest.main(verbosity=2, exit=False)

if __name__ == "__main__":
    run_integration_tests()