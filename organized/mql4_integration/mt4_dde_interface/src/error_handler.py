"""
Comprehensive error handling and performance optimization system
"""
import logging
import traceback
import threading
import time
import psutil
import gc
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from collections import deque, defaultdict
from dataclasses import dataclass
from contextlib import contextmanager
from functools import wraps
import json


@dataclass
class ErrorInfo:
    """Error information structure"""
    timestamp: datetime
    error_type: str
    error_message: str
    module: str
    function: str
    severity: str
    stack_trace: str
    context: Dict[str, Any]
    resolved: bool = False


@dataclass
class PerformanceMetric:
    """Performance metric structure"""
    timestamp: datetime
    metric_name: str
    value: float
    unit: str
    context: Dict[str, Any]


class ErrorSeverity:
    """Error severity levels"""
    CRITICAL = "CRITICAL"  # System cannot continue
    ERROR = "ERROR"        # Significant functionality loss
    WARNING = "WARNING"    # Minor issues, degraded performance
    INFO = "INFO"         # Informational messages


class ErrorHandler:
    """Comprehensive error handling system"""
    
    def __init__(self, max_errors: int = 1000):
        self.max_errors = max_errors
        self.errors = deque(maxlen=max_errors)
        self.error_counts = defaultdict(int)
        self.suppressed_errors = set()
        self.error_callbacks = []
        self.lock = threading.RLock()
        self.logger = logging.getLogger(__name__)
        
        # Circuit breaker state
        self.circuit_breakers = {}
        self.circuit_breaker_timeouts = {}
        
        # Auto-recovery mechanisms
        self.recovery_handlers = {}
        self.auto_recovery_enabled = True
    
    def log_error(self, error: Exception, module: str, function: str,
                  severity: str = ErrorSeverity.ERROR, context: Dict = None,
                  suppress_duplicates: bool = True) -> str:
        """Log error with context and return error ID"""
        
        error_id = f"{module}_{function}_{int(time.time())}"
        error_type = type(error).__name__
        error_message = str(error)
        stack_trace = traceback.format_exc()
        
        # Check for duplicate suppression
        error_signature = f"{error_type}_{error_message}_{module}_{function}"
        if suppress_duplicates and error_signature in self.suppressed_errors:
            self.error_counts[error_signature] += 1
            return error_id
        
        # Create error info
        error_info = ErrorInfo(
            timestamp=datetime.now(),
            error_type=error_type,
            error_message=error_message,
            module=module,
            function=function,
            severity=severity,
            stack_trace=stack_trace,
            context=context or {}
        )
        
        with self.lock:
            self.errors.append(error_info)
            self.error_counts[error_signature] += 1
            
            # Add to suppressed if frequent
            if self.error_counts[error_signature] > 5:
                self.suppressed_errors.add(error_signature)
        
        # Log to standard logger
        log_level = getattr(logging, severity, logging.ERROR)
        self.logger.log(log_level, f"{module}.{function}: {error_message}")
        
        # Trigger callbacks
        self._notify_error_callbacks(error_info)
        
        # Check circuit breaker
        self._check_circuit_breaker(module, function, severity)
        
        # Auto-recovery if enabled
        if self.auto_recovery_enabled:
            self._attempt_recovery(error_info)
        
        return error_id
    
    def add_error_callback(self, callback: Callable):
        """Add callback for error notifications"""
        self.error_callbacks.append(callback)
    
    def set_circuit_breaker(self, component: str, threshold: int = 10, 
                           timeout: int = 300):
        """Set up circuit breaker for component"""
        self.circuit_breakers[component] = {
            'threshold': threshold,
            'count': 0,
            'timeout': timeout,
            'last_failure': None,
            'state': 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
        }
    
    def is_circuit_open(self, component: str) -> bool:
        """Check if circuit breaker is open"""
        if component not in self.circuit_breakers:
            return False
        
        breaker = self.circuit_breakers[component]
        
        if breaker['state'] == 'OPEN':
            # Check if timeout expired
            if breaker['last_failure']:
                time_since_failure = (datetime.now() - breaker['last_failure']).total_seconds()
                if time_since_failure > breaker['timeout']:
                    breaker['state'] = 'HALF_OPEN'
                    return False
            return True
        
        return False
    
    def register_recovery_handler(self, error_type: str, handler: Callable):
        """Register auto-recovery handler for specific error type"""
        self.recovery_handlers[error_type] = handler
    
    def get_error_statistics(self) -> Dict:
        """Get error statistics"""
        with self.lock:
            total_errors = len(self.errors)
            severity_counts = defaultdict(int)
            module_counts = defaultdict(int)
            recent_errors = 0
            
            one_hour_ago = datetime.now() - timedelta(hours=1)
            
            for error in self.errors:
                severity_counts[error.severity] += 1
                module_counts[error.module] += 1
                if error.timestamp > one_hour_ago:
                    recent_errors += 1
        
        return {
            'total_errors': total_errors,
            'recent_errors': recent_errors,
            'severity_breakdown': dict(severity_counts),
            'module_breakdown': dict(module_counts),
            'suppressed_signatures': len(self.suppressed_errors),
            'circuit_breakers': {k: v['state'] for k, v in self.circuit_breakers.items()}
        }
    
    def get_recent_errors(self, limit: int = 50) -> List[ErrorInfo]:
        """Get recent errors"""
        with self.lock:
            return list(self.errors)[-limit:]
    
    def clear_suppressed_errors(self):
        """Clear suppressed error list"""
        with self.lock:
            self.suppressed_errors.clear()
            self.error_counts.clear()
    
    def _notify_error_callbacks(self, error_info: ErrorInfo):
        """Notify error callbacks"""
        for callback in self.error_callbacks:
            try:
                callback(error_info)
            except Exception as e:
                self.logger.error(f"Error in error callback: {e}")
    
    def _check_circuit_breaker(self, module: str, function: str, severity: str):
        """Check and update circuit breaker status"""
        component = f"{module}.{function}"
        
        if component in self.circuit_breakers:
            breaker = self.circuit_breakers[component]
            
            if severity in [ErrorSeverity.CRITICAL, ErrorSeverity.ERROR]:
                breaker['count'] += 1
                breaker['last_failure'] = datetime.now()
                
                if breaker['count'] >= breaker['threshold']:
                    breaker['state'] = 'OPEN'
                    self.logger.critical(f"Circuit breaker OPEN for {component}")
    
    def _attempt_recovery(self, error_info: ErrorInfo):
        """Attempt automatic error recovery"""
        error_type = error_info.error_type
        
        if error_type in self.recovery_handlers:
            try:
                recovery_handler = self.recovery_handlers[error_type]
                recovery_handler(error_info)
                error_info.resolved = True
                self.logger.info(f"Auto-recovery successful for {error_type}")
            except Exception as e:
                self.logger.error(f"Auto-recovery failed for {error_type}: {e}")


class PerformanceMonitor:
    """System performance monitoring"""
    
    def __init__(self, max_metrics: int = 10000):
        self.max_metrics = max_metrics
        self.metrics = deque(maxlen=max_metrics)
        self.metric_thresholds = {}
        self.performance_callbacks = []
        self.lock = threading.RLock()
        self.logger = logging.getLogger(__name__)
        
        # System monitoring
        self.system_metrics = {
            'cpu_percent': 0.0,
            'memory_percent': 0.0,
            'memory_available': 0.0,
            'disk_usage': 0.0
        }
        
        # Performance tracking
        self.function_timings = defaultdict(list)
        self.function_call_counts = defaultdict(int)
        
        # Start system monitoring
        self._start_system_monitoring()
    
    def record_metric(self, name: str, value: float, unit: str = "", 
                     context: Dict = None):
        """Record performance metric"""
        metric = PerformanceMetric(
            timestamp=datetime.now(),
            metric_name=name,
            value=value,
            unit=unit,
            context=context or {}
        )
        
        with self.lock:
            self.metrics.append(metric)
        
        # Check thresholds
        self._check_threshold(name, value)
        
        # Notify callbacks
        self._notify_performance_callbacks(metric)
    
    def set_threshold(self, metric_name: str, max_value: float, 
                     callback: Callable = None):
        """Set performance threshold with optional callback"""
        self.metric_thresholds[metric_name] = {
            'max_value': max_value,
            'callback': callback
        }
    
    def add_performance_callback(self, callback: Callable):
        """Add performance monitoring callback"""
        self.performance_callbacks.append(callback)
    
    def track_function_performance(self, func: Callable) -> Callable:
        """Decorator for tracking function performance"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                success = True
            except Exception as e:
                success = False
                raise
            finally:
                end_time = time.time()
                duration = (end_time - start_time) * 1000  # Convert to ms
                
                function_name = f"{func.__module__}.{func.__name__}"
                
                with self.lock:
                    self.function_timings[function_name].append(duration)
                    if len(self.function_timings[function_name]) > 1000:
                        self.function_timings[function_name].pop(0)
                    
                    self.function_call_counts[function_name] += 1
                
                # Record metric
                self.record_metric(
                    f"function_time_{function_name}", 
                    duration, 
                    "ms",
                    {'success': success, 'args_count': len(args)}
                )
            
            return result
        return wrapper
    
    def get_system_metrics(self) -> Dict:
        """Get current system metrics"""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            self.system_metrics.update({
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_available': memory.available / (1024**3),  # GB
                'disk_usage': disk.percent
            })
        except Exception as e:
            self.logger.error(f"Error getting system metrics: {e}")
        
        return self.system_metrics.copy()
    
    def get_function_statistics(self) -> Dict:
        """Get function performance statistics"""
        with self.lock:
            stats = {}
            
            for func_name, timings in self.function_timings.items():
                if timings:
                    stats[func_name] = {
                        'call_count': self.function_call_counts[func_name],
                        'avg_time_ms': sum(timings) / len(timings),
                        'min_time_ms': min(timings),
                        'max_time_ms': max(timings),
                        'total_time_ms': sum(timings)
                    }
        
        return stats
    
    def get_performance_summary(self) -> Dict:
        """Get comprehensive performance summary"""
        with self.lock:
            recent_metrics = [m for m in self.metrics 
                            if m.timestamp > datetime.now() - timedelta(minutes=5)]
        
        return {
            'system_metrics': self.get_system_metrics(),
            'function_stats': self.get_function_statistics(),
            'recent_metric_count': len(recent_metrics),
            'total_metric_count': len(self.metrics),
            'thresholds_exceeded': self._get_threshold_violations()
        }
    
    def _start_system_monitoring(self):
        """Start background system monitoring"""
        def monitor_loop():
            while True:
                try:
                    metrics = self.get_system_metrics()
                    for name, value in metrics.items():
                        self.record_metric(f"system_{name}", value)
                    
                    time.sleep(30)  # Update every 30 seconds
                except Exception as e:
                    self.logger.error(f"Error in system monitoring: {e}")
                    time.sleep(60)  # Wait longer on error
        
        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()
    
    def _check_threshold(self, metric_name: str, value: float):
        """Check if metric exceeds threshold"""
        if metric_name in self.metric_thresholds:
            threshold = self.metric_thresholds[metric_name]
            if value > threshold['max_value']:
                self.logger.warning(f"Threshold exceeded for {metric_name}: {value} > {threshold['max_value']}")
                
                if threshold['callback']:
                    try:
                        threshold['callback'](metric_name, value, threshold['max_value'])
                    except Exception as e:
                        self.logger.error(f"Error in threshold callback: {e}")
    
    def _notify_performance_callbacks(self, metric: PerformanceMetric):
        """Notify performance callbacks"""
        for callback in self.performance_callbacks:
            try:
                callback(metric)
            except Exception as e:
                self.logger.error(f"Error in performance callback: {e}")
    
    def _get_threshold_violations(self) -> List[Dict]:
        """Get recent threshold violations"""
        violations = []
        one_hour_ago = datetime.now() - timedelta(hours=1)
        
        for metric in self.metrics:
            if metric.timestamp > one_hour_ago:
                if metric.metric_name in self.metric_thresholds:
                    threshold = self.metric_thresholds[metric.metric_name]['max_value']
                    if metric.value > threshold:
                        violations.append({
                            'metric_name': metric.metric_name,
                            'value': metric.value,
                            'threshold': threshold,
                            'timestamp': metric.timestamp.isoformat()
                        })
        
        return violations


class MemoryOptimizer:
    """Memory usage optimization"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.cleanup_callbacks = []
        self.memory_threshold = 80.0  # Percent
        
    def add_cleanup_callback(self, callback: Callable):
        """Add memory cleanup callback"""
        self.cleanup_callbacks.append(callback)
    
    def check_memory_usage(self) -> Dict:
        """Check current memory usage"""
        try:
            memory = psutil.virtual_memory()
            process = psutil.Process()
            process_memory = process.memory_info()
            
            return {
                'system_total_gb': memory.total / (1024**3),
                'system_available_gb': memory.available / (1024**3),
                'system_percent': memory.percent,
                'process_rss_mb': process_memory.rss / (1024**2),
                'process_vms_mb': process_memory.vms / (1024**2),
                'needs_cleanup': memory.percent > self.memory_threshold
            }
        except Exception as e:
            self.logger.error(f"Error checking memory usage: {e}")
            return {'needs_cleanup': False}
    
    def perform_cleanup(self):
        """Perform memory cleanup"""
        try:
            # Run registered cleanup callbacks
            for callback in self.cleanup_callbacks:
                try:
                    callback()
                except Exception as e:
                    self.logger.error(f"Error in cleanup callback: {e}")
            
            # Force garbage collection
            collected = gc.collect()
            self.logger.info(f"Garbage collection freed {collected} objects")
            
            return True
        except Exception as e:
            self.logger.error(f"Error performing cleanup: {e}")
            return False
    
    def auto_cleanup_if_needed(self):
        """Automatically cleanup if memory usage is high"""
        memory_info = self.check_memory_usage()
        
        if memory_info.get('needs_cleanup', False):
            self.logger.warning(f"High memory usage detected: {memory_info.get('system_percent', 0):.1f}%")
            self.perform_cleanup()


@contextmanager
def error_context(error_handler: ErrorHandler, module: str, function: str,
                  severity: str = ErrorSeverity.ERROR, context: Dict = None):
    """Context manager for error handling"""
    try:
        yield
    except Exception as e:
        error_handler.log_error(e, module, function, severity, context)
        raise


def with_error_handling(error_handler: ErrorHandler, module: str = None, 
                       severity: str = ErrorSeverity.ERROR):
    """Decorator for automatic error handling"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            func_module = module or func.__module__
            func_name = func.__name__
            
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_handler.log_error(e, func_module, func_name, severity)
                raise
        return wrapper
    return decorator


# Global instances
global_error_handler = ErrorHandler()
global_performance_monitor = PerformanceMonitor()
global_memory_optimizer = MemoryOptimizer()


# Convenience functions
def log_error(error: Exception, module: str, function: str, 
              severity: str = ErrorSeverity.ERROR, context: Dict = None):
    """Log error using global error handler"""
    return global_error_handler.log_error(error, module, function, severity, context)


def record_metric(name: str, value: float, unit: str = "", context: Dict = None):
    """Record metric using global performance monitor"""
    global_performance_monitor.record_metric(name, value, unit, context)


def track_performance(func: Callable) -> Callable:
    """Decorator for performance tracking"""
    return global_performance_monitor.track_function_performance(func)


def with_error_handling_global(module: str = None, severity: str = ErrorSeverity.ERROR):
    """Decorator using global error handler"""
    return with_error_handling(global_error_handler, module, severity)


def cleanup_memory():
    """Perform memory cleanup"""
    global_memory_optimizer.perform_cleanup()


# Example usage
if __name__ == "__main__":
    # Example error handling
    @with_error_handling_global("test_module")
    @track_performance
    def test_function():
        time.sleep(0.1)  # Simulate work
        raise ValueError("Test error")
    
    try:
        test_function()
    except ValueError:
        pass
    
    # Check statistics
    print("Error Statistics:")
    print(json.dumps(global_error_handler.get_error_statistics(), indent=2))
    
    print("\nPerformance Summary:")
    print(json.dumps(global_performance_monitor.get_performance_summary(), indent=2, default=str))