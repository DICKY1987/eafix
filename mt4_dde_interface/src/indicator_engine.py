"""
Indicator Engine - Coordinates multiple indicators across multiple symbols
"""
import threading
import time
import logging
from collections import defaultdict
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta

from .price_manager import PriceManager, PriceTick
from ..indicators.base_indicator import BaseIndicator, IndicatorFactory
from ..indicators.moving_averages import *
from ..indicators.oscillators import *
from ..indicators.volatility import *


class IndicatorInstance:
    """Wrapper for indicator instance with metadata"""
    
    def __init__(self, indicator: BaseIndicator, symbol: str, enabled: bool = True):
        self.indicator = indicator
        self.symbol = symbol
        self.enabled = enabled
        self.created_at = datetime.now()
        self.last_update = None
        self.update_count = 0
        self.error_count = 0
        self.last_error = None
        
    def update(self, price: float) -> Any:
        """Update indicator with new price"""
        if not self.enabled:
            return None
        
        try:
            result = self.indicator.update(price)
            self.last_update = datetime.now()
            self.update_count += 1
            return result
        except Exception as e:
            self.error_count += 1
            self.last_error = str(e)
            logging.error(f"Error updating indicator {self.indicator.name} for {self.symbol}: {e}")
            return None
    
    def get_info(self) -> Dict:
        """Get instance information"""
        info = self.indicator.get_info()
        info.update({
            'symbol': self.symbol,
            'enabled': self.enabled,
            'created_at': self.created_at.isoformat(),
            'last_update': self.last_update.isoformat() if self.last_update else None,
            'update_count': self.update_count,
            'error_count': self.error_count,
            'last_error': self.last_error
        })
        return info


class IndicatorGroup:
    """Group of indicators for a specific symbol"""
    
    def __init__(self, symbol: str):
        self.symbol = symbol
        self.indicators = {}  # indicator_name -> IndicatorInstance
        self.lock = threading.RLock()
        self.created_at = datetime.now()
        self.total_updates = 0
        
    def add_indicator(self, instance: IndicatorInstance) -> bool:
        """Add indicator instance to group"""
        with self.lock:
            if instance.indicator.name in self.indicators:
                logging.warning(f"Indicator {instance.indicator.name} already exists for {self.symbol}")
                return False
            
            self.indicators[instance.indicator.name] = instance
            logging.info(f"Added indicator {instance.indicator.name} to {self.symbol}")
            return True
    
    def remove_indicator(self, indicator_name: str) -> bool:
        """Remove indicator from group"""
        with self.lock:
            if indicator_name in self.indicators:
                del self.indicators[indicator_name]
                logging.info(f"Removed indicator {indicator_name} from {self.symbol}")
                return True
            return False
    
    def update_all(self, price: float) -> Dict[str, Any]:
        """Update all indicators in group with new price"""
        results = {}
        with self.lock:
            for name, instance in self.indicators.items():
                result = instance.update(price)
                if result is not None:
                    results[name] = result
            
            self.total_updates += 1
        
        return results
    
    def get_indicator(self, name: str) -> Optional[IndicatorInstance]:
        """Get indicator instance by name"""
        return self.indicators.get(name)
    
    def get_all_values(self) -> Dict[str, Any]:
        """Get current values from all indicators"""
        with self.lock:
            values = {}
            for name, instance in self.indicators.items():
                if instance.enabled and instance.indicator.is_initialized:
                    # Handle multi-value indicators
                    if hasattr(instance.indicator, 'get_current_values'):
                        values[name] = instance.indicator.get_current_values()
                    else:
                        values[name] = instance.indicator.get_current_value()
            return values
    
    def get_info(self) -> Dict:
        """Get group information"""
        with self.lock:
            return {
                'symbol': self.symbol,
                'indicator_count': len(self.indicators),
                'enabled_count': sum(1 for i in self.indicators.values() if i.enabled),
                'total_updates': self.total_updates,
                'created_at': self.created_at.isoformat(),
                'indicators': [name for name in self.indicators.keys()]
            }


class IndicatorEngine:
    """Main indicator coordination engine"""
    
    def __init__(self, price_manager: PriceManager):
        self.price_manager = price_manager
        self.symbol_groups = {}  # symbol -> IndicatorGroup
        self.update_callbacks = []  # List of callback functions
        self.lock = threading.RLock()
        self.logger = logging.getLogger(__name__)
        
        # Performance tracking
        self.total_indicator_updates = 0
        self.update_start_time = datetime.now()
        self.last_performance_check = datetime.now()
        
        # Configuration
        self.max_indicators_per_symbol = 50
        self.performance_check_interval = timedelta(minutes=5)
        
        # Register price callback
        self.price_manager_callback_id = None
        self._register_price_callback()

    def _register_price_callback(self):
        """Register callback with price manager for automatic updates"""
        if hasattr(self.price_manager, 'add_callback'):
            self.price_manager.add_callback(self._on_price_tick)

    def _on_price_tick(self, tick: PriceTick):
        """Internal handler for price manager callbacks"""
        self.update_indicators(tick.symbol, tick.mid_price)
    
    def add_indicator(self, symbol: str, indicator_type: str, name: str, 
                     config: Dict, enabled: bool = True) -> bool:
        """
        Add indicator to engine
        
        Args:
            symbol: Currency pair symbol
            indicator_type: Type of indicator (SMA, RSI, etc.)
            name: Unique name for this indicator instance
            config: Indicator configuration parameters
            enabled: Whether indicator should be enabled
            
        Returns:
            True if successfully added, False otherwise
        """
        try:
            with self.lock:
                # Check limits
                if symbol in self.symbol_groups:
                    if len(self.symbol_groups[symbol].indicators) >= self.max_indicators_per_symbol:
                        self.logger.error(f"Maximum indicators ({self.max_indicators_per_symbol}) "
                                        f"reached for symbol {symbol}")
                        return False
                
                # Create indicator instance
                indicator = IndicatorFactory.create(indicator_type, name, config)
                instance = IndicatorInstance(indicator, symbol, enabled)
                
                # Create symbol group if needed
                if symbol not in self.symbol_groups:
                    self.symbol_groups[symbol] = IndicatorGroup(symbol)
                
                # Add to group
                success = self.symbol_groups[symbol].add_indicator(instance)
                
                if success:
                    # Initialize with historical data if available
                    self._initialize_indicator_with_history(symbol, instance)
                    
                    self.logger.info(f"Added {indicator_type} indicator '{name}' for {symbol}")
                
                return success
                
        except Exception as e:
            self.logger.error(f"Error adding indicator {name} for {symbol}: {e}")
            return False
    
    def remove_indicator(self, symbol: str, indicator_name: str) -> bool:
        """Remove indicator from engine"""
        with self.lock:
            if symbol in self.symbol_groups:
                return self.symbol_groups[symbol].remove_indicator(indicator_name)
            return False
    
    def update_indicators(self, symbol: str, new_price: float) -> Dict[str, Any]:
        """
        Update all indicators for a symbol with new price
        
        Args:
            symbol: Currency pair symbol
            new_price: New price value
            
        Returns:
            Dictionary of indicator results
        """
        results = {}
        
        with self.lock:
            if symbol in self.symbol_groups:
                start_time = datetime.now()
                
                # Update all indicators for this symbol
                results = self.symbol_groups[symbol].update_all(new_price)
                
                # Performance tracking
                update_time = (datetime.now() - start_time).total_seconds()
                self.total_indicator_updates += len(results)
                
                # Notify callbacks
                self._notify_callbacks(symbol, new_price, results)
                
                # Periodic performance check
                if datetime.now() - self.last_performance_check > self.performance_check_interval:
                    self._check_performance()
        
        return results
    
    def get_indicator_value(self, symbol: str, indicator_name: str) -> Any:
        """Get current value of specific indicator"""
        with self.lock:
            if symbol in self.symbol_groups:
                instance = self.symbol_groups[symbol].get_indicator(indicator_name)
                if instance and instance.enabled:
                    if hasattr(instance.indicator, 'get_current_values'):
                        return instance.indicator.get_current_values()
                    else:
                        return instance.indicator.get_current_value()
            return None
    
    def get_all_indicators(self, symbol: str) -> Dict[str, Any]:
        """Get all indicator values for a symbol"""
        with self.lock:
            if symbol in self.symbol_groups:
                return self.symbol_groups[symbol].get_all_values()
            return {}
    
    def configure_indicator(self, symbol: str, indicator_name: str, params: Dict) -> bool:
        """
        Configure indicator parameters
        Note: This requires indicator recreation as parameters are set at initialization
        """
        with self.lock:
            if symbol not in self.symbol_groups:
                return False
            
            instance = self.symbol_groups[symbol].get_indicator(indicator_name)
            if not instance:
                return False
            
            try:
                # Store current state
                indicator_type = instance.indicator.__class__.__name__
                enabled = instance.enabled
                
                # Remove old indicator
                self.symbol_groups[symbol].remove_indicator(indicator_name)
                
                # Create new indicator with updated config
                new_indicator = IndicatorFactory.create(indicator_type, indicator_name, params)
                new_instance = IndicatorInstance(new_indicator, symbol, enabled)
                
                # Add new indicator
                success = self.symbol_groups[symbol].add_indicator(new_instance)
                
                if success:
                    # Re-initialize with historical data
                    self._initialize_indicator_with_history(symbol, new_instance)
                    self.logger.info(f"Reconfigured indicator {indicator_name} for {symbol}")
                
                return success
                
            except Exception as e:
                self.logger.error(f"Error configuring indicator {indicator_name}: {e}")
                return False
    
    def enable_indicator(self, symbol: str, indicator_name: str) -> bool:
        """Enable indicator"""
        with self.lock:
            if symbol in self.symbol_groups:
                instance = self.symbol_groups[symbol].get_indicator(indicator_name)
                if instance:
                    instance.enabled = True
                    self.logger.info(f"Enabled indicator {indicator_name} for {symbol}")
                    return True
            return False
    
    def disable_indicator(self, symbol: str, indicator_name: str) -> bool:
        """Disable indicator"""
        with self.lock:
            if symbol in self.symbol_groups:
                instance = self.symbol_groups[symbol].get_indicator(indicator_name)
                if instance:
                    instance.enabled = False
                    self.logger.info(f"Disabled indicator {indicator_name} for {symbol}")
                    return True
            return False
    
    def add_update_callback(self, callback: Callable):
        """Add callback function to receive indicator updates"""
        if callback not in self.update_callbacks:
            self.update_callbacks.append(callback)
    
    def remove_update_callback(self, callback: Callable):
        """Remove callback function"""
        if callback in self.update_callbacks:
            self.update_callbacks.remove(callback)
    
    def get_engine_stats(self) -> Dict:
        """Get engine statistics"""
        with self.lock:
            total_indicators = sum(len(group.indicators) for group in self.symbol_groups.values())
            enabled_indicators = sum(
                sum(1 for i in group.indicators.values() if i.enabled)
                for group in self.symbol_groups.values()
            )
            
            runtime = datetime.now() - self.update_start_time
            updates_per_second = self.total_indicator_updates / runtime.total_seconds() if runtime.total_seconds() > 0 else 0
            
            return {
                'symbols': len(self.symbol_groups),
                'total_indicators': total_indicators,
                'enabled_indicators': enabled_indicators,
                'total_updates': self.total_indicator_updates,
                'updates_per_second': updates_per_second,
                'runtime_seconds': runtime.total_seconds(),
                'last_performance_check': self.last_performance_check.isoformat()
            }
    
    def get_symbol_info(self, symbol: str) -> Optional[Dict]:
        """Get information about indicators for a specific symbol"""
        with self.lock:
            if symbol in self.symbol_groups:
                return self.symbol_groups[symbol].get_info()
            return None
    
    def get_indicator_info(self, symbol: str, indicator_name: str) -> Optional[Dict]:
        """Get detailed information about specific indicator"""
        with self.lock:
            if symbol in self.symbol_groups:
                instance = self.symbol_groups[symbol].get_indicator(indicator_name)
                if instance:
                    return instance.get_info()
            return None
    
    def reset_indicator(self, symbol: str, indicator_name: str) -> bool:
        """Reset indicator state"""
        with self.lock:
            if symbol in self.symbol_groups:
                instance = self.symbol_groups[symbol].get_indicator(indicator_name)
                if instance:
                    instance.indicator.reset()
                    instance.update_count = 0
                    instance.error_count = 0
                    instance.last_error = None
                    self.logger.info(f"Reset indicator {indicator_name} for {symbol}")
                    return True
            return False
    
    def bulk_add_indicators(self, symbol: str, indicator_configs: List[Dict]) -> Dict[str, bool]:
        """
        Add multiple indicators at once
        
        Args:
            symbol: Currency pair symbol
            indicator_configs: List of config dicts with keys: type, name, config, enabled
            
        Returns:
            Dictionary mapping indicator names to success status
        """
        results = {}
        
        for config in indicator_configs:
            try:
                success = self.add_indicator(
                    symbol=symbol,
                    indicator_type=config['type'],
                    name=config['name'],
                    config=config.get('config', {}),
                    enabled=config.get('enabled', True)
                )
                results[config['name']] = success
            except Exception as e:
                self.logger.error(f"Error adding indicator {config.get('name', 'unknown')}: {e}")
                results[config.get('name', 'unknown')] = False
        
        return results
    
    def _initialize_indicator_with_history(self, symbol: str, instance: IndicatorInstance):
        """Initialize indicator with historical price data"""
        try:
            # Get historical prices from price manager
            required_periods = instance.indicator.get_required_periods()
            history = self.price_manager.get_price_history(symbol, required_periods * 2)
            
            if history:
                # Update indicator with historical data
                for tick in history:
                    instance.indicator.update(tick.mid_price)
                
                self.logger.debug(f"Initialized {instance.indicator.name} with {len(history)} historical points")
            
        except Exception as e:
            self.logger.warning(f"Could not initialize {instance.indicator.name} with history: {e}")
    
    def _notify_callbacks(self, symbol: str, price: float, results: Dict[str, Any]):
        """Notify all registered callbacks of indicator updates"""
        for callback in self.update_callbacks:
            try:
                callback(symbol, price, results)
            except Exception as e:
                self.logger.error(f"Error in indicator update callback: {e}")
    
    def _check_performance(self):
        """Check and log performance metrics"""
        self.last_performance_check = datetime.now()
        stats = self.get_engine_stats()
        
        self.logger.info(f"Indicator Engine Performance: "
                        f"{stats['updates_per_second']:.1f} updates/sec, "
                        f"{stats['enabled_indicators']} active indicators, "
                        f"{stats['symbols']} symbols")
        
        # Check for performance issues
        if stats['updates_per_second'] < 10 and stats['enabled_indicators'] > 20:
            self.logger.warning("Low update rate detected - consider reducing indicator count")
    
    def export_configuration(self) -> Dict:
        """Export current indicator configuration"""
        config = {
            'symbols': {},
            'created_at': datetime.now().isoformat()
        }
        
        with self.lock:
            for symbol, group in self.symbol_groups.items():
                indicators = []
                for name, instance in group.indicators.items():
                    indicators.append({
                        'name': name,
                        'type': instance.indicator.__class__.__name__,
                        'config': instance.indicator.config.to_dict(),
                        'enabled': instance.enabled
                    })
                
                config['symbols'][symbol] = {
                    'indicators': indicators,
                    'group_info': group.get_info()
                }
        
        return config
    
    def import_configuration(self, config: Dict) -> Dict[str, Dict[str, bool]]:
        """
        Import indicator configuration
        
        Returns:
            Dictionary mapping symbols to indicator add results
        """
        results = {}
        
        for symbol, symbol_config in config.get('symbols', {}).items():
            indicator_configs = symbol_config.get('indicators', [])
            results[symbol] = self.bulk_add_indicators(symbol, indicator_configs)
        
        return results


# Example usage and configuration
def create_default_indicator_set(engine: IndicatorEngine, symbol: str) -> Dict[str, bool]:
    """Create a default set of indicators for a symbol"""
    default_indicators = [
        {'type': 'SMA', 'name': 'SMA_20', 'config': {'period': 20}},
        {'type': 'SMA', 'name': 'SMA_50', 'config': {'period': 50}},
        {'type': 'EMA', 'name': 'EMA_12', 'config': {'period': 12}},
        {'type': 'EMA', 'name': 'EMA_26', 'config': {'period': 26}},
        {'type': 'RSI', 'name': 'RSI_14', 'config': {'period': 14}},
        {'type': 'MACD', 'name': 'MACD', 'config': {'fast_period': 12, 'slow_period': 26, 'signal_period': 9}},
        {'type': 'BollingerBands', 'name': 'BB_20', 'config': {'period': 20, 'std_dev': 2.0}},
        {'type': 'ATR', 'name': 'ATR_14', 'config': {'period': 14}}
    ]
    
    return engine.bulk_add_indicators(symbol, default_indicators)


if __name__ == "__main__":
    # Example usage
    from price_manager import PriceManager
    
    # Create price manager and engine
    price_manager = PriceManager()
    engine = IndicatorEngine(price_manager)
    
    # Add some indicators
    symbol = "EURUSD"
    results = create_default_indicator_set(engine, symbol)
    print(f"Added indicators: {results}")
    
    # Simulate price updates
    import random
    base_price = 1.1000
    
    for i in range(100):
        # Generate price tick
        base_price += random.uniform(-0.0010, 0.0010)
        
        # Add to price manager
        price_data = {
            'bid': base_price - 0.0002,
            'ask': base_price + 0.0002,
            'timestamp': datetime.now()
        }
        price_manager.add_price_tick(symbol, price_data)
        
        # Update indicators
        indicator_results = engine.update_indicators(symbol, base_price)
        
        if i % 20 == 0:  # Print every 20 updates
            print(f"\nPrice: {base_price:.5f}")
            for name, value in indicator_results.items():
                print(f"  {name}: {value}")
    
    # Print engine statistics
    print(f"\nEngine Stats: {engine.get_engine_stats()}")