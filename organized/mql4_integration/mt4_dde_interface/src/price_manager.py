"""
Price Data Management System with circular buffers and OHLC aggregation
"""
import threading
import time
from collections import deque, defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
import logging
import numpy as np
from dataclasses import dataclass


@dataclass
class PriceTick:
    """Single price tick data structure"""
    symbol: str
    bid: float
    ask: float
    spread: float
    timestamp: datetime
    
    @property
    def mid_price(self) -> float:
        """Calculate mid price"""
        return (self.bid + self.ask) / 2.0


@dataclass
class OHLCBar:
    """OHLC bar data structure"""
    symbol: str
    timeframe: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    timestamp: datetime
    
    def __post_init__(self):
        """Validate OHLC data after initialization"""
        if self.high < max(self.open, self.close) or self.low > min(self.open, self.close):
            raise ValueError("Invalid OHLC data: high/low inconsistent with open/close")


class CircularBuffer:
    """Thread-safe circular buffer for price data"""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.buffer = deque(maxlen=max_size)
        self.lock = threading.RLock()
        
    def add(self, item: Any):
        """Add item to buffer (thread-safe)"""
        with self.lock:
            self.buffer.append(item)
    
    def get_last(self, count: int = 1) -> List[Any]:
        """Get last N items from buffer"""
        with self.lock:
            if count <= 0:
                return []
            return list(self.buffer)[-count:] if len(self.buffer) >= count else list(self.buffer)
    
    def get_all(self) -> List[Any]:
        """Get all items from buffer"""
        with self.lock:
            return list(self.buffer)
    
    def size(self) -> int:
        """Get current buffer size"""
        with self.lock:
            return len(self.buffer)
    
    def clear(self):
        """Clear buffer contents"""
        with self.lock:
            self.buffer.clear()


class TimeframeAggregator:
    """Aggregates tick data into OHLC bars for different timeframes"""
    
    TIMEFRAMES = {
        'M1': timedelta(minutes=1),
        'M5': timedelta(minutes=5),
        'M15': timedelta(minutes=15),
        'M30': timedelta(minutes=30),
        'H1': timedelta(hours=1),
        'H4': timedelta(hours=4),
        'D1': timedelta(days=1)
    }
    
    def __init__(self):
        self.current_bars = {}  # Current incomplete bars
        self.completed_bars = defaultdict(lambda: CircularBuffer(1000))  # Completed bars by timeframe
        self.lock = threading.RLock()
    
    def add_tick(self, tick: PriceTick) -> Dict[str, OHLCBar]:
        """
        Add tick and return any completed OHLC bars
        
        Args:
            tick: Price tick to process
            
        Returns:
            Dictionary of completed bars by timeframe
        """
        completed = {}
        
        with self.lock:
            for timeframe, delta in self.TIMEFRAMES.items():
                bar_key = f"{tick.symbol}_{timeframe}"
                bar_time = self._get_bar_time(tick.timestamp, timeframe)
                
                # Check if we need to complete current bar and start new one
                current_bar = self.current_bars.get(bar_key)
                if current_bar is None or current_bar.timestamp != bar_time:
                    # Complete previous bar if exists
                    if current_bar is not None:
                        self.completed_bars[bar_key].add(current_bar)
                        completed[timeframe] = current_bar
                    
                    # Start new bar
                    self.current_bars[bar_key] = OHLCBar(
                        symbol=tick.symbol,
                        timeframe=timeframe,
                        open=tick.mid_price,
                        high=tick.mid_price,
                        low=tick.mid_price,
                        close=tick.mid_price,
                        volume=1,
                        timestamp=bar_time
                    )
                else:
                    # Update current bar
                    current_bar.high = max(current_bar.high, tick.mid_price)
                    current_bar.low = min(current_bar.low, tick.mid_price)
                    current_bar.close = tick.mid_price
                    current_bar.volume += 1
        
        return completed
    
    def _get_bar_time(self, timestamp: datetime, timeframe: str) -> datetime:
        """Calculate bar start time for given timestamp and timeframe"""
        if timeframe == 'M1':
            return timestamp.replace(second=0, microsecond=0)
        elif timeframe == 'M5':
            minute = (timestamp.minute // 5) * 5
            return timestamp.replace(minute=minute, second=0, microsecond=0)
        elif timeframe == 'M15':
            minute = (timestamp.minute // 15) * 15
            return timestamp.replace(minute=minute, second=0, microsecond=0)
        elif timeframe == 'M30':
            minute = (timestamp.minute // 30) * 30
            return timestamp.replace(minute=minute, second=0, microsecond=0)
        elif timeframe == 'H1':
            return timestamp.replace(minute=0, second=0, microsecond=0)
        elif timeframe == 'H4':
            hour = (timestamp.hour // 4) * 4
            return timestamp.replace(hour=hour, minute=0, second=0, microsecond=0)
        elif timeframe == 'D1':
            return timestamp.replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            return timestamp
    
    def get_bars(self, symbol: str, timeframe: str, count: int = 100) -> List[OHLCBar]:
        """Get OHLC bars for symbol and timeframe"""
        bar_key = f"{symbol}_{timeframe}"
        return self.completed_bars[bar_key].get_last(count)


class PriceManager:
    """Main price data management system"""
    
    def __init__(self, buffer_size: int = 1000):
        self.buffer_size = buffer_size
        self.tick_buffers = defaultdict(lambda: CircularBuffer(buffer_size))
        self.aggregator = TimeframeAggregator()
        self.symbol_stats = defaultdict(dict)
        self.lock = threading.RLock()
        self.logger = logging.getLogger(__name__)

        # Performance tracking
        self.total_ticks_received = 0
        self.ticks_per_symbol = defaultdict(int)
        self.last_cleanup = datetime.now()
        self.cleanup_interval = timedelta(hours=1)

        # Callback management for price updates
        self._callbacks: List[Callable[[PriceTick], None]] = []

    def add_callback(self, callback: Callable[[PriceTick], None]):
        """Register a callback to receive price ticks"""
        with self.lock:
            if callback not in self._callbacks:
                self._callbacks.append(callback)

    def remove_callback(self, callback: Callable[[PriceTick], None]):
        """Remove a previously registered callback"""
        with self.lock:
            if callback in self._callbacks:
                self._callbacks.remove(callback)

    def _notify_callbacks(self, tick: PriceTick):
        """Notify all registered callbacks of a new tick"""
        # Make a snapshot of callbacks to avoid modification during iteration
        callbacks = list(self._callbacks)
        for cb in callbacks:
            try:
                cb(tick)
            except Exception as e:
                self.logger.error(f"Error in price callback: {e}")
    
    def add_price_tick(self, symbol: str, price_data: Dict) -> bool:
        """
        Add price tick to management system
        
        Args:
            symbol: Currency pair symbol
            price_data: Dictionary containing price data
            
        Returns:
            True if tick was valid and added, False otherwise
        """
        try:
            # Validate price data
            if not self.validate_price_data(price_data):
                self.logger.warning(f"Invalid price data for {symbol}: {price_data}")
                return False
            
            # Create price tick
            tick = PriceTick(
                symbol=symbol,
                bid=float(price_data['bid']),
                ask=float(price_data['ask']),
                spread=float(price_data.get('spread', price_data['ask'] - price_data['bid'])),
                timestamp=price_data.get('timestamp', datetime.now())
            )
            
            with self.lock:
                # Add to tick buffer
                self.tick_buffers[symbol].add(tick)
                
                # Update statistics
                self.total_ticks_received += 1
                self.ticks_per_symbol[symbol] += 1
                
                # Update symbol statistics
                self._update_symbol_stats(symbol, tick)
                
                # Process OHLC aggregation
                completed_bars = self.aggregator.add_tick(tick)
                
                # Periodic cleanup
                if datetime.now() - self.last_cleanup > self.cleanup_interval:
                    self.cleanup_old_data()

            # Notify listeners outside lock to avoid potential deadlocks
            self._notify_callbacks(tick)

            return True
            
        except Exception as e:
            self.logger.error(f"Error adding price tick for {symbol}: {e}")
            return False
    
    def get_price_history(self, symbol: str, count: int = 100) -> List[PriceTick]:
        """
        Get price history for symbol
        
        Args:
            symbol: Currency pair symbol
            count: Number of ticks to retrieve
            
        Returns:
            List of PriceTick objects
        """
        return self.tick_buffers[symbol].get_last(count)
    
    def get_latest_price(self, symbol: str) -> Optional[PriceTick]:
        """
        Get latest price for symbol
        
        Args:
            symbol: Currency pair symbol
            
        Returns:
            Latest PriceTick or None if not available
        """
        ticks = self.tick_buffers[symbol].get_last(1)
        return ticks[0] if ticks else None
    
    def get_ohlc_data(self, symbol: str, timeframe: str, count: int = 100) -> List[OHLCBar]:
        """
        Get OHLC data for symbol and timeframe
        
        Args:
            symbol: Currency pair symbol
            timeframe: Timeframe (M1, M5, M15, M30, H1, H4, D1)
            count: Number of bars to retrieve
            
        Returns:
            List of OHLCBar objects
        """
        return self.aggregator.get_bars(symbol, timeframe, count)
    
    def get_price_array(self, symbol: str, price_type: str = 'mid', count: int = 100) -> np.ndarray:
        """
        Get price data as numpy array for calculations
        
        Args:
            symbol: Currency pair symbol
            price_type: 'bid', 'ask', 'mid', or 'spread'
            count: Number of prices to retrieve
            
        Returns:
            Numpy array of prices
        """
        ticks = self.get_price_history(symbol, count)
        if not ticks:
            return np.array([])
        
        if price_type == 'bid':
            return np.array([tick.bid for tick in ticks])
        elif price_type == 'ask':
            return np.array([tick.ask for tick in ticks])
        elif price_type == 'mid':
            return np.array([tick.mid_price for tick in ticks])
        elif price_type == 'spread':
            return np.array([tick.spread for tick in ticks])
        else:
            raise ValueError(f"Invalid price_type: {price_type}")
    
    def validate_price_data(self, price_data: Dict) -> bool:
        """
        Validate price data structure and values
        
        Args:
            price_data: Price data dictionary
            
        Returns:
            True if valid, False otherwise
        """
        required_fields = ['bid', 'ask']
        
        # Check required fields
        for field in required_fields:
            if field not in price_data:
                return False
        
        try:
            bid = float(price_data['bid'])
            ask = float(price_data['ask'])
            
            # Basic validation
            if bid <= 0 or ask <= 0:
                return False
            
            if ask < bid:  # Ask should be >= bid
                return False
            
            # Reasonable spread check (adjust as needed)
            spread = ask - bid
            if spread > bid * 0.01:  # Spread > 1% of bid price might be suspicious
                self.logger.warning(f"Large spread detected: {spread} (bid: {bid}, ask: {ask})")
            
            return True
            
        except (ValueError, TypeError):
            return False
    
    def _update_symbol_stats(self, symbol: str, tick: PriceTick):
        """Update statistics for symbol"""
        stats = self.symbol_stats[symbol]
        
        # Update basic stats
        stats['last_tick'] = tick.timestamp
        stats['last_bid'] = tick.bid
        stats['last_ask'] = tick.ask
        stats['last_spread'] = tick.spread
        
        # Initialize or update min/max tracking
        if 'min_bid' not in stats or tick.bid < stats['min_bid']:
            stats['min_bid'] = tick.bid
        if 'max_bid' not in stats or tick.bid > stats['max_bid']:
            stats['max_bid'] = tick.bid
        
        if 'min_ask' not in stats or tick.ask < stats['min_ask']:
            stats['min_ask'] = tick.ask
        if 'max_ask' not in stats or tick.ask > stats['max_ask']:
            stats['max_ask'] = tick.ask
        
        # Calculate average spread (simple moving average over last 100 ticks)
        recent_ticks = self.get_price_history(symbol, 100)
        if recent_ticks:
            avg_spread = sum(t.spread for t in recent_ticks) / len(recent_ticks)
            stats['avg_spread'] = avg_spread
    
    def get_symbol_statistics(self, symbol: str) -> Dict:
        """Get statistics for symbol"""
        stats = self.symbol_stats[symbol].copy()
        stats['total_ticks'] = self.ticks_per_symbol[symbol]
        stats['buffer_size'] = self.tick_buffers[symbol].size()
        return stats
    
    def get_all_symbols(self) -> List[str]:
        """Get list of all symbols with data"""
        return list(self.tick_buffers.keys())
    
    def cleanup_old_data(self):
        """Clean up old data and update cleanup timestamp"""
        # Buffers are automatically managed by CircularBuffer
        # This method can be extended for additional cleanup tasks
        self.last_cleanup = datetime.now()
        self.logger.debug("Performed data cleanup")
    
    def get_system_stats(self) -> Dict:
        """Get overall system statistics"""
        return {
            'total_ticks_received': self.total_ticks_received,
            'active_symbols': len(self.tick_buffers),
            'buffer_size': self.buffer_size,
            'last_cleanup': self.last_cleanup,
            'memory_usage_mb': self._estimate_memory_usage()
        }
    
    def _estimate_memory_usage(self) -> float:
        """Estimate memory usage in MB (rough calculation)"""
        # Rough estimate: each tick ~200 bytes, buffer size * symbols * tick size
        total_ticks = sum(buffer.size() for buffer in self.tick_buffers.values())
        return (total_ticks * 200) / (1024 * 1024)  # Convert to MB
    
    def reset_symbol_data(self, symbol: str):
        """Reset all data for a specific symbol"""
        with self.lock:
            if symbol in self.tick_buffers:
                self.tick_buffers[symbol].clear()
            if symbol in self.symbol_stats:
                del self.symbol_stats[symbol]
            self.ticks_per_symbol[symbol] = 0
            
            # Clear OHLC data
            for timeframe in TimeframeAggregator.TIMEFRAMES.keys():
                bar_key = f"{symbol}_{timeframe}"
                if bar_key in self.aggregator.completed_bars:
                    self.aggregator.completed_bars[bar_key].clear()
                if bar_key in self.aggregator.current_bars:
                    del self.aggregator.current_bars[bar_key]
    
    def export_data(self, symbol: str, filename: str, format: str = 'csv'):
        """
        Export price data to file
        
        Args:
            symbol: Symbol to export
            filename: Output filename
            format: Export format ('csv' or 'json')
        """
        ticks = self.get_price_history(symbol, self.buffer_size)
        
        if format.lower() == 'csv':
            import csv
            with open(filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['timestamp', 'symbol', 'bid', 'ask', 'spread'])
                for tick in ticks:
                    writer.writerow([
                        tick.timestamp.isoformat(),
                        tick.symbol,
                        tick.bid,
                        tick.ask,
                        tick.spread
                    ])
        elif format.lower() == 'json':
            import json
            data = [{
                'timestamp': tick.timestamp.isoformat(),
                'symbol': tick.symbol,
                'bid': tick.bid,
                'ask': tick.ask,
                'spread': tick.spread
            } for tick in ticks]
            
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
        else:
            raise ValueError(f"Unsupported export format: {format}")