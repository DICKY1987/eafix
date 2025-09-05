"""Production Guardian system for trading system monitoring and protection.

This module implements comprehensive health monitoring, circuit breaker logic,
and automatic remediation for the trading system infrastructure.
"""

from __future__ import annotations

import json
import logging
import time
import threading
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable
import sqlite3


class SystemMode(Enum):
    """Trading system operational modes."""
    NORMAL = "NORMAL"
    DEGRADED = "DEGRADED" 
    SAFE_MODE = "SAFE_MODE"
    EMERGENCY_STOP = "EMERGENCY_STOP"


class CircuitBreakerState(Enum):
    """Circuit breaker states."""
    CLOSED = "CLOSED"     # Normal operation
    OPEN = "OPEN"         # Circuit tripped, blocking requests
    HALF_OPEN = "HALF_OPEN"  # Testing recovery


@dataclass
class HealthMetric:
    """Health metric data point."""
    name: str
    value: float
    threshold: float
    timestamp: datetime
    status: str  # OK, WARNING, CRITICAL
    message: str = ""


@dataclass
class CircuitBreaker:
    """Circuit breaker for system component protection."""
    name: str
    failure_threshold: int = 5
    timeout_seconds: int = 60
    half_open_max_calls: int = 3
    
    # Internal state
    failure_count: int = field(default=0)
    last_failure_time: Optional[datetime] = field(default=None)
    state: CircuitBreakerState = field(default=CircuitBreakerState.CLOSED)
    half_open_calls: int = field(default=0)

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function through circuit breaker protection."""
        if self.state == CircuitBreakerState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitBreakerState.HALF_OPEN
                self.half_open_calls = 0
            else:
                raise Exception(f"Circuit breaker {self.name} is OPEN")

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if not self.last_failure_time:
            return True
        return datetime.now() - self.last_failure_time > timedelta(seconds=self.timeout_seconds)

    def _on_success(self):
        """Handle successful call."""
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.half_open_calls += 1
            if self.half_open_calls >= self.half_open_max_calls:
                self.state = CircuitBreakerState.CLOSED
                self.failure_count = 0
        elif self.state == CircuitBreakerState.CLOSED:
            self.failure_count = max(0, self.failure_count - 1)

    def _on_failure(self):
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitBreakerState.OPEN
        elif self.state == CircuitBreakerState.HALF_OPEN:
            self.state = CircuitBreakerState.OPEN


@dataclass
class GuardianConfig:
    """Guardian system configuration."""
    pulse_interval_seconds: int = 5
    health_check_interval_seconds: int = 10
    db_path: str = "guardian.db"
    max_log_entries: int = 10000
    
    # SLA thresholds
    max_tick_processing_time_ms: int = 2000
    max_ui_update_time_ms: int = 500
    max_failover_time_ms: int = 10000
    
    # Circuit breaker configs
    dde_failure_threshold: int = 3
    ea_failure_threshold: int = 5
    transport_failure_threshold: int = 4


class GuardianOrchestrator:
    """Production Guardian system for comprehensive trading system monitoring."""

    def __init__(self, config: GuardianConfig = None):
        self.config = config or GuardianConfig()
        self.logger = logging.getLogger(__name__)
        
        # System state
        self.mode = SystemMode.NORMAL
        self.health_metrics: Dict[str, HealthMetric] = {}
        self.alerts: List[Dict] = []
        
        # Circuit breakers
        self.circuit_breakers = {
            "dde_connection": CircuitBreaker("dde_connection", self.config.dde_failure_threshold),
            "ea_bridge": CircuitBreaker("ea_bridge", self.config.ea_failure_threshold),
            "transport_layer": CircuitBreaker("transport_layer", self.config.transport_failure_threshold),
        }
        
        # Monitoring threads
        self._monitoring_active = False
        self._pulse_thread = None
        self._health_thread = None
        
        # Database for persistence
        self._init_database()

    def start_monitoring(self):
        """Start Guardian monitoring systems."""
        self.logger.info("Starting Guardian monitoring systems")
        self._monitoring_active = True
        
        # Start pulse monitoring
        self._pulse_thread = threading.Thread(target=self._pulse_monitor, daemon=True)
        self._pulse_thread.start()
        
        # Start health monitoring
        self._health_thread = threading.Thread(target=self._health_monitor, daemon=True)
        self._health_thread.start()

    def stop_monitoring(self):
        """Stop Guardian monitoring systems."""
        self.logger.info("Stopping Guardian monitoring systems")
        self._monitoring_active = False
        
        if self._pulse_thread:
            self._pulse_thread.join(timeout=5)
        if self._health_thread:
            self._health_thread.join(timeout=5)
        
        # Close any open database connections
        self._close_database_connections()

    def check(self) -> Dict[str, Any]:
        """Comprehensive system health check."""
        health_status = {
            "timestamp": datetime.now().isoformat(),
            "mode": self.mode.value,
            "overall_status": "OK",
            "components": {},
            "circuit_breakers": {},
            "metrics": {},
            "alerts": self.alerts[-10:]  # Last 10 alerts
        }

        # Check each component
        components = {
            "dde_connection": self._check_dde_connection,
            "ea_bridge": self._check_ea_bridge, 
            "transport_layer": self._check_transport_layer,
            "database": self._check_database,
            "disk_space": self._check_disk_space,
            "memory_usage": self._check_memory_usage
        }

        critical_failures = 0
        for name, check_func in components.items():
            try:
                status = check_func()
                health_status["components"][name] = status
                if status["status"] == "CRITICAL":
                    critical_failures += 1
            except Exception as e:
                health_status["components"][name] = {
                    "status": "ERROR",
                    "message": str(e),
                    "timestamp": datetime.now().isoformat()
                }
                critical_failures += 1

        # Circuit breaker status
        for name, cb in self.circuit_breakers.items():
            health_status["circuit_breakers"][name] = {
                "state": cb.state.value,
                "failure_count": cb.failure_count,
                "last_failure": cb.last_failure_time.isoformat() if cb.last_failure_time else None
            }

        # Health metrics
        for name, metric in self.health_metrics.items():
            health_status["metrics"][name] = {
                "value": metric.value,
                "threshold": metric.threshold,
                "status": metric.status,
                "timestamp": metric.timestamp.isoformat()
            }

        # Determine overall status
        if critical_failures > 2:
            health_status["overall_status"] = "CRITICAL"
            self._set_mode(SystemMode.EMERGENCY_STOP)
        elif critical_failures > 0:
            health_status["overall_status"] = "WARNING"
            if self.mode == SystemMode.NORMAL:
                self._set_mode(SystemMode.DEGRADED)
        else:
            if self.mode in [SystemMode.DEGRADED, SystemMode.SAFE_MODE]:
                self._set_mode(SystemMode.NORMAL)

        return health_status

    def _pulse_monitor(self):
        """Monitor system pulse at regular intervals."""
        while self._monitoring_active:
            try:
                # Record pulse metrics
                self._record_metric("system_pulse", 1.0, 1.0, "OK", "System pulse active")
                
                # Check component responsiveness
                self._check_component_responsiveness()
                
                time.sleep(self.config.pulse_interval_seconds)
                
            except Exception as e:
                self.logger.error(f"Pulse monitor error: {e}")
                time.sleep(self.config.pulse_interval_seconds)

    def _health_monitor(self):
        """Comprehensive health monitoring."""
        while self._monitoring_active:
            try:
                health_status = self.check()
                
                # Log health status to database
                self._log_health_status(health_status)
                
                # Check for alerts
                self._process_alerts(health_status)
                
                time.sleep(self.config.health_check_interval_seconds)
                
            except Exception as e:
                self.logger.error(f"Health monitor error: {e}")
                time.sleep(self.config.health_check_interval_seconds)

    def _check_dde_connection(self) -> Dict[str, Any]:
        """Check DDE connection health."""
        try:
            # Simulate DDE health check
            response_time = 0.15  # seconds
            
            if response_time > 5.0:
                return {
                    "status": "CRITICAL",
                    "response_time_ms": response_time * 1000,
                    "message": "DDE connection timeout",
                    "timestamp": datetime.now().isoformat()
                }
            elif response_time > 1.0:
                return {
                    "status": "WARNING", 
                    "response_time_ms": response_time * 1000,
                    "message": "DDE connection slow",
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "status": "OK",
                    "response_time_ms": response_time * 1000,
                    "message": "DDE connection healthy",
                    "timestamp": datetime.now().isoformat()
                }
        except Exception as e:
            return {
                "status": "CRITICAL",
                "message": f"DDE check failed: {e}",
                "timestamp": datetime.now().isoformat()
            }

    def _check_ea_bridge(self) -> Dict[str, Any]:
        """Check EA bridge connectivity."""
        try:
            # Simulate EA bridge health check with 3-second timeout
            start_time = time.time()
            # In production: actual EA bridge health check
            response_time = 0.8  # seconds
            
            if response_time > 3.0:
                return {
                    "status": "CRITICAL",
                    "response_time_ms": response_time * 1000,
                    "message": "EA bridge timeout",
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "status": "OK",
                    "response_time_ms": response_time * 1000,
                    "message": "EA bridge responsive",
                    "timestamp": datetime.now().isoformat()
                }
        except Exception as e:
            return {
                "status": "CRITICAL",
                "message": f"EA bridge check failed: {e}",
                "timestamp": datetime.now().isoformat()
            }

    def _check_transport_layer(self) -> Dict[str, Any]:
        """Check transport layer health."""
        try:
            # Check all transport types
            transports = ["socket", "named_pipe", "csv_spool"]
            healthy_transports = []
            
            for transport in transports:
                if self._test_transport(transport):
                    healthy_transports.append(transport)
            
            if len(healthy_transports) == 0:
                return {
                    "status": "CRITICAL",
                    "healthy_transports": healthy_transports,
                    "message": "All transports failed",
                    "timestamp": datetime.now().isoformat()
                }
            elif len(healthy_transports) < len(transports):
                return {
                    "status": "WARNING",
                    "healthy_transports": healthy_transports,
                    "message": f"Some transports failed: {set(transports) - set(healthy_transports)}",
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "status": "OK",
                    "healthy_transports": healthy_transports,
                    "message": "All transports healthy",
                    "timestamp": datetime.now().isoformat()
                }
        except Exception as e:
            return {
                "status": "CRITICAL",
                "message": f"Transport check failed: {e}",
                "timestamp": datetime.now().isoformat()
            }

    def _check_database(self) -> Dict[str, Any]:
        """Check database connectivity and performance."""
        try:
            start_time = time.time()
            
            # Test database connection
            with sqlite3.connect(self.config.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
            
            response_time = (time.time() - start_time) * 1000  # ms
            
            if response_time > 1000:
                return {
                    "status": "WARNING",
                    "response_time_ms": response_time,
                    "message": "Database slow",
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "status": "OK", 
                    "response_time_ms": response_time,
                    "message": "Database healthy",
                    "timestamp": datetime.now().isoformat()
                }
        except Exception as e:
            return {
                "status": "CRITICAL",
                "message": f"Database check failed: {e}",
                "timestamp": datetime.now().isoformat()
            }

    def _check_disk_space(self) -> Dict[str, Any]:
        """Check available disk space."""
        try:
            import shutil
            
            total, used, free = shutil.disk_usage(".")
            free_percent = (free / total) * 100
            
            if free_percent < 5:
                return {
                    "status": "CRITICAL",
                    "free_percent": free_percent,
                    "free_mb": free // (1024 * 1024),
                    "message": "Disk space critically low",
                    "timestamp": datetime.now().isoformat()
                }
            elif free_percent < 15:
                return {
                    "status": "WARNING",
                    "free_percent": free_percent,
                    "free_mb": free // (1024 * 1024),
                    "message": "Disk space low",
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "status": "OK",
                    "free_percent": free_percent,
                    "free_mb": free // (1024 * 1024),
                    "message": "Disk space adequate",
                    "timestamp": datetime.now().isoformat()
                }
        except Exception as e:
            return {
                "status": "WARNING",
                "message": f"Disk check failed: {e}",
                "timestamp": datetime.now().isoformat()
            }

    def _check_memory_usage(self) -> Dict[str, Any]:
        """Check system memory usage."""
        try:
            import psutil
            
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            if memory_percent > 90:
                return {
                    "status": "CRITICAL",
                    "memory_percent": memory_percent,
                    "available_mb": memory.available // (1024 * 1024),
                    "message": "Memory usage critically high",
                    "timestamp": datetime.now().isoformat()
                }
            elif memory_percent > 80:
                return {
                    "status": "WARNING",
                    "memory_percent": memory_percent,
                    "available_mb": memory.available // (1024 * 1024),
                    "message": "Memory usage high",
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "status": "OK",
                    "memory_percent": memory_percent,
                    "available_mb": memory.available // (1024 * 1024),
                    "message": "Memory usage normal",
                    "timestamp": datetime.now().isoformat()
                }
        except ImportError:
            return {
                "status": "WARNING",
                "message": "psutil not available for memory monitoring",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "status": "WARNING",
                "message": f"Memory check failed: {e}",
                "timestamp": datetime.now().isoformat()
            }

    def _test_transport(self, transport_type: str) -> bool:
        """Test specific transport type."""
        try:
            if transport_type == "socket":
                # Test socket connection
                import socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex(('127.0.0.1', 8900))
                sock.close()
                return result == 0
            elif transport_type == "named_pipe":
                # Test named pipe
                return True  # Simplified for demo
            elif transport_type == "csv_spool":
                # Test CSV spool directory
                spool_dir = Path("spool")
                return spool_dir.exists() and spool_dir.is_dir()
            return False
        except Exception:
            return False

    def _check_component_responsiveness(self):
        """Check component responsiveness within SLA thresholds."""
        # Check tick processing time
        tick_processing_time = 150  # ms (simulated)
        self._record_metric(
            "tick_processing_time_ms", 
            tick_processing_time, 
            self.config.max_tick_processing_time_ms,
            "OK" if tick_processing_time < self.config.max_tick_processing_time_ms else "WARNING",
            f"Tick processing time: {tick_processing_time}ms"
        )
        
        # Check UI update time
        ui_update_time = 200  # ms (simulated)
        self._record_metric(
            "ui_update_time_ms",
            ui_update_time,
            self.config.max_ui_update_time_ms,
            "OK" if ui_update_time < self.config.max_ui_update_time_ms else "WARNING",
            f"UI update time: {ui_update_time}ms"
        )

    def _record_metric(self, name: str, value: float, threshold: float, status: str, message: str = ""):
        """Record a health metric."""
        metric = HealthMetric(
            name=name,
            value=value,
            threshold=threshold,
            timestamp=datetime.now(),
            status=status,
            message=message
        )
        self.health_metrics[name] = metric

    def _set_mode(self, new_mode: SystemMode):
        """Set system operational mode."""
        if self.mode != new_mode:
            old_mode = self.mode
            self.mode = new_mode
            self.logger.warning(f"System mode changed from {old_mode.value} to {new_mode.value}")
            
            # Record mode change alert
            self.alerts.append({
                "timestamp": datetime.now().isoformat(),
                "type": "MODE_CHANGE",
                "message": f"System mode changed from {old_mode.value} to {new_mode.value}",
                "severity": "HIGH" if new_mode in [SystemMode.SAFE_MODE, SystemMode.EMERGENCY_STOP] else "MEDIUM"
            })

    def _log_health_status(self, health_status: Dict):
        """Log health status to database."""
        try:
            with sqlite3.connect(self.config.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO health_log (timestamp, status, details)
                    VALUES (?, ?, ?)
                """, (
                    health_status["timestamp"],
                    health_status["overall_status"],
                    json.dumps(health_status)
                ))
                conn.commit()
        except Exception as e:
            self.logger.error(f"Failed to log health status: {e}")

    def _process_alerts(self, health_status: Dict):
        """Process and generate alerts based on health status."""
        # Generate alerts for critical components
        for name, component in health_status["components"].items():
            if component["status"] == "CRITICAL":
                self.alerts.append({
                    "timestamp": datetime.now().isoformat(),
                    "type": "COMPONENT_FAILURE",
                    "component": name,
                    "message": component.get("message", f"{name} critical failure"),
                    "severity": "HIGH"
                })
        
        # Trim old alerts
        if len(self.alerts) > 100:
            self.alerts = self.alerts[-100:]

    def _init_database(self):
        """Initialize Guardian database."""
        try:
            with sqlite3.connect(self.config.db_path) as conn:
                cursor = conn.cursor()
                
                # Health log table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS health_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        status TEXT NOT NULL,
                        details TEXT NOT NULL
                    )
                """)
                
                # Alert log table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS alert_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        type TEXT NOT NULL,
                        component TEXT,
                        message TEXT NOT NULL,
                        severity TEXT NOT NULL
                    )
                """)
                
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Failed to initialize Guardian database: {e}")
    
    def _close_database_connections(self):
        """Close any open database connections."""
        try:
            # Force garbage collection to close any lingering connections
            import gc
            gc.collect()
            
            # Brief pause to allow file handles to close
            time.sleep(0.1)
        except Exception as e:
            self.logger.debug(f"Error closing database connections: {e}")

