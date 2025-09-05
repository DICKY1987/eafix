import os
import sys

# Ensure package path for huey_p_gui
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'huey_p_gui')))

from src.core.event_bus import EventBus


def test_publish_and_subscribe():
    bus = EventBus()
    received = []

    def handler(event):
        received.append(event.data["value"])

    bus.subscribe("test_topic", handler)
    bus.publish("test_topic", {"value": 42}, source="unit")

    assert received == [42]
    stats = bus.get_stats()
    assert stats["events_published"] == 1
    assert stats["subscribers_count"] == 1
    assert "test_topic" in stats["active_topics"]


def test_unsubscribe_stops_events():
    bus = EventBus()
    received = []

    def handler(event):
        received.append(event.data["value"])

    bus.subscribe("topic", handler)
    bus.unsubscribe("topic", handler)
    bus.publish("topic", {"value": 1})

    assert received == []


def test_event_history_filtering():
    bus = EventBus()
    bus.publish("a", {"v": 1})
    bus.publish("b", {"v": 2})
    bus.publish("a", {"v": 3})

    recent = bus.get_recent_events(topic="a")
    assert len(recent) == 2
    assert all(event.topic == "a" for event in recent)
