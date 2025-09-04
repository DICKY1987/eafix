#!/usr/bin/env python3
"""
HUEY_P System-Level Error Recovery Framework

Provides a comprehensive error handling and recovery system that goes beyond
component-level error handling to offer system-wide resilience, graceful
degradation, and automatic recovery capabilities.
"""

import json
import logging
import threading
import time
import traceback
from collections import deque
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Enumeration for the severity of a detected error."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ComponentStatus(Enum):
    """Enumeration for the health status of a system component."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILING = "failing"
    FAILED = "failed"
    RECOVERING = "recovering"


class RecoveryStrategy(Enum):
    """Enumeration for predefined error recovery strategies."""
    RESTART_COMPONENT = "restart_component"
    FALLBACK_MODE = "fallback_mode"
    CIRCUIT_BREAKER = "circuit_breaker"
    GRACEFUL_DEGRADATION = "graceful_degradation"
    MANUAL_INTERVENTION = "manual_intervention"


@dataclass
class ErrorContext:
    """
    A data structure to hold contextual information about a detected error.

    Attributes:
        component_id: The ID of the component where the error occurred.
        error_type: The class name of the exception.
        error_message: The error message from the exception.
        severity: The severity level of the error.
        timestamp: The time when the error was detected.
        stack_trace: An optional stack trace.
        additional_data: A dictionary for any other relevant data.
    """
    component_id: str
    error_type: str
    error_message: str
    severity: ErrorSeverity
    timestamp: datetime
    stack_trace: Optional[str] = None
    additional_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ComponentHealth:
    """Represents the health status of a single system component."""
    component_id: str
    status: ComponentStatus
    last_heartbeat: datetime
    error_count: int = 0
    availability: float = 100.0


class CircuitBreaker:
    """
    Implements the Circuit Breaker pattern to protect components from overload.

    This prevents an application from repeatedly trying to execute an operation
    that is likely to fail, allowing it to fail fast and preventing system
    resource exhaustion.
    """

    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        """
        Initializes the CircuitBreaker.

        Args:
            failure_threshold: The number of failures required to open the circuit.
            recovery_timeout: The number of seconds to wait before moving
                              from OPEN to HALF_OPEN state.
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = "CLOSED"  # "CLOSED", "OPEN", "HALF_OPEN"
        self.lock = threading.Lock()

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Executes a function call protected by the circuit breaker.

        Args:
            func: The function to execute.
            *args: Positional arguments for the function.
            **kwargs: Keyword arguments for the function.

        Returns:
            The result of the function call.

        Raises:
            Exception: Re-raises the exception from the function call on failure,
                       or raises a RuntimeError if the circuit is open.
        """
        with self.lock:
            if self.state == "OPEN":
                if self._should_attempt_reset():
                    self.state = "HALF_OPEN"
                else:
                    raise RuntimeError("Circuit breaker is open.")

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e

    def _on_success(self):
        """Resets the circuit breaker state on a successful call."""
        with self.lock:
            self.state = "CLOSED"
            self.failure_count = 0

    def _on_failure(self):
        """Increments failure count and opens the circuit if threshold is met."""
        with self.lock:
            self.failure_count += 1
            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
                self.last_failure_time = datetime.now()

    def _should_attempt_reset(self) -> bool:
        """Determines if the breaker should move to the HALF_OPEN state."""
        if self.last_failure_time:
            return (datetime.now() - self.last_failure_time).total_seconds() >= self.recovery_timeout
        return False


class SystemHealthMonitor:
    """Monitors the health of all registered system components."""

    def __init__(self):
        """Initializes the SystemHealthMonitor."""
        self.component_health: Dict[str, ComponentHealth] = {}
        self.lock = threading.Lock()

    def register_component(self, component_id: str):
        """
        Registers a component for health monitoring.

        Args:
            component_id: The unique ID of the component to monitor.
        """
        with self.lock:
            self.component_health[component_id] = ComponentHealth(
                component_id=component_id,
                status=ComponentStatus.HEALTHY,
                last_heartbeat=datetime.now(),
            )
        logger.info(f"Component '{component_id}' registered for health monitoring.")

    def update_component_health(self, component_id: str, status: ComponentStatus, error: Optional[ErrorContext] = None):
        """
        Updates the health status of a registered component.

        Args:
            component_id: The ID of the component to update.
            status: The new health status of the component.
            error: An optional ErrorContext object if an error occurred.
        """
        with self.lock:
            if component_id in self.component_health:
                health = self.component_health[component_id]
                health.status = status
                health.last_heartbeat = datetime.now()
                if error:
                    health.error_count += 1


class SystemRecoveryManager:
    """Main orchestrator for system-level error recovery."""

    def __init__(self):
        """Initializes the SystemRecoveryManager."""
        self.health_monitor = SystemHealthMonitor()
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.is_running = False

    def start(self):
        """Starts the recovery management system."""
        self.is_running = True
        logger.info("System Recovery Manager started.")

    def stop(self):
        """Stops the recovery management system."""
        self.is_running = False
        logger.info("System Recovery Manager stopped.")

    def register_component(self, component_id: str):
        """
        Registers a component for monitoring and recovery.

        Args:
            component_id: The unique ID of the component.
        """
        self.health_monitor.register_component(component_id)
        self.circuit_breakers[component_id] = CircuitBreaker()

    def report_error(
        self,
        component_id: str,
        error_type: str,
        error_message: str,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    ):
        """
        Reports an error for processing by the recovery system.

        Args:
            component_id: The ID of the component that reported the error.
            error_type: The class name of the exception.
            error_message: The error message.
            severity: The severity of the error.
        """
        error_context = ErrorContext(
            component_id=component_id,
            error_type=error_type,
            error_message=error_message,
            severity=severity,
            timestamp=datetime.now(),
            stack_trace=traceback.format_exc(),
        )
        status = {
            ErrorSeverity.MEDIUM: ComponentStatus.DEGRADED,
            ErrorSeverity.HIGH: ComponentStatus.FAILING,
            ErrorSeverity.CRITICAL: ComponentStatus.FAILED,
        }.get(severity, ComponentStatus.HEALTHY)
        
        self.health_monitor.update_component_health(component_id, status, error_context)
        logger.error(f"Error reported for '{component_id}': {error_message}")

    @contextmanager
    def protected_operation(self, component_id: str, operation_name: str):
        """
        A context manager for operations protected by a circuit breaker.

        Args:
            component_id: The ID of the component performing the operation.
            operation_name: A descriptive name for the operation.

        Yields:
            None.

        Raises:
            Exception: Re-raises any exception that occurs during the operation.
        """
        breaker = self.circuit_breakers.get(component_id)
        if not breaker:
            logger.warning(f"No circuit breaker for '{component_id}'. Operation is not protected.")
            yield
            return

        try:
            breaker.call(lambda: None) # Probe the breaker
            yield
        except Exception as e:
            self.report_error(
                component_id=component_id,
                error_type=type(e).__name__,
                error_message=str(e),
                severity=ErrorSeverity.HIGH,
            )
            raise e


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    recovery_mgr = SystemRecoveryManager()
    recovery_mgr.start()
    recovery_mgr.register_component("signal_service")

    def failing_operation():
        """A sample operation that always fails."""
        raise ValueError("Signal processing failed due to invalid data.")

    logger.info("--- Testing protected operation with failure ---")
    for i in range(7):
        try:
            with recovery_mgr.protected_operation("signal_service", "process_signal"):
                logger.info(f"Attempt {i+1}: Operation successful (this should not happen).")
                failing_operation()
        except Exception as e:
            logger.error(f"Attempt {i+1}: Caught expected failure: {e}")
        time.sleep(1)

    recovery_mgr.stop()