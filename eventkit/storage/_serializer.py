"""Internal event serialization/deserialization.

Handles converting ``Event`` instances to and from plain dictionaries
for storage backends. Not part of the public API.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from eventkit.core.event import Event, EventMeta, Priority


# Internal format version — bumped when the serialised schema changes
_FORMAT_VERSION = 1


class _EventSerializer:
    """Bidirectional serializer for Event objects.

    Handles format versioning so older serialised events can still
    be read after schema changes.
    """

    def serialize(self, event: Event) -> Dict[str, Any]:
        """Convert an Event to a storage-friendly dictionary."""
        return {
            "_v": _FORMAT_VERSION,
            "topic": event.topic,
            "payload": event.payload,
            "priority": event.priority.name,
            "event_id": event.meta.event_id,
            "timestamp": event.meta.timestamp.isoformat(),
            "source": event.meta.source,
            "correlation_id": event.meta.correlation_id,
            "causation_id": event.meta.causation_id,
        }

    def deserialize(self, data: Dict[str, Any]) -> Event:
        """Reconstruct an Event from a serialised dictionary."""
        version = data.get("_v", 1)
        if version == 1:
            return self._deserialize_v1(data)
        raise ValueError(f"Unknown serialisation format version: {version}")

    # ── Private per-version deserializers ───────────────────────────

    def _deserialize_v1(self, data: Dict[str, Any]) -> Event:
        """Deserialize format version 1."""
        timestamp = data.get("timestamp", "")
        try:
            ts = datetime.fromisoformat(timestamp) if timestamp else datetime.utcnow()
        except ValueError:
            ts = datetime.utcnow()

        return Event(
            topic=data["topic"],
            payload=data.get("payload", {}),
            priority=Priority[data.get("priority", "NORMAL")],
            meta=EventMeta(
                event_id=data.get("event_id", ""),
                timestamp=ts,
                source=data.get("source", ""),
                correlation_id=data.get("correlation_id", ""),
                causation_id=data.get("causation_id", ""),
            ),
        )

    @staticmethod
    def _strip_internal_keys(payload: Dict[str, Any]) -> Dict[str, Any]:
        """Remove keys starting with __ from payload before storage."""
        return {k: v for k, v in payload.items() if not k.startswith("__")}
