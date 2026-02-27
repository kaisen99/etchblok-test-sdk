"""Retry middleware — automatically retries handler failures.

Note: this middleware does NOT retry delivery itself. It annotates
events with retry metadata that the bus uses to re-dispatch on failure.
"""
from __future__ import annotations

from typing import Optional

from eventkit.core.event import Event
from eventkit.middleware.base import Middleware


# Internal retry metadata key
_RETRY_COUNT_KEY = "__retry_count"
_MAX_RETRIES_KEY = "__max_retries"


class RetryMiddleware(Middleware):
    """Annotates events with retry policy metadata.

    Args:
        max_retries: Maximum number of delivery attempts per event.
        backoff_factor: Multiplier for exponential backoff (reserved for future use).
    """

    def __init__(self, max_retries: int = 3, backoff_factor: float = 1.0) -> None:
        self._max_retries = max_retries
        self._backoff_factor = backoff_factor

    def process(self, event: Event) -> Optional[Event]:
        """Stamp retry metadata onto the event payload."""
        if _RETRY_COUNT_KEY not in event.payload:
            event.payload[_RETRY_COUNT_KEY] = 0
            event.payload[_MAX_RETRIES_KEY] = self._max_retries
        return event

    @property
    def max_retries(self) -> int:
        """The configured maximum retry count."""
        return self._max_retries

    @staticmethod
    def get_retry_count(event: Event) -> int:
        """Read the current retry count from an event.

        Args:
            event: The event to inspect.

        Returns:
            The number of retries attempted so far.
        """
        return event.payload.get(_RETRY_COUNT_KEY, 0)

    @staticmethod
    def should_retry(event: Event) -> bool:
        """Check whether the event has retries remaining.

        Args:
            event: The event to check.

        Returns:
            True if the event can be retried.
        """
        count = event.payload.get(_RETRY_COUNT_KEY, 0)
        max_r = event.payload.get(_MAX_RETRIES_KEY, 0)
        return count < max_r

    # ── Private ─────────────────────────────────────────────────────

    def _calculate_delay(self, retry_number: int) -> float:
        """Compute backoff delay in seconds. Internal helper."""
        return self._backoff_factor * (2 ** retry_number)
