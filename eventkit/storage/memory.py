"""In-memory storage backend.

Fast but non-durable — events are lost when the process exits.
Suitable for testing and short-lived applications.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Optional

from eventkit.core.event import Event
from eventkit.storage.base import StorageBackend
from eventkit.storage._serializer import _EventSerializer


class InMemoryStorage(StorageBackend):
    """Store events in plain Python dictionaries.

    Args:
        max_events: Maximum events to retain. Oldest are evicted when exceeded.
    """

    def __init__(self, max_events: int = 10000) -> None:
        self._max_events = max_events
        self._events: Dict[str, Event] = {}
        self._by_topic: Dict[str, List[str]] = defaultdict(list)
        self._order: List[str] = []
        self._serializer = _EventSerializer()

    # ── StorageBackend interface ────────────────────────────────────

    def store(self, event: Event) -> None:
        """Persist an event in memory."""
        eid = event.meta.event_id
        self._events[eid] = event
        self._by_topic[event.topic].append(eid)
        self._order.append(eid)
        self._enforce_limit()

    def get(self, event_id: str) -> Optional[Event]:
        """Retrieve an event by ID."""
        return self._events.get(event_id)

    def query(self, topic: Optional[str] = None, limit: int = 100) -> List[Event]:
        """Query events, newest first."""
        if topic:
            ids = self._by_topic.get(topic, [])
        else:
            ids = self._order
        result = [self._events[eid] for eid in reversed(ids) if eid in self._events]
        return result[:limit]

    def count(self, topic: Optional[str] = None) -> int:
        """Count events, optionally filtered by topic."""
        if topic:
            return len(self._by_topic.get(topic, []))
        return len(self._events)

    def clear(self) -> int:
        """Remove all events and return the count removed."""
        n = len(self._events)
        self._events.clear()
        self._by_topic.clear()
        self._order.clear()
        return n

    # ── Extra public methods ────────────────────────────────────────

    def export_all(self) -> List[Dict]:
        """Export all events as serialised dictionaries.

        Useful for snapshotting in-memory state to disk.
        """
        return [self._serializer.serialize(e) for e in self._events.values()]

    @property
    def is_full(self) -> bool:
        """Whether the store has reached its capacity limit."""
        return len(self._events) >= self._max_events

    # ── Private ─────────────────────────────────────────────────────

    def _enforce_limit(self) -> None:
        """Evict oldest events if over capacity."""
        while len(self._events) > self._max_events and self._order:
            oldest_id = self._order.pop(0)
            event = self._events.pop(oldest_id, None)
            if event:
                topic_list = self._by_topic.get(event.topic, [])
                if oldest_id in topic_list:
                    topic_list.remove(oldest_id)

    def _snapshot(self) -> Dict:
        """Create a diagnostic snapshot. Internal only."""
        return {
            "total_events": len(self._events),
            "topics": {t: len(ids) for t, ids in self._by_topic.items()},
            "is_full": self.is_full,
        }
