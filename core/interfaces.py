"""
HUEY_P Trading Interface - Core Interfaces
Base interfaces for system components
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class UIInterface(ABC):
    """Base interface for UI components"""
    
    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the UI component"""
        pass
    
    @abstractmethod
    def update_display(self) -> None:
        """Update the display with current data"""
        pass
    
    @abstractmethod
    def shutdown(self) -> None:
        """Clean shutdown of UI component"""
        pass


class TimerInterface(ABC):
    """Interface for timer-based components"""
    
    @abstractmethod
    def start_timer(self) -> None:
        """Start the timer"""
        pass
    
    @abstractmethod
    def stop_timer(self) -> None:
        """Stop the timer"""
        pass
    
    @abstractmethod
    def reset_timer(self) -> None:
        """Reset the timer"""
        pass


class IntegrationInterface(ABC):
    """Interface for integration components"""
    
    @abstractmethod
    def connect(self) -> bool:
        """Establish connection"""
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """Close connection"""
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """Check connection status"""
        pass
    
    @abstractmethod
    def send_data(self, data: Dict[str, Any]) -> bool:
        """Send data through integration"""
        pass