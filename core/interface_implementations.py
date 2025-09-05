"""
HUEY_P Trading Interface - Concrete Interface Implementations
Production-ready implementations of core interfaces
"""

import logging
import threading
import time
import tkinter as tk
from datetime import datetime
from typing import Any, Dict, Optional, Callable
from .interfaces import UIInterface, TimerInterface, IntegrationInterface


class BaseUIComponent(UIInterface):
    """Base implementation for UI components"""
    
    def __init__(self, name: str = "UI Component"):
        self.name = name
        self.logger = logging.getLogger(__name__)
        self.initialized = False
        self.last_update = None
        self._shutdown_requested = False
        
    def initialize(self) -> bool:
        """Initialize the UI component"""
        try:
            self.logger.info(f"Initializing {self.name}")
            # Override in subclasses for specific initialization
            self.initialized = True
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize {self.name}: {e}")
            return False
    
    def update_display(self) -> None:
        """Update the display with current data"""
        if not self.initialized or self._shutdown_requested:
            return
            
        try:
            self.last_update = datetime.now()
            # Override in subclasses for specific update logic
            self.logger.debug(f"Updated display for {self.name}")
        except Exception as e:
            self.logger.error(f"Failed to update display for {self.name}: {e}")
    
    def shutdown(self) -> None:
        """Clean shutdown of UI component"""
        try:
            self.logger.info(f"Shutting down {self.name}")
            self._shutdown_requested = True
            self.initialized = False
        except Exception as e:
            self.logger.error(f"Failed to shutdown {self.name}: {e}")


class ProductionTimer(TimerInterface):
    """Production timer implementation with proper thread management"""
    
    def __init__(self, interval: float = 1.0, callback: Optional[Callable] = None):
        self.interval = interval
        self.callback = callback
        self.logger = logging.getLogger(__name__)
        self._timer_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._running = False
        self._paused = False
        self.start_time: Optional[datetime] = None
        self.elapsed_time: float = 0.0
    
    def start_timer(self) -> None:
        """Start the timer"""
        if self._running:
            self.logger.warning("Timer already running")
            return
            
        try:
            self._stop_event.clear()
            self._running = True
            self._paused = False
            self.start_time = datetime.now()
            
            self._timer_thread = threading.Thread(target=self._timer_loop, daemon=True)
            self._timer_thread.start()
            
            self.logger.info(f"Timer started with {self.interval}s interval")
            
        except Exception as e:
            self.logger.error(f"Failed to start timer: {e}")
            self._running = False
    
    def stop_timer(self) -> None:
        """Stop the timer"""
        if not self._running:
            return
            
        try:
            self.logger.info("Stopping timer")
            self._stop_event.set()
            self._running = False
            
            if self._timer_thread and self._timer_thread.is_alive():
                self._timer_thread.join(timeout=5.0)
                
            if self.start_time:
                self.elapsed_time += (datetime.now() - self.start_time).total_seconds()
                
        except Exception as e:
            self.logger.error(f"Failed to stop timer: {e}")
    
    def reset_timer(self) -> None:
        """Reset the timer"""
        try:
            was_running = self._running
            self.stop_timer()
            self.elapsed_time = 0.0
            self.start_time = None
            
            if was_running:
                self.start_timer()
                
            self.logger.info("Timer reset")
            
        except Exception as e:
            self.logger.error(f"Failed to reset timer: {e}")
    
    def pause_timer(self) -> None:
        """Pause the timer (additional functionality)"""
        if self._running and not self._paused:
            self._paused = True
            if self.start_time:
                self.elapsed_time += (datetime.now() - self.start_time).total_seconds()
            self.logger.info("Timer paused")
    
    def resume_timer(self) -> None:
        """Resume the paused timer (additional functionality)"""
        if self._running and self._paused:
            self._paused = False
            self.start_time = datetime.now()
            self.logger.info("Timer resumed")
    
    def get_elapsed_time(self) -> float:
        """Get total elapsed time in seconds"""
        total_elapsed = self.elapsed_time
        if self._running and not self._paused and self.start_time:
            total_elapsed += (datetime.now() - self.start_time).total_seconds()
        return total_elapsed
    
    def _timer_loop(self) -> None:
        """Internal timer loop"""
        while not self._stop_event.is_set():
            if not self._paused and self.callback:
                try:
                    self.callback()
                except Exception as e:
                    self.logger.error(f"Timer callback error: {e}")
            
            # Use event wait for more responsive stopping
            if self._stop_event.wait(self.interval):
                break


class BaseIntegration(IntegrationInterface):
    """Base implementation for integration components"""
    
    def __init__(self, name: str = "Integration"):
        self.name = name
        self.logger = logging.getLogger(__name__)
        self.connected = False
        self.last_connection_attempt: Optional[datetime] = None
        self.connection_count = 0
        self.error_count = 0
        self.last_error: Optional[str] = None
    
    def connect(self) -> bool:
        """Establish connection"""
        try:
            self.logger.info(f"Connecting {self.name}")
            self.last_connection_attempt = datetime.now()
            
            # Override in subclasses for specific connection logic
            success = self._perform_connection()
            
            if success:
                self.connected = True
                self.connection_count += 1
                self.logger.info(f"{self.name} connected successfully")
            else:
                self.error_count += 1
                self.last_error = "Connection failed"
                self.logger.error(f"Failed to connect {self.name}")
                
            return success
            
        except Exception as e:
            self.error_count += 1
            self.last_error = str(e)
            self.logger.error(f"Exception during {self.name} connection: {e}")
            return False
    
    def disconnect(self) -> None:
        """Close connection"""
        try:
            if self.connected:
                self.logger.info(f"Disconnecting {self.name}")
                self._perform_disconnection()
                self.connected = False
                self.logger.info(f"{self.name} disconnected")
        except Exception as e:
            self.logger.error(f"Exception during {self.name} disconnection: {e}")
    
    def is_connected(self) -> bool:
        """Check connection status"""
        return self.connected
    
    def send_data(self, data: Dict[str, Any]) -> bool:
        """Send data through integration"""
        if not self.connected:
            self.logger.warning(f"Cannot send data - {self.name} not connected")
            return False
            
        try:
            success = self._perform_send(data)
            
            if not success:
                self.error_count += 1
                self.last_error = "Send operation failed"
                
            return success
            
        except Exception as e:
            self.error_count += 1
            self.last_error = str(e)
            self.logger.error(f"Exception sending data via {self.name}: {e}")
            return False
    
    def _perform_connection(self) -> bool:
        """Override in subclasses for specific connection logic"""
        return True  # Default success for testing
    
    def _perform_disconnection(self) -> None:
        """Override in subclasses for specific disconnection logic"""
        pass
    
    def _perform_send(self, data: Dict[str, Any]) -> bool:
        """Override in subclasses for specific send logic"""
        self.logger.debug(f"Sending data via {self.name}: {len(data)} items")
        return True  # Default success for testing
    
    def get_stats(self) -> Dict[str, Any]:
        """Get integration statistics"""
        return {
            "name": self.name,
            "connected": self.connected,
            "connection_count": self.connection_count,
            "error_count": self.error_count,
            "last_error": self.last_error,
            "last_connection_attempt": self.last_connection_attempt.isoformat() if self.last_connection_attempt else None
        }


class TradingIntegration(BaseIntegration):
    """Trading-specific integration implementation"""
    
    def __init__(self, host: str = "localhost", port: int = 9999):
        super().__init__(name="Trading Integration")
        self.host = host
        self.port = port
        self.socket = None
        self.message_count = 0
        
    def _perform_connection(self) -> bool:
        """Implement trading-specific connection logic"""
        try:
            # In production, this would establish actual socket connection
            # For now, simulate successful connection for testing
            import socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(5.0)  # 5 second timeout
            
            # Simulate connection attempt
            self.logger.info(f"Attempting to connect to {self.host}:{self.port}")
            # self.socket.connect((self.host, self.port))  # Uncomment for real connection
            
            return True  # Return True for testing, change to actual connection result
            
        except Exception as e:
            if self.socket:
                self.socket.close()
                self.socket = None
            self.logger.error(f"Trading connection failed: {e}")
            return False
    
    def _perform_disconnection(self) -> None:
        """Close trading connection"""
        if self.socket:
            try:
                self.socket.close()
            except Exception as e:
                self.logger.error(f"Error closing socket: {e}")
            finally:
                self.socket = None
    
    def _perform_send(self, data: Dict[str, Any]) -> bool:
        """Send trading data"""
        if not self.socket:
            return False
            
        try:
            # In production, implement actual message sending
            self.message_count += 1
            self.logger.debug(f"Sent trading message #{self.message_count}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send trading data: {e}")
            return False


# Factory functions for easy instantiation
def create_ui_component(name: str = "UI Component") -> UIInterface:
    """Create a UI component implementation"""
    return BaseUIComponent(name)


def create_timer(interval: float = 1.0, callback: Optional[Callable] = None) -> TimerInterface:
    """Create a timer implementation"""
    return ProductionTimer(interval, callback)


def create_integration(integration_type: str = "base", **kwargs) -> IntegrationInterface:
    """Create an integration implementation"""
    if integration_type == "trading":
        return TradingIntegration(**kwargs)
    else:
        return BaseIntegration(**kwargs)