"""Production database manager for trading system persistence.

This module provides comprehensive database operations for:
- Conditional probability tables storage and queries  
- Historical tick data persistence
- Trading system configuration management
- Performance metrics and logging
- SQLite integration with fast queries (<100ms requirement)
"""

from __future__ import annotations

import json
import logging
import sqlite3
import time
import threading
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from contextlib import contextmanager

from .conditional_signals import ConditionalRow


@dataclass
class DatabaseConfig:
    """Database configuration settings."""
    db_path: str = "trading_system.db"
    connection_timeout: float = 30.0
    max_connections: int = 10
    vacuum_interval_hours: int = 24
    backup_interval_hours: int = 6
    performance_target_ms: float = 100.0
    
    # Table settings
    probability_table_retention_days: int = 90
    tick_data_retention_days: int = 7
    log_retention_days: int = 30


class DatabaseManager:
    """Production database manager with optimized queries and connection pooling."""

    def __init__(self, config: DatabaseConfig = None):
        self.config = config or DatabaseConfig()
        self.logger = logging.getLogger(__name__)
        self.db_path = Path(self.config.db_path)
        
        # Connection management with better concurrency control
        self._connection_pool: List[sqlite3.Connection] = []
        self._pool_lock = threading.RLock()  # Use RLock for nested acquisitions
        self._active_connections: Dict[int, sqlite3.Connection] = {}
        self._maintenance_thread: Optional[threading.Thread] = None
        self._maintenance_active = False
        self._shutdown_requested = False
        
        # Performance metrics
        self._query_stats = {
            'total_queries': 0,
            'avg_query_time_ms': 0.0,
            'slow_queries': 0,
            'last_query_time': None
        }
        
        # Initialize database
        self._initialize_database()
        self._start_maintenance()

    def __del__(self):
        """Cleanup on destruction."""
        self._stop_maintenance()
        self._close_all_connections()

    @contextmanager
    def get_connection(self):
        """Context manager for database connections with automatic cleanup and error handling."""
        conn = None
        try:
            conn = self._get_connection_from_pool()
            yield conn
        except sqlite3.Error as e:
            self.logger.error(f"Database error: {e}")
            if conn:
                try:
                    conn.rollback()
                except sqlite3.Error:
                    pass
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error in database operation: {e}")
            if conn:
                try:
                    conn.rollback()
                except sqlite3.Error:
                    pass
            raise
        finally:
            if conn:
                self._return_connection_to_pool(conn)

    def store_probability_table(self, symbol: str, rows: List[ConditionalRow]) -> bool:
        """Store conditional probability table for a symbol."""
        start_time = time.time()
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Clear existing data for symbol
                cursor.execute("DELETE FROM probability_tables WHERE symbol = ?", (symbol,))
                
                # Insert new probability data
                insert_data = []
                for row in rows:
                    insert_data.append((
                        symbol,
                        row.trigger,
                        row.outcome,
                        row.direction,
                        row.state,
                        row.succ,
                        row.tot,
                        row.p,
                        datetime.now().isoformat()
                    ))
                
                cursor.executemany("""
                    INSERT INTO probability_tables 
                    (symbol, trigger_type, outcome, direction, state, successes, total, probability, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, insert_data)
                
                conn.commit()
                
                self.logger.info(f"Stored {len(rows)} probability rows for {symbol}")
                self._update_query_stats(time.time() - start_time)
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to store probability table for {symbol}: {e}")
            return False

    def get_probability_table(self, symbol: str, min_samples: int = 200) -> List[ConditionalRow]:
        """Retrieve conditional probability table for a symbol."""
        start_time = time.time()
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT trigger_type, outcome, direction, state, successes, total, probability
                    FROM probability_tables 
                    WHERE symbol = ? AND total >= ?
                    ORDER BY probability DESC, total DESC
                """, (symbol, min_samples))
                
                rows = []
                for row in cursor.fetchall():
                    conditional_row = ConditionalRow(
                        trigger=row[0],
                        outcome=row[1], 
                        direction=row[2],
                        state=row[3],
                        succ=row[4],
                        tot=row[5],
                        p=row[6]
                    )
                    rows.append(conditional_row)
                
                self._update_query_stats(time.time() - start_time)
                return rows
                
        except Exception as e:
            self.logger.error(f"Failed to retrieve probability table for {symbol}: {e}")
            return []

    def get_top_probabilities(self, symbol: str, limit: int = 200) -> List[ConditionalRow]:
        """Get top probability entries for a symbol (fast query)."""
        start_time = time.time()
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Optimized query with index usage
                cursor.execute("""
                    SELECT trigger_type, outcome, direction, state, successes, total, probability
                    FROM probability_tables 
                    WHERE symbol = ?
                    ORDER BY probability DESC, total DESC
                    LIMIT ?
                """, (symbol, limit))
                
                rows = []
                for row in cursor.fetchall():
                    conditional_row = ConditionalRow(
                        trigger=row[0],
                        outcome=row[1],
                        direction=row[2], 
                        state=row[3],
                        succ=row[4],
                        tot=row[5],
                        p=row[6]
                    )
                    rows.append(conditional_row)
                
                query_time = time.time() - start_time
                self._update_query_stats(query_time)
                
                # Log slow queries
                if query_time * 1000 > self.config.performance_target_ms:
                    self.logger.warning(f"Slow query: get_top_probabilities took {query_time*1000:.1f}ms")
                
                return rows
                
        except Exception as e:
            self.logger.error(f"Failed to get top probabilities for {symbol}: {e}")
            return []

    def store_tick_data(self, symbol: str, bid: float, ask: float, timestamp: datetime = None) -> bool:
        """Store tick data for historical analysis."""
        start_time = time.time()
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                tick_time = timestamp or datetime.now()
                
                cursor.execute("""
                    INSERT INTO tick_data (symbol, bid, ask, spread, timestamp)
                    VALUES (?, ?, ?, ?, ?)
                """, (symbol, bid, ask, ask - bid, tick_time.isoformat()))
                
                conn.commit()
                self._update_query_stats(time.time() - start_time)
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to store tick data for {symbol}: {e}")
            return False

    def get_historical_ticks(self, symbol: str, hours_back: int = 24, limit: int = 10000) -> List[Dict]:
        """Retrieve historical tick data for analysis."""
        start_time = time.time()
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                since_time = datetime.now() - timedelta(hours=hours_back)
                
                cursor.execute("""
                    SELECT bid, ask, spread, timestamp
                    FROM tick_data 
                    WHERE symbol = ? AND timestamp >= ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (symbol, since_time.isoformat(), limit))
                
                ticks = []
                for row in cursor.fetchall():
                    ticks.append({
                        'bid': row[0],
                        'ask': row[1],
                        'spread': row[2],
                        'timestamp': row[3]
                    })
                
                self._update_query_stats(time.time() - start_time)
                return ticks
                
        except Exception as e:
            self.logger.error(f"Failed to get historical ticks for {symbol}: {e}")
            return []

    def store_system_config(self, config_name: str, config_data: Dict) -> bool:
        """Store system configuration."""
        start_time = time.time()
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT OR REPLACE INTO system_config (name, config_data, updated_at)
                    VALUES (?, ?, ?)
                """, (config_name, json.dumps(config_data), datetime.now().isoformat()))
                
                conn.commit()
                self._update_query_stats(time.time() - start_time)
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to store config {config_name}: {e}")
            return False

    def get_system_config(self, config_name: str) -> Optional[Dict]:
        """Retrieve system configuration."""
        start_time = time.time()
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT config_data FROM system_config WHERE name = ?
                """, (config_name,))
                
                row = cursor.fetchone()
                self._update_query_stats(time.time() - start_time)
                
                if row:
                    return json.loads(row[0])
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to get config {config_name}: {e}")
            return None

    def log_performance_metric(self, metric_name: str, value: float, context: Dict = None) -> bool:
        """Log performance metrics for monitoring."""
        start_time = time.time()
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO performance_log (metric_name, value, context, timestamp)
                    VALUES (?, ?, ?, ?)
                """, (
                    metric_name, 
                    value, 
                    json.dumps(context or {}), 
                    datetime.now().isoformat()
                ))
                
                conn.commit()
                self._update_query_stats(time.time() - start_time)
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to log performance metric {metric_name}: {e}")
            return False

    def get_performance_metrics(self, metric_name: str = None, hours_back: int = 24) -> List[Dict]:
        """Retrieve performance metrics for analysis."""
        start_time = time.time()
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                since_time = datetime.now() - timedelta(hours=hours_back)
                
                if metric_name:
                    cursor.execute("""
                        SELECT metric_name, value, context, timestamp
                        FROM performance_log 
                        WHERE metric_name = ? AND timestamp >= ?
                        ORDER BY timestamp DESC
                    """, (metric_name, since_time.isoformat()))
                else:
                    cursor.execute("""
                        SELECT metric_name, value, context, timestamp
                        FROM performance_log 
                        WHERE timestamp >= ?
                        ORDER BY timestamp DESC
                    """, (since_time.isoformat(),))
                
                metrics = []
                for row in cursor.fetchall():
                    metrics.append({
                        'metric_name': row[0],
                        'value': row[1],
                        'context': json.loads(row[2]) if row[2] else {},
                        'timestamp': row[3]
                    })
                
                self._update_query_stats(time.time() - start_time)
                return metrics
                
        except Exception as e:
            self.logger.error(f"Failed to get performance metrics: {e}")
            return []

    def get_database_stats(self) -> Dict:
        """Get database statistics and health metrics."""
        stats = {
            'connection_pool_size': len(self._connection_pool),
            'query_stats': self._query_stats.copy(),
            'db_size_mb': 0,
            'table_counts': {},
            'last_maintenance': None
        }
        
        try:
            if self.db_path.exists():
                stats['db_size_mb'] = self.db_path.stat().st_size / (1024 * 1024)
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get table counts
                tables = ['probability_tables', 'tick_data', 'system_config', 'performance_log']
                for table in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    stats['table_counts'][table] = cursor.fetchone()[0]
                
        except Exception as e:
            self.logger.error(f"Failed to get database stats: {e}")
        
        return stats

    def cleanup_old_data(self) -> bool:
        """Clean up old data based on retention policies."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Clean old probability tables
                prob_cutoff = datetime.now() - timedelta(days=self.config.probability_table_retention_days)
                cursor.execute("DELETE FROM probability_tables WHERE created_at < ?", (prob_cutoff.isoformat(),))
                prob_deleted = cursor.rowcount
                
                # Clean old tick data
                tick_cutoff = datetime.now() - timedelta(days=self.config.tick_data_retention_days)
                cursor.execute("DELETE FROM tick_data WHERE timestamp < ?", (tick_cutoff.isoformat(),))
                tick_deleted = cursor.rowcount
                
                # Clean old performance logs
                log_cutoff = datetime.now() - timedelta(days=self.config.log_retention_days)
                cursor.execute("DELETE FROM performance_log WHERE timestamp < ?", (log_cutoff.isoformat(),))
                log_deleted = cursor.rowcount
                
                conn.commit()
                
                self.logger.info(f"Cleaned up {prob_deleted} probability records, {tick_deleted} tick records, {log_deleted} log records")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to cleanup old data: {e}")
            return False

    def _initialize_database(self):
        """Initialize database schema with optimized indexes."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Probability tables
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS probability_tables (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        symbol TEXT NOT NULL,
                        trigger_type TEXT NOT NULL,
                        outcome TEXT NOT NULL,
                        direction TEXT NOT NULL,
                        state TEXT NOT NULL,
                        successes INTEGER NOT NULL,
                        total INTEGER NOT NULL,
                        probability REAL NOT NULL,
                        created_at TEXT NOT NULL
                    )
                """)
                
                # Tick data table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS tick_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        symbol TEXT NOT NULL,
                        bid REAL NOT NULL,
                        ask REAL NOT NULL,
                        spread REAL NOT NULL,
                        timestamp TEXT NOT NULL
                    )
                """)
                
                # System configuration
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS system_config (
                        name TEXT PRIMARY KEY,
                        config_data TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                """)
                
                # Performance logging
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS performance_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        metric_name TEXT NOT NULL,
                        value REAL NOT NULL,
                        context TEXT,
                        timestamp TEXT NOT NULL
                    )
                """)
                
                # Create optimized indexes for fast queries
                indexes = [
                    "CREATE INDEX IF NOT EXISTS idx_prob_symbol_prob ON probability_tables (symbol, probability DESC)",
                    "CREATE INDEX IF NOT EXISTS idx_prob_symbol_total ON probability_tables (symbol, total DESC)", 
                    "CREATE INDEX IF NOT EXISTS idx_tick_symbol_time ON tick_data (symbol, timestamp)",
                    "CREATE INDEX IF NOT EXISTS idx_perf_metric_time ON performance_log (metric_name, timestamp)"
                ]
                
                for index_sql in indexes:
                    cursor.execute(index_sql)
                
                conn.commit()
                self.logger.info("Database schema initialized successfully")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            raise

    def _get_connection_from_pool(self) -> sqlite3.Connection:
        """Get connection from pool or create new one with proper concurrency controls."""
        with self._pool_lock:
            if self._connection_pool:
                conn = self._connection_pool.pop()
                # Track active connection
                self._active_connections[id(conn)] = conn
                return conn
        
        # Create new connection with better locking strategy
        conn = sqlite3.connect(
            self.db_path,
            timeout=self.config.connection_timeout,
            check_same_thread=False,
            isolation_level=None  # Autocommit mode to prevent locks
        )
        
        # Configure connection for better concurrency and performance
        conn.execute("PRAGMA journal_mode=WAL")  # WAL mode for better concurrency
        conn.execute("PRAGMA synchronous=NORMAL")  # Balance safety and speed
        conn.execute("PRAGMA cache_size=10000")
        conn.execute("PRAGMA temp_store=MEMORY")
        conn.execute("PRAGMA busy_timeout=30000")  # 30 second timeout for locks
        conn.execute("PRAGMA locking_mode=NORMAL")  # Allow concurrent access
        
        # Track active connection
        self._active_connections[id(conn)] = conn
        return conn

    def _return_connection_to_pool(self, conn: sqlite3.Connection):
        """Return connection to pool with proper cleanup."""
        with self._pool_lock:
            # Remove from active connections
            conn_id = id(conn)
            if conn_id in self._active_connections:
                del self._active_connections[conn_id]
            
            # Ensure connection is not in a transaction
            try:
                conn.rollback()  # Clear any pending transaction
            except sqlite3.Error:
                pass
            
            if len(self._connection_pool) < self.config.max_connections and not self._shutdown_requested:
                self._connection_pool.append(conn)
            else:
                try:
                    conn.close()
                except sqlite3.Error:
                    pass

    def _close_all_connections(self):
        """Close all pooled and active connections."""
        self._shutdown_requested = True
        with self._pool_lock:
            # Close pooled connections
            for conn in self._connection_pool:
                try:
                    conn.close()
                except sqlite3.Error:
                    pass
            self._connection_pool.clear()
            
            # Close any remaining active connections
            for conn in self._active_connections.values():
                try:
                    conn.close()
                except sqlite3.Error:
                    pass
            self._active_connections.clear()

    def shutdown(self):
        """Public method to gracefully shutdown the database manager."""
        self.logger.info("Shutting down database manager...")
        self._stop_maintenance()
        self._close_all_connections()
        self.logger.info("Database manager shutdown complete")

    def _update_query_stats(self, query_time: float):
        """Update query performance statistics."""
        self._query_stats['total_queries'] += 1
        self._query_stats['last_query_time'] = datetime.now()
        
        # Update rolling average
        if self._query_stats['avg_query_time_ms'] == 0:
            self._query_stats['avg_query_time_ms'] = query_time * 1000
        else:
            self._query_stats['avg_query_time_ms'] = (
                self._query_stats['avg_query_time_ms'] * 0.9 + (query_time * 1000) * 0.1
            )
        
        # Track slow queries
        if query_time * 1000 > self.config.performance_target_ms:
            self._query_stats['slow_queries'] += 1

    def _start_maintenance(self):
        """Start background maintenance thread."""
        self._maintenance_active = True
        self._maintenance_thread = threading.Thread(target=self._maintenance_loop, daemon=True)
        self._maintenance_thread.start()

    def _stop_maintenance(self):
        """Stop background maintenance."""
        self._maintenance_active = False
        if self._maintenance_thread:
            self._maintenance_thread.join(timeout=5)

    def _maintenance_loop(self):
        """Background maintenance tasks."""
        last_vacuum = datetime.now()
        last_backup = datetime.now()
        
        while self._maintenance_active:
            try:
                now = datetime.now()
                
                # Periodic VACUUM
                if now - last_vacuum > timedelta(hours=self.config.vacuum_interval_hours):
                    self._vacuum_database()
                    last_vacuum = now
                
                # Periodic cleanup
                if now - last_backup > timedelta(hours=self.config.backup_interval_hours):
                    self.cleanup_old_data()
                    last_backup = now
                
                time.sleep(3600)  # Check hourly
                
            except Exception as e:
                self.logger.error(f"Maintenance loop error: {e}")
                time.sleep(3600)

    def _vacuum_database(self):
        """Vacuum database to reclaim space and optimize."""
        try:
            with self.get_connection() as conn:
                conn.execute("VACUUM")
                conn.execute("ANALYZE") 
            self.logger.info("Database vacuum and analyze completed")
        except Exception as e:
            self.logger.error(f"Database vacuum failed: {e}")