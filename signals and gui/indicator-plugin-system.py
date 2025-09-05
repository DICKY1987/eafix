# indicator_plugin_system.py
"""
Plugin Architecture for Systematic Indicator Creation with Display Interface
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable
from enum import Enum
import pandas as pd
import numpy as np
from datetime import datetime
import json
import importlib
import os
import threading
import queue
import winsound
from pathlib import Path

# ============== INDICATOR PLUGIN ARCHITECTURE ==============

class SignalType(Enum):
    BUY = "BUY"
    SELL = "SELL"
    NEUTRAL = "NEUTRAL"
    CLOSE = "CLOSE"

@dataclass
class ThresholdAlert:
    """Configuration for threshold-based alerts"""
    level: float
    direction: str  # 'above' or 'below'
    pip_proximity: float  # Alert when within X pips
    sound_file: Optional[str] = None
    enabled: bool = True
    last_triggered: Optional[datetime] = None
    
class IndicatorBase(ABC):
    """Base class for all indicator plugins"""
    
    def __init__(self, symbol: str, timeframe: str, params: Dict = None):
        self.symbol = symbol
        self.timeframe = timeframe
        self.params = params or {}
        self.thresholds: List[ThresholdAlert] = []
        self.current_value = None
        self.history = []
        
    @abstractmethod
    def calculate(self, data: pd.DataFrame) -> float:
        """Calculate indicator value from price data"""
        pass
    
    @abstractmethod
    def get_signal(self) -> SignalType:
        """Generate trading signal based on current value"""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Indicator name for display"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Indicator description"""
        pass
    
    def check_thresholds(self, price: float) -> List[str]:
        """Check proximity and threshold hits"""
        alerts = []
        
        for threshold in self.thresholds:
            if not threshold.enabled:
                continue
                
            distance = abs(price - threshold.level)
            
            # Check proximity alert
            if distance <= threshold.pip_proximity * 0.0001:  # Convert pips to price
                alerts.append(f"PROXIMITY: {self.symbol} within {threshold.pip_proximity} pips of {threshold.level}")
                
                # Play sound if configured
                if threshold.sound_file:
                    threading.Thread(target=lambda: winsound.PlaySound(
                        threshold.sound_file, winsound.SND_FILENAME
                    )).start()
            
            # Check threshold hit
            if threshold.direction == 'above' and price >= threshold.level:
                alerts.append(f"THRESHOLD HIT: {self.symbol} above {threshold.level}")
                threshold.last_triggered = datetime.now()
            elif threshold.direction == 'below' and price <= threshold.level:
                alerts.append(f"THRESHOLD HIT: {self.symbol} below {threshold.level}")
                threshold.last_triggered = datetime.now()
                
        return alerts

# ============== INDICATOR PLUGIN MANAGER ==============

class IndicatorPluginManager:
    """Manages loading and execution of indicator plugins"""
    
    def __init__(self, plugin_dir: str = "indicators/plugins"):
        self.plugin_dir = Path(plugin_dir)
        self.indicators: Dict[str, Dict[str, IndicatorBase]] = {}  # symbol -> {indicator_name: instance}
        self.plugin_classes: Dict[str, type] = {}
        self.load_plugins()
        
    def load_plugins(self):
        """Dynamically load indicator plugins from directory"""
        if not self.plugin_dir.exists():
            self.plugin_dir.mkdir(parents=True)
            return
            
        for file in self.plugin_dir.glob("*.py"):
            if file.stem.startswith("_"):
                continue
                
            module_name = f"indicators.plugins.{file.stem}"
            spec = importlib.util.spec_from_file_location(module_name, file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Find all IndicatorBase subclasses
            for name, obj in module.__dict__.items():
                if (isinstance(obj, type) and 
                    issubclass(obj, IndicatorBase) and 
                    obj != IndicatorBase):
                    self.plugin_classes[name] = obj
                    
    def create_indicator(self, symbol: str, indicator_class: str, 
                        timeframe: str = "H1", params: Dict = None) -> IndicatorBase:
        """Create indicator instance for a symbol"""
        if indicator_class not in self.plugin_classes:
            raise ValueError(f"Unknown indicator class: {indicator_class}")
            
        indicator = self.plugin_classes[indicator_class](symbol, timeframe, params)
        
        if symbol not in self.indicators:
            self.indicators[symbol] = {}
        self.indicators[symbol][indicator.name] = indicator
        
        return indicator
    
    def get_all_indicators(self, symbol: str) -> Dict[str, IndicatorBase]:
        """Get all indicators for a symbol"""
        return self.indicators.get(symbol, {})

# ============== INDICATOR WIZARD ==============

class IndicatorWizard:
    """Interactive wizard for creating custom indicators"""
    
    TEMPLATE = '''
# {indicator_name}.py
from indicator_plugin_system import IndicatorBase, SignalType
import pandas as pd
import numpy as np

class {class_name}(IndicatorBase):
    """
    {description}
    """
    
    def __init__(self, symbol: str, timeframe: str, params: Dict = None):
        super().__init__(symbol, timeframe, params)
        self.period = params.get('period', {default_period})
        self.threshold_buy = params.get('threshold_buy', {threshold_buy})
        self.threshold_sell = params.get('threshold_sell', {threshold_sell})
        
    @property
    def name(self) -> str:
        return "{indicator_name}"
    
    @property
    def description(self) -> str:
        return "{description}"
    
    def calculate(self, data: pd.DataFrame) -> float:
        """
        Calculate indicator value
        data columns: ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        """
        if len(data) < self.period:
            return 0.0
            
        # TODO: Implement your calculation logic here
        {calculation_logic}
        
        self.current_value = value
        self.history.append({{'timestamp': data['timestamp'].iloc[-1], 'value': value}})
        return value
    
    def get_signal(self) -> SignalType:
        """Generate signal based on indicator value"""
        if self.current_value is None:
            return SignalType.NEUTRAL
            
        if self.current_value > self.threshold_buy:
            return SignalType.BUY
        elif self.current_value < self.threshold_sell:
            return SignalType.SELL
        else:
            return SignalType.NEUTRAL
'''
    
    @staticmethod
    def create_indicator(name: str, description: str, 
                        default_period: int = 14,
                        threshold_buy: float = 70,
                        threshold_sell: float = 30,
                        calculation_type: str = "momentum") -> str:
        """Generate indicator plugin code"""
        
        # Generate calculation logic based on type
        calc_logic = {
            "momentum": """
        closes = data['close'].tail(self.period)
        value = ((closes.iloc[-1] - closes.iloc[0]) / closes.iloc[0]) * 100""",
            
            "oscillator": """
        high = data['high'].tail(self.period).max()
        low = data['low'].tail(self.period).min()
        close = data['close'].iloc[-1]
        value = ((close - low) / (high - low)) * 100 if high != low else 50""",
            
            "moving_average": """
        value = data['close'].tail(self.period).mean()""",
            
            "volatility": """
        returns = data['close'].pct_change().tail(self.period)
        value = returns.std() * np.sqrt(252) * 100"""
        }
        
        class_name = ''.join(word.capitalize() for word in name.split('_'))
        
        return IndicatorWizard.TEMPLATE.format(
            indicator_name=name,
            class_name=class_name,
            description=description,
            default_period=default_period,
            threshold_buy=threshold_buy,
            threshold_sell=threshold_sell,
            calculation_logic=calc_logic.get(calculation_type, calc_logic["momentum"])
        )

# ============== DISPLAY INTERFACE ==============

class IndicatorDisplay:
    """Table/List display interface for indicators and thresholds"""
    
    def __init__(self, manager: IndicatorPluginManager):
        self.manager = manager
        self.display_data = pd.DataFrame()
        
    def update_display(self, symbols: List[str]) -> pd.DataFrame:
        """Update display data for all indicators"""
        rows = []
        
        for symbol in symbols:
            indicators = self.manager.get_all_indicators(symbol)
            
            for name, indicator in indicators.items():
                row = {
                    'Symbol': symbol,
                    'Indicator': name,
                    'Value': indicator.current_value,
                    'Signal': indicator.get_signal().value if indicator.current_value else 'N/A',
                    'Thresholds': len(indicator.thresholds),
                    'Last Update': datetime.now().strftime('%H:%M:%S')
                }
                
                # Add threshold proximity info
                if indicator.thresholds:
                    proximities = []
                    for t in indicator.thresholds:
                        if indicator.current_value:
                            dist = abs(indicator.current_value - t.level)
                            proximities.append(f"{t.level:.5f} ({dist:.1f} pips)")
                    row['Threshold Levels'] = ', '.join(proximities[:3])  # Show top 3
                else:
                    row['Threshold Levels'] = 'None'
                    
                rows.append(row)
        
        self.display_data = pd.DataFrame(rows)
        return self.display_data
    
    def get_html_table(self) -> str:
        """Generate HTML table for web display"""
        if self.display_data.empty:
            return "<p>No indicators configured</p>"
            
        # Apply conditional formatting
        def color_signal(val):
            colors = {
                'BUY': 'background-color: #90EE90',
                'SELL': 'background-color: #FFB6C1',
                'NEUTRAL': 'background-color: #F0F0F0'
            }
            return colors.get(val, '')
        
        styled = self.display_data.style.applymap(
            color_signal, subset=['Signal']
        ).set_table_styles([
            {'selector': 'th', 'props': [('background-color', '#4CAF50'), ('color', 'white')]},
            {'selector': 'td', 'props': [('padding', '8px')]},
            {'selector': 'table', 'props': [('border-collapse', 'collapse'), ('width', '100%')]}
        ])
        
        return styled.to_html()

# ============== MULTI-PAIR CALCULATOR ==============

class MultiPairCalculator:
    """Calculate same indicator across multiple pairs"""
    
    def __init__(self, manager: IndicatorPluginManager):
        self.manager = manager
        self.calculation_threads = {}
        self.results_queue = queue.Queue()
        
    def calculate_all_pairs(self, pairs: List[str], indicator_class: str, 
                           params: Dict = None, data_provider: Callable = None):
        """Calculate indicator for all pairs in parallel"""
        
        for pair in pairs:
            if pair in self.calculation_threads and self.calculation_threads[pair].is_alive():
                continue  # Skip if already calculating
                
            thread = threading.Thread(
                target=self._calculate_pair,
                args=(pair, indicator_class, params, data_provider)
            )
            thread.start()
            self.calculation_threads[pair] = thread
    
    def _calculate_pair(self, pair: str, indicator_class: str, 
                        params: Dict, data_provider: Callable):
        """Calculate indicator for single pair"""
        try:
            # Get price data
            data = data_provider(pair) if data_provider else pd.DataFrame()
            
            # Create or get indicator
            indicator = self.manager.create_indicator(pair, indicator_class, params=params)
            
            # Calculate
            value = indicator.calculate(data)
            signal = indicator.get_signal()
            
            # Check thresholds
            if 'close' in data.columns and not data.empty:
                alerts = indicator.check_thresholds(data['close'].iloc[-1])
                for alert in alerts:
                    self.results_queue.put(('alert', alert))
            
            # Queue result
            self.results_queue.put(('result', {
                'pair': pair,
                'indicator': indicator.name,
                'value': value,
                'signal': signal,
                'timestamp': datetime.now()
            }))
            
        except Exception as e:
            self.results_queue.put(('error', f"Error calculating {pair}: {str(e)}"))

# ============== AUTOMATIC TRADING RULES ==============

@dataclass
class TradingRule:
    """Rule for automatic trading based on indicators"""
    indicator_name: str
    condition: str  # 'cross_above', 'cross_below', 'above', 'below'
    threshold: float
    action: str  # 'buy', 'sell', 'close'
    lot_size_pct: float  # As percentage of account
    enabled: bool = True
    cooldown_seconds: int = 300
    last_triggered: Optional[datetime] = None
    
class AutoTrader:
    """Execute trades based on indicator rules"""
    
    def __init__(self, manager: IndicatorPluginManager):
        self.manager = manager
        self.rules: Dict[str, List[TradingRule]] = {}  # symbol -> rules
        self.trade_queue = queue.Queue()
        
    def add_rule(self, symbol: str, rule: TradingRule):
        """Add trading rule for symbol"""
        if symbol not in self.rules:
            self.rules[symbol] = []
        self.rules[symbol].append(rule)
        
    def check_rules(self, symbol: str) -> List[Dict]:
        """Check all rules for a symbol and generate trade signals"""
        trades = []
        indicators = self.manager.get_all_indicators(symbol)
        
        for rule in self.rules.get(symbol, []):
            if not rule.enabled:
                continue
                
            # Check cooldown
            if rule.last_triggered:
                elapsed = (datetime.now() - rule.last_triggered).total_seconds()
                if elapsed < rule.cooldown_seconds:
                    continue
            
            # Get indicator
            indicator = indicators.get(rule.indicator_name)
            if not indicator or indicator.current_value is None:
                continue
            
            # Check condition
            triggered = False
            if rule.condition == 'above' and indicator.current_value > rule.threshold:
                triggered = True
            elif rule.condition == 'below' and indicator.current_value < rule.threshold:
                triggered = True
            # Add cross conditions logic here if needed
            
            if triggered:
                trade = {
                    'symbol': symbol,
                    'action': rule.action,
                    'lot_size_pct': rule.lot_size_pct,
                    'indicator': rule.indicator_name,
                    'value': indicator.current_value,
                    'rule': f"{rule.condition} {rule.threshold}",
                    'timestamp': datetime.now()
                }
                trades.append(trade)
                rule.last_triggered = datetime.now()
                
        return trades

# ============== EXAMPLE INDICATOR PLUGINS ==============

class RSIIndicator(IndicatorBase):
    """RSI Indicator Plugin Example"""
    
    def __init__(self, symbol: str, timeframe: str, params: Dict = None):
        super().__init__(symbol, timeframe, params)
        self.period = params.get('period', 14) if params else 14
        
    @property
    def name(self) -> str:
        return f"RSI_{self.period}"
    
    @property
    def description(self) -> str:
        return f"Relative Strength Index with period {self.period}"
    
    def calculate(self, data: pd.DataFrame) -> float:
        if len(data) < self.period + 1:
            return 0.0
            
        closes = data['close'].tail(self.period + 1)
        deltas = closes.diff()
        
        gains = deltas.where(deltas > 0, 0)
        losses = -deltas.where(deltas < 0, 0)
        
        avg_gain = gains.mean()
        avg_loss = losses.mean()
        
        if avg_loss == 0:
            rsi = 100
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            
        self.current_value = rsi
        return rsi
    
    def get_signal(self) -> SignalType:
        if self.current_value is None:
            return SignalType.NEUTRAL
        if self.current_value > 70:
            return SignalType.SELL
        elif self.current_value < 30:
            return SignalType.BUY
        return SignalType.NEUTRAL

# ============== USAGE EXAMPLE ==============

def example_usage():
    """Example of using the indicator plugin system"""
    
    # Initialize manager
    manager = IndicatorPluginManager()
    
    # Create wizard-generated indicator
    wizard_code = IndicatorWizard.create_indicator(
        name="custom_momentum",
        description="Custom momentum oscillator",
        calculation_type="momentum"
    )
    
    # Save to plugin directory
    with open("indicators/plugins/custom_momentum.py", "w") as f:
        f.write(wizard_code)
    
    # Reload plugins
    manager.load_plugins()
    
    # Create indicators for multiple pairs
    pairs = ["EURUSD", "GBPUSD", "USDJPY"]
    for pair in pairs:
        # Create RSI
        rsi = manager.create_indicator(pair, "RSIIndicator", params={'period': 14})
        
        # Add thresholds
        rsi.thresholds.append(ThresholdAlert(
            level=70, 
            direction='above', 
            pip_proximity=5,
            sound_file="alert_high.wav"
        ))
        rsi.thresholds.append(ThresholdAlert(
            level=30, 
            direction='below', 
            pip_proximity=5,
            sound_file="alert_low.wav"
        ))
    
    # Setup display
    display = IndicatorDisplay(manager)
    
    # Setup multi-pair calculator
    calculator = MultiPairCalculator(manager)
    
    # Setup auto trader
    trader = AutoTrader(manager)
    
    # Add trading rule
    trader.add_rule("EURUSD", TradingRule(
        indicator_name="RSI_14",
        condition="below",
        threshold=30,
        action="buy",
        lot_size_pct=2.0  # 2% of account
    ))
    
    # Generate display
    display_df = display.update_display(pairs)
    print(display_df)
    
    # Check trading rules
    for pair in pairs:
        trades = trader.check_rules(pair)
        for trade in trades:
            print(f"Trade Signal: {trade}")

if __name__ == "__main__":
    example_usage()
