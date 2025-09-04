"""
Base indicator framework for technical analysis
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union
from collections import deque
import numpy as np
from datetime import datetime
import logging


class IndicatorConfig:
    """Configuration class for indicator parameters"""
    
    def __init__(self, **kwargs):
        self.params = kwargs
        self.validate_parameters()
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get parameter value"""
        return self.params.get(key, default)
    
    def set(self, key: str, value: Any):
        """Set parameter value"""
        self.params[key] = value
        self.validate_parameters()
    
    def validate_parameters(self):
        """Override in subclasses for parameter validation"""
        pass
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return self.params.copy()


class BaseIndicator(ABC):
    """Abstract base class for all technical indicators"""
    
    def __init__(self, name: str, config: IndicatorConfig):
        self.name = name
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{name}")
        
        # Internal state
        self.is_initialized = False
        self.last_value = None
        self.last_update = None
        self.calculation_count = 0
        
        # Data buffer for historical values
        self.history_buffer = deque(maxlen=self.get_required_history())
        
        # Performance tracking
        self.total_calculation_time = 0.0
        self.min_calculation_time = float('inf')
        self.max_calculation_time = 0.0
        
        # Validate configuration
        self.validate_config()
    
    @abstractmethod
    def calculate(self, price_data: Union[List[float], np.ndarray]) -> Optional[float]:
        """
        Calculate indicator value from price data
        
        Args:
            price_data: Array of price values (most recent last)
            
        Returns:
            Calculated indicator value or None if insufficient data
        """
        pass
    
    @abstractmethod
    def get_required_periods(self) -> int:
        """
        Get minimum number of periods required for calculation
        
        Returns:
            Minimum periods required
        """
        pass
    
    def get_required_history(self) -> int:
        """
        Get number of historical values to maintain
        Default is 2x required periods, override if needed
        
        Returns:
            Number of historical values to keep
        """
        return max(100, self.get_required_periods() * 2)
    
    def validate_config(self) -> bool:
        """
        Validate indicator configuration
        Override in subclasses for specific validation
        
        Returns:
            True if configuration is valid
        """
        required_periods = self.get_required_periods()
        if required_periods <= 0:
            raise ValueError(f"Required periods must be positive: {required_periods}")
        return True
    
    def update(self, new_price: float) -> Optional[float]:
        """
        Update indicator with new price value
        
        Args:
            new_price: New price value
            
        Returns:
            Updated indicator value or None if insufficient data
        """
        start_time = datetime.now()
        
        try:
            # Add to price history (this will be passed to calculate method)
            self.history_buffer.append(new_price)
            
            # Calculate if we have enough data
            if len(self.history_buffer) >= self.get_required_periods():
                result = self.calculate(list(self.history_buffer))
                
                if result is not None:
                    self.last_value = result
                    self.last_update = datetime.now()
                    self.is_initialized = True
                    self.calculation_count += 1
                    
                    # Update performance metrics
                    calc_time = (datetime.now() - start_time).total_seconds()
                    self._update_performance_metrics(calc_time)
                    
                    return result
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error updating indicator {self.name}: {e}")
            return None
    
    def batch_update(self, price_data: List[float]) -> List[Optional[float]]:
        """
        Update indicator with multiple price values
        
        Args:
            price_data: List of price values
            
        Returns:
            List of indicator values (None where insufficient data)
        """
        results = []
        for price in price_data:
            result = self.update(price)
            results.append(result)
        return results
    
    def reset(self):
        """Reset indicator state"""
        self.history_buffer.clear()
        self.last_value = None
        self.last_update = None
        self.is_initialized = False
        self.calculation_count = 0
        
        # Reset performance metrics
        self.total_calculation_time = 0.0
        self.min_calculation_time = float('inf')
        self.max_calculation_time = 0.0
        
        self.logger.debug(f"Reset indicator {self.name}")
    
    def get_current_value(self) -> Optional[float]:
        """Get current indicator value"""
        return self.last_value
    
    def get_history(self, count: int = None) -> List[float]:
        """
        Get historical price values used by indicator
        
        Args:
            count: Number of values to return (None for all)
            
        Returns:
            List of historical price values
        """
        if count is None:
            return list(self.history_buffer)
        else:
            return list(self.history_buffer)[-count:] if count > 0 else []
    
    def is_ready(self) -> bool:
        """Check if indicator has enough data to produce values"""
        return len(self.history_buffer) >= self.get_required_periods()
    
    def get_info(self) -> Dict:
        """Get indicator information"""
        return {
            'name': self.name,
            'type': self.__class__.__name__,
            'config': self.config.to_dict(),
            'is_initialized': self.is_initialized,
            'is_ready': self.is_ready(),
            'required_periods': self.get_required_periods(),
            'current_value': self.last_value,
            'last_update': self.last_update.isoformat() if self.last_update else None,
            'calculation_count': self.calculation_count,
            'data_points': len(self.history_buffer)
        }
    
    def get_performance_stats(self) -> Dict:
        """Get performance statistics"""
        avg_time = (self.total_calculation_time / self.calculation_count 
                   if self.calculation_count > 0 else 0.0)
        
        return {
            'calculation_count': self.calculation_count,
            'avg_calculation_time_ms': avg_time * 1000,
            'min_calculation_time_ms': (self.min_calculation_time * 1000 
                                      if self.min_calculation_time != float('inf') else 0),
            'max_calculation_time_ms': self.max_calculation_time * 1000,
            'total_calculation_time_ms': self.total_calculation_time * 1000
        }
    
    def _update_performance_metrics(self, calc_time: float):
        """Update performance tracking metrics"""
        self.total_calculation_time += calc_time
        self.min_calculation_time = min(self.min_calculation_time, calc_time)
        self.max_calculation_time = max(self.max_calculation_time, calc_time)
    
    def export_config(self) -> Dict:
        """Export indicator configuration for saving"""
        return {
            'name': self.name,
            'type': self.__class__.__name__,
            'config': self.config.to_dict()
        }
    
    @classmethod
    def from_config(cls, config_dict: Dict) -> 'BaseIndicator':
        """Create indicator from configuration dictionary"""
        name = config_dict['name']
        params = config_dict['config']
        indicator_config = IndicatorConfig(**params)
        return cls(name, indicator_config)


class MultiValueIndicator(BaseIndicator):
    """Base class for indicators that return multiple values (like Bollinger Bands)"""
    
    def __init__(self, name: str, config: IndicatorConfig):
        super().__init__(name, config)
        self.last_values = {}  # Dictionary of named values
        
    @abstractmethod
    def calculate_values(self, price_data: Union[List[float], np.ndarray]) -> Optional[Dict[str, float]]:
        """
        Calculate multiple indicator values
        
        Args:
            price_data: Array of price values
            
        Returns:
            Dictionary of calculated values or None if insufficient data
        """
        pass
    
    def calculate(self, price_data: Union[List[float], np.ndarray]) -> Optional[float]:
        """
        Calculate single primary value (for compatibility with BaseIndicator)
        Override get_primary_value_name() to specify which value is primary
        """
        values = self.calculate_values(price_data)
        if values is None:
            return None
        
        primary_name = self.get_primary_value_name()
        return values.get(primary_name)
    
    def get_primary_value_name(self) -> str:
        """
        Get name of primary value for single-value interface
        Override in subclasses
        """
        return 'main'
    
    def update(self, new_price: float) -> Optional[Dict[str, float]]:
        """
        Update indicator with new price value
        
        Args:
            new_price: New price value
            
        Returns:
            Dictionary of updated indicator values or None if insufficient data
        """
        start_time = datetime.now()
        
        try:
            self.history_buffer.append(new_price)
            
            if len(self.history_buffer) >= self.get_required_periods():
                result = self.calculate_values(list(self.history_buffer))
                
                if result is not None:
                    self.last_values = result
                    self.last_value = result.get(self.get_primary_value_name())
                    self.last_update = datetime.now()
                    self.is_initialized = True
                    self.calculation_count += 1
                    
                    calc_time = (datetime.now() - start_time).total_seconds()
                    self._update_performance_metrics(calc_time)
                    
                    return result
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error updating multi-value indicator {self.name}: {e}")
            return None
    
    def get_current_values(self) -> Dict[str, float]:
        """Get all current indicator values"""
        return self.last_values.copy()
    
    def get_value(self, name: str) -> Optional[float]:
        """Get specific indicator value by name"""
        return self.last_values.get(name)


class IndicatorFactory:
    """Factory for creating indicators"""
    
    _indicator_classes = {}
    
    @classmethod
    def register(cls, indicator_type: str, indicator_class: type):
        """Register indicator class"""
        cls._indicator_classes[indicator_type] = indicator_class
    
    @classmethod
    def create(cls, indicator_type: str, name: str, config: Dict) -> BaseIndicator:
        """
        Create indicator instance
        
        Args:
            indicator_type: Type of indicator (e.g., 'SMA', 'RSI')
            name: Instance name
            config: Configuration parameters
            
        Returns:
            Indicator instance
        """
        if indicator_type not in cls._indicator_classes:
            raise ValueError(f"Unknown indicator type: {indicator_type}")
        
        indicator_class = cls._indicator_classes[indicator_type]
        indicator_config = IndicatorConfig(**config)
        return indicator_class(name, indicator_config)
    
    @classmethod
    def get_available_types(cls) -> List[str]:
        """Get list of available indicator types"""
        return list(cls._indicator_classes.keys())


# Utility functions for common calculations
def sma(values: Union[List[float], np.ndarray], period: int) -> Optional[float]:
    """Simple Moving Average"""
    if len(values) < period:
        return None
    return float(np.mean(values[-period:]))


def ema(values: Union[List[float], np.ndarray], period: int, 
        previous_ema: Optional[float] = None) -> Optional[float]:
    """Exponential Moving Average"""
    if len(values) < 1:
        return None
    
    current_value = values[-1]
    
    if previous_ema is None or len(values) < period:
        # Use SMA for initial value
        if len(values) >= period:
            return sma(values, period)
        else:
            return sma(values, len(values))
    
    # EMA formula: (current_value * multiplier) + (previous_ema * (1 - multiplier))
    multiplier = 2.0 / (period + 1)
    return (current_value * multiplier) + (previous_ema * (1 - multiplier))


def wma(values: Union[List[float], np.ndarray], period: int) -> Optional[float]:
    """Weighted Moving Average"""
    if len(values) < period:
        return None
    
    weights = np.arange(1, period + 1)
    return float(np.average(values[-period:], weights=weights))


def stddev(values: Union[List[float], np.ndarray], period: int) -> Optional[float]:
    """Standard Deviation"""
    if len(values) < period:
        return None
    return float(np.std(values[-period:], ddof=1))


def true_range(high: float, low: float, prev_close: float) -> float:
    """Calculate True Range for ATR calculation"""
    return max(
        high - low,
        abs(high - prev_close),
        abs(low - prev_close)
    )