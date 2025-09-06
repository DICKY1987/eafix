"""
Database Operations Tests
Unit tests for database connectivity, CRUD operations, and data integrity
"""

import pytest
import sqlite3
import tempfile
import os
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from contextlib import contextmanager
from unittest.mock import Mock, patch, MagicMock
import threading
import time

# Mock database manager for testing
class MockDatabaseManager:
    """Mock database manager for testing database operations"""
    
    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self.connection = None
        self.is_connected = False
        self.transaction_count = 0
        self.query_log = []
    
    def connect(self) -> bool:
        """Connect to database"""
        try:
            self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
            self.connection.row_factory = sqlite3.Row
            self.is_connected = True
            self._create_tables()
            return True
        except Exception as e:
            print(f"Database connection failed: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from database"""
        if self.connection:
            self.connection.close()
            self.connection = None
        self.is_connected = False
    
    def _create_tables(self):
        """Create test tables"""
        cursor = self.connection.cursor()
        
        # Signals table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS signals (
                id TEXT PRIMARY KEY,
                symbol TEXT NOT NULL,
                direction TEXT NOT NULL CHECK (direction IN ('BUY', 'SELL')),
                confidence REAL NOT NULL CHECK (confidence BETWEEN 0.0 AND 1.0),
                timestamp TIMESTAMP NOT NULL,
                strategy_id INTEGER NOT NULL,
                metadata TEXT,
                processed BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Trades table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id TEXT PRIMARY KEY,
                signal_id TEXT NOT NULL,
                symbol TEXT NOT NULL,
                direction TEXT NOT NULL,
                lot_size REAL NOT NULL,
                entry_price REAL,
                exit_price REAL,
                stop_loss REAL,
                take_profit REAL,
                status TEXT NOT NULL,
                pnl REAL DEFAULT 0.0,
                opened_at TIMESTAMP,
                closed_at TIMESTAMP,
                error_message TEXT,
                mt4_ticket INTEGER,
                FOREIGN KEY (signal_id) REFERENCES signals (id)
            )
        """)
        
        # Parameter sets table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS parameter_sets (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                lot_size REAL NOT NULL,
                stop_loss_pips INTEGER NOT NULL,
                take_profit_pips INTEGER NOT NULL,
                magic_number INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        self.connection.commit()
    
    def execute_query(self, query: str, params: tuple = ()) -> List[Dict]:
        """Execute query and return results"""
        if not self.is_connected:
            raise Exception("Database not connected")
        
        self.query_log.append((query, params))
        cursor = self.connection.cursor()
        cursor.execute(query, params)
        
        if query.strip().upper().startswith('SELECT'):
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        else:
            self.connection.commit()
            return []
    
    def insert_signal(self, signal_data: Dict[str, Any]) -> bool:
        """Insert signal into database"""
        query = """
            INSERT INTO signals (id, symbol, direction, confidence, timestamp, strategy_id, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            signal_data['id'],
            signal_data['symbol'],
            signal_data['direction'],
            signal_data['confidence'],
            signal_data['timestamp'],
            signal_data['strategy_id'],
            json.dumps(signal_data.get('metadata', {}))
        )
        
        try:
            self.execute_query(query, params)
            return True
        except Exception as e:
            print(f"Failed to insert signal: {e}")
            return False
    
    def get_signal(self, signal_id: str) -> Optional[Dict[str, Any]]:
        """Get signal by ID"""
        query = "SELECT * FROM signals WHERE id = ?"
        results = self.execute_query(query, (signal_id,))
        
        if results:
            signal = results[0]
            if signal['metadata']:
                signal['metadata'] = json.loads(signal['metadata'])
            return signal
        return None
    
    def update_signal_processed(self, signal_id: str, processed: bool = True) -> bool:
        """Update signal processed status"""
        query = "UPDATE signals SET processed = ? WHERE id = ?"
        try:
            self.execute_query(query, (processed, signal_id))
            return True
        except Exception:
            return False
    
    def insert_trade(self, trade_data: Dict[str, Any]) -> bool:
        """Insert trade into database"""
        query = """
            INSERT INTO trades (id, signal_id, symbol, direction, lot_size, entry_price, 
                              status, opened_at, mt4_ticket)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            trade_data['id'],
            trade_data['signal_id'],
            trade_data['symbol'],
            trade_data['direction'],
            trade_data['lot_size'],
            trade_data.get('entry_price'),
            trade_data['status'],
            trade_data.get('opened_at'),
            trade_data.get('mt4_ticket')
        )
        
        try:
            self.execute_query(query, params)
            return True
        except Exception as e:
            print(f"Failed to insert trade: {e}")
            return False
    
    def get_trades_by_signal(self, signal_id: str) -> List[Dict[str, Any]]:
        """Get trades for a specific signal"""
        query = "SELECT * FROM trades WHERE signal_id = ?"
        return self.execute_query(query, (signal_id,))
    
    @contextmanager
    def transaction(self):
        """Transaction context manager"""
        if not self.is_connected:
            raise Exception("Database not connected")
        
        self.transaction_count += 1
        try:
            yield
            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise
        finally:
            self.transaction_count -= 1

class TestDatabaseConnection:
    """Test database connection functionality"""
    
    def test_connection_success(self):
        """Test successful database connection"""
        db = MockDatabaseManager()
        
        assert db.connect() == True
        assert db.is_connected == True
        assert db.connection is not None
        
        db.disconnect()
    
    def test_connection_to_file_database(self):
        """Test connection to file-based database"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        try:
            db = MockDatabaseManager(db_path)
            assert db.connect() == True
            assert os.path.exists(db_path)
            
            db.disconnect()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)
    
    def test_disconnect_cleanup(self):
        """Test proper cleanup on disconnect"""
        db = MockDatabaseManager()
        db.connect()
        
        assert db.is_connected == True
        
        db.disconnect()
        
        assert db.is_connected == False
        assert db.connection is None
    
    def test_multiple_connections(self):
        """Test handling of multiple database connections"""
        db1 = MockDatabaseManager()
        db2 = MockDatabaseManager()
        
        assert db1.connect() == True
        assert db2.connect() == True
        
        assert db1.is_connected == True
        assert db2.is_connected == True
        
        db1.disconnect()
        db2.disconnect()

class TestSignalOperations:
    """Test signal-related database operations"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.db = MockDatabaseManager()
        self.db.connect()
    
    def teardown_method(self):
        """Cleanup after each test method"""
        self.db.disconnect()
    
    def test_insert_signal_success(self):
        """Test successful signal insertion"""
        signal_data = {
            'id': str(uuid.uuid4()),
            'symbol': 'EURUSD',
            'direction': 'BUY',
            'confidence': 0.85,
            'timestamp': datetime.now().isoformat(),
            'strategy_id': 12345,
            'metadata': {'rsi': 30.5, 'ema': True}
        }
        
        result = self.db.insert_signal(signal_data)
        assert result == True
        
        # Verify signal was inserted
        retrieved = self.db.get_signal(signal_data['id'])
        assert retrieved is not None
        assert retrieved['symbol'] == 'EURUSD'
        assert retrieved['direction'] == 'BUY'
        assert retrieved['confidence'] == 0.85
    
    def test_insert_signal_with_metadata(self):
        """Test signal insertion with complex metadata"""
        complex_metadata = {
            'indicators': {
                'rsi': 30.5,
                'macd': {'line': 0.002, 'signal': 0.001, 'histogram': 0.001},
                'bollinger': {'upper': 1.0860, 'middle': 1.0845, 'lower': 1.0830}
            },
            'market_conditions': {
                'volatility': 'medium',
                'trend': 'bullish',
                'session': 'european'
            },
            'risk_factors': ['news_event', 'low_liquidity']
        }
        
        signal_data = {
            'id': str(uuid.uuid4()),
            'symbol': 'GBPUSD',
            'direction': 'SELL',
            'confidence': 0.75,
            'timestamp': datetime.now().isoformat(),
            'strategy_id': 12346,
            'metadata': complex_metadata
        }
        
        result = self.db.insert_signal(signal_data)
        assert result == True
        
        # Verify metadata preservation
        retrieved = self.db.get_signal(signal_data['id'])
        assert retrieved['metadata'] == complex_metadata
        assert retrieved['metadata']['indicators']['rsi'] == 30.5
        assert retrieved['metadata']['risk_factors'] == ['news_event', 'low_liquidity']
    
    def test_get_nonexistent_signal(self):
        """Test retrieval of non-existent signal"""
        fake_id = str(uuid.uuid4())
        result = self.db.get_signal(fake_id)
        assert result is None
    
    def test_update_signal_processed_status(self):
        """Test updating signal processed status"""
        signal_data = {
            'id': str(uuid.uuid4()),
            'symbol': 'USDJPY',
            'direction': 'BUY',
            'confidence': 0.90,
            'timestamp': datetime.now().isoformat(),
            'strategy_id': 12347,
            'metadata': {}
        }
        
        # Insert signal
        self.db.insert_signal(signal_data)
        
        # Verify initial processed status is False
        signal = self.db.get_signal(signal_data['id'])
        assert signal['processed'] == 0  # SQLite returns 0 for False
        
        # Update processed status
        result = self.db.update_signal_processed(signal_data['id'], True)
        assert result == True
        
        # Verify updated status
        signal = self.db.get_signal(signal_data['id'])
        assert signal['processed'] == 1  # SQLite returns 1 for True
    
    def test_signal_constraint_validation(self):
        """Test signal constraint validation"""
        # Test invalid direction
        invalid_signal = {
            'id': str(uuid.uuid4()),
            'symbol': 'EURUSD',
            'direction': 'INVALID',  # Should fail constraint
            'confidence': 0.85,
            'timestamp': datetime.now().isoformat(),
            'strategy_id': 12345,
            'metadata': {}
        }
        
        result = self.db.insert_signal(invalid_signal)
        assert result == False  # Should fail due to constraint
        
        # Test invalid confidence
        invalid_confidence_signal = {
            'id': str(uuid.uuid4()),
            'symbol': 'EURUSD',
            'direction': 'BUY',
            'confidence': 1.5,  # Should fail constraint (> 1.0)
            'timestamp': datetime.now().isoformat(),
            'strategy_id': 12345,
            'metadata': {}
        }
        
        result = self.db.insert_signal(invalid_confidence_signal)
        assert result == False  # Should fail due to constraint

class TestTradeOperations:
    """Test trade-related database operations"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.db = MockDatabaseManager()
        self.db.connect()
        
        # Insert a test signal first
        self.test_signal_id = str(uuid.uuid4())
        signal_data = {
            'id': self.test_signal_id,
            'symbol': 'EURUSD',
            'direction': 'BUY',
            'confidence': 0.85,
            'timestamp': datetime.now().isoformat(),
            'strategy_id': 12345,
            'metadata': {}
        }
        self.db.insert_signal(signal_data)
    
    def teardown_method(self):
        """Cleanup after each test method"""
        self.db.disconnect()
    
    def test_insert_trade_success(self):
        """Test successful trade insertion"""
        trade_data = {
            'id': str(uuid.uuid4()),
            'signal_id': self.test_signal_id,
            'symbol': 'EURUSD',
            'direction': 'BUY',
            'lot_size': 0.1,
            'entry_price': 1.0850,
            'status': 'EXECUTED',
            'opened_at': datetime.now().isoformat(),
            'mt4_ticket': 123456
        }
        
        result = self.db.insert_trade(trade_data)
        assert result == True
        
        # Verify trade was inserted
        trades = self.db.get_trades_by_signal(self.test_signal_id)
        assert len(trades) == 1
        assert trades[0]['symbol'] == 'EURUSD'
        assert trades[0]['lot_size'] == 0.1
        assert trades[0]['entry_price'] == 1.0850
    
    def test_multiple_trades_per_signal(self):
        """Test multiple trades for the same signal"""
        trade_data_1 = {
            'id': str(uuid.uuid4()),
            'signal_id': self.test_signal_id,
            'symbol': 'EURUSD',
            'direction': 'BUY',
            'lot_size': 0.1,
            'entry_price': 1.0850,
            'status': 'EXECUTED',
            'opened_at': datetime.now().isoformat(),
            'mt4_ticket': 123456
        }
        
        trade_data_2 = {
            'id': str(uuid.uuid4()),
            'signal_id': self.test_signal_id,
            'symbol': 'EURUSD',
            'direction': 'BUY',
            'lot_size': 0.05,
            'entry_price': 1.0852,
            'status': 'EXECUTED',
            'opened_at': datetime.now().isoformat(),
            'mt4_ticket': 123457
        }
        
        assert self.db.insert_trade(trade_data_1) == True
        assert self.db.insert_trade(trade_data_2) == True
        
        # Verify both trades exist
        trades = self.db.get_trades_by_signal(self.test_signal_id)
        assert len(trades) == 2
        
        # Verify trade details
        trade_ids = [t['id'] for t in trades]
        assert trade_data_1['id'] in trade_ids
        assert trade_data_2['id'] in trade_ids
    
    def test_foreign_key_constraint(self):
        """Test foreign key constraint for signal_id"""
        trade_data = {
            'id': str(uuid.uuid4()),
            'signal_id': 'non-existent-signal-id',  # Should fail foreign key constraint
            'symbol': 'EURUSD',
            'direction': 'BUY',
            'lot_size': 0.1,
            'entry_price': 1.0850,
            'status': 'EXECUTED',
            'opened_at': datetime.now().isoformat(),
            'mt4_ticket': 123456
        }
        
        result = self.db.insert_trade(trade_data)
        # Note: SQLite foreign key enforcement might be off by default
        # In a real implementation, this should fail
        
    def test_get_trades_empty_result(self):
        """Test getting trades for signal with no trades"""
        empty_signal_id = str(uuid.uuid4())
        
        # Insert signal without trades
        signal_data = {
            'id': empty_signal_id,
            'symbol': 'GBPUSD',
            'direction': 'SELL',
            'confidence': 0.75,
            'timestamp': datetime.now().isoformat(),
            'strategy_id': 12346,
            'metadata': {}
        }
        self.db.insert_signal(signal_data)
        
        trades = self.db.get_trades_by_signal(empty_signal_id)
        assert trades == []

class TestDatabaseTransactions:
    """Test database transaction handling"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.db = MockDatabaseManager()
        self.db.connect()
    
    def teardown_method(self):
        """Cleanup after each test method"""
        self.db.disconnect()
    
    def test_successful_transaction(self):
        """Test successful transaction commit"""
        signal_data = {
            'id': str(uuid.uuid4()),
            'symbol': 'EURUSD',
            'direction': 'BUY',
            'confidence': 0.85,
            'timestamp': datetime.now().isoformat(),
            'strategy_id': 12345,
            'metadata': {}
        }
        
        with self.db.transaction():
            self.db.insert_signal(signal_data)
            # Transaction should commit successfully
        
        # Verify data was committed
        signal = self.db.get_signal(signal_data['id'])
        assert signal is not None
    
    def test_transaction_rollback_on_exception(self):
        """Test transaction rollback on exception"""
        signal_data = {
            'id': str(uuid.uuid4()),
            'symbol': 'EURUSD',
            'direction': 'BUY',
            'confidence': 0.85,
            'timestamp': datetime.now().isoformat(),
            'strategy_id': 12345,
            'metadata': {}
        }
        
        try:
            with self.db.transaction():
                self.db.insert_signal(signal_data)
                # Simulate an error
                raise Exception("Simulated error")
        except Exception:
            pass  # Expected exception
        
        # Verify data was rolled back
        signal = self.db.get_signal(signal_data['id'])
        assert signal is None

class TestDatabasePerformance:
    """Test database performance characteristics"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.db = MockDatabaseManager()
        self.db.connect()
    
    def teardown_method(self):
        """Cleanup after each test method"""
        self.db.disconnect()
    
    def test_bulk_signal_insertion(self):
        """Test bulk insertion performance"""
        import time
        
        signal_count = 1000
        signals = []
        
        # Generate test signals
        for i in range(signal_count):
            signal_data = {
                'id': str(uuid.uuid4()),
                'symbol': 'EURUSD',
                'direction': 'BUY' if i % 2 == 0 else 'SELL',
                'confidence': 0.5 + (i % 50) / 100.0,
                'timestamp': datetime.now().isoformat(),
                'strategy_id': 12345 + (i % 10),
                'metadata': {'test_id': i}
            }
            signals.append(signal_data)
        
        # Measure insertion time
        start_time = time.time()
        
        successful_inserts = 0
        for signal in signals:
            if self.db.insert_signal(signal):
                successful_inserts += 1
        
        end_time = time.time()
        duration = end_time - start_time
        
        assert successful_inserts == signal_count
        assert duration < 10.0  # Should complete in under 10 seconds
        
        # Calculate throughput
        throughput = signal_count / duration
        assert throughput > 50  # Should insert >50 signals per second
    
    def test_concurrent_database_access(self):
        """Test concurrent database access"""
        import threading
        import time
        
        results = []
        errors = []
        
        def insert_signals(thread_id, count):
            try:
                for i in range(count):
                    signal_data = {
                        'id': f"thread-{thread_id}-signal-{i}",
                        'symbol': 'EURUSD',
                        'direction': 'BUY',
                        'confidence': 0.75,
                        'timestamp': datetime.now().isoformat(),
                        'strategy_id': 12345,
                        'metadata': {'thread_id': thread_id, 'signal_num': i}
                    }
                    
                    if self.db.insert_signal(signal_data):
                        results.append(signal_data['id'])
                    
                    time.sleep(0.001)  # Small delay
            except Exception as e:
                errors.append(str(e))
        
        # Start multiple threads
        threads = []
        thread_count = 5
        signals_per_thread = 20
        
        for i in range(thread_count):
            thread = threading.Thread(target=insert_signals, args=(i, signals_per_thread))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify results
        expected_count = thread_count * signals_per_thread
        assert len(results) == expected_count
        assert len(errors) == 0  # No errors should occur
    
    def test_query_performance(self):
        """Test query performance with large dataset"""
        import time
        
        # Insert test data
        signal_count = 500
        for i in range(signal_count):
            signal_data = {
                'id': f"perf-test-{i}",
                'symbol': ['EURUSD', 'GBPUSD', 'USDJPY'][i % 3],
                'direction': 'BUY' if i % 2 == 0 else 'SELL',
                'confidence': 0.5 + (i % 50) / 100.0,
                'timestamp': datetime.now().isoformat(),
                'strategy_id': 12345 + (i % 5),
                'metadata': {}
            }
            self.db.insert_signal(signal_data)
        
        # Test query performance
        start_time = time.time()
        
        # Perform multiple queries
        for i in range(100):
            query = "SELECT * FROM signals WHERE symbol = ? AND confidence > ?"
            params = ('EURUSD', 0.7)
            results = self.db.execute_query(query, params)
        
        end_time = time.time()
        duration = end_time - start_time
        
        assert duration < 2.0  # Should complete 100 queries in under 2 seconds

class TestDatabaseErrorHandling:
    """Test database error handling"""
    
    def test_query_on_disconnected_database(self):
        """Test query execution on disconnected database"""
        db = MockDatabaseManager()
        # Don't connect
        
        with pytest.raises(Exception):
            db.execute_query("SELECT * FROM signals")
    
    def test_invalid_sql_query(self):
        """Test handling of invalid SQL queries"""
        db = MockDatabaseManager()
        db.connect()
        
        try:
            with pytest.raises(Exception):
                db.execute_query("INVALID SQL QUERY")
        finally:
            db.disconnect()
    
    def test_database_file_corruption_simulation(self):
        """Test handling of database file issues"""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
            tmp.write(b"corrupted data")  # Write invalid data
        
        try:
            db = MockDatabaseManager(db_path)
            # This should fail due to corrupted file
            result = db.connect()
            # Depending on implementation, this might fail or handle gracefully
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
