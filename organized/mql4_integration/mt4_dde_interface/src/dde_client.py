"""
MT4 DDE Client for real-time price data connection
"""
import win32ui
import win32con
import dde
import time
import threading
import logging
from datetime import datetime
from typing import Dict, List, Callable, Optional
from collections import defaultdict


class MT4DDEClient:
    """DDE client for connecting to MetaTrader 4 and receiving real-time price data"""
    
    def __init__(self, server_name: str = "MT4"):
        self.server_name = server_name
        self.server = None
        self.conversations = {}
        self.is_connected = False
        self.is_monitoring = False
        self.price_callbacks = []
        self.symbol_data = defaultdict(dict)
        self.monitor_thread = None
        self.update_interval = 0.1
        self.logger = logging.getLogger(__name__)
        
        # Initialize logging
        logging.basicConfig(level=logging.INFO)
        
    def connect(self) -> bool:
        """
        Connect to MT4 DDE server
        Returns True if connection successful, False otherwise
        """
        try:
            self.server = dde.CreateServer()
            self.server.Create("DDEClient")
            self.is_connected = True
            self.logger.info(f"Connected to {self.server_name} DDE server")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to DDE server: {e}")
            self.is_connected = False
            return False
    
    def disconnect(self):
        """Disconnect from DDE server and cleanup resources"""
        self.stop_monitoring()
        
        # Close all conversations
        for symbol, conversation in self.conversations.items():
            try:
                conversation.Disconnect()
            except Exception as e:
                self.logger.error(f"Error disconnecting {symbol}: {e}")
        
        if self.server:
            try:
                self.server.Destroy()
            except Exception as e:
                self.logger.error(f"Error destroying server: {e}")
        
        self.conversations.clear()
        self.is_connected = False
        self.logger.info("Disconnected from DDE server")
    
    def subscribe_to_symbol(self, symbol: str) -> bool:
        """
        Subscribe to price data for a specific symbol
        
        Args:
            symbol: Currency pair symbol (e.g., 'EURUSD')
            
        Returns:
            True if subscription successful, False otherwise
        """
        if not self.is_connected:
            self.logger.error("Not connected to DDE server")
            return False
        
        try:
            # Create conversation for this symbol
            conversation = dde.CreateConversation(self.server)
            conversation.ConnectTo(self.server_name, symbol)
            self.conversations[symbol] = conversation
            
            self.logger.info(f"Subscribed to {symbol}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to subscribe to {symbol}: {e}")
            return False
    
    def unsubscribe_from_symbol(self, symbol: str):
        """Unsubscribe from price data for a specific symbol"""
        if symbol in self.conversations:
            try:
                self.conversations[symbol].Disconnect()
                del self.conversations[symbol]
                if symbol in self.symbol_data:
                    del self.symbol_data[symbol]
                self.logger.info(f"Unsubscribed from {symbol}")
            except Exception as e:
                self.logger.error(f"Error unsubscribing from {symbol}: {e}")
    
    def get_price_data(self, symbol: str) -> Optional[Dict]:
        """
        Get current price data for a symbol
        
        Args:
            symbol: Currency pair symbol
            
        Returns:
            Dictionary with price data or None if not available
        """
        if symbol not in self.conversations:
            return None
        
        try:
            conversation = self.conversations[symbol]
            
            # Request bid and ask prices
            bid_data = conversation.Request("BID")
            ask_data = conversation.Request("ASK")
            time_data = conversation.Request("TIME")
            
            if bid_data and ask_data:
                bid = float(bid_data)
                ask = float(ask_data)
                spread = ask - bid
                timestamp = datetime.now()
                
                price_data = {
                    'symbol': symbol,
                    'bid': bid,
                    'ask': ask,
                    'spread': spread,
                    'timestamp': timestamp,
                    'last_update': timestamp
                }
                
                # Store in symbol data cache
                self.symbol_data[symbol] = price_data
                return price_data
            
        except Exception as e:
            self.logger.error(f"Error getting price data for {symbol}: {e}")
        
        return None
    
    def add_price_callback(self, callback: Callable):
        """Add callback function to receive price updates"""
        if callback not in self.price_callbacks:
            self.price_callbacks.append(callback)
    
    def remove_price_callback(self, callback: Callable):
        """Remove callback function from price updates"""
        if callback in self.price_callbacks:
            self.price_callbacks.remove(callback)
    
    def start_monitoring(self, symbols: List[str], update_interval: float = 0.1):
        """
        Start monitoring price data for specified symbols
        
        Args:
            symbols: List of symbol names to monitor
            update_interval: Update interval in seconds
        """
        if self.is_monitoring:
            self.stop_monitoring()
        
        self.update_interval = update_interval
        
        # Subscribe to all symbols
        for symbol in symbols:
            self.subscribe_to_symbol(symbol)
        
        # Start monitoring thread
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(symbols, update_interval),
            daemon=True
        )
        self.monitor_thread.start()
        
        self.logger.info(f"Started monitoring {len(symbols)} symbols")
    
    def stop_monitoring(self):
        """Stop monitoring price data"""
        self.is_monitoring = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=1.0)
        self.logger.info("Stopped monitoring")
    
    def _monitor_loop(self, symbols: List[str], update_interval: float):
        """
        Internal monitoring loop that runs in separate thread
        
        Args:
            symbols: List of symbols to monitor
            update_interval: Update interval in seconds
        """
        while self.is_monitoring:
            try:
                for symbol in symbols:
                    if not self.is_monitoring:
                        break
                    
                    price_data = self.get_price_data(symbol)
                    if price_data:
                        # Notify all callbacks
                        for callback in self.price_callbacks:
                            try:
                                callback(price_data)
                            except Exception as e:
                                self.logger.error(f"Error in price callback: {e}")
                
                time.sleep(update_interval)
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(1.0)  # Wait before retrying
    
    def get_subscribed_symbols(self) -> List[str]:
        """Get list of currently subscribed symbols"""
        return list(self.conversations.keys())
    
    def get_connection_status(self) -> Dict:
        """Get connection status information"""
        return {
            'is_connected': self.is_connected,
            'is_monitoring': self.is_monitoring,
            'subscribed_symbols': len(self.conversations),
            'active_callbacks': len(self.price_callbacks),
            'server_name': self.server_name
        }
    
    def test_connection(self) -> bool:
        """Test DDE connection by attempting to connect and disconnect"""
        if self.connect():
            # Test with a common symbol
            if self.subscribe_to_symbol("EURUSD"):
                price_data = self.get_price_data("EURUSD")
                self.unsubscribe_from_symbol("EURUSD")
                self.disconnect()
                return price_data is not None
            self.disconnect()
        return False


class DDEConnectionManager:
    """Manager for handling DDE connection lifecycle and reconnection"""
    
    def __init__(self, client: MT4DDEClient):
        self.client = client
        self.auto_reconnect = True
        self.reconnect_interval = 5.0
        self.max_reconnect_attempts = 10
        self.reconnect_thread = None
        self.is_reconnecting = False
        self.logger = logging.getLogger(__name__)
    
    def start_auto_reconnect(self):
        """Start automatic reconnection monitoring"""
        if not self.reconnect_thread or not self.reconnect_thread.is_alive():
            self.reconnect_thread = threading.Thread(
                target=self._reconnect_loop,
                daemon=True
            )
            self.reconnect_thread.start()
    
    def stop_auto_reconnect(self):
        """Stop automatic reconnection monitoring"""
        self.auto_reconnect = False
        if self.reconnect_thread and self.reconnect_thread.is_alive():
            self.reconnect_thread.join(timeout=2.0)
    
    def _reconnect_loop(self):
        """Internal reconnection monitoring loop"""
        while self.auto_reconnect:
            try:
                if not self.client.is_connected and not self.is_reconnecting:
                    self._attempt_reconnection()
                
                time.sleep(self.reconnect_interval)
                
            except Exception as e:
                self.logger.error(f"Error in reconnection loop: {e}")
                time.sleep(self.reconnect_interval)
    
    def _attempt_reconnection(self):
        """Attempt to reconnect to DDE server"""
        self.is_reconnecting = True
        attempts = 0
        
        while attempts < self.max_reconnect_attempts and self.auto_reconnect:
            attempts += 1
            self.logger.info(f"Attempting reconnection {attempts}/{self.max_reconnect_attempts}")
            
            if self.client.connect():
                self.logger.info("Reconnection successful")
                self.is_reconnecting = False
                return
            
            time.sleep(self.reconnect_interval)
        
        self.logger.error("Maximum reconnection attempts reached")
        self.is_reconnecting = False