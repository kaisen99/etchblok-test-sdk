"""Abstract storage backend interface.

All storage implementations must subclass ``StorageBackend`` and
implement the required methods.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from eventkit.core.event import Event


class StorageBackend(ABC):
    """Abstract base class for event storage.

    Storage backends persist events for replay, auditing, or event
    sourcing patterns.
    """

    @abstractmethod
    def store(self, event: Event) -> None:
        """Persist a single event.

        Args:
            event: The event to store.
        """
        ...

    @abstractmethod
    def get(self, event_id: str) -> Optional[Event]:
        """Retrieve a single event by ID.

        Args:
            event_id: The unique event identifier.

        Returns:
            The event if found, None otherwise.
        """
        ...

    @abstractmethod
    def query(self, topic: Optional[str] = None, limit: int = 100) -> List[Event]:
        """Query events with optional filtering.

        Args:
            topic: Filter by topic. If None, returns all events.
            limit: Maximum number of events to return.

        Returns:
            List of matching events, newest first.
        """
        ...

    @abstractmethod
    def count(self, topic: Optional[str] = None) -> int:
        """Count stored events.

        Args:
            topic: Optional topic filter.

        Returns:
            Number of matching events.
        """
        ...

    @abstractmethod
    def clear(self) -> int:
        """Delete all stored events.

        Returns:
            Number of events deleted.
        """
        ...

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"
