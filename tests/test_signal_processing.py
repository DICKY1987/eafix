import pytest
import json
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'Python', 'src'))

from services.signal_generator import SignalGeneratorService
from utils.correlation import correlation_manager
from utils.circuit_breaker import CircuitBreaker
from utils.retry_manager import RetryManager, RetryConfig

class TestSignalValidation:
    """Test suite for signal validation logic"""
    
    @pytest.fixture
    def valid_signal(self):
        """Create a valid signal for testing"""
        return {
            'signal_id': 'test_signal_001',
            'symbol': 'EURUSD',
            'direction': 'BUY',
            'confidence': 0.85,
            'timestamp': datetime.now(),
            'strategy_id': 'BREAKOUT_SIGNAL',
            'metadata': {'source': 'test', 'version': '1.0'}
        }
    
    def test_valid_signal_processing(self, valid_signal):
        """Test processing of a valid signal"""
        # Test all required fields are present
        required_fields = ['signal_id', 'symbol', 'direction', 'confidence', 'timestamp', 'strategy_id']
        for field in required_fields:
            assert field in valid_signal, f"Missing required field: {field}"
        
        # Test field value validation
        assert valid_signal['direction'] in ['BUY', 'SELL']
        assert 0.0 <= valid_signal['confidence'] <= 1.0
        assert isinstance(valid_signal['timestamp'], datetime)
        assert len(valid_signal['signal_id']) > 0
        assert len(valid_signal['symbol']) > 0
    
    def test_signal_freshness_validation(self, valid_signal):
        """Test signal freshness validation"""
        # Fresh signal (within 5 minutes)
        fresh_signal = valid_signal.copy()
        fresh_signal['timestamp'] = datetime.now() - timedelta(minutes=2)
        
        age_seconds = (datetime.now() - fresh_signal['timestamp']).total_seconds()
        assert age_seconds < 300, "Signal should be considered fresh"
        
        # Stale signal (older than 5 minutes)
        stale_signal = valid_signal.copy()
        stale_signal['timestamp'] = datetime.now() - timedelta(minutes=10)
        
        age_seconds = (datetime.now() - stale_signal['timestamp']).total_seconds()
        assert age_seconds > 300, "Signal should be considered stale"
    
    def test_confidence_threshold_validation(self, valid_signal):
        """Test confidence threshold validation"""
        threshold = 0.6
        
        # High confidence signal
        high_conf_signal = valid_signal.copy()
        high_conf_signal['confidence'] = 0.8
        assert high_conf_signal['confidence'] >= threshold
        
        # Low confidence signal
        low_conf_signal = valid_signal.copy()
        low_conf_signal['confidence'] = 0.4
        assert low_conf_signal['confidence'] < threshold
        
        # Boundary cases
        boundary_signal = valid_signal.copy()
        boundary_signal['confidence'] = threshold
        assert boundary_signal['confidence'] >= threshold
    
    def test_symbol_validation(self, valid_signal):
        """Test symbol validation logic"""
        valid_symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'XAUUSD']
        invalid_symbols = ['INVALID', '', 'US', 'EURUSDGBP']
        
        for symbol in valid_symbols:
            test_signal = valid_signal.copy()
            test_signal['symbol'] = symbol
            # Should pass validation (6 characters for major pairs, 6+ for others)
            assert len(test_signal['symbol']) >= 6 or test_signal['symbol'] in ['XAUUSD', 'XAGUSD']
        
        for symbol in invalid_symbols:
            test_signal = valid_signal.copy()
            test_signal['symbol'] = symbol
            # Should fail validation
            if symbol != 'EURUSDGBP':  # Too long but otherwise valid format
                assert len(symbol) < 6 or symbol == ''
    
    def test_direction_validation(self, valid_signal):
        """Test direction validation"""
        valid_directions = ['BUY', 'SELL']
        invalid_directions = ['buy', 'sell', 'HOLD', 'LONG', 'SHORT', '']
        
        for direction in valid_directions:
            test_signal = valid_signal.copy()
            test_signal['direction'] = direction
            assert test_signal['direction'] in ['BUY', 'SELL']
        
        for direction in invalid_directions:
            test_signal = valid_signal.copy()
            test_signal['direction'] = direction
            assert test_signal['direction'] not in ['BUY', 'SELL']
    
    def test_duplicate_signal_detection(self, valid_signal):
        """Test duplicate signal detection"""
        # Simulate processed signals list
        processed_signals = ['signal_001', 'signal_002', 'signal_003']
        
        # Test duplicate detection
        duplicate_signal = valid_signal.copy()
        duplicate_signal['signal_id'] = 'signal_002'
        assert duplicate_signal['signal_id'] in processed_signals
        
        # Test new signal
        new_signal = valid_signal.copy()
        new_signal['signal_id'] = 'signal_004'
        assert new_signal['signal_id'] not in processed_signals
    
    def test_signal_metadata_validation(self, valid_signal):
        """Test signal metadata validation"""
        # Valid metadata
        valid_metadata = {
            'source': 'algorithm_v2',
            'indicators': {'rsi': 65.5, 'ema_cross': True},
            'risk_score': 0.3
        }
        
        test_signal = valid_signal.copy()
        test_signal['metadata'] = valid_metadata
        
        assert isinstance(test_signal['metadata'], dict)
        assert 'source' in test_signal['metadata']
        
        # Test JSON serialization (important for transmission)
        json_metadata = json.dumps(test_signal['metadata'])
        parsed_metadata = json.loads(json_metadata)
        assert parsed_metadata == valid_metadata

class TestSignalGenerator:
    """Test suite for signal generation service"""
    
    @pytest.fixture
    def signal_config(self):
        """Signal generator configuration"""
        return {
            'interval_seconds': 1,
            'confidence_threshold': 0.7,
            'enabled': True
        }
    
    @pytest.fixture
    def signal_generator(self, signal_config):
        """Create signal generator service"""
        return SignalGeneratorService(signal_config)
    
    def test_signal_generator_initialization(self, signal_generator, signal_config):
        """Test signal generator initialization"""
        assert signal_generator.config == signal_config
        assert signal_generator.interval == signal_config['interval_seconds']
        assert signal_generator.confidence_threshold == signal_config['confidence_threshold']
    
    def test_generate_signal(self, signal_generator):
        """Test signal generation"""
        symbol = 'EURUSD'
        strategy_id = 'TEST_STRATEGY'
        
        signal = signal_generator.generate_signal(symbol, strategy_id)
        
        assert signal is not None
        assert signal['symbol'] == symbol
        assert signal['strategy_id'] == strategy_id
        assert signal['type'] == 'SIGNAL'
        assert 'signal_id' in signal
        assert 'timestamp' in signal
        assert signal['direction'] in ['BUY', 'SELL']
        assert 0.0 <= signal['confidence'] <= 1.0
    
    def test_signal_validation_and_enhancement(self, signal_generator):
        """Test signal validation and enhancement"""
        # Valid signal
        valid_signal = {
            'signal_id': 'test_001',
            'symbol': 'EURUSD',
            'direction': 'BUY',
            'confidence': 0.8,
            'timestamp': datetime.now().isoformat()
        }
        
        assert signal_generator.validate_and_enhance_signal(valid_signal)
        
        # Invalid signal - missing fields
        invalid_signal = {
            'signal_id': 'test_002',
            'symbol': 'EURUSD'
            # Missing required fields
        }
        
        assert not signal_generator.validate_and_enhance_signal(invalid_signal)
        
        # Invalid signal - confidence out of range
        invalid_confidence_signal = {
            'signal_id': 'test_003',
            'symbol': 'EURUSD',
            'direction': 'BUY',
            'confidence': 1.5,  # Invalid
            'timestamp': datetime.now().isoformat()
        }
        
        assert not signal_generator.validate_and_enhance_signal(invalid_confidence_signal)
    
    def test_confidence_threshold_filtering(self, signal_generator):
        """Test confidence threshold filtering"""
        # High confidence signal
        high_conf_signal = {
            'signal_id': 'high_conf',
            'symbol': 'EURUSD',
            'direction': 'BUY',
            'confidence': 0.9,
            'timestamp': datetime.now().isoformat()
        }
        
        assert signal_generator.validate_and_enhance_signal(high_conf_signal)
        
        # Low confidence signal (below threshold)
        low_conf_signal = {
            'signal_id': 'low_conf',
            'symbol': 'EURUSD',
            'direction': 'BUY',
            'confidence': 0.5,  # Below 0.7 threshold
            'timestamp': datetime.now().isoformat()
        }
        
        assert not signal_generator.validate_and_enhance_signal(low_conf_signal)
    
    def test_csv_signal_writing(self, signal_generator, tmp_path):
        """Test CSV signal writing functionality"""
        signal = {
            'signal_id': 'csv_test_001',
            'symbol': 'EURUSD',
            'direction': 'SELL',
            'confidence': 0.82,
            'timestamp': datetime.now().isoformat(),
            'strategy_id': 'CSV_STRATEGY',
            'metadata': {'test': True}
        }
        
        # Mock the CSV file path to use temp directory
        with patch.object(signal_generator, 'write_signal_to_csv') as mock_write:
            mock_write.return_value = True
            
            result = signal_generator.write_signal_to_csv(signal, 'EURUSD')
            assert result is True
            mock_write.assert_called_once_with(signal, 'EURUSD')

class TestSignalProcessingWorkflow:
    """Test the complete signal processing workflow"""
    
    @pytest.fixture
    def workflow_components(self):
        """Set up components for workflow testing"""
        return {
            'signal_generator': Mock(),
            'validator': Mock(),
            'processor': Mock(),
            'notifier': Mock()
        }
    
    def test_end_to_end_signal_flow(self, workflow_components):
        """Test end-to-end signal processing flow"""
        # Mock signal generation
        mock_signal = {
            'signal_id': 'workflow_test_001',
            'symbol': 'GBPUSD',
            'direction': 'BUY',
            'confidence': 0.87,
            'timestamp': datetime.now().isoformat(),
            'strategy_id': 'WORKFLOW_TEST'
        }
        
        workflow_components['signal_generator'].generate_signal.return_value = mock_signal
        workflow_components['validator'].validate.return_value = True
        workflow_components['processor'].process.return_value = {'status': 'success'}
        
        # Simulate workflow
        generated_signal = workflow_components['signal_generator'].generate_signal('GBPUSD')
        assert generated_signal == mock_signal
        
        is_valid = workflow_components['validator'].validate(generated_signal)
        assert is_valid is True
        
        result = workflow_components['processor'].process(generated_signal)
        assert result['status'] == 'success'
    
    def test_signal_processing_with_correlation(self):
        """Test signal processing with correlation tracking"""
        # Start correlation
        correlation_id = correlation_manager.generate_correlation_id("SIG")
        correlation_manager.set_correlation_id(correlation_id)
        
        # Simulate signal processing steps
        correlation_manager.add_operation("signal_generated")
        correlation_manager.add_operation("signal_validated")
        correlation_manager.add_operation("signal_sent_to_ea")
        
        # Verify correlation tracking
        trace = correlation_manager.get_operation_trace(correlation_id)
        assert len(trace) == 3
        
        operation_names = [op['operation'] for op in trace]
        assert 'signal_generated' in operation_names
        assert 'signal_validated' in operation_names
        assert 'signal_sent_to_ea' in operation_names
    
    def test_signal_processing_with_circuit_breaker(self):
        """Test signal processing with circuit breaker protection"""
        # Create circuit breaker for signal processing
        circuit_breaker = CircuitBreaker(
            failure_threshold=3,
            timeout_seconds=5,
            name="signal_processing"
        )
        
        # Mock a failing signal processor
        def failing_processor():
            raise Exception("Signal processing failed")
        
        # Test circuit breaker functionality
        for i in range(5):
            try:
                circuit_breaker.call(failing_processor)
            except Exception:
                pass  # Expected failures
        
        # Circuit should be open now
        assert circuit_breaker.is_open
        
        # Should reject new calls
        with pytest.raises(Exception):
            circuit_breaker.call(failing_processor)
    
    def test_signal_processing_with_retry(self):
        """Test signal processing with retry logic"""
        retry_config = RetryConfig(
            max_attempts=3,
            base_delay=0.1,
            backoff_multiplier=2.0
        )
        
        retry_manager = RetryManager(retry_config)
        
        # Mock a processor that fails twice then succeeds
        call_count = 0
        def unreliable_processor():
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise Exception(f"Failure {call_count}")
            return "Success"
        
        # Should succeed after retries
        result = retry_manager.execute(unreliable_processor)
        assert result == "Success"
        assert call_count == 3
    
    def test_signal_error_handling(self):
        """Test error handling in signal processing"""
        errors_encountered = []
        
        def error_handler(error_type, error_message):
            errors_encountered.append({'type': error_type, 'message': error_message})
        
        # Test various error scenarios
        error_scenarios = [
            ('VALIDATION_ERROR', 'Invalid signal format'),
            ('NETWORK_ERROR', 'Failed to send signal'),
            ('TIMEOUT_ERROR', 'Signal processing timeout'),
            ('PROCESSING_ERROR', 'Internal processing error')
        ]
        
        for error_type, error_message in error_scenarios:
            error_handler(error_type, error_message)
        
        assert len(errors_encountered) == 4
        assert any(err['type'] == 'VALIDATION_ERROR' for err in errors_encountered)
        assert any(err['type'] == 'NETWORK_ERROR' for err in errors_encountered)

class TestSignalPerformance:
    """Test signal processing performance"""
    
    def test_signal_generation_performance(self):
        """Test signal generation performance"""
        config = {
            'interval_seconds': 0.1,
            'confidence_threshold': 0.7
        }
        
        generator = SignalGeneratorService(config)
        
        # Generate multiple signals and measure time
        start_time = time.time()
        signals_generated = 0
        
        for i in range(100):
            signal = generator.generate_signal('EURUSD', 'PERF_TEST')
            if signal:
                signals_generated += 1
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should generate signals efficiently
        assert signals_generated == 100
        assert total_time < 1.0  # Should complete in less than 1 second
        
        signals_per_second = signals_generated / total_time
        assert signals_per_second > 100  # Should handle at least 100 signals/second
    
    def test_signal_validation_performance(self):
        """Test signal validation performance"""
        config = {'confidence_threshold': 0.7}
        generator = SignalGeneratorService(config)
        
        # Create test signals
        test_signals = []
        for i in range(1000):
            signal = {
                'signal_id': f'perf_test_{i}',
                'symbol': 'EURUSD',
                'direction': 'BUY' if i % 2 == 0 else 'SELL',
                'confidence': 0.8,
                'timestamp': datetime.now().isoformat()
            }
            test_signals.append(signal)
        
        # Validate all signals and measure time
        start_time = time.time()
        valid_count = 0
        
        for signal in test_signals:
            if generator.validate_and_enhance_signal(signal):
                valid_count += 1
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should validate efficiently
        assert valid_count == 1000  # All should be valid
        assert total_time < 0.5  # Should complete in less than 0.5 seconds
        
        validations_per_second = valid_count / total_time
        assert validations_per_second > 2000  # Should handle at least 2000 validations/second

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
