"""
Event Bus Implementation for HUEY_P GUI
Handles all inter-component communication
"""

import threading
import time
from collections import defaultdict, deque
from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import json

@dataclass
class Event:
    """Standard event structure"""
    topic: str
    data: Dict[str, Any]
    timestamp: datetime
    source: str
    event_id: str

class EventBus:
    """Thread-safe event bus for GUI communication"""
    
    def __init__(self, max_history: int = 1000):
        self._subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self._event_history: deque = deque(maxlen=max_history)
        self._lock = threading.RLock()
        self._running = True
        self._stats = {
            'events_published': 0,
            'events_failed': 0,
            'subscribers_count': 0
        }
        
    def subscribe(self, topic: str, callback: Callable[[Event], None]) -> str:
        """
        Subscribe to events on a specific topic
        
        Args:
            topic: Event topic to subscribe to
            callback: Function to call when event is published
            
        Returns:
            subscription_id: Unique identifier for this subscription
        """
        with self._lock:
            subscription_id = f"{topic}_{len(self._subscribers[topic])}"
            self._subscribers[topic].append(callback)
            self._stats['subscribers_count'] = sum(len(subs) for subs in self._subscribers.values())
            return subscription_id
    
    def unsubscribe(self, topic: str, callback: Callable) -> bool:
        """Remove subscription"""
        with self._lock:
            if topic in self._subscribers and callback in self._subscribers[topic]:
                self._subscribers[topic].remove(callback)
                self._stats['subscribers_count'] = sum(len(subs) for subs in self._subscribers.values())
                return True
            return False
    
    def publish(self, topic: str, data: Dict[str, Any], source: str = "unknown") -> str:
        """
        Publish event to all subscribers
        
        Args:
            topic: Event topic
            data: Event payload
            source: Source component name
            
        Returns:
            event_id: Unique event identifier
        """
        event_id = f"{topic}_{time.time()}"
        event = Event(
            topic=topic,
            data=data,
            timestamp=datetime.now(),
            source=source,
            event_id=event_id
        )
        
        with self._lock:
            self._event_history.append(event)
            self._stats['events_published'] += 1
            
            # Notify subscribers
            subscribers = self._subscribers.get(topic, [])
            failed_count = 0
            
            for callback in subscribers:
                try:
                    callback(event)
                except Exception as e:
                    failed_count += 1
                    print(f"Event callback failed: {e}")
                    
            if failed_count > 0:
                self._stats['events_failed'] += failed_count
                
        return event_id
    
    def get_stats(self) -> Dict[str, Any]:
        """Get event bus statistics"""
        with self._lock:
            return {
                **self._stats,
                'active_topics': list(self._subscribers.keys()),
                'total_subscribers': self._stats['subscribers_count']
            }
    
    def get_recent_events(self, count: int = 10, topic: Optional[str] = None) -> List[Event]:
        """Get recent events, optionally filtered by topic"""
        with self._lock:
            events = list(self._event_history)
            if topic:
                events = [e for e in events if e.topic == topic]
            return events[-count:]

# Global event bus instance
event_bus = EventBus()