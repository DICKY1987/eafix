#!/usr/bin/env python3
"""
Extended DDE Bridge - Enhanced Version
Combines existing DDE functionality with plugin interface capabilities
Adds signal generation, alert system, and advanced data processing
"""

import win32ui
import dde
import pandas as pd
import numpy as np
import json
import sqlite3
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Union
from dataclasses import dataclass, asdict
from collections import deque
import logging
import smtplib
from email.mime.text import MimeText
import requests
import websocket

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class TradingSignal:
    """Trading signal with comprehensive details"""
    timestamp: datetime
    symbol: str
    signal_type: str  # BUY, SELL, HOLD
    confidence: float  # 0.0 to 1.0
    entry_price: float
    stop_loss: float
    take_profit: float
    timeframe: str
    indicators: Dict[str, float]
    risk_level: str  # LOW, MEDIUM, HIGH
    notes: str = ""

@dataclass
class MarketAlert:
    """Market alert with notification details"""
    timestamp: datetime
    symbol: str
    alert_type: str  # PRICE, VOLATILITY, STRENGTH, CUSTOM
    message: str
    priority: str  # LOW, MEDIUM, HIGH, CRITICAL
    triggered_value: float
    threshold_value: float
    action_required: bool = False

class EnhancedDDEConnector:
    """Enhanced DDE connector with advanced features"""
    
    def __init__(self, server_name: str = "MT4"):
        # Base DDE functionality (from your existing code)
        self.server_name = server_name
        self.server = None
        self.conversation = None
        self.connected = False
        self.symbols = []
        
        # Enhanced features
        self.price_history = {}  # symbol -> deque
        self.indicators = {}     # symbol -> indicators dict
        self.signals = deque(maxlen=1000)
        self.alerts = deque(maxlen=500)
        self.callbacks = {
            'price_update': [],
            'signal_generated': [],
            'alert_triggered': [],
            'market_event': []
        }
        
        # Configuration
        self.config = {
            'max_history': 10000,
            'signal_threshold': 0.7,
            'volatility_threshold': 0.05,
            'update_interval': 0.1,
            'enable_alerts': True,
            'enable_signals': True,
            'auto_export': True
        }
        
        # Database for persistence
        self.db_path = "enhanced_dde_data.db"
        self.init_database()
        
    def connect(self) -> bool:
        """Enhanced connection with error handling and status reporting"""
        try:
            self.server = dde.CreateServer()
            self.server.Create("EnhancedDDEClient")
            self.conversation = dde.CreateConversation(self.server)
            self.conversation.ConnectTo(self.server_name, "QUOTE")
            self.connected = True
            
            logger.info(f"✅ Enhanced DDE connection established: {self.server_name}")
            
            # Initialize monitoring threads
            self.start_background_processes()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to MT4 DDE: {e}")
            return False
    
    def init_database(self):
        """Initialize SQLite database for data persistence"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Price history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS price_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                symbol TEXT,
                bid REAL,
                ask REAL,
                spread REAL,
                mid REAL,
                volume INTEGER DEFAULT 0
            )
        ''')
        
        # Signals table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trading_signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                symbol TEXT,
                signal_type TEXT,
                confidence REAL,
                entry_price REAL,
                stop_loss REAL,
                take_profit REAL,
                timeframe TEXT,
                risk_level TEXT,
                indicators TEXT,
                notes TEXT
            )
        ''')
        
        # Alerts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS market_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                symbol TEXT,
                alert_type TEXT,
                message TEXT,
                priority TEXT,
                triggered_value REAL,
                threshold_value REAL,
                action_required BOOLEAN
            )
        ''')
        
        # Create indexes for better performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_price_symbol_time ON price_history(symbol, timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_signal_symbol_time ON trading_signals(symbol, timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_alert_symbol_time ON market_alerts(symbol, timestamp)')
        
        conn.commit()
        conn.close()
        logger.info("📊 Database initialized successfully")
    
    def get_enhanced_price(self, symbol: str) -> Optional[Dict]:
        """Get enhanced price data with additional metrics"""
        if not self.connected:
            return None
            
        try:
            # Get basic price data (from your existing implementation)
            bid_data = self.conversation.Request(f"{symbol}_BID")
            ask_data = self.conversation.Request(f"{symbol}_ASK")
            time_data = self.conversation.Request(f"{symbol}_TIME")
            
            if bid_data and ask_data:
                bid = float(bid_data)
                ask = float(ask_data)
                spread = ask - bid
                mid = (bid + ask) / 2
                
                # Enhanced price data
                price_data = {
                    'timestamp': datetime.now(),
                    'symbol': symbol,
                    'bid': bid,
                    'ask': ask,
                    'spread': spread,
                    'mid': mid,
                    'spread_pct': (spread / mid) * 100 if mid > 0 else 0,
                    'tick_direction': self._get_tick_direction(symbol, mid),
                    'volatility': self._calculate_volatility(symbol),
                    'trend': self._get_trend(symbol)
                }
                
                # Store in history
                self._store_price_data(price_data)
                
                # Check for alerts
                self._check_price_alerts(price_data)
                
                return price_data
                
        except Exception as e:
            logger.error(f"❌ Error getting enhanced price for {symbol}: {e}")
            
        return None
    
    def _get_tick_direction(self, symbol: str, current_price: float) -> str:
        """Determine tick direction (UP, DOWN, UNCHANGED)"""
        if symbol in self.price_history and len(self.price_history[symbol]) > 0:
            last_price = self.price_history[symbol][-1]['mid']
            if current_price > last_price:
                return "UP"
            elif current_price < last_price:
                return "DOWN"
        return "UNCHANGED"
    
    def _calculate_volatility(self, symbol: str, periods: int = 20) -> float:
        """Calculate price volatility over specified periods"""
        if symbol not in self.price_history or len(self.price_history[symbol]) < periods:
            return 0.0
            
        prices = [p['mid'] for p in list(self.price_history[symbol])[-periods:]]
        returns = np.diff(prices) / prices[:-1]
        return np.std(returns) * 100  # Convert to percentage
    
    def _get_trend(self, symbol: str, periods: int = 10) -> str:
        """Determine short-term trend direction"""
        if symbol not in self.price_history or len(self.price_history[symbol]) < periods:
            return "NEUTRAL"
            
        prices = [p['mid'] for p in list(self.price_history[symbol])[-periods:]]
        slope = np.polyfit(range(len(prices)), prices, 1)[0]
        
        if slope > 0.0001:
            return "BULLISH"
        elif slope < -0.0001:
            return "BEARISH"
        else:
            return "NEUTRAL"
    
    def _store_price_data(self, price_data: Dict):
        """Store price data in memory and database"""
        symbol = price_data['symbol']
        
        # Store in memory
        if symbol not in self.price_history:
            self.price_history[symbol] = deque(maxlen=self.config['max_history'])
        
        self.price_history[symbol].append(price_data)
        
        # Store in database (async to avoid blocking)
        threading.Thread(target=self._async_db_store, args=(price_data,), daemon=True).start()
    
    def _async_db_store(self, price_data: Dict):
        """Asynchronously store price data to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO price_history (timestamp, symbol, bid, ask, spread, mid)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                price_data['timestamp'].isoformat(),
                price_data['symbol'],
                price_data['bid'],
                price_data['ask'],
                price_data['spread'],
                price_data['mid']
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"❌ Database storage error: {e}")
    
    def generate_trading_signal(self, symbol: str) -> Optional[TradingSignal]:
        """Generate trading signals based on technical analysis"""
        if not self.config['enable_signals']:
            return None
            
        if symbol not in self.price_history or len(self.price_history[symbol]) < 50:
            return None
            
        try:
            # Get recent price data
            recent_data = list(self.price_history[symbol])[-100:]  # Last 100 ticks
            prices = [p['mid'] for p in recent_data]
            
            # Calculate indicators
            indicators = self._calculate_indicators(prices)
            
            # Signal generation logic
            signal_strength = 0.0
            signal_type = "HOLD"
            
            # RSI signals
            if indicators['rsi'] < 30:
                signal_strength += 0.3
                signal_type = "BUY"
            elif indicators['rsi'] > 70:
                signal_strength += 0.3
                signal_type = "SELL"
            
            # Moving average crossover
            if indicators['sma_fast'] > indicators['sma_slow']:
                signal_strength += 0.2
                if signal_type == "HOLD":
                    signal_type = "BUY"
            elif indicators['sma_fast'] < indicators['sma_slow']:
                signal_strength += 0.2
                if signal_type == "HOLD":
                    signal_type = "SELL"
            
            # Bollinger Bands
            current_price = prices[-1]
            if current_price < indicators['bb_lower']:
                signal_strength += 0.25
                signal_type = "BUY"
            elif current_price > indicators['bb_upper']:
                signal_strength += 0.25
                signal_type = "SELL"
            
            # Volatility adjustment
            volatility = self._calculate_volatility(symbol)
            if volatility > self.config['volatility_threshold']:
                signal_strength *= 0.8  # Reduce confidence in high volatility
            
            # Only generate signal if confidence is above threshold
            if signal_strength >= self.config['signal_threshold'] and signal_type != "HOLD":
                # Calculate stop loss and take profit
                atr = self._calculate_atr(prices)
                
                if signal_type == "BUY":
                    entry_price = current_price
                    stop_loss = current_price - (2 * atr)
                    take_profit = current_price + (3 * atr)
                else:  # SELL
                    entry_price = current_price
                    stop_loss = current_price + (2 * atr)
                    take_profit = current_price - (3 * atr)
                
                signal = TradingSignal(
                    timestamp=datetime.now(),
                    symbol=symbol,
                    signal_type=signal_type,
                    confidence=min(signal_strength, 1.0),
                    entry_price=entry_price,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    timeframe="M5",
                    indicators=indicators,
                    risk_level=self._assess_risk_level(signal_strength, volatility),
                    notes=f"Generated by Enhanced DDE Bridge - Vol: {volatility:.4f}"
                )
                
                # Store signal
                self.signals.append(signal)
                self._store_signal(signal)
                
                # Trigger callbacks
                for callback in self.callbacks['signal_generated']:
                    try:
                        callback(signal)
                    except Exception as e:
                        logger.error(f"❌ Signal callback error: {e}")
                
                logger.info(f"📈 Signal generated: {signal_type} {symbol} @ {entry_price:.5f} (Confidence: {signal_strength:.2f})")
                return signal
                
        except Exception as e:
            logger.error(f"❌ Signal generation error: {e}")
            
        return None
    
    def _calculate_indicators(self, prices: List[float]) -> Dict[str, float]:
        """Calculate technical indicators"""
        df = pd.Series(prices)
        
        indicators = {}
        
        # Simple Moving Averages
        indicators['sma_fast'] = df.rolling(10).mean().iloc[-1] if len(df) >= 10 else df.iloc[-1]
        indicators['sma_slow'] = df.rolling(20).mean().iloc[-1] if len(df) >= 20 else df.iloc[-1]
        
        # RSI
        delta = df.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        indicators['rsi'] = (100 - (100 / (1 + rs))).iloc[-1] if len(df) >= 14 else 50.0
        
        # Bollinger Bands
        sma_20 = df.rolling(20).mean()
        std_20 = df.rolling(20).std()
        indicators['bb_upper'] = (sma_20 + (2 * std_20)).iloc[-1] if len(df) >= 20 else df.iloc[-1]
        indicators['bb_lower'] = (sma_20 - (2 * std_20)).iloc[-1] if len(df) >= 20 else df.iloc[-1]
        indicators['bb_middle'] = sma_20.iloc[-1] if len(df) >= 20 else df.iloc[-1]
        
        return indicators
    
    def _calculate_atr(self, prices: List[float], period: int = 14) -> float:
        """Calculate Average True Range for stop loss calculation"""
        if len(prices) < period + 1:
            return 0.001  # Default small ATR
            
        # Simplified ATR calculation using price differences
        price_ranges = [abs(prices[i] - prices[i-1]) for i in range(1, len(prices))]
        return np.mean(price_ranges[-period:]) if len(price_ranges) >= period else 0.001
    
    def _assess_risk_level(self, signal_strength: float, volatility: float) -> str:
        """Assess risk level based on signal strength and volatility"""
        if volatility > 0.1 or signal_strength < 0.6:
            return "HIGH"
        elif volatility > 0.05 or signal_strength < 0.8:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _store_signal(self, signal: TradingSignal):
        """Store trading signal to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO trading_signals 
                (timestamp, symbol, signal_type, confidence, entry_price, stop_loss, 
                 take_profit, timeframe, risk_level, indicators, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                signal.timestamp.isoformat(),
                signal.symbol,
                signal.signal_type,
                signal.confidence,
                signal.entry_price,
                signal.stop_loss,
                signal.take_profit,
                signal.timeframe,
                signal.risk_level,
                json.dumps(signal.indicators),
                signal.notes
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"❌ Signal storage error: {e}")
    
    def _check_price_alerts(self, price_data: Dict):
        """Check for price-based alerts"""
        if not self.config['enable_alerts']:
            return
            
        symbol = price_data['symbol']
        current_price = price_data['mid']
        
        # High spread alert
        if price_data['spread_pct'] > 0.1:  # 0.1% spread
            alert = MarketAlert(
                timestamp=datetime.now(),
                symbol=symbol,
                alert_type="VOLATILITY",
                message=f"High spread detected: {price_data['spread_pct']:.3f}%",
                priority="MEDIUM",
                triggered_value=price_data['spread_pct'],
                threshold_value=0.1
            )
            self._trigger_alert(alert)
        
        # High volatility alert
        volatility = price_data.get('volatility', 0)
        if volatility > self.config['volatility_threshold']:
            alert = MarketAlert(
                timestamp=datetime.now(),
                symbol=symbol,
                alert_type="VOLATILITY",
                message=f"High volatility detected: {volatility:.4f}",
                priority="HIGH",
                triggered_value=volatility,
                threshold_value=self.config['volatility_threshold'],
                action_required=True
            )
            self._trigger_alert(alert)
    
    def _trigger_alert(self, alert: MarketAlert):
        """Trigger market alert with notifications"""
        self.alerts.append(alert)
        
        # Store in database
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO market_alerts 
                (timestamp, symbol, alert_type, message, priority, triggered_value, 
                 threshold_value, action_required)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                alert.timestamp.isoformat(),
                alert.symbol,
                alert.alert_type,
                alert.message,
                alert.priority,
                alert.triggered_value,
                alert.threshold_value,
                alert.action_required
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"❌ Alert storage error: {e}")
        
        # Trigger callbacks
        for callback in self.callbacks['alert_triggered']:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"❌ Alert callback error: {e}")
        
        logger.warning(f"🚨 ALERT [{alert.priority}]: {alert.message}")
    
    def start_background_processes(self):
        """Start background monitoring processes"""
        # Signal generation thread
        def signal_generator():
            while self.connected:
                try:
                    for symbol in self.symbols:
                        self.generate_trading_signal(symbol)
                    time.sleep(5)  # Generate signals every 5 seconds
                except Exception as e:
                    logger.error(f"❌ Signal generator error: {e}")
                    time.sleep(1)
        
        # Data export thread
        def data_exporter():
            while self.connected:
                try:
                    if self.config['auto_export']:
                        self.export_recent_data()
                    time.sleep(60)  # Export every minute
                except Exception as e:
                    logger.error(f"❌ Data export error: {e}")
                    time.sleep(5)
        
        threading.Thread(target=signal_generator, daemon=True).start()
        threading.Thread(target=data_exporter, daemon=True).start()
        
        logger.info("🚀 Background processes started")
    
    def export_recent_data(self):
        """Export recent signals and alerts to CSV files"""
        try:
            # Export recent signals
            if len(self.signals) > 0:
                signals_df = pd.DataFrame([asdict(signal) for signal in self.signals])
                signals_df['indicators'] = signals_df['indicators'].apply(json.dumps)
                signals_df.to_csv(f"signals_{datetime.now().strftime('%Y%m%d_%H%M')}.csv", index=False)
            
            # Export recent alerts
            if len(self.alerts) > 0:
                alerts_df = pd.DataFrame([asdict(alert) for alert in self.alerts])
                alerts_df.to_csv(f"alerts_{datetime.now().strftime('%Y%m%d_%H%M')}.csv", index=False)
                
        except Exception as e:
            logger.error(f"❌ Export error: {e}")
    
    def add_callback(self, event_type: str, callback: Callable):
        """Add callback for specific events"""
        if event_type in self.callbacks:
            self.callbacks[event_type].append(callback)
            logger.info(f"📞 Callback added for {event_type}")
    
    def get_recent_signals(self, symbol: str = None, limit: int = 10) -> List[TradingSignal]:
        """Get recent trading signals"""
        if symbol:
            return [s for s in list(self.signals)[-limit:] if s.symbol == symbol]
        return list(self.signals)[-limit:]
    
    def get_recent_alerts(self, symbol: str = None, limit: int = 10) -> List[MarketAlert]:
        """Get recent market alerts"""
        if symbol:
            return [a for a in list(self.alerts)[-limit:] if a.symbol == symbol]
        return list(self.alerts)[-limit:]
    
    def disconnect(self):
        """Enhanced disconnect with cleanup"""
        self.connected = False
        
        # Export final data
        if self.config['auto_export']:
            self.export_recent_data()
        
        # Close DDE connections
        if self.conversation:
            try:
                self.conversation.Disconnect()
            except:
                pass
                
        if self.server:
            try:
                self.server.Shutdown()
            except:
                pass
        
        logger.info("🔌 Enhanced DDE bridge disconnected")

# Example usage and integration
if __name__ == "__main__":
    # Create enhanced connector
    connector = EnhancedDDEConnector()
    
    # Add callback functions
    def signal_callback(signal: TradingSignal):
        print(f"🎯 NEW SIGNAL: {signal.signal_type} {signal.symbol} @ {signal.entry_price:.5f}")
    
    def alert_callback(alert: MarketAlert):
        print(f"🚨 ALERT: {alert.message}")
    
    connector.add_callback('signal_generated', signal_callback)
    connector.add_callback('alert_triggered', alert_callback)
    
    # Connect and start monitoring
    if connector.connect():
        # Add symbols to monitor
        symbols = ['EURUSD', 'GBPUSD', 'USDJPY']
        
        for symbol in symbols:
            connector.symbols.append(symbol)
        
        print("🚀 Enhanced DDE Bridge running...")
        print("📈 Monitoring for signals and alerts...")
        
        # Main monitoring loop
        try:
            while True:
                for symbol in symbols:
                    price_data = connector.get_enhanced_price(symbol)
                    if price_data:
                        print(f"{symbol}: {price_data['mid']:.5f} "
                              f"({price_data['tick_direction']}) "
                              f"Vol: {price_data['volatility']:.4f}")
                
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n🛑 Stopping Enhanced DDE Bridge...")
            connector.disconnect()
    else:
        print("❌ Failed to connect to MT4")