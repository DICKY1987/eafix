"""
Moving Average Indicators: SMA, EMA, WMA
"""
from typing import List, Optional, Union
import numpy as np
from .base_indicator import BaseIndicator, IndicatorConfig, IndicatorFactory


class SMAConfig(IndicatorConfig):
    """Configuration for Simple Moving Average"""
    
    def validate_parameters(self):
        period = self.get('period', 0)
        if not isinstance(period, int) or period < 1:
            raise ValueError("SMA period must be a positive integer")
        if period > 1000:
            raise ValueError("SMA period too large (max 1000)")


class SimpleMovingAverage(BaseIndicator):
    """Simple Moving Average (SMA) indicator"""
    
    def __init__(self, name: str, config: SMAConfig):
        super().__init__(name, config)
        self.period = config.get('period', 20)
    
    def get_required_periods(self) -> int:
        return self.period
    
    def calculate(self, price_data: Union[List[float], np.ndarray]) -> Optional[float]:
        """Calculate SMA value"""
        if len(price_data) < self.period:
            return None
        
        # Take the last 'period' values and calculate mean
        recent_prices = price_data[-self.period:]
        return float(np.mean(recent_prices))
    
    def validate_config(self) -> bool:
        super().validate_config()
        if self.period < 1:
            raise ValueError("SMA period must be at least 1")
        return True


class EMAConfig(IndicatorConfig):
    """Configuration for Exponential Moving Average"""
    
    def validate_parameters(self):
        period = self.get('period', 0)
        if not isinstance(period, int) or period < 1:
            raise ValueError("EMA period must be a positive integer")
        if period > 1000:
            raise ValueError("EMA period too large (max 1000)")
        
        smoothing = self.get('smoothing', 2.0)
        if smoothing <= 0:
            raise ValueError("EMA smoothing factor must be positive")


class ExponentialMovingAverage(BaseIndicator):
    """Exponential Moving Average (EMA) indicator"""
    
    def __init__(self, name: str, config: EMAConfig):
        super().__init__(name, config)
        self.period = config.get('period', 20)
        self.smoothing = config.get('smoothing', 2.0)
        self.multiplier = self.smoothing / (1 + self.period)
        self.previous_ema = None
        
    def get_required_periods(self) -> int:
        return self.period
    
    def calculate(self, price_data: Union[List[float], np.ndarray]) -> Optional[float]:
        """Calculate EMA value"""
        if len(price_data) < 1:
            return None
        
        current_price = price_data[-1]
        
        # For initial calculation or when we don't have previous EMA
        if self.previous_ema is None or len(price_data) < self.period:
            if len(price_data) >= self.period:
                # Use SMA for initial EMA value
                self.previous_ema = float(np.mean(price_data[-self.period:]))
            else:
                # Use SMA of available data
                self.previous_ema = float(np.mean(price_data))
            return self.previous_ema
        
        # EMA calculation: (current_price * multiplier) + (previous_ema * (1 - multiplier))
        current_ema = (current_price * self.multiplier) + (self.previous_ema * (1 - self.multiplier))
        self.previous_ema = current_ema
        
        return current_ema
    
    def reset(self):
        """Reset EMA state"""
        super().reset()
        self.previous_ema = None
    
    def validate_config(self) -> bool:
        super().validate_config()
        if self.period < 1:
            raise ValueError("EMA period must be at least 1")
        if self.smoothing <= 0:
            raise ValueError("EMA smoothing factor must be positive")
        return True


class WMAConfig(IndicatorConfig):
    """Configuration for Weighted Moving Average"""
    
    def validate_parameters(self):
        period = self.get('period', 0)
        if not isinstance(period, int) or period < 1:
            raise ValueError("WMA period must be a positive integer")
        if period > 1000:
            raise ValueError("WMA period too large (max 1000)")


class WeightedMovingAverage(BaseIndicator):
    """Weighted Moving Average (WMA) indicator"""
    
    def __init__(self, name: str, config: WMAConfig):
        super().__init__(name, config)
        self.period = config.get('period', 20)
        
        # Pre-calculate weights for efficiency
        self.weights = np.arange(1, self.period + 1, dtype=np.float64)
        self.weight_sum = np.sum(self.weights)
    
    def get_required_periods(self) -> int:
        return self.period
    
    def calculate(self, price_data: Union[List[float], np.ndarray]) -> Optional[float]:
        """Calculate WMA value"""
        if len(price_data) < self.period:
            return None
        
        # Take the last 'period' values
        recent_prices = np.array(price_data[-self.period:], dtype=np.float64)
        
        # Calculate weighted average
        weighted_sum = np.sum(recent_prices * self.weights)
        return float(weighted_sum / self.weight_sum)
    
    def validate_config(self) -> bool:
        super().validate_config()
        if self.period < 1:
            raise ValueError("WMA period must be at least 1")
        return True


class HMAConfig(IndicatorConfig):
    """Configuration for Hull Moving Average"""
    
    def validate_parameters(self):
        period = self.get('period', 0)
        if not isinstance(period, int) or period < 1:
            raise ValueError("HMA period must be a positive integer")
        if period > 1000:
            raise ValueError("HMA period too large (max 1000)")


class HullMovingAverage(BaseIndicator):
    """Hull Moving Average (HMA) indicator"""
    
    def __init__(self, name: str, config: HMAConfig):
        super().__init__(name, config)
        self.period = config.get('period', 20)
        
        # Hull MA uses WMA internally
        self.half_period = max(1, self.period // 2)
        self.sqrt_period = max(1, int(np.sqrt(self.period)))
        
        # Create weights for different periods
        self.weights_half = np.arange(1, self.half_period + 1, dtype=np.float64)
        self.weights_full = np.arange(1, self.period + 1, dtype=np.float64)
        self.weights_sqrt = np.arange(1, self.sqrt_period + 1, dtype=np.float64)
        
        self.weight_sum_half = np.sum(self.weights_half)
        self.weight_sum_full = np.sum(self.weights_full)
        self.weight_sum_sqrt = np.sum(self.weights_sqrt)
        
        # Buffer for intermediate HMA calculation
        self.hma_values = []
    
    def get_required_periods(self) -> int:
        return self.period
    
    def calculate(self, price_data: Union[List[float], np.ndarray]) -> Optional[float]:
        """Calculate HMA value"""
        if len(price_data) < self.period:
            return None
        
        # Convert to numpy array for efficiency
        prices = np.array(price_data, dtype=np.float64)
        
        # Step 1: Calculate WMA with half period
        if len(prices) >= self.half_period:
            wma_half = np.sum(prices[-self.half_period:] * self.weights_half) / self.weight_sum_half
        else:
            return None
        
        # Step 2: Calculate WMA with full period
        wma_full = np.sum(prices[-self.period:] * self.weights_full) / self.weight_sum_full
        
        # Step 3: Calculate 2*WMA(half) - WMA(full)
        raw_hma = 2 * wma_half - wma_full
        
        # Step 4: Add to HMA values buffer
        self.hma_values.append(raw_hma)
        
        # Keep only required values for sqrt period calculation
        if len(self.hma_values) > self.sqrt_period * 2:
            self.hma_values = self.hma_values[-self.sqrt_period * 2:]
        
        # Step 5: Calculate WMA of raw HMA values with sqrt(period)
        if len(self.hma_values) >= self.sqrt_period:
            hma_array = np.array(self.hma_values[-self.sqrt_period:], dtype=np.float64)
            final_hma = np.sum(hma_array * self.weights_sqrt) / self.weight_sum_sqrt
            return float(final_hma)
        
        return None
    
    def reset(self):
        """Reset HMA state"""
        super().reset()
        self.hma_values.clear()
    
    def validate_config(self) -> bool:
        super().validate_config()
        if self.period < 1:
            raise ValueError("HMA period must be at least 1")
        return True


class SMMConfig(IndicatorConfig):
    """Configuration for Smoothed Moving Average"""
    
    def validate_parameters(self):
        period = self.get('period', 0)
        if not isinstance(period, int) or period < 1:
            raise ValueError("SMMA period must be a positive integer")
        if period > 1000:
            raise ValueError("SMMA period too large (max 1000)")


class SmoothedMovingAverage(BaseIndicator):
    """Smoothed Moving Average (SMMA) indicator - also known as Modified Moving Average"""
    
    def __init__(self, name: str, config: SMMConfig):
        super().__init__(name, config)
        self.period = config.get('period', 20)
        self.previous_smma = None
        self.is_first_calculation = True
    
    def get_required_periods(self) -> int:
        return self.period
    
    def calculate(self, price_data: Union[List[float], np.ndarray]) -> Optional[float]:
        """Calculate SMMA value"""
        if len(price_data) < self.period:
            return None
        
        current_price = price_data[-1]
        
        # For first calculation, use SMA
        if self.is_first_calculation or self.previous_smma is None:
            self.previous_smma = float(np.mean(price_data[-self.period:]))
            self.is_first_calculation = False
            return self.previous_smma
        
        # SMMA formula: (SMMA(i-1) * (n-1) + Price(i)) / n
        current_smma = (self.previous_smma * (self.period - 1) + current_price) / self.period
        self.previous_smma = current_smma
        
        return current_smma
    
    def reset(self):
        """Reset SMMA state"""
        super().reset()
        self.previous_smma = None
        self.is_first_calculation = True
    
    def validate_config(self) -> bool:
        super().validate_config()
        if self.period < 1:
            raise ValueError("SMMA period must be at least 1")
        return True


# Factory method for creating moving average indicators
def create_moving_average(ma_type: str, name: str, period: int, **kwargs) -> BaseIndicator:
    """
    Factory function to create moving average indicators
    
    Args:
        ma_type: Type of moving average ('SMA', 'EMA', 'WMA', 'HMA', 'SMMA')
        name: Instance name
        period: Period for calculation
        **kwargs: Additional parameters
        
    Returns:
        Moving average indicator instance
    """
    ma_type = ma_type.upper()
    
    if ma_type == 'SMA':
        config = SMAConfig(period=period, **kwargs)
        return SimpleMovingAverage(name, config)
    elif ma_type == 'EMA':
        config = EMAConfig(period=period, **kwargs)
        return ExponentialMovingAverage(name, config)
    elif ma_type == 'WMA':
        config = WMAConfig(period=period, **kwargs)
        return WeightedMovingAverage(name, config)
    elif ma_type == 'HMA':
        config = HMAConfig(period=period, **kwargs)
        return HullMovingAverage(name, config)
    elif ma_type == 'SMMA':
        config = SMMConfig(period=period, **kwargs)
        return SmoothedMovingAverage(name, config)
    else:
        raise ValueError(f"Unknown moving average type: {ma_type}")


# Register indicators with factory
IndicatorFactory.register('SMA', SimpleMovingAverage)
IndicatorFactory.register('EMA', ExponentialMovingAverage)
IndicatorFactory.register('WMA', WeightedMovingAverage)
IndicatorFactory.register('HMA', HullMovingAverage)
IndicatorFactory.register('SMMA', SmoothedMovingAverage)


# Utility functions for direct calculations (without indicator objects)
def calculate_sma(prices: Union[List[float], np.ndarray], period: int) -> Optional[float]:
    """Direct SMA calculation"""
    if len(prices) < period:
        return None
    return float(np.mean(prices[-period:]))


def calculate_ema(prices: Union[List[float], np.ndarray], period: int, 
                  previous_ema: Optional[float] = None) -> Optional[float]:
    """Direct EMA calculation"""
    if len(prices) < 1:
        return None
    
    current_price = prices[-1]
    multiplier = 2.0 / (period + 1)
    
    if previous_ema is None:
        if len(prices) >= period:
            previous_ema = calculate_sma(prices, period)
        else:
            previous_ema = calculate_sma(prices, len(prices))
        
        if previous_ema is None:
            return None
        
        return previous_ema
    
    return (current_price * multiplier) + (previous_ema * (1 - multiplier))


def calculate_wma(prices: Union[List[float], np.ndarray], period: int) -> Optional[float]:
    """Direct WMA calculation"""
    if len(prices) < period:
        return None
    
    weights = np.arange(1, period + 1, dtype=np.float64)
    recent_prices = np.array(prices[-period:], dtype=np.float64)
    
    return float(np.sum(recent_prices * weights) / np.sum(weights))


# Example usage and testing
if __name__ == "__main__":
    # Example usage
    import random
    
    # Generate sample price data
    prices = [100 + random.uniform(-5, 5) for _ in range(100)]
    
    # Test SMA
    sma = create_moving_average('SMA', 'SMA_20', 20)
    for price in prices:
        value = sma.update(price)
        if value:
            print(f"SMA: {value:.4f}")
    
    # Test EMA
    ema = create_moving_average('EMA', 'EMA_20', 20)
    for price in prices:
        value = ema.update(price)
        if value:
            print(f"EMA: {value:.4f}")
    
    # Test performance
    print("\nPerformance Stats:")
    print("SMA:", sma.get_performance_stats())
    print("EMA:", ema.get_performance_stats())