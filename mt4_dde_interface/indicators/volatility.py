"""
Volatility Indicators: Bollinger Bands, ATR, Standard Deviation, Volatility Index
"""
from typing import List, Optional, Union, Dict
import numpy as np
from collections import deque
from .base_indicator import BaseIndicator, MultiValueIndicator, IndicatorConfig, IndicatorFactory
from .moving_averages import calculate_sma


class BollingerBandsConfig(IndicatorConfig):
    """Configuration for Bollinger Bands indicator"""
    
    def validate_parameters(self):
        period = self.get('period', 0)
        if not isinstance(period, int) or period < 2:
            raise ValueError("Bollinger Bands period must be at least 2")
        
        std_dev = self.get('std_dev', 0)
        if not isinstance(std_dev, (int, float)) or std_dev <= 0:
            raise ValueError("Bollinger Bands standard deviation must be positive")


class BollingerBands(MultiValueIndicator):
    """Bollinger Bands volatility indicator"""
    
    def __init__(self, name: str, config: BollingerBandsConfig):
        super().__init__(name, config)
        self.period = config.get('period', 20)
        self.std_dev_multiplier = config.get('std_dev', 2.0)
    
    def get_required_periods(self) -> int:
        return self.period
    
    def get_primary_value_name(self) -> str:
        return 'Middle'
    
    def calculate_values(self, price_data: Union[List[float], np.ndarray]) -> Optional[Dict[str, float]]:
        """Calculate Bollinger Bands values (Upper, Middle, Lower)"""
        if len(price_data) < self.period:
            return None
        
        recent_prices = np.array(price_data[-self.period:])
        
        # Calculate middle band (SMA)
        middle_band = np.mean(recent_prices)
        
        # Calculate standard deviation
        std_dev = np.std(recent_prices, ddof=1)
        
        # Calculate upper and lower bands
        band_width = std_dev * self.std_dev_multiplier
        upper_band = middle_band + band_width
        lower_band = middle_band - band_width
        
        # Calculate additional metrics
        current_price = recent_prices[-1]
        percent_b = ((current_price - lower_band) / (upper_band - lower_band)) * 100 if upper_band != lower_band else 50
        bandwidth = ((upper_band - lower_band) / middle_band) * 100
        
        return {
            'Upper': upper_band,
            'Middle': middle_band,
            'Lower': lower_band,
            'PercentB': percent_b,
            'Bandwidth': bandwidth
        }
    
    def is_squeeze(self, threshold: float = 10.0) -> bool:
        """Check if bands are in squeeze condition (low volatility)"""
        values = self.get_current_values()
        return values.get('Bandwidth', 100) < threshold
    
    def is_expansion(self, threshold: float = 25.0) -> bool:
        """Check if bands are expanding (high volatility)"""
        values = self.get_current_values()
        return values.get('Bandwidth', 0) > threshold


class ATRConfig(IndicatorConfig):
    """Configuration for Average True Range indicator"""
    
    def validate_parameters(self):
        period = self.get('period', 0)
        if not isinstance(period, int) or period < 1:
            raise ValueError("ATR period must be a positive integer")


class AverageTrueRange(BaseIndicator):
    """Average True Range (ATR) volatility indicator"""
    
    def __init__(self, name: str, config: ATRConfig):
        super().__init__(name, config)
        self.period = config.get('period', 14)
        self.true_ranges = deque(maxlen=self.period)
        self.previous_close = None
        self.atr_value = None
    
    def get_required_periods(self) -> int:
        return self.period + 1  # Need extra for previous close
    
    def calculate(self, price_data: Union[List[float], np.ndarray]) -> Optional[float]:
        """
        Calculate ATR value
        Note: This simplified version uses price data as close prices
        Real implementation would need High, Low, Close data
        """
        if len(price_data) < 2:
            return None
        
        current_price = price_data[-1]
        
        # Calculate True Range
        if self.previous_close is not None:
            # Simplified TR calculation using only close prices
            # Real TR = max(H-L, |H-C_prev|, |L-C_prev|)
            true_range = abs(current_price - self.previous_close)
        else:
            # First calculation
            if len(price_data) >= 2:
                true_range = abs(price_data[-1] - price_data[-2])
            else:
                true_range = 0.0
        
        self.true_ranges.append(true_range)
        self.previous_close = current_price
        
        if len(self.true_ranges) < self.period:
            return None
        
        # Calculate ATR using Wilder's smoothing
        if self.atr_value is None:
            # First ATR calculation - use simple average
            self.atr_value = sum(self.true_ranges) / len(self.true_ranges)
        else:
            # Subsequent calculations - use smoothing
            self.atr_value = ((self.atr_value * (self.period - 1)) + true_range) / self.period
        
        return self.atr_value
    
    def reset(self):
        """Reset ATR state"""
        super().reset()
        self.true_ranges.clear()
        self.previous_close = None
        self.atr_value = None
    
    def get_volatility_level(self) -> str:
        """Get volatility level description based on ATR value"""
        if self.last_value is None:
            return "Unknown"
        
        # These thresholds would need to be adjusted based on the instrument
        if self.last_value < 0.001:
            return "Very Low"
        elif self.last_value < 0.005:
            return "Low"
        elif self.last_value < 0.015:
            return "Medium"
        elif self.last_value < 0.030:
            return "High"
        else:
            return "Very High"


class StandardDeviationConfig(IndicatorConfig):
    """Configuration for Standard Deviation indicator"""
    
    def validate_parameters(self):
        period = self.get('period', 0)
        if not isinstance(period, int) or period < 2:
            raise ValueError("Standard Deviation period must be at least 2")


class StandardDeviation(BaseIndicator):
    """Standard Deviation volatility indicator"""
    
    def __init__(self, name: str, config: StandardDeviationConfig):
        super().__init__(name, config)
        self.period = config.get('period', 20)
        self.use_sample = config.get('use_sample', True)  # Use sample std dev (ddof=1)
    
    def get_required_periods(self) -> int:
        return self.period
    
    def calculate(self, price_data: Union[List[float], np.ndarray]) -> Optional[float]:
        """Calculate Standard Deviation value"""
        if len(price_data) < self.period:
            return None
        
        recent_prices = np.array(price_data[-self.period:])
        
        # Calculate standard deviation
        ddof = 1 if self.use_sample else 0
        std_dev = np.std(recent_prices, ddof=ddof)
        
        return float(std_dev)


class VolatilityIndexConfig(IndicatorConfig):
    """Configuration for Volatility Index indicator"""
    
    def validate_parameters(self):
        period = self.get('period', 0)
        if not isinstance(period, int) or period < 2:
            raise ValueError("Volatility Index period must be at least 2")


class VolatilityIndex(BaseIndicator):
    """Volatility Index - measures price volatility relative to average"""
    
    def __init__(self, name: str, config: VolatilityIndexConfig):
        super().__init__(name, config)
        self.period = config.get('period', 14)
        self.scaling_factor = config.get('scaling_factor', 100.0)
    
    def get_required_periods(self) -> int:
        return self.period + 1  # Need extra for price changes
    
    def calculate(self, price_data: Union[List[float], np.ndarray]) -> Optional[float]:
        """Calculate Volatility Index value"""
        if len(price_data) < self.period + 1:
            return None
        
        # Calculate price changes
        prices = np.array(price_data)
        price_changes = np.abs(np.diff(prices))
        
        if len(price_changes) < self.period:
            return None
        
        # Calculate volatility as standard deviation of price changes
        recent_changes = price_changes[-self.period:]
        volatility = np.std(recent_changes, ddof=1)
        
        # Scale by current price level to get relative volatility
        current_price = prices[-1]
        if current_price != 0:
            volatility_index = (volatility / current_price) * self.scaling_factor
        else:
            volatility_index = 0.0
        
        return float(volatility_index)


class KeltnerChannelsConfig(IndicatorConfig):
    """Configuration for Keltner Channels indicator"""
    
    def validate_parameters(self):
        period = self.get('period', 0)
        if not isinstance(period, int) or period < 1:
            raise ValueError("Keltner Channels period must be a positive integer")
        
        multiplier = self.get('multiplier', 0)
        if not isinstance(multiplier, (int, float)) or multiplier <= 0:
            raise ValueError("Keltner Channels multiplier must be positive")


class KeltnerChannels(MultiValueIndicator):
    """Keltner Channels volatility indicator"""
    
    def __init__(self, name: str, config: KeltnerChannelsConfig):
        super().__init__(name, config)
        self.period = config.get('period', 20)
        self.multiplier = config.get('multiplier', 2.0)
        
        # ATR calculation for channel width
        self.atr_calculator = AverageTrueRange(
            f"{name}_ATR", 
            ATRConfig(period=self.period)
        )
    
    def get_required_periods(self) -> int:
        return self.period + 1
    
    def get_primary_value_name(self) -> str:
        return 'Middle'
    
    def calculate_values(self, price_data: Union[List[float], np.ndarray]) -> Optional[Dict[str, float]]:
        """Calculate Keltner Channels values (Upper, Middle, Lower)"""
        if len(price_data) < self.get_required_periods():
            return None
        
        # Calculate middle line (EMA or SMA of typical price)
        recent_prices = price_data[-self.period:]
        middle_line = np.mean(recent_prices)  # Using SMA for simplicity
        
        # Update ATR calculator
        for price in price_data:
            self.atr_calculator.update(price)
        
        atr_value = self.atr_calculator.get_current_value()
        if atr_value is None:
            return None
        
        # Calculate channel width
        channel_width = atr_value * self.multiplier
        
        # Calculate upper and lower channels
        upper_channel = middle_line + channel_width
        lower_channel = middle_line - channel_width
        
        return {
            'Upper': upper_channel,
            'Middle': middle_line,
            'Lower': lower_channel,
            'Width': channel_width * 2
        }
    
    def reset(self):
        """Reset Keltner Channels state"""
        super().reset()
        self.atr_calculator.reset()


# Factory functions for creating volatility indicators
def create_bollinger_bands(name: str, period: int = 20, std_dev: float = 2.0) -> BollingerBands:
    """Create Bollinger Bands indicator"""
    config = BollingerBandsConfig(period=period, std_dev=std_dev)
    return BollingerBands(name, config)


def create_atr(name: str, period: int = 14) -> AverageTrueRange:
    """Create ATR indicator"""
    config = ATRConfig(period=period)
    return AverageTrueRange(name, config)


def create_standard_deviation(name: str, period: int = 20, use_sample: bool = True) -> StandardDeviation:
    """Create Standard Deviation indicator"""
    config = StandardDeviationConfig(period=period, use_sample=use_sample)
    return StandardDeviation(name, config)


def create_volatility_index(name: str, period: int = 14, scaling_factor: float = 100.0) -> VolatilityIndex:
    """Create Volatility Index indicator"""
    config = VolatilityIndexConfig(period=period, scaling_factor=scaling_factor)
    return VolatilityIndex(name, config)


def create_keltner_channels(name: str, period: int = 20, multiplier: float = 2.0) -> KeltnerChannels:
    """Create Keltner Channels indicator"""
    config = KeltnerChannelsConfig(period=period, multiplier=multiplier)
    return KeltnerChannels(name, config)


# Register indicators with factory
IndicatorFactory.register('BollingerBands', BollingerBands)
IndicatorFactory.register('ATR', AverageTrueRange)
IndicatorFactory.register('StandardDeviation', StandardDeviation)
IndicatorFactory.register('VolatilityIndex', VolatilityIndex)
IndicatorFactory.register('KeltnerChannels', KeltnerChannels)


# Direct calculation functions
def calculate_bollinger_bands(prices: Union[List[float], np.ndarray], 
                            period: int = 20, 
                            std_dev: float = 2.0) -> Optional[Dict[str, float]]:
    """Direct Bollinger Bands calculation"""
    if len(prices) < period:
        return None
    
    recent_prices = np.array(prices[-period:])
    middle = np.mean(recent_prices)
    std = np.std(recent_prices, ddof=1)
    
    band_width = std * std_dev
    upper = middle + band_width
    lower = middle - band_width
    
    current_price = recent_prices[-1]
    percent_b = ((current_price - lower) / (upper - lower)) * 100 if upper != lower else 50
    bandwidth = ((upper - lower) / middle) * 100
    
    return {
        'Upper': upper,
        'Middle': middle,
        'Lower': lower,
        'PercentB': percent_b,
        'Bandwidth': bandwidth
    }


def calculate_standard_deviation(prices: Union[List[float], np.ndarray], 
                               period: int = 20, 
                               use_sample: bool = True) -> Optional[float]:
    """Direct Standard Deviation calculation"""
    if len(prices) < period:
        return None
    
    recent_prices = np.array(prices[-period:])
    ddof = 1 if use_sample else 0
    return float(np.std(recent_prices, ddof=ddof))


# Utility functions for volatility analysis
def classify_volatility(atr_value: float, price_level: float) -> str:
    """Classify volatility level based on ATR relative to price"""
    if atr_value is None or price_level <= 0:
        return "Unknown"
    
    volatility_ratio = atr_value / price_level
    
    if volatility_ratio < 0.005:
        return "Very Low"
    elif volatility_ratio < 0.015:
        return "Low"
    elif volatility_ratio < 0.025:
        return "Medium"
    elif volatility_ratio < 0.040:
        return "High"
    else:
        return "Very High"


def volatility_breakout_signal(bb_values: Dict[str, float], 
                             price: float, 
                             squeeze_threshold: float = 10.0) -> str:
    """Generate volatility breakout signals"""
    if not bb_values or price is None:
        return "No Signal"
    
    percent_b = bb_values.get('PercentB', 50)
    bandwidth = bb_values.get('Bandwidth', 20)
    
    # Check for squeeze condition
    if bandwidth < squeeze_threshold:
        if percent_b > 80:
            return "Squeeze - Bullish Breakout Pending"
        elif percent_b < 20:
            return "Squeeze - Bearish Breakout Pending"
        else:
            return "Squeeze - Neutral"
    
    # Check for expansion
    if bandwidth > squeeze_threshold * 2:
        if percent_b > 80:
            return "High Volatility - Overbought"
        elif percent_b < 20:
            return "High Volatility - Oversold"
        else:
            return "High Volatility - Trending"
    
    return "Normal Volatility"


# Example usage and testing
if __name__ == "__main__":
    import random
    
    # Generate sample price data with varying volatility
    prices = []
    base_price = 100.0
    volatility_factor = 1.0
    
    for i in range(100):
        # Simulate changing volatility
        if i % 20 == 0:
            volatility_factor = random.uniform(0.5, 3.0)
        
        change = random.uniform(-volatility_factor, volatility_factor)
        base_price += change
        prices.append(base_price)
    
    print("Testing Volatility Indicators")
    print("=" * 40)
    
    # Test Bollinger Bands
    bb = create_bollinger_bands('BB_20_2', 20, 2.0)
    print(f"\nBollinger Bands Results (last 5):")
    for i, price in enumerate(prices):
        values = bb.update(price)
        if values and i >= len(prices) - 5:
            print(f"Price: {price:.2f}, Upper: {values['Upper']:.2f}, "
                  f"Middle: {values['Middle']:.2f}, Lower: {values['Lower']:.2f}")
            print(f"  %B: {values['PercentB']:.1f}, Bandwidth: {values['Bandwidth']:.1f}")
    
    # Test ATR
    atr = create_atr('ATR_14', 14)
    print(f"\nATR Results (last 5):")
    for i, price in enumerate(prices):
        value = atr.update(price)
        if value and i >= len(prices) - 5:
            print(f"Price: {price:.2f}, ATR: {value:.4f}, "
                  f"Volatility: {atr.get_volatility_level()}")
    
    # Performance stats
    print(f"\nPerformance Stats:")
    print(f"Bollinger Bands: {bb.get_performance_stats()}")
    print(f"ATR: {atr.get_performance_stats()}")