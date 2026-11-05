"""Logging middleware — records every event that passes through the bus."""
from __future__ import annotations

import logging
from typing import Optional

from eventkit.core.event import Event
from eventkit.middleware.base import Middleware
from eventkit.utils._helpers import _truncate

logger = logging.getLogger("eventkit.middleware.logging")


class LoggingMiddleware(Middleware):
    """Logs event topic and metadata at configurable verbosity.

    Args:
        level: Python logging level (default ``logging.DEBUG``).
        include_payload: Whether to log the full payload dict.
    """

    def __init__(self, level: int = logging.DEBUG, include_payload: bool = False) -> None:
        self._level = level
        self._include_payload = include_payload
        self._event_count = 0

    def process(self, event: Event) -> Optional[Event]:
        """Log the event and pass it through unchanged."""
        self._event_count += 1
        msg = f"[{self._event_count}] {event.topic} id={event.meta.event_id}"
        if self._include_payload:
            msg += f" payload={_truncate(str(event.payload))}"
        logger.log(self._level, msg)
        return event

    @property
    def events_logged(self) -> int:
        """Total number of events seen by this middleware."""
        return self._event_count

    def _reset_count(self) -> None:
        """Reset the event counter. Internal/test use."""
        self._event_count = 0
