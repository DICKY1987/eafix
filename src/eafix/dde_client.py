"""Production DDE client for MetaTrader 4/5 connectivity with real-time price feeds.

This module implements comprehensive DDE (Dynamic Data Exchange) communication
with MetaTrader platforms, including:
- Real-time BID/ASK/TIME topic subscription
- Connection management with automatic reconnection
- Thread-safe circular buffers for tick data
- 0.1s polling intervals with configurable timeouts
- Comprehensive error handling and recovery
"""

from __future__ import annotations

import logging
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Callable, Deque
from enum import Enum


class DDEConnectionState(Enum):
    """DDE connection states."""
    DISCONNECTED = "DISCONNECTED"
    CONNECTING = "CONNECTING"
    CONNECTED = "CONNECTED"
    FAILED = "FAILED"
    RECONNECTING = "RECONNECTING"


@dataclass
class TickData:
    """Individual tick data point."""
    symbol: str
    bid: float
    ask: float
    spread: float
    timestamp: datetime
    server_time: Optional[datetime] = None
    
    @property
    def mid_price(self) -> float:
        """Calculate mid price: (bid + ask) / 2"""
        return (self.bid + self.ask) / 2.0


@dataclass
class DDEConfig:
    """DDE client configuration."""
    poll_interval_ms: int = 100  # 0.1s polling
    timeout_sec: int = 30
    reconnect_sec: int = 5
    reconnect_attempts: int = 10
    buffer_size: int = 1000
    
    # DDE specific settings
    server_name: str = "MT4"
    service_name: str = ""  # Auto-detect
    topics: List[str] = field(default_factory=lambda: ["BID", "ASK", "TIME"])
    
    # Symbols to monitor
    symbols: List[str] = field(default_factory=lambda: [
        "EURUSD", "GBPUSD", "USDJPY", "USDCAD", "AUDUSD", "NZDUSD", "USDCHF"
    ])


class DDEClient:
    """Production DDE client with MT4/MT5 integration."""

    def __init__(self, config: DDEConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Connection state
        self.state = DDEConnectionState.DISCONNECTED
        self.connection_handle = None
        self._connected_topics = set()
        
        # Thread-safe tick buffers
        self._buffers: Dict[str, Deque[TickData]] = {}
        self._buffer_lock = threading.RLock()
        
        # Background polling
        self._polling_active = False
        self._polling_thread: Optional[threading.Thread] = None
        
        # Callbacks for real-time data
        self._tick_callbacks: List[Callable[[TickData], None]] = []
        
        # Statistics
        self._stats = {
            'ticks_received': 0,
            'connection_failures': 0,
            'last_tick_time': None,
            'symbols_active': set()
        }

    def connect(self) -> bool:
        """Establish DDE connection to MetaTrader."""
        if self.state == DDEConnectionState.CONNECTED:
            return True
            
        try:
            self.state = DDEConnectionState.CONNECTING
            self.logger.info("Connecting to MetaTrader DDE server...")
            
            # Try to import DDE libraries
            try:
                import win32ui
                import dde
                
                # Create DDE server connection
                self.dde_server = dde.CreateServer()
                self.dde_server.Create("PythonDDEClient")
                
                # Try to connect to MT4/MT5
                service_names = [self.config.service_name] if self.config.service_name else ["MT4", "MT5", "MetaTrader"]
                
                connection_established = False
                for service in service_names:
                    try:
                        self.connection_handle = dde.CreateConversation(self.dde_server)
                        self.connection_handle.ConnectTo(service, "QUOTE")
                        connection_established = True
                        self.logger.info(f"Connected to {service} DDE service")
                        break
                    except Exception as e:
                        self.logger.debug(f"Failed to connect to {service}: {e}")
                        continue
                
                if not connection_established:
                    raise Exception("Could not connect to any MetaTrader DDE service")
                
                # Subscribe to symbols and topics
                self._subscribe_to_symbols()
                
                self.state = DDEConnectionState.CONNECTED
                
                # Start background polling
                self._start_polling()
                
                self.logger.info(f"DDE client connected successfully, monitoring {len(self.config.symbols)} symbols")
                return True
                
            except ImportError:
                self.logger.error("DDE libraries not available - install pywin32")
                self.state = DDEConnectionState.FAILED
                return False
                
        except Exception as e:
            self.logger.error(f"DDE connection failed: {e}")
            self.state = DDEConnectionState.FAILED
            self._stats['connection_failures'] += 1
            return False

    def disconnect(self):
        """Disconnect from DDE server."""
        self.logger.info("Disconnecting DDE client...")
        
        # Stop polling
        self._stop_polling()
        
        # Close DDE connection
        if self.connection_handle:
            try:
                self.connection_handle.Disconnect()
            except Exception as e:
                self.logger.debug(f"Error disconnecting DDE: {e}")
            self.connection_handle = None
        
        if hasattr(self, 'dde_server'):
            try:
                self.dde_server.Destroy()
            except Exception as e:
                self.logger.debug(f"Error destroying DDE server: {e}")
            delattr(self, 'dde_server')
        
        self.state = DDEConnectionState.DISCONNECTED
        self._connected_topics.clear()
        
        self.logger.info("DDE client disconnected")

    def subscribe(self, symbol: str) -> bool:
        """Subscribe to real-time data for a symbol."""
        if symbol not in self.config.symbols:
            self.config.symbols.append(symbol)
        
        # Initialize buffer for symbol
        with self._buffer_lock:
            if symbol not in self._buffers:
                self._buffers[symbol] = deque(maxlen=self.config.buffer_size)
        
        # If connected, subscribe to DDE topics
        if self.state == DDEConnectionState.CONNECTED:
            return self._subscribe_symbol_topics(symbol)
        
        return True

    def unsubscribe(self, symbol: str) -> bool:
        """Unsubscribe from symbol data."""
        if symbol in self.config.symbols:
            self.config.symbols.remove(symbol)
        
        with self._buffer_lock:
            if symbol in self._buffers:
                del self._buffers[symbol]
        
        # Remove from active stats
        self._stats['symbols_active'].discard(symbol)
        
        return True

    def get_latest_tick(self, symbol: str) -> Optional[TickData]:
        """Get the most recent tick for a symbol."""
        with self._buffer_lock:
            buffer = self._buffers.get(symbol)
            if buffer and len(buffer) > 0:
                return buffer[-1]
        return None

    def get_tick_history(self, symbol: str, count: int = 100) -> List[TickData]:
        """Get recent tick history for a symbol."""
        with self._buffer_lock:
            buffer = self._buffers.get(symbol, deque())
            return list(buffer)[-count:]

    def add_tick_callback(self, callback: Callable[[TickData], None]):
        """Add callback for real-time tick updates."""
        self._tick_callbacks.append(callback)

    def remove_tick_callback(self, callback: Callable[[TickData], None]):
        """Remove tick update callback."""
        if callback in self._tick_callbacks:
            self._tick_callbacks.remove(callback)

    def get_connection_status(self) -> Dict:
        """Get detailed connection status."""
        with self._buffer_lock:
            buffer_stats = {
                symbol: len(buffer) for symbol, buffer in self._buffers.items()
            }
        
        return {
            "state": self.state.value,
            "connected": self.state == DDEConnectionState.CONNECTED,
            "symbols_subscribed": len(self.config.symbols),
            "symbols_active": len(self._stats['symbols_active']),
            "ticks_received": self._stats['ticks_received'],
            "connection_failures": self._stats['connection_failures'],
            "last_tick_time": self._stats['last_tick_time'].isoformat() if self._stats['last_tick_time'] else None,
            "buffer_stats": buffer_stats,
            "polling_active": self._polling_active
        }

    def push_tick(self, symbol: str, bid: float, ask: float, timestamp: float = None):
        """Push tick data (for testing or manual data injection)."""
        tick_time = datetime.fromtimestamp(timestamp) if timestamp else datetime.now()
        
        tick = TickData(
            symbol=symbol,
            bid=bid,
            ask=ask,
            spread=ask - bid,
            timestamp=tick_time
        )
        
        self._process_tick(tick)

    def _subscribe_to_symbols(self):
        """Subscribe to all configured symbols."""
        for symbol in self.config.symbols:
            self._subscribe_symbol_topics(symbol)

    def _subscribe_symbol_topics(self, symbol: str) -> bool:
        """Subscribe to DDE topics for a specific symbol."""
        if not self.connection_handle:
            return False
        
        try:
            for topic in self.config.topics:
                topic_name = f"{symbol}_{topic}"
                try:
                    # Request initial data for the topic
                    self.connection_handle.Request(topic_name)
                    self._connected_topics.add(topic_name)
                except Exception as e:
                    self.logger.warning(f"Could not subscribe to {topic_name}: {e}")
            
            return len(self._connected_topics) > 0
            
        except Exception as e:
            self.logger.error(f"Failed to subscribe topics for {symbol}: {e}")
            return False

    def _start_polling(self):
        """Start background DDE polling thread."""
        if self._polling_active:
            return
        
        self._polling_active = True
        self._polling_thread = threading.Thread(target=self._polling_loop, daemon=True)
        self._polling_thread.start()
        
        self.logger.info(f"Started DDE polling at {self.config.poll_interval_ms}ms intervals")

    def _stop_polling(self):
        """Stop background DDE polling."""
        self._polling_active = False
        if self._polling_thread:
            self._polling_thread.join(timeout=5)
        self._polling_thread = None

    def _polling_loop(self):
        """Background polling loop for DDE data."""
        poll_interval = self.config.poll_interval_ms / 1000.0  # Convert to seconds
        
        while self._polling_active:
            try:
                if self.state == DDEConnectionState.CONNECTED and self.connection_handle:
                    self._poll_all_symbols()
                
                time.sleep(poll_interval)
                
            except Exception as e:
                self.logger.error(f"Polling loop error: {e}")
                if self.state == DDEConnectionState.CONNECTED:
                    self._attempt_reconnection()
                time.sleep(poll_interval)

    def _poll_all_symbols(self):
        """Poll all subscribed symbols for latest data."""
        symbol_data = {}
        
        # Collect current data for all symbols
        for symbol in self.config.symbols:
            try:
                bid_topic = f"{symbol}_BID"
                ask_topic = f"{symbol}_ASK"
                time_topic = f"{symbol}_TIME"
                
                if bid_topic in self._connected_topics and ask_topic in self._connected_topics:
                    # Request current values
                    bid_data = self.connection_handle.Request(bid_topic)
                    ask_data = self.connection_handle.Request(ask_topic)
                    
                    if bid_data and ask_data:
                        try:
                            bid = float(bid_data)
                            ask = float(ask_data)
                            
                            # Try to get server time
                            server_time = None
                            if time_topic in self._connected_topics:
                                time_data = self.connection_handle.Request(time_topic)
                                if time_data:
                                    try:
                                        server_time = datetime.strptime(time_data, "%Y.%m.%d %H:%M:%S")
                                    except ValueError as e:
                                        self.logger.debug(f"Invalid time format from server: {time_data}, error: {e}")
                                        server_time = None
                                    except Exception as e:
                                        self.logger.error(f"Unexpected error parsing server time: {e}")
                                        server_time = None
                            
                            # Create tick data
                            tick = TickData(
                                symbol=symbol,
                                bid=bid,
                                ask=ask,
                                spread=ask - bid,
                                timestamp=datetime.now(),
                                server_time=server_time
                            )
                            
                            self._process_tick(tick)
                            
                        except (ValueError, TypeError) as e:
                            self.logger.debug(f"Invalid price data for {symbol}: {e}")
                            
            except Exception as e:
                self.logger.debug(f"Failed to poll {symbol}: {e}")

    def _process_tick(self, tick: TickData):
        """Process incoming tick data."""
        # Update statistics
        self._stats['ticks_received'] += 1
        self._stats['last_tick_time'] = tick.timestamp
        self._stats['symbols_active'].add(tick.symbol)
        
        # Store in buffer
        with self._buffer_lock:
            buffer = self._buffers.setdefault(tick.symbol, deque(maxlen=self.config.buffer_size))
            buffer.append(tick)
        
        # Notify callbacks
        for callback in self._tick_callbacks:
            try:
                callback(tick)
            except Exception as e:
                self.logger.error(f"Tick callback error: {e}")

    def _attempt_reconnection(self):
        """Attempt to reconnect after connection failure."""
        if self.state == DDEConnectionState.RECONNECTING:
            return  # Already attempting
        
        self.state = DDEConnectionState.RECONNECTING
        self.logger.warning("DDE connection lost, attempting reconnection...")
        
        for attempt in range(self.config.reconnect_attempts):
            try:
                time.sleep(self.config.reconnect_sec)
                
                # Disconnect and try to reconnect
                if self.connection_handle:
                    try:
                        self.connection_handle.Disconnect()
                    except Exception as e:
                        self.logger.debug(f"Error during reconnection disconnect: {e}")
                
                if self.connect():
                    self.logger.info(f"DDE reconnected after {attempt + 1} attempts")
                    return
                
            except Exception as e:
                self.logger.error(f"Reconnection attempt {attempt + 1} failed: {e}")
        
        self.logger.error("DDE reconnection failed after all attempts")
        self.state = DDEConnectionState.FAILED

