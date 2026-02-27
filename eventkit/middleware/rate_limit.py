"""Rate-limiting middleware — drops events that exceed a per-topic rate.

Uses a simple sliding-window counter. Events that exceed the configured
rate are rejected (``process`` returns ``None``).
"""
from __future__ import annotations

import time
from collections import defaultdict
from typing import Dict, List, Optional

from eventkit.core.event import Event
from eventkit.middleware.base import Middleware


class RateLimitMiddleware(Middleware):
    """Reject events exceeding a per-topic rate limit.

    Args:
        max_per_second: Maximum events allowed per topic per second.
        burst: Additional burst allowance above the steady rate.
    """

    def __init__(self, max_per_second: float = 10.0, burst: int = 5) -> None:
        self._max_per_second = max_per_second
        self._burst = burst
        self._windows: Dict[str, List[float]] = defaultdict(list)
        self._rejected_count = 0

    def process(self, event: Event) -> Optional[Event]:
        """Allow or reject the event based on the rate limit."""
        now = time.monotonic()
        window = self._windows[event.topic]

        # Prune old timestamps outside the 1-second window
        self._prune_window(window, now)

        if len(window) >= self._max_per_second + self._burst:
            self._rejected_count += 1
            return None

        window.append(now)
        return event

    @property
    def rejected_count(self) -> int:
        """Number of events rejected by this middleware."""
        return self._rejected_count

    def reset(self) -> None:
        """Clear all rate limit state."""
        self._windows.clear()
        self._rejected_count = 0

    # ── Private ─────────────────────────────────────────────────────

    @staticmethod
    def _prune_window(window: List[float], now: float) -> None:
        """Remove timestamps older than 1 second from the window."""
        cutoff = now - 1.0
        while window and window[0] < cutoff:
            window.pop(0)

    def _get_current_rate(self, topic: str) -> float:
        """Calculate the current event rate for a topic. Internal diagnostic."""
        window = self._windows.get(topic, [])
        if len(window) < 2:
            return 0.0
        duration = window[-1] - window[0]
        return len(window) / duration if duration > 0 else 0.0
