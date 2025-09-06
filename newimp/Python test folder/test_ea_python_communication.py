"""
Integration Tests for EA-Python Communication
Tests end-to-end communication between MQL4 Expert Advisor and Python trading server
"""

import asyncio
import json
import pytest
import tempfile
import time
import uuid
import os
import subprocess
import sqlite3
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from pathlib import Path
import csv
import threading
from datetime import datetime, timedelta

# Test configuration
TEST_CONFIG = {
    "python_server": {
        "host": "localhost",
        "port": 8999,
        "timeout": 30
    },
    "communication": {
        "socket_timeout": 10,
        "file_poll_interval": 0.1,
        "max_retries": 3
    },
    "database": {
        "type": "sqlite",
        "path": ":memory:"
    },
    "test_data": {
        "signals_file": "test_signals.csv",
        "responses_file": "test_responses.csv",
        "parameters_file": "test_parameters.csv"
    }
}

@dataclass
class TestSignal:
    """Test signal data structure"""
    id: str
    symbol: str
    direction: str
    confidence: float
    timestamp: str
    strategy_id: int
    metadata: Dict[str, Any]

@dataclass
class TestTradeResponse:
    """Expected trade response structure"""
    signal_id: str
    trade_id: Optional[str]
    status: str
    execution_price: Optional[float]
    timestamp: str
    error_message: Optional[str] = None

class MockMT4Environment:
    """Simulates MT4 environment for testing"""
    
    def __init__(self, test_dir: str):
        self.test_dir = Path(test_dir)
        self.files_dir = self.test_dir / "Files"
        self.files_dir.mkdir(parents=True, exist_ok=True)
        
        # Create test file paths
        self.signals_file = self.files_dir / "current_signal.csv"
        self.responses_file = self.files_dir / "trade_responses.csv"
        self.mapping_file = self.files_dir / "signal_id_mapping.csv"
        
        # Initialize files
        self._init_test_files()
        
    def _init_test_files(self):
        """Initialize test CSV files with headers"""
        # Signal file header
        with open(self.signals_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'symbol', 'direction', 'confidence', 'timestamp', 'strategy_id', 'metadata'])
        
        # Response file header
        with open(self.responses_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['signal_id', 'trade_id', 'status', 'execution_price', 'timestamp', 'error_message'])
        
        # Mapping file
        with open(self.mapping_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['signal_id', 'parameter_set', 'description'])
            writer.writerow([12345, 1, 'Conservative RSI+EMA strategy'])
            writer.writerow([12346, 2, 'Moderate Bollinger Bands strategy'])
            writer.writerow([12347, 3, 'Aggressive Breakout strategy'])
            writer.writerow([12348, 4, 'Scalping strategy'])
    
    def write_signal(self, signal: TestSignal):
        """Write signal to CSV file (simulating Python server)"""
        with open(self.signals_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'symbol', 'direction', 'confidence', 'timestamp', 'strategy_id', 'metadata'])
            writer.writerow([
                signal.id,
                signal.symbol,
                signal.direction,
                signal.confidence,
                signal.timestamp,
                signal.strategy_id,
                json.dumps(signal.metadata)
            ])
    
    def read_response(self) -> Optional[TestTradeResponse]:
        """Read trade response from CSV file (simulating EA response)"""
        try:
            with open(self.responses_file, 'r') as f:
                reader = csv.DictReader(f)
                responses = list(reader)
                if len(responses) > 0:
                    latest = responses[-1]  # Get latest response
                    return TestTradeResponse(
                        signal_id=latest['signal_id'],
                        trade_id=latest['trade_id'] if latest['trade_id'] else None,
                        status=latest['status'],
                        execution_price=float(latest['execution_price']) if latest['execution_price'] else None,
                        timestamp=latest['timestamp'],
                        error_message=latest['error_message'] if latest['error_message'] else None
                    )
        except (FileNotFoundError, ValueError, KeyError) as e:
            print(f"Error reading response: {e}")
        return None
    
    def clear_files(self):
        """Clear all test files"""
        self._init_test_files()

class PythonServerMock:
    """Mock Python trading server for testing"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.running = False
        self.signals_processed = []
        self.responses_sent = []
        
    async def start(self):
        """Start the mock server"""
        self.running = True
        print("Mock Python server started")
    
    async def stop(self):
        """Stop the mock server"""
        self.running = False
        print("Mock Python server stopped")
    
    def process_signal(self, signal: TestSignal) -> TestTradeResponse:
        """Process a test signal and return mock response"""
        self.signals_processed.append(signal)
        
        # Simulate processing delay
        time.sleep(0.1)
        
        # Generate mock response based on signal
        if signal.confidence > 0.8:
            response = TestTradeResponse(
                signal_id=signal.id,
                trade_id=f"trade_{uuid.uuid4().hex[:8]}",
                status="EXECUTED",
                execution_price=1.0850 if signal.direction == "BUY" else 1.0840,
                timestamp=datetime.now().isoformat()
            )
        elif signal.confidence < 0.5:
            response = TestTradeResponse(
                signal_id=signal.id,
                trade_id=None,
                status="REJECTED",
                execution_price=None,
                timestamp=datetime.now().isoformat(),
                error_message="Confidence too low"
            )
        else:
            response = TestTradeResponse(
                signal_id=signal.id,
                trade_id=f"trade_{uuid.uuid4().hex[:8]}",
                status="EXECUTED",
                execution_price=1.0845,
                timestamp=datetime.now().isoformat()
            )
        
        self.responses_sent.append(response)
        return response

@pytest.fixture
def test_environment():
    """Create test environment with temporary directory"""
    with tempfile.TemporaryDirectory() as temp_dir:
        mock_mt4 = MockMT4Environment(temp_dir)
        yield mock_mt4

@pytest.fixture
def python_server():
    """Create mock Python server"""
    server = PythonServerMock(TEST_CONFIG)
    return server

@pytest.fixture
def test_signals():
    """Generate test signals for testing"""
    return [
        TestSignal(
            id=str(uuid.uuid4()),
            symbol="EURUSD",
            direction="BUY",
            confidence=0.85,
            timestamp=datetime.now().isoformat(),
            strategy_id=12345,
            metadata={"rsi": 30.5, "ema_cross": True}
        ),
        TestSignal(
            id=str(uuid.uuid4()),
            symbol="GBPUSD",
            direction="SELL",
            confidence=0.92,
            timestamp=datetime.now().isoformat(),
            strategy_id=12346,
            metadata={"rsi": 75.2, "bollinger_position": "upper"}
        ),
        TestSignal(
            id=str(uuid.uuid4()),
            symbol="USDJPY",
            direction="BUY",
            confidence=0.45,  # Low confidence for rejection test
            timestamp=datetime.now().isoformat(),
            strategy_id=12347,
            metadata={"rsi": 55.0}
        )
    ]

class TestCommunicationBridges:
    """Test different communication bridge types"""
    
    def test_file_based_communication(self, test_environment, python_server, test_signals):
        """Test file-based communication between Python and EA"""
        # Test signal processing
        for signal in test_signals:
            # Python writes signal
            test_environment.write_signal(signal)
            
            # Process signal (simulating EA reading and Python processing)
            response = python_server.process_signal(signal)
            
            # Verify signal was processed
            assert response.signal_id == signal.id
            assert response.status in ["EXECUTED", "REJECTED"]
            
            # Clear for next test
            test_environment.clear_files()
    
    def test_bidirectional_communication(self, test_environment, python_server, test_signals):
        """Test bidirectional communication flow"""
        signal = test_signals[0]
        
        # 1. Python server writes signal to file
        test_environment.write_signal(signal)
        
        # 2. Simulate EA reading signal and processing
        # (In real scenario, EA would read this file)
        
        # 3. Python processes signal and generates response
        response = python_server.process_signal(signal)
        
        # 4. Simulate EA writing response (in real scenario, EA writes to response file)
        # Here we'll manually write the response to test the full cycle
        with open(test_environment.responses_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                response.signal_id,
                response.trade_id,
                response.status,
                response.execution_price,
                response.timestamp,
                response.error_message
            ])
        
        # 5. Read back the response
        read_response = test_environment.read_response()
        
        # Verify complete cycle
        assert read_response is not None
        assert read_response.signal_id == signal.id
        assert read_response.status == response.status

class TestSignalProcessing:
    """Test signal processing logic"""
    
    def test_valid_signal_processing(self, python_server, test_signals):
        """Test processing of valid signals"""
        valid_signal = test_signals[0]  # High confidence signal
        
        response = python_server.process_signal(valid_signal)
        
        assert response.signal_id == valid_signal.id
        assert response.status == "EXECUTED"
        assert response.trade_id is not None
        assert response.execution_price is not None
        assert response.error_message is None
    
    def test_low_confidence_signal_rejection(self, python_server, test_signals):
        """Test rejection of low confidence signals"""
        low_confidence_signal = test_signals[2]  # 0.45 confidence
        
        response = python_server.process_signal(low_confidence_signal)
        
        assert response.signal_id == low_confidence_signal.id
        assert response.status == "REJECTED"
        assert response.trade_id is None
        assert response.execution_price is None
        assert response.error_message is not None
    
    def test_signal_validation(self, python_server):
        """Test signal validation logic"""
        # Test invalid signal (missing required fields)
        invalid_signal = TestSignal(
            id="",  # Invalid empty ID
            symbol="INVALID",  # Invalid symbol
            direction="INVALID_DIR",  # Invalid direction
            confidence=1.5,  # Invalid confidence > 1.0
            timestamp="invalid-timestamp",  # Invalid timestamp
            strategy_id=-1,  # Invalid strategy ID
            metadata={}
        )
        
        # Should handle invalid signal gracefully
        with pytest.raises((ValueError, Exception)):
            python_server.process_signal(invalid_signal)

class TestErrorHandling:
    """Test error handling and recovery"""
    
    def test_file_access_errors(self, test_environment):
        """Test handling of file access errors"""
        # Make files read-only to simulate access errors
        os.chmod(test_environment.signals_file, 0o444)
        
        signal = TestSignal(
            id=str(uuid.uuid4()),
            symbol="EURUSD",
            direction="BUY",
            confidence=0.75,
            timestamp=datetime.now().isoformat(),
            strategy_id=12345,
            metadata={}
        )
        
        # Should handle file access error gracefully
        with pytest.raises((PermissionError, OSError)):
            test_environment.write_signal(signal)
        
        # Restore permissions
        os.chmod(test_environment.signals_file, 0o666)
    
    def test_malformed_data_handling(self, test_environment):
        """Test handling of malformed CSV data"""
        # Write malformed data to signal file
        with open(test_environment.signals_file, 'w') as f:
            f.write("malformed,csv,data,without,proper,structure\n")
        
        # Should handle malformed data gracefully
        response = test_environment.read_response()
        assert response is None  # Should return None for malformed data
    
    def test_concurrent_file_access(self, test_environment, test_signals):
        """Test concurrent file access scenarios"""
        def write_signals_concurrently():
            for i, signal in enumerate(test_signals):
                signal.id = f"{signal.id}_{i}"
                test_environment.write_signal(signal)
                time.sleep(0.01)  # Small delay between writes
        
        # Start multiple threads writing signals
        threads = []
        for _ in range(3):
            thread = threading.Thread(target=write_signals_concurrently)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # File should still be in valid state
        assert test_environment.signals_file.exists()

class TestPerformance:
    """Test performance characteristics"""
    
    def test_signal_processing_latency(self, python_server, test_signals):
        """Test signal processing latency"""
        signal = test_signals[0]
        
        start_time = time.time()
        response = python_server.process_signal(signal)
        end_time = time.time()
        
        latency = end_time - start_time
        
        # Should process signal within reasonable time (< 1 second)
        assert latency < 1.0
        assert response.signal_id == signal.id
    
    def test_high_frequency_signals(self, python_server):
        """Test handling of high frequency signals"""
        signal_count = 100
        signals = []
        
        # Generate many signals
        for i in range(signal_count):
            signal = TestSignal(
                id=str(uuid.uuid4()),
                symbol="EURUSD",
                direction="BUY" if i % 2 == 0 else "SELL",
                confidence=0.75,
                timestamp=datetime.now().isoformat(),
                strategy_id=12345,
                metadata={"sequence": i}
            )
            signals.append(signal)
        
        start_time = time.time()
        responses = []
        
        for signal in signals:
            response = python_server.process_signal(signal)
            responses.append(response)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Verify all signals were processed
        assert len(responses) == signal_count
        
        # Calculate throughput (signals per second)
        throughput = signal_count / total_time
        print(f"Processed {signal_count} signals in {total_time:.2f}s ({throughput:.2f} signals/sec)")
        
        # Should achieve reasonable throughput (>10 signals/sec for this mock)
        assert throughput > 10

class TestDataIntegrity:
    """Test data integrity and consistency"""
    
    def test_signal_data_consistency(self, test_environment, test_signals):
        """Test that signal data remains consistent through the communication cycle"""
        original_signal = test_signals[0]
        
        # Write signal
        test_environment.write_signal(original_signal)
        
        # Read signal back from file
        with open(test_environment.signals_file, 'r') as f:
            reader = csv.DictReader(f)
            read_signals = list(reader)
        
        assert len(read_signals) == 1
        read_signal = read_signals[0]
        
        # Verify data consistency
        assert read_signal['id'] == original_signal.id
        assert read_signal['symbol'] == original_signal.symbol
        assert read_signal['direction'] == original_signal.direction
        assert float(read_signal['confidence']) == original_signal.confidence
        assert int(read_signal['strategy_id']) == original_signal.strategy_id
    
    def test_timestamp_handling(self, test_environment):
        """Test proper timestamp handling across time zones"""
        # Test with different timestamp formats
        timestamp_formats = [
            datetime.now().isoformat(),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            datetime.now().isoformat() + "Z",
        ]
        
        for timestamp_format in timestamp_formats:
            signal = TestSignal(
                id=str(uuid.uuid4()),
                symbol="EURUSD",
                direction="BUY",
                confidence=0.75,
                timestamp=timestamp_format,
                strategy_id=12345,
                metadata={}
            )
            
            # Should handle different timestamp formats
            test_environment.write_signal(signal)
            test_environment.clear_files()

class TestConfigurationManagement:
    """Test configuration management"""
    
    def test_parameter_set_mapping(self, test_environment):
        """Test signal ID to parameter set mapping"""
        # Read mapping file
        with open(test_environment.mapping_file, 'r') as f:
            reader = csv.DictReader(f)
            mappings = {int(row['signal_id']): int(row['parameter_set']) for row in reader}
        
        # Verify expected mappings exist
        assert 12345 in mappings
        assert 12346 in mappings
        assert 12347 in mappings
        assert 12348 in mappings
        
        # Verify mapping values
        assert mappings[12345] == 1
        assert mappings[12346] == 2
        assert mappings[12347] == 3
        assert mappings[12348] == 4

@pytest.mark.asyncio
class TestAsyncCommunication:
    """Test asynchronous communication patterns"""
    
    async def test_async_signal_processing(self, python_server, test_signals):
        """Test asynchronous signal processing"""
        async def process_signal_async(signal):
            # Simulate async processing
            await asyncio.sleep(0.01)
            return python_server.process_signal(signal)
        
        # Process multiple signals concurrently
        tasks = [process_signal_async(signal) for signal in test_signals]
        responses = await asyncio.gather(*tasks)
        
        # Verify all signals were processed
        assert len(responses) == len(test_signals)
        
        for i, response in enumerate(responses):
            assert response.signal_id == test_signals[i].id
    
    async def test_signal_timeout_handling(self, python_server):
        """Test handling of signal processing timeouts"""
        signal = TestSignal(
            id=str(uuid.uuid4()),
            symbol="EURUSD",
            direction="BUY",
            confidence=0.75,
            timestamp=datetime.now().isoformat(),
            strategy_id=12345,
            metadata={}
        )
        
        async def slow_process_signal(signal):
            # Simulate slow processing
            await asyncio.sleep(2.0)
            return python_server.process_signal(signal)
        
        # Should complete within reasonable time or timeout
        try:
            response = await asyncio.wait_for(slow_process_signal(signal), timeout=1.0)
            assert False, "Should have timed out"
        except asyncio.TimeoutError:
            # Expected timeout
            pass

# Integration test runner
def run_integration_tests():
    """Run all integration tests"""
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--durations=10",
        "-x"  # Stop on first failure
    ])

if __name__ == "__main__":
    # Load test signals from file if available
    test_signals_file = Path("fixtures/test_signals.json")
    if test_signals_file.exists():
        with open(test_signals_file) as f:
            test_data = json.load(f)
            print(f"Loaded test data with {len(test_data.get('test_signals', {}))} signals")
    
    # Run integration tests
    run_integration_tests()
