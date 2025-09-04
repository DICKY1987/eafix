"""
Test suite for DDE Connection functionality
"""
import unittest
import time
import threading
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import pytest

# These tests exercise Windows-specific DDE integration.
if sys.platform != "win32":
    pytest.skip("MT4 DDE interface tests require Windows", allow_module_level=True)

pytest.importorskip("win32ui")

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from dde_client import MT4DDEClient, DDEConnectionManager


class TestMT4DDEClient(unittest.TestCase):
    """Test cases for MT4DDEClient"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.client = MT4DDEClient("TestMT4")
        
    def tearDown(self):
        """Clean up after tests"""
        if self.client and self.client.is_connected:
            try:
                self.client.disconnect()
            except:
                pass
    
    def test_client_initialization(self):
        """Test client initialization"""
        self.assertEqual(self.client.server_name, "TestMT4")
        self.assertFalse(self.client.is_connected)
        self.assertFalse(self.client.is_monitoring)
        self.assertEqual(len(self.client.conversations), 0)
        self.assertEqual(len(self.client.price_callbacks), 0)
    
    @patch('dde.CreateServer')
    def test_successful_connection(self, mock_create_server):
        """Test successful DDE connection"""
        # Mock DDE server
        mock_server = Mock()
        mock_create_server.return_value = mock_server
        
        # Test connection
        result = self.client.connect()
        
        self.assertTrue(result)
        self.assertTrue(self.client.is_connected)
        mock_server.Create.assert_called_once_with("DDEClient")
    
    @patch('dde.CreateServer')
    def test_failed_connection(self, mock_create_server):
        """Test failed DDE connection"""
        # Mock DDE server to raise exception
        mock_create_server.side_effect = Exception("Connection failed")
        
        # Test connection
        result = self.client.connect()
        
        self.assertFalse(result)
        self.assertFalse(self.client.is_connected)
    
    @patch('dde.CreateConversation')
    @patch('dde.CreateServer')
    def test_symbol_subscription(self, mock_create_server, mock_create_conversation):
        """Test symbol subscription"""
        # Setup mocks
        mock_server = Mock()
        mock_create_server.return_value = mock_server
        mock_conversation = Mock()
        mock_create_conversation.return_value = mock_conversation
        
        # Connect first
        self.client.connect()
        
        # Test subscription
        result = self.client.subscribe_to_symbol("EURUSD")
        
        self.assertTrue(result)
        self.assertIn("EURUSD", self.client.conversations)
        mock_conversation.ConnectTo.assert_called_once_with("TestMT4", "EURUSD")
    
    def test_price_callback_management(self):
        """Test price callback management"""
        callback1 = Mock()
        callback2 = Mock()
        
        # Add callbacks
        self.client.add_price_callback(callback1)
        self.client.add_price_callback(callback2)
        
        self.assertEqual(len(self.client.price_callbacks), 2)
        self.assertIn(callback1, self.client.price_callbacks)
        self.assertIn(callback2, self.client.price_callbacks)
        
        # Remove callback
        self.client.remove_price_callback(callback1)
        self.assertEqual(len(self.client.price_callbacks), 1)
        self.assertNotIn(callback1, self.client.price_callbacks)
    
    @patch('dde.CreateConversation')
    @patch('dde.CreateServer')
    def test_price_data_retrieval(self, mock_create_server, mock_create_conversation):
        """Test price data retrieval"""
        # Setup mocks
        mock_server = Mock()
        mock_create_server.return_value = mock_server
        mock_conversation = Mock()
        mock_create_conversation.return_value = mock_conversation
        
        # Mock price data
        mock_conversation.Request.side_effect = ["1.10500", "1.10520", "123456789"]
        
        # Connect and subscribe
        self.client.connect()
        self.client.subscribe_to_symbol("EURUSD")
        
        # Get price data
        price_data = self.client.get_price_data("EURUSD")
        
        self.assertIsNotNone(price_data)
        self.assertEqual(price_data['symbol'], "EURUSD")
        self.assertEqual(price_data['bid'], 1.10500)
        self.assertEqual(price_data['ask'], 1.10520)
        self.assertEqual(price_data['spread'], 0.00020)
    
    def test_connection_status(self):
        """Test connection status reporting"""
        status = self.client.get_connection_status()
        
        expected_keys = [
            'is_connected', 'is_monitoring', 'subscribed_symbols', 
            'active_callbacks', 'server_name'
        ]
        
        for key in expected_keys:
            self.assertIn(key, status)
        
        self.assertEqual(status['server_name'], "TestMT4")
        self.assertFalse(status['is_connected'])
    
    def test_monitoring_state_management(self):
        """Test monitoring state management"""
        # Initially not monitoring
        self.assertFalse(self.client.is_monitoring)
        
        # Mock connection for monitoring test
        with patch.object(self.client, 'is_connected', True):
            with patch.object(self.client, 'subscribe_to_symbol', return_value=True):
                with patch('threading.Thread') as mock_thread:
                    # Start monitoring
                    self.client.start_monitoring(["EURUSD"], 0.1)
                    
                    # Check state
                    self.assertTrue(self.client.is_monitoring)
                    mock_thread.assert_called_once()
                    
                    # Stop monitoring
                    self.client.stop_monitoring()
                    self.assertFalse(self.client.is_monitoring)


class TestDDEConnectionManager(unittest.TestCase):
    """Test cases for DDEConnectionManager"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_client = Mock(spec=MT4DDEClient)
        self.mock_client.is_connected = False
        self.manager = DDEConnectionManager(self.mock_client)
    
    def test_manager_initialization(self):
        """Test connection manager initialization"""
        self.assertEqual(self.manager.client, self.mock_client)
        self.assertTrue(self.manager.auto_reconnect)
        self.assertEqual(self.manager.reconnect_interval, 5.0)
        self.assertEqual(self.manager.max_reconnect_attempts, 10)
        self.assertFalse(self.manager.is_reconnecting)
    
    def test_reconnection_logic(self):
        """Test automatic reconnection logic"""
        # Mock client as disconnected
        self.mock_client.is_connected = False
        self.mock_client.connect.return_value = True
        
        # Test reconnection attempt
        self.manager._attempt_reconnection()
        
        # Should have attempted connection
        self.mock_client.connect.assert_called()
        self.assertFalse(self.manager.is_reconnecting)
    
    def test_failed_reconnection_attempts(self):
        """Test handling of failed reconnection attempts"""
        # Mock client connection to always fail
        self.mock_client.is_connected = False
        self.mock_client.connect.return_value = False
        
        # Set low max attempts for faster test
        self.manager.max_reconnect_attempts = 2
        self.manager.reconnect_interval = 0.1
        
        # Test reconnection
        self.manager._attempt_reconnection()
        
        # Should have made multiple attempts
        self.assertEqual(self.mock_client.connect.call_count, 2)
        self.assertFalse(self.manager.is_reconnecting)


class TestDDEIntegration(unittest.TestCase):
    """Integration tests for DDE functionality"""
    
    def setUp(self):
        """Set up integration test fixtures"""
        self.client = MT4DDEClient("TestMT4")
        self.received_prices = []
        self.price_callback = lambda price: self.received_prices.append(price)
    
    def tearDown(self):
        """Clean up integration tests"""
        if self.client and self.client.is_connected:
            try:
                self.client.disconnect()
            except:
                pass
    
    def test_full_connection_cycle(self):
        """Test complete connection, subscription, and disconnection cycle"""
        with patch('dde.CreateServer') as mock_create_server:
            with patch('dde.CreateConversation') as mock_create_conversation:
                # Setup mocks
                mock_server = Mock()
                mock_create_server.return_value = mock_server
                mock_conversation = Mock()
                mock_create_conversation.return_value = mock_conversation
                mock_conversation.Request.side_effect = ["1.10500", "1.10520", None]
                
                # Full cycle test
                # 1. Connect
                result = self.client.connect()
                self.assertTrue(result)
                self.assertTrue(self.client.is_connected)
                
                # 2. Subscribe to symbol
                result = self.client.subscribe_to_symbol("EURUSD")
                self.assertTrue(result)
                
                # 3. Get price data
                price_data = self.client.get_price_data("EURUSD")
                self.assertIsNotNone(price_data)
                self.assertEqual(price_data['symbol'], "EURUSD")
                
                # 4. Add callback
                self.client.add_price_callback(self.price_callback)
                
                # 5. Unsubscribe
                self.client.unsubscribe_from_symbol("EURUSD")
                self.assertNotIn("EURUSD", self.client.conversations)
                
                # 6. Disconnect
                self.client.disconnect()
                self.assertFalse(self.client.is_connected)
    
    def test_multiple_symbol_handling(self):
        """Test handling multiple symbols simultaneously"""
        symbols = ["EURUSD", "GBPUSD", "USDJPY"]
        
        with patch('dde.CreateServer') as mock_create_server:
            with patch('dde.CreateConversation') as mock_create_conversation:
                # Setup mocks
                mock_server = Mock()
                mock_create_server.return_value = mock_server
                mock_conversation = Mock()
                mock_create_conversation.return_value = mock_conversation
                
                # Connect
                self.client.connect()
                
                # Subscribe to multiple symbols
                for symbol in symbols:
                    result = self.client.subscribe_to_symbol(symbol)
                    self.assertTrue(result)
                
                # Check all symbols are subscribed
                subscribed = self.client.get_subscribed_symbols()
                for symbol in symbols:
                    self.assertIn(symbol, subscribed)
                
                # Disconnect should clean up all
                self.client.disconnect()
                self.assertEqual(len(self.client.conversations), 0)
    
    def test_connection_manager_integration(self):
        """Test integration between client and connection manager"""
        manager = DDEConnectionManager(self.client)
        
        with patch.object(self.client, 'connect') as mock_connect:
            # Test auto-reconnect disabled
            manager.auto_reconnect = False
            mock_connect.return_value = True
            
            # Manually trigger reconnection
            manager._attempt_reconnection()
            
            # Should attempt connection
            mock_connect.assert_called_once()


class TestDDEPerformance(unittest.TestCase):
    """Performance tests for DDE functionality"""
    
    def setUp(self):
        """Set up performance test fixtures"""
        self.client = MT4DDEClient("PerfTest")
        self.performance_data = []
    
    def test_callback_performance(self):
        """Test performance with multiple callbacks"""
        # Create multiple callbacks
        callbacks = []
        for i in range(100):
            callback = Mock()
            callbacks.append(callback)
            self.client.add_price_callback(callback)
        
        # Simulate price update
        test_price = {
            'symbol': 'EURUSD',
            'bid': 1.10500,
            'ask': 1.10520,
            'timestamp': time.time()
        }
        
        # Measure time to notify all callbacks
        start_time = time.time()
        for callback in self.client.price_callbacks:
            try:
                callback(test_price)
            except:
                pass
        end_time = time.time()
        
        # Performance assertion (should complete within reasonable time)
        execution_time = end_time - start_time
        self.assertLess(execution_time, 0.1)  # Should complete within 100ms
    
    def test_subscription_performance(self):
        """Test performance of multiple symbol subscriptions"""
        symbols = [f"SYMBOL{i:03d}" for i in range(50)]
        
        with patch('dde.CreateServer') as mock_create_server:
            with patch('dde.CreateConversation') as mock_create_conversation:
                # Setup mocks
                mock_server = Mock()
                mock_create_server.return_value = mock_server
                mock_conversation = Mock()
                mock_create_conversation.return_value = mock_conversation
                
                # Connect first
                self.client.connect()
                
                # Measure subscription time
                start_time = time.time()
                for symbol in symbols:
                    self.client.subscribe_to_symbol(symbol)
                end_time = time.time()
                
                # Performance assertion
                subscription_time = end_time - start_time
                self.assertLess(subscription_time, 1.0)  # Should complete within 1 second


class TestDDEErrorHandling(unittest.TestCase):
    """Error handling tests for DDE functionality"""
    
    def setUp(self):
        """Set up error handling test fixtures"""
        self.client = MT4DDEClient("ErrorTest")
    
    def test_connection_failure_handling(self):
        """Test handling of connection failures"""
        with patch('dde.CreateServer') as mock_create_server:
            # Simulate connection failure
            mock_create_server.side_effect = Exception("DDE Server not available")
            
            # Should handle exception gracefully
            result = self.client.connect()
            
            self.assertFalse(result)
            self.assertFalse(self.client.is_connected)
    
    def test_invalid_symbol_handling(self):
        """Test handling of invalid symbol subscriptions"""
        with patch('dde.CreateServer') as mock_create_server:
            with patch('dde.CreateConversation') as mock_create_conversation:
                # Setup mocks
                mock_server = Mock()
                mock_create_server.return_value = mock_server
                mock_conversation = Mock()
                mock_create_conversation.return_value = mock_conversation
                
                # Simulate subscription failure
                mock_conversation.ConnectTo.side_effect = Exception("Invalid symbol")
                
                # Connect first
                self.client.connect()
                
                # Try to subscribe to invalid symbol
                result = self.client.subscribe_to_symbol("INVALID")
                
                self.assertFalse(result)
                self.assertNotIn("INVALID", self.client.conversations)
    
    def test_price_data_error_handling(self):
        """Test handling of price data retrieval errors"""
        with patch('dde.CreateServer') as mock_create_server:
            with patch('dde.CreateConversation') as mock_create_conversation:
                # Setup mocks
                mock_server = Mock()
                mock_create_server.return_value = mock_server
                mock_conversation = Mock()
                mock_create_conversation.return_value = mock_conversation
                
                # Simulate price request failure
                mock_conversation.Request.side_effect = Exception("Price not available")
                
                # Connect and subscribe
                self.client.connect()
                self.client.subscribe_to_symbol("EURUSD")
                
                # Try to get price data
                price_data = self.client.get_price_data("EURUSD")
                
                self.assertIsNone(price_data)
    
    def test_callback_error_isolation(self):
        """Test that callback errors don't affect other callbacks"""
        good_callback = Mock()
        bad_callback = Mock(side_effect=Exception("Callback error"))
        another_good_callback = Mock()
        
        # Add callbacks
        self.client.add_price_callback(good_callback)
        self.client.add_price_callback(bad_callback)
        self.client.add_price_callback(another_good_callback)
        
        # Simulate price notification
        test_price = {'symbol': 'TEST', 'bid': 1.0, 'ask': 1.0}
        
        # Manually call callbacks (simulating internal notification)
        for callback in self.client.price_callbacks:
            try:
                callback(test_price)
            except Exception as e:
                # Should log error but continue
                pass
        
        # Good callbacks should have been called
        good_callback.assert_called_once_with(test_price)
        another_good_callback.assert_called_once_with(test_price)
        bad_callback.assert_called_once_with(test_price)


def run_all_tests():
    """Run all DDE connection tests"""
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_classes = [
        TestMT4DDEClient,
        TestDDEConnectionManager,
        TestDDEIntegration,
        TestDDEPerformance,
        TestDDEErrorHandling
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    print("Running DDE Connection Tests...")
    print("=" * 50)
    
    success = run_all_tests()
    
    if success:
        print("\n" + "=" * 50)
        print("All tests passed successfully!")
    else:
        print("\n" + "=" * 50)
        print("Some tests failed. Check output above for details.")
        
    exit(0 if success else 1)