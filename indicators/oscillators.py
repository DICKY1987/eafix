"""
Oscillator Indicators: RSI, Stochastic, MACD, Williams %R, CCI
"""
from typing import List, Optional, Union, Dict
import numpy as np
from collections import deque
from .base_indicator import BaseIndicator, MultiValueIndicator, IndicatorConfig, IndicatorFactory
from .moving_averages import calculate_ema, calculate_sma


class RSIConfig(IndicatorConfig):
    """Configuration for RSI indicator"""
    
    def validate_parameters(self):
        period = self.get('period', 0)
        if not isinstance(period, int) or period < 1:
            raise ValueError("RSI period must be a positive integer")
        if period > 100:
            raise ValueError("RSI period too large (max 100)")


class RelativeStrengthIndex(BaseIndicator):
    """Relative Strength Index (RSI) oscillator"""
    
    def __init__(self, name: str, config: RSIConfig):
        super().__init__(name, config)
        self.period = config.get('period', 14)
        self.price_changes = deque(maxlen=self.period + 1)
        self.avg_gain = None
        self.avg_loss = None
    
    def get_required_periods(self) -> int:
        return self.period + 1  # Need one extra for price change calculation
    
    def calculate(self, price_data: Union[List[float], np.ndarray]) -> Optional[float]:
        """Calculate RSI value"""
        if len(price_data) < self.get_required_periods():
            return None
        
        # Calculate price changes
        changes = np.diff(price_data)
        
        if len(changes) < self.period:
            return None
        
        # Separate gains and losses
        gains = np.where(changes > 0, changes, 0)
        losses = np.where(changes < 0, -changes, 0)
        
        # Calculate average gain and loss
        if self.avg_gain is None or self.avg_loss is None:
            # First calculation - use simple average
            self.avg_gain = np.mean(gains[-self.period:])
            self.avg_loss = np.mean(losses[-self.period:])
        else:
            # Subsequent calculations - use smoothed average (Wilder's smoothing)
            current_gain = gains[-1]
            current_loss = losses[-1]
            
            self.avg_gain = (self.avg_gain * (self.period - 1) + current_gain) / self.period
            self.avg_loss = (self.avg_loss * (self.period - 1) + current_loss) / self.period
        
        # Avoid division by zero
        if self.avg_loss == 0:
            return 100.0
        
        # Calculate RSI
        rs = self.avg_gain / self.avg_loss
        rsi = 100.0 - (100.0 / (1.0 + rs))
        
        return rsi
    
    def reset(self):
        """Reset RSI state"""
        super().reset()
        self.price_changes.clear()
        self.avg_gain = None
        self.avg_loss = None
    
    def is_overbought(self, threshold: float = 70.0) -> bool:
        """Check if RSI indicates overbought condition"""
        return self.last_value is not None and self.last_value > threshold
    
    def is_oversold(self, threshold: float = 30.0) -> bool:
        """Check if RSI indicates oversold condition"""
        return self.last_value is not None and self.last_value < threshold


class StochasticConfig(IndicatorConfig):
    """Configuration for Stochastic oscillator"""
    
    def validate_parameters(self):
        k_period = self.get('k_period', 0)
        if not isinstance(k_period, int) or k_period < 1:
            raise ValueError("Stochastic K period must be a positive integer")
        
        d_period = self.get('d_period', 0)
        if not isinstance(d_period, int) or d_period < 1:
            raise ValueError("Stochastic D period must be a positive integer")


class StochasticOscillator(MultiValueIndicator):
    """Stochastic Oscillator (%K and %D)"""
    
    def __init__(self, name: str, config: StochasticConfig):
        super().__init__(name, config)
        self.k_period = config.get('k_period', 14)
        self.d_period = config.get('d_period', 3)
        self.slowing = config.get('slowing', 3)  # For slow stochastic
        
        # Store high/low values for %K calculation
        self.highs = deque(maxlen=self.k_period)
        self.lows = deque(maxlen=self.k_period)
        
        # Store %K values for %D calculation
        self.k_values = deque(maxlen=self.d_period)
    
    def get_required_periods(self) -> int:
        return max(self.k_period, self.d_period)
    
    def get_primary_value_name(self) -> str:
        return 'K'
    
    def calculate_values(self, price_data: Union[List[float], np.ndarray]) -> Optional[Dict[str, float]]:
        """Calculate Stochastic %K and %D values"""
        if len(price_data) < self.k_period:
            return None
        
        # For simplicity, assume price_data represents closing prices
        # In real implementation, you'd need high, low, close data
        recent_prices = price_data[-self.k_period:]
        
        current_close = recent_prices[-1]
        highest_high = max(recent_prices)
        lowest_low = min(recent_prices)
        
        # Calculate %K
        if highest_high == lowest_low:
            k_value = 50.0  # Neutral when no price movement
        else:
            k_value = ((current_close - lowest_low) / (highest_high - lowest_low)) * 100.0
        
        # Store %K value for %D calculation
        self.k_values.append(k_value)
        
        # Calculate %D (moving average of %K)
        if len(self.k_values) >= self.d_period:
            d_value = sum(self.k_values) / len(self.k_values)
        else:
            d_value = k_value  # Use %K until we have enough values
        
        return {
            'K': k_value,
            'D': d_value
        }
    
    def reset(self):
        """Reset Stochastic state"""
        super().reset()
        self.highs.clear()
        self.lows.clear()
        self.k_values.clear()


class MACDConfig(IndicatorConfig):
    """Configuration for MACD indicator"""
    
    def validate_parameters(self):
        fast_period = self.get('fast_period', 0)
        slow_period = self.get('slow_period', 0)
        signal_period = self.get('signal_period', 0)
        
        if not isinstance(fast_period, int) or fast_period < 1:
            raise ValueError("MACD fast period must be a positive integer")
        if not isinstance(slow_period, int) or slow_period < 1:
            raise ValueError("MACD slow period must be a positive integer")
        if not isinstance(signal_period, int) or signal_period < 1:
            raise ValueError("MACD signal period must be a positive integer")
        
        if fast_period >= slow_period:
            raise ValueError("MACD fast period must be less than slow period")


class MACD(MultiValueIndicator):
    """Moving Average Convergence Divergence (MACD) indicator"""
    
    def __init__(self, name: str, config: MACDConfig):
        super().__init__(name, config)
        self.fast_period = config.get('fast_period', 12)
        self.slow_period = config.get('slow_period', 26)
        self.signal_period = config.get('signal_period', 9)
        
        # EMA values for calculation
        self.fast_ema = None
        self.slow_ema = None
        self.signal_ema = None
        
        # Store MACD values for signal line calculation
        self.macd_values = deque(maxlen=self.signal_period + 10)
    
    def get_required_periods(self) -> int:
        return self.slow_period
    
    def get_primary_value_name(self) -> str:
        return 'MACD'
    
    def calculate_values(self, price_data: Union[List[float], np.ndarray]) -> Optional[Dict[str, float]]:
        """Calculate MACD, Signal, and Histogram values"""
        if len(price_data) < self.slow_period:
            return None
        
        current_price = price_data[-1]
        
        # Calculate fast EMA
        if len(price_data) >= self.fast_period:
            if self.fast_ema is None:
                self.fast_ema = calculate_ema(price_data, self.fast_period)
            else:
                self.fast_ema = calculate_ema([current_price], self.fast_period, self.fast_ema)
        
        # Calculate slow EMA
        if self.slow_ema is None:
            self.slow_ema = calculate_ema(price_data, self.slow_period)
        else:
            self.slow_ema = calculate_ema([current_price], self.slow_period, self.slow_ema)
        
        if self.fast_ema is None or self.slow_ema is None:
            return None
        
        # Calculate MACD line
        macd_value = self.fast_ema - self.slow_ema
        self.macd_values.append(macd_value)
        
        # Calculate Signal line (EMA of MACD)
        if len(self.macd_values) >= self.signal_period:
            if self.signal_ema is None:
                # Initialize signal EMA with simple average
                self.signal_ema = sum(list(self.macd_values)[-self.signal_period:]) / self.signal_period
            else:
                # Calculate EMA of MACD values
                multiplier = 2.0 / (self.signal_period + 1)
                self.signal_ema = (macd_value * multiplier) + (self.signal_ema * (1 - multiplier))
        else:
            self.signal_ema = macd_value
        
        # Calculate Histogram
        histogram = macd_value - self.signal_ema
        
        return {
            'MACD': macd_value,
            'Signal': self.signal_ema,
            'Histogram': histogram
        }
    
    def reset(self):
        """Reset MACD state"""
        super().reset()
        self.fast_ema = None
        self.slow_ema = None
        self.signal_ema = None
        self.macd_values.clear()
    
    def is_bullish_crossover(self) -> bool:
        """Check if MACD crossed above Signal line"""
        values = self.get_current_values()
        return (values.get('MACD', 0) > values.get('Signal', 0) and 
                values.get('Histogram', 0) > 0)
    
    def is_bearish_crossover(self) -> bool:
        """Check if MACD crossed below Signal line"""
        values = self.get_current_values()
        return (values.get('MACD', 0) < values.get('Signal', 0) and 
                values.get('Histogram', 0) < 0)


class WilliamsRConfig(IndicatorConfig):
    """Configuration for Williams %R indicator"""
    
    def validate_parameters(self):
        period = self.get('period', 0)
        if not isinstance(period, int) or period < 1:
            raise ValueError("Williams %R period must be a positive integer")


class WilliamsPercentR(BaseIndicator):
    """Williams %R oscillator"""
    
    def __init__(self, name: str, config: WilliamsRConfig):
        super().__init__(name, config)
        self.period = config.get('period', 14)
    
    def get_required_periods(self) -> int:
        return self.period
    
    def calculate(self, price_data: Union[List[float], np.ndarray]) -> Optional[float]:
        """Calculate Williams %R value"""
        if len(price_data) < self.period:
            return None
        
        # Use price data as close prices (in real implementation, need high/low/close)
        recent_prices = price_data[-self.period:]
        
        current_close = recent_prices[-1]
        highest_high = max(recent_prices)
        lowest_low = min(recent_prices)
        
        # Calculate Williams %R
        if highest_high == lowest_low:
            return -50.0  # Neutral when no price movement
        
        williams_r = ((highest_high - current_close) / (highest_high - lowest_low)) * -100.0
        
        return williams_r
    
    def is_overbought(self, threshold: float = -20.0) -> bool:
        """Check if Williams %R indicates overbought condition"""
        return self.last_value is not None and self.last_value > threshold
    
    def is_oversold(self, threshold: float = -80.0) -> bool:
        """Check if Williams %R indicates oversold condition"""
        return self.last_value is not None and self.last_value < threshold


class CCIConfig(IndicatorConfig):
    """Configuration for Commodity Channel Index"""
    
    def validate_parameters(self):
        period = self.get('period', 0)
        if not isinstance(period, int) or period < 1:
            raise ValueError("CCI period must be a positive integer")


class CommodityChannelIndex(BaseIndicator):
    """Commodity Channel Index (CCI) oscillator"""
    
    def __init__(self, name: str, config: CCIConfig):
        super().__init__(name, config)
        self.period = config.get('period', 20)
        self.constant = config.get('constant', 0.015)  # CCI constant
    
    def get_required_periods(self) -> int:
        return self.period
    
    def calculate(self, price_data: Union[List[float], np.ndarray]) -> Optional[float]:
        """Calculate CCI value"""
        if len(price_data) < self.period:
            return None
        
        # Use price data as typical price (in real implementation: (H+L+C)/3)
        recent_prices = np.array(price_data[-self.period:])
        
        # Calculate Simple Moving Average of typical prices
        sma_tp = np.mean(recent_prices)
        
        # Calculate Mean Deviation
        mean_deviation = np.mean(np.abs(recent_prices - sma_tp))
        
        if mean_deviation == 0:
            return 0.0
        
        # Calculate CCI
        current_tp = recent_prices[-1]
        cci = (current_tp - sma_tp) / (self.constant * mean_deviation)
        
        return cci
    
    def is_overbought(self, threshold: float = 100.0) -> bool:
        """Check if CCI indicates overbought condition"""
        return self.last_value is not None and self.last_value > threshold
    
    def is_oversold(self, threshold: float = -100.0) -> bool:
        """Check if CCI indicates oversold condition"""
        return self.last_value is not None and self.last_value < threshold


# Factory functions for creating oscillator indicators
def create_rsi(name: str, period: int = 14) -> RSI:
    """Create RSI indicator"""
    config = RSIConfig(period=period)
    return RelativeStrengthIndex(name, config)


def create_stochastic(name: str, k_period: int = 14, d_period: int = 3, slowing: int = 3) -> StochasticOscillator:
    """Create Stochastic oscillator"""
    config = StochasticConfig(k_period=k_period, d_period=d_period, slowing=slowing)
    return StochasticOscillator(name, config)


def create_macd(name: str, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9) -> MACD:
    """Create MACD indicator"""
    config = MACDConfig(fast_period=fast_period, slow_period=slow_period, signal_period=signal_period)
    return MACD(name, config)


def create_williams_r(name: str, period: int = 14) -> WilliamsPercentR:
    """Create Williams %R indicator"""
    config = WilliamsRConfig(period=period)
    return WilliamsPercentR(name, config)


def create_cci(name: str, period: int = 20) -> CommodityChannelIndex:
    """Create CCI indicator"""
    config = CCIConfig(period=period)
    return CommodityChannelIndex(name, config)


# Register indicators with factory
IndicatorFactory.register('RSI', RelativeStrengthIndex)
IndicatorFactory.register('Stochastic', StochasticOscillator)
IndicatorFactory.register('MACD', MACD)
IndicatorFactory.register('WilliamsR', WilliamsPercentR)
IndicatorFactory.register('CCI', CommodityChannelIndex)


# Direct calculation functions
def calculate_rsi(prices: Union[List[float], np.ndarray], period: int = 14) -> Optional[float]:
    """Direct RSI calculation"""
    if len(prices) < period + 1:
        return None
    
    changes = np.diff(prices)
    gains = np.where(changes > 0, changes, 0)
    losses = np.where(changes < 0, -changes, 0)
    
    avg_gain = np.mean(gains[-period:])
    avg_loss = np.mean(losses[-period:])
    
    if avg_loss == 0:
        return 100.0
    
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def calculate_williams_r(prices: Union[List[float], np.ndarray], period: int = 14) -> Optional[float]:
    """Direct Williams %R calculation"""
    if len(prices) < period:
        return None
    
    recent_prices = prices[-period:]
    current_close = recent_prices[-1]
    highest_high = max(recent_prices)
    lowest_low = min(recent_prices)
    
    if highest_high == lowest_low:
        return -50.0
    
    return ((highest_high - current_close) / (highest_high - lowest_low)) * -100.0


# Example usage and testing
if __name__ == "__main__":
    import random
    
    # Generate sample price data with trend
    base_price = 100.0
    prices = []
    for i in range(100):
        base_price += random.uniform(-1, 1.5)  # Slight upward bias
        prices.append(base_price)
    
    print("Testing Oscillator Indicators")
    print("=" * 40)
    
    # Test RSI
    rsi = create_rsi('RSI_14', 14)
    print(f"\nRSI Results (last 10):")
    for i, price in enumerate(prices):
        value = rsi.update(price)
        if value and i >= len(prices) - 10:
            print(f"Price: {price:.2f}, RSI: {value:.2f}")
    
    # Test MACD
    macd = create_macd('MACD_Standard')
    print(f"\nMACD Results (last 5):")
    for i, price in enumerate(prices):
        values = macd.update(price)
        if values and i >= len(prices) - 5:
            print(f"Price: {price:.2f}, MACD: {values['MACD']:.4f}, "
                  f"Signal: {values['Signal']:.4f}, Histogram: {values['Histogram']:.4f}")
    
    # Performance stats
    print(f"\nPerformance Stats:")
    print(f"RSI: {rsi.get_performance_stats()}")
    print(f"MACD: {macd.get_performance_stats()}")