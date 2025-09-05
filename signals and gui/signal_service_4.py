#!/usr/bin/env python3
"""
HUEY_P Trading System - Signal Generation Service
Provides ML-enhanced trading signals to HUEY_P EA system
"""

import asyncio
import logging
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

class TradingSignal:
    """Represents a trading signal for HUEY_P EAs"""
    
    def __init__(self, pair: str, direction: str, confidence: float, 
                 entry_price: float, stop_loss: float, take_profit: float,
                 signal_type: str = "ML_GENERATED"):
        self.pair = pair
        self.direction = direction  # "BUY", "SELL", "CLOSE"
        self.confidence = confidence  # 0.0 to 1.0
        self.entry_price = entry_price
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.signal_type = signal_type
        self.timestamp = datetime.utcnow()
        self.signal_id = f"{pair}_{int(time.time())}"
    
    def to_dict(self) -> Dict:
        """Convert signal to dictionary for JSON serialization"""
        return {
            "signal_id": self.signal_id,
            "pair": self.pair,
            "direction": self.direction,
            "confidence": self.confidence,
            "entry_price": self.entry_price,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "signal_type": self.signal_type,
            "timestamp": self.timestamp.isoformat(),
            "formatted_timestamp": self.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def to_mql4_format(self) -> str:
        """Convert signal to MQL4-compatible CSV format"""
        return f"{self.pair},{self.direction},{self.confidence:.3f},{self.entry_price:.5f},{self.stop_loss:.5f},{self.take_profit:.5f},{self.signal_type},{self.timestamp.strftime('%Y.%m.%d %H:%M:%S')}"

class SignalService:
    """Main signal generation service for HUEY_P trading system"""
    
    def __init__(self):
        self.currency_pairs = [
            # Major pairs
            "EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "USDCAD", "NZDUSD", "EURGBP",
            # Minor pairs
            "EURJPY", "EURCHF", "EURAUD", "EURCAD", "EURNZD", "GBPJPY", "GBPCHF", "GBPAUD",
            "GBPCAD", "GBPNZD", "AUDJPY", "AUDCHF", "AUDCAD", "AUDNZD",
            # Cross pairs
            "CADJPY", "CADCHF", "CHFJPY", "NZDJPY", "NZDCHF", "NZDCAD", "JPYCHF", "JPYCAD"
        ]
        
        self.signal_history = {}
        self.market_data = {}
        self.economic_calendar = {}
        
        # Signal generation parameters
        self.min_confidence = 0.6
        self.max_signals_per_hour = 5
        self.signal_cooldown = 300  # 5 minutes between signals for same pair
        
        logger.info(f"SignalService initialized for {len(self.currency_pairs)} pairs")
    
    async def generate_signals(self) -> List[TradingSignal]:
        """Generate trading signals for all currency pairs"""
        signals = []
        
        for pair in self.currency_pairs:
            try:
                signal = await self._generate_pair_signal(pair)
                if signal and signal.confidence >= self.min_confidence:
                    if self._should_generate_signal(pair):
                        signals.append(signal)
                        self._record_signal(signal)
                        logger.info(f"Generated signal: {pair} {signal.direction} (confidence: {signal.confidence:.3f})")
            
            except Exception as e:
                logger.error(f"Error generating signal for {pair}: {e}")
        
        return signals
    
    async def _generate_pair_signal(self, pair: str) -> Optional[TradingSignal]:
        """Generate signal for specific currency pair using ML models"""
        
        # Get market data (simulated for now)
        market_data = await self._get_market_data(pair)
        if not market_data:
            return None
        
        # Technical analysis component
        technical_score = self._analyze_technical_indicators(pair, market_data)
        
        # Economic calendar component  
        fundamental_score = self._analyze_economic_calendar(pair)
        
        # ML model prediction (placeholder for now)
        ml_score = self._run_ml_prediction(pair, market_data)
        
        # Combine scores
        combined_confidence = (technical_score * 0.4 + fundamental_score * 0.3 + ml_score * 0.3)
        
        if combined_confidence < self.min_confidence:
            return None
        
        # Determine direction and price levels
        direction = "BUY" if combined_confidence > 0.5 else "SELL"
        current_price = market_data['bid']
        
        # Calculate stop loss and take profit based on volatility
        atr_value = market_data.get('atr', 0.001)  # Average True Range
        
        if direction == "BUY":
            entry_price = market_data['ask']
            stop_loss = entry_price - (2.0 * atr_value)
            take_profit = entry_price + (3.0 * atr_value)
        else:
            entry_price = market_data['bid']  
            stop_loss = entry_price + (2.0 * atr_value)
            take_profit = entry_price - (3.0 * atr_value)
        
        return TradingSignal(
            pair=pair,
            direction=direction,
            confidence=combined_confidence,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            signal_type="ML_HYBRID"
        )
    
    async def _get_market_data(self, pair: str) -> Optional[Dict]:
        """Get current market data for pair (simulated)"""
        # In real implementation, this would connect to market data feed
        
        # Simulate market data
        base_prices = {
            "EURUSD": 1.0500, "GBPUSD": 1.2500, "USDJPY": 150.00, "USDCHF": 0.9000,
            "AUDUSD": 0.6500, "USDCAD": 1.3500, "NZDUSD": 0.6000, "EURGBP": 0.8400
        }
        
        base_price = base_prices.get(pair[:6], 1.0000)
        
        # Add some random variation
        variation = np.random.normal(0, 0.001)
        current_price = base_price + variation
        
        spread = 0.0002 if "JPY" not in pair else 0.02
        
        return {
            'pair': pair,
            'bid': current_price - spread/2,
            'ask': current_price + spread/2,
            'atr': abs(np.random.normal(0.001, 0.0002)),
            'timestamp': datetime.utcnow()
        }
    
    def _analyze_technical_indicators(self, pair: str, market_data: Dict) -> float:
        """Analyze technical indicators for signal generation"""
        # Placeholder for technical analysis
        # In real implementation, would calculate RSI, MACD, MA, etc.
        
        # Simulate technical analysis score
        return np.random.uniform(0.3, 0.9) if market_data else 0.0
    
    def _analyze_economic_calendar(self, pair: str) -> float:
        """Analyze economic calendar events for fundamental analysis"""
        # Placeholder for economic calendar analysis
        # In real implementation, would check upcoming news events
        
        # Simulate fundamental score
        return np.random.uniform(0.4, 0.8)
    
    def _run_ml_prediction(self, pair: str, market_data: Dict) -> float:
        """Run machine learning model prediction"""
        # Placeholder for ML model
        # In real implementation, would use trained models
        
        # Simulate ML prediction
        return np.random.uniform(0.4, 0.9)
    
    def _should_generate_signal(self, pair: str) -> bool:
        """Check if we should generate a signal for this pair"""
        current_time = time.time()
        
        # Check signal history for cooldown
        if pair in self.signal_history:
            last_signal_time = self.signal_history[pair][-1]['timestamp']
            if current_time - last_signal_time < self.signal_cooldown:
                return False
        
        # Check hourly signal limit
        recent_signals = self._get_recent_signals(pair, 3600)  # 1 hour
        if len(recent_signals) >= self.max_signals_per_hour:
            return False
        
        return True
    
    def _record_signal(self, signal: TradingSignal):
        """Record signal in history"""
        if signal.pair not in self.signal_history:
            self.signal_history[signal.pair] = []
        
        self.signal_history[signal.pair].append({
            'timestamp': time.time(),
            'signal_id': signal.signal_id,
            'direction': signal.direction,
            'confidence': signal.confidence
        })
        
        # Keep only last 100 signals per pair
        if len(self.signal_history[signal.pair]) > 100:
            self.signal_history[signal.pair] = self.signal_history[signal.pair][-100:]
    
    def _get_recent_signals(self, pair: str, seconds: int) -> List[Dict]:
        """Get recent signals for pair within specified time window"""
        if pair not in self.signal_history:
            return []
        
        current_time = time.time()
        cutoff_time = current_time - seconds
        
        return [s for s in self.signal_history[pair] if s['timestamp'] > cutoff_time]
    
    def get_signal_statistics(self) -> Dict:
        """Get signal generation statistics"""
        stats = {
            'total_pairs': len(self.currency_pairs),
            'pairs_with_signals': len(self.signal_history),
            'total_signals_generated': sum(len(signals) for signals in self.signal_history.values()),
            'last_generation_time': datetime.utcnow().isoformat()
        }
        
        for pair in self.signal_history:
            recent_signals = self._get_recent_signals(pair, 3600)
            stats[f'{pair}_signals_last_hour'] = len(recent_signals)
        
        return stats

# Usage example and testing
if __name__ == "__main__":
    async def test_signal_service():
        service = SignalService()
        
        print("Testing HUEY_P Signal Service...")
        
        for i in range(3):
            print(f"\n--- Signal Generation Cycle {i+1} ---")
            signals = await service.generate_signals()
            
            print(f"Generated {len(signals)} signals:")
            for signal in signals:
                print(f"  {signal.pair}: {signal.direction} (conf: {signal.confidence:.3f})")
                print(f"    MQL4 Format: {signal.to_mql4_format()}")
            
            await asyncio.sleep(2)
        
        print("\n--- Signal Statistics ---")
        stats = service.get_signal_statistics()
        for key, value in stats.items():
            print(f"{key}: {value}")
    
    asyncio.run(test_signal_service())