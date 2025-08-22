"""
HUEY_P Trading Interface - Database Manager
Manages connection to existing HUEY_P trading database
"""

import sqlite3
import pandas as pd
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import shutil

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages database connections and queries for HUEY_P system"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.db_path = Path(config.get('path', 'Database/trading_system.db'))
        self.connection = None
        self.is_connected_flag = False
        
        # Cache for frequently accessed data
        self.cache = {}
        self.cache_expiry = {}
        self.cache_duration = 30  # seconds
        
    def connect(self) -> bool:
        """Connect to the trading database"""
        try:
            # Check if database file exists
            if not self.db_path.exists():
                logger.error(f"Database file not found: {self.db_path}")
                return False
            
            # Create backup if configured
            if self.config.get('backup_on_start', False):
                self.create_backup()
            
            # Connect to database
            self.connection = sqlite3.connect(
                str(self.db_path),
                check_same_thread=False,
                timeout=10.0
            )
            
            # Enable row factory for easier data access
            self.connection.row_factory = sqlite3.Row
            
            # Test connection
            cursor = self.connection.cursor()
            cursor.execute("SELECT 1")
            
            self.is_connected_flag = True
            logger.info(f"Connected to database: {self.db_path}")
            
            # Verify database structure
            self.verify_database_structure()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            self.is_connected_flag = False
            return False
    
    def disconnect(self):
        """Disconnect from database"""
        if self.connection:
            try:
                self.connection.close()
                logger.info("Database connection closed")
            except Exception as e:
                logger.error(f"Error closing database connection: {e}")
            finally:
                self.connection = None
                self.is_connected_flag = False
    
    def is_connected(self) -> bool:
        """Check if database is connected"""
        if not self.is_connected_flag or not self.connection:
            return False
        
        try:
            # Test connection with a simple query
            cursor = self.connection.cursor()
            cursor.execute("SELECT 1")
            return True
        except Exception:
            self.is_connected_flag = False
            return False
    
    def create_backup(self):
        """Create a backup of the database"""
        try:
            backup_path = self.db_path.with_suffix(f'.backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db')
            shutil.copy2(self.db_path, backup_path)
            logger.info(f"Database backup created: {backup_path}")
        except Exception as e:
            logger.warning(f"Failed to create database backup: {e}")
    
    def verify_database_structure(self):
        """Verify that required tables exist"""
        required_tables = [
            'trade_results',
            'performance_metrics', 
            'ea_status',
            'signal_history'
        ]
        
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            existing_tables = [row[0] for row in cursor.fetchall()]
            
            missing_tables = [table for table in required_tables if table not in existing_tables]
            
            if missing_tables:
                logger.warning(f"Missing database tables: {missing_tables}")
            else:
                logger.info("All required database tables found")
                
        except Exception as e:
            logger.error(f"Failed to verify database structure: {e}")
    
    def get_cached_data(self, key: str) -> Optional[Any]:
        """Get cached data if still valid"""
        if key in self.cache and key in self.cache_expiry:
            if datetime.now() < self.cache_expiry[key]:
                return self.cache[key]
        return None
    
    def set_cached_data(self, key: str, data: Any):
        """Set cached data with expiry"""
        self.cache[key] = data
        self.cache_expiry[key] = datetime.now() + timedelta(seconds=self.cache_duration)
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> Optional[List[sqlite3.Row]]:
        """Execute a database query safely"""
        if not self.is_connected():
            logger.error("Database not connected")
            return None
        
        try:
            cursor = self.connection.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            return cursor.fetchall()
            
        except Exception as e:
            logger.error(f"Database query failed: {e}")
            logger.error(f"Query: {query}")
            return None
    
    def get_recent_trades(self, limit: int = 100) -> pd.DataFrame:
        """Get recent closed trades"""
        cache_key = f"recent_trades_{limit}"
        cached_data = self.get_cached_data(cache_key)
        
        if cached_data is not None:
            return cached_data
        
        query = """
        SELECT 
            ticket,
            symbol,
            order_type,
            volume,
            open_price,
            close_price,
            open_time,
            close_time,
            profit,
            commission,
            swap,
            comment
        FROM trade_results 
        WHERE close_time IS NOT NULL 
        ORDER BY close_time DESC 
        LIMIT ?
        """
        
        try:
            rows = self.execute_query(query, (limit,))
            if rows:
                df = pd.DataFrame([dict(row) for row in rows])
                # Convert datetime strings to datetime objects
                df['open_time'] = pd.to_datetime(df['open_time'])
                df['close_time'] = pd.to_datetime(df['close_time'])
                
                self.set_cached_data(cache_key, df)
                return df
            else:
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"Failed to get recent trades: {e}")
            return pd.DataFrame()
    
    def get_daily_performance(self, days: int = 30) -> pd.DataFrame:
        """Get daily performance metrics"""
        cache_key = f"daily_performance_{days}"
        cached_data = self.get_cached_data(cache_key)
        
        if cached_data is not None:
            return cached_data
        
        query = """
        SELECT 
            DATE(close_time) as trade_date,
            COUNT(*) as trade_count,
            SUM(CASE WHEN profit > 0 THEN 1 ELSE 0 END) as wins,
            SUM(CASE WHEN profit <= 0 THEN 1 ELSE 0 END) as losses,
            SUM(profit + commission + swap) as net_profit,
            AVG(profit + commission + swap) as avg_profit,
            MAX(profit) as max_win,
            MIN(profit) as max_loss
        FROM trade_results 
        WHERE close_time IS NOT NULL 
        AND close_time >= date('now', '-{} days')
        GROUP BY DATE(close_time)
        ORDER BY trade_date DESC
        """.format(days)
        
        try:
            rows = self.execute_query(query)
            if rows:
                df = pd.DataFrame([dict(row) for row in rows])
                df['trade_date'] = pd.to_datetime(df['trade_date'])
                df['win_rate'] = df['wins'] / df['trade_count'] * 100
                
                self.set_cached_data(cache_key, df)
                return df
            else:
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"Failed to get daily performance: {e}")
            return pd.DataFrame()
    
    def get_symbol_performance(self) -> pd.DataFrame:
        """Get performance breakdown by symbol"""
        cache_key = "symbol_performance"
        cached_data = self.get_cached_data(cache_key)
        
        if cached_data is not None:
            return cached_data
        
        query = """
        SELECT 
            symbol,
            COUNT(*) as trade_count,
            SUM(CASE WHEN profit > 0 THEN 1 ELSE 0 END) as wins,
            SUM(CASE WHEN profit <= 0 THEN 1 ELSE 0 END) as losses,
            SUM(profit + commission + swap) as net_profit,
            AVG(profit + commission + swap) as avg_profit,
            MAX(profit) as max_win,
            MIN(profit) as max_loss
        FROM trade_results 
        WHERE close_time IS NOT NULL 
        GROUP BY symbol
        ORDER BY net_profit DESC
        """
        
        try:
            rows = self.execute_query(query)
            if rows:
                df = pd.DataFrame([dict(row) for row in rows])
                df['win_rate'] = df['wins'] / df['trade_count'] * 100
                
                self.set_cached_data(cache_key, df)
                return df
            else:
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"Failed to get symbol performance: {e}")
            return pd.DataFrame()
    
    def get_current_positions(self) -> pd.DataFrame:
        """Get currently open positions"""
        query = """
        SELECT 
            ticket,
            symbol,
            order_type,
            volume,
            open_price,
            stop_loss,
            take_profit,
            open_time,
            current_profit,
            comment
        FROM trade_results 
        WHERE close_time IS NULL 
        ORDER BY open_time DESC
        """
        
        try:
            rows = self.execute_query(query)
            if rows:
                df = pd.DataFrame([dict(row) for row in rows])
                df['open_time'] = pd.to_datetime(df['open_time'])
                return df
            else:
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"Failed to get current positions: {e}")
            return pd.DataFrame()
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get overall performance metrics"""
        cache_key = "performance_metrics"
        cached_data = self.get_cached_data(cache_key)
        
        if cached_data is not None:
            return cached_data
        
        query = """
        SELECT 
            COUNT(*) as total_trades,
            SUM(CASE WHEN profit > 0 THEN 1 ELSE 0 END) as total_wins,
            SUM(CASE WHEN profit <= 0 THEN 1 ELSE 0 END) as total_losses,
            SUM(profit + commission + swap) as total_profit,
            AVG(profit + commission + swap) as avg_profit,
            MAX(profit) as max_win,
            MIN(profit) as max_loss,
            AVG(volume) as avg_volume
        FROM trade_results 
        WHERE close_time IS NOT NULL
        """
        
        try:
            rows = self.execute_query(query)
            if rows and len(rows) > 0:
                row = rows[0]
                metrics = {
                    'total_trades': row['total_trades'] or 0,
                    'total_wins': row['total_wins'] or 0,
                    'total_losses': row['total_losses'] or 0,
                    'total_profit': row['total_profit'] or 0.0,
                    'avg_profit': row['avg_profit'] or 0.0,
                    'max_win': row['max_win'] or 0.0,
                    'max_loss': row['max_loss'] or 0.0,
                    'avg_volume': row['avg_volume'] or 0.0,
                    'win_rate': (row['total_wins'] / max(row['total_trades'], 1)) * 100 if row['total_trades'] else 0,
                    'profit_factor': abs(row['max_win'] / row['max_loss']) if row['max_loss'] and row['max_loss'] != 0 else 0
                }
                
                self.set_cached_data(cache_key, metrics)
                return metrics
            else:
                return {}
                
        except Exception as e:
            logger.error(f"Failed to get performance metrics: {e}")
            return {}
    
    def get_ea_status(self) -> Dict[str, Any]:
        """Get current EA status from database"""
        query = """
        SELECT 
            ea_state,
            recovery_state,
            active_trades,
            last_update,
            daily_drawdown,
            account_equity,
            risk_percent
        FROM ea_status 
        ORDER BY last_update DESC 
        LIMIT 1
        """
        
        try:
            rows = self.execute_query(query)
            if rows and len(rows) > 0:
                row = rows[0]
                return dict(row)
            else:
                return {}
                
        except Exception as e:
            logger.error(f"Failed to get EA status: {e}")
            return {}
    
    def get_signal_history(self, limit: int = 50) -> pd.DataFrame:
        """Get recent signal history"""
        query = """
        SELECT 
            signal_id,
            symbol,
            signal_type,
            confidence,
            entry_price,
            stop_loss,
            take_profit,
            timestamp,
            executed,
            result
        FROM signal_history 
        ORDER BY timestamp DESC 
        LIMIT ?
        """
        
        try:
            rows = self.execute_query(query, (limit,))
            if rows:
                df = pd.DataFrame([dict(row) for row in rows])
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                return df
            else:
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"Failed to get signal history: {e}")
            return pd.DataFrame()
    
    def clear_cache(self):
        """Clear all cached data"""
        self.cache.clear()
        self.cache_expiry.clear()
        logger.info("Database cache cleared")