"""Event model and supporting types.

``Event`` is the fundamental unit flowing through the bus. Each event
has a topic, a payload dict, metadata, and a priority level.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import IntEnum
from typing import Any, Dict, Optional


class Priority(IntEnum):
    """Delivery priority — lower numeric value means higher priority.

    Handlers receiving events are sorted by priority so that ``CRITICAL``
    handlers always run before ``LOW`` handlers.
    """

    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3


@dataclass(frozen=True)
class EventMeta:
    """Immutable metadata attached to every event.

    Attributes:
        event_id: Globally unique identifier.
        timestamp: UTC creation time.
        source: Optional origin identifier (e.g. service name).
        correlation_id: Optional ID linking related events together.
        causation_id: Optional ID of the event that caused this one.
    """

    event_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    source: str = ""
    correlation_id: str = ""
    causation_id: str = ""


@dataclass
class Event:
    """A typed event flowing through the ``EventBus``.

    Attributes:
        topic: Dot-separated event name (e.g. ``user.created``).
        payload: Arbitrary data dictionary.
        priority: Delivery priority.
        meta: Automatically generated metadata.
    """

    topic: str
    payload: Dict[str, Any] = field(default_factory=dict)
    priority: Priority = Priority.NORMAL
    meta: EventMeta = field(default_factory=EventMeta)

    # ── Public methods ──────────────────────────────────────────────

    def derive(self, new_topic: str, extra_payload: Optional[Dict[str, Any]] = None) -> "Event":
        """Create a causally-linked child event.

        The child inherits this event's correlation ID and sets its
        causation ID to this event's ID.

        Args:
            new_topic: Topic for the derived event.
            extra_payload: Additional payload merged with the parent's.

        Returns:
            A new Event linked to this one.
        """
        merged = {**self.payload, **(extra_payload or {})}
        return Event(
            topic=new_topic,
            payload=merged,
            priority=self.priority,
            meta=EventMeta(
                correlation_id=self.meta.correlation_id or self.meta.event_id,
                causation_id=self.meta.event_id,
                source=self.meta.source,
            ),
        )

    def with_priority(self, priority: Priority) -> "Event":
        """Return a copy of this event with a different priority."""
        return Event(
            topic=self.topic,
            payload=self.payload,
            priority=priority,
            meta=self.meta,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serialise to a plain dictionary."""
        return {
            "topic": self.topic,
            "payload": self.payload,
            "priority": self.priority.name,
            "event_id": self.meta.event_id,
            "timestamp": self.meta.timestamp.isoformat(),
            "source": self.meta.source,
            "correlation_id": self.meta.correlation_id,
            "causation_id": self.meta.causation_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Event":
        """Reconstruct an event from a serialised dictionary.

        Args:
            data: Dictionary previously produced by ``to_dict()``.

        Returns:
            Reconstructed Event instance.
        """
        return cls(
            topic=data["topic"],
            payload=data.get("payload", {}),
            priority=Priority[data.get("priority", "NORMAL")],
            meta=EventMeta(
                event_id=data.get("event_id", ""),
                source=data.get("source", ""),
                correlation_id=data.get("correlation_id", ""),
                causation_id=data.get("causation_id", ""),
            ),
        )

    # ── Dunder ──────────────────────────────────────────────────────

    def __repr__(self) -> str:
        return f"Event(topic={self.topic!r}, priority={self.priority.name})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Event):
            return NotImplemented
        return self.meta.event_id == other.meta.event_id

    def __hash__(self) -> int:
        return hash(self.meta.event_id)

    def __lt__(self, other: "Event") -> bool:
        """Events are comparable by priority for use in priority queues."""
        return self.priority < other.priority

    # ── Private ─────────────────────────────────────────────────────

    def _validate(self) -> bool:
        """Check that the event is well-formed. Internal use only."""
        return bool(self.topic) and "." in self.topic
