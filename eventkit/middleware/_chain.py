"""Internal middleware chain executor.

Manages the ordered execution of middleware. Not part of the public API —
the ``EventBus`` uses this internally.
"""
from __future__ import annotations

from typing import List, Optional, Tuple

from eventkit.core.event import Event
from eventkit.middleware.base import Middleware


class _MiddlewareChain:
    """Executes an ordered list of middleware, tracking results.

    Each middleware is called in sequence. If any middleware returns None,
    the chain halts and the event is considered rejected.
    """

    def __init__(self, middleware: Optional[List[Middleware]] = None) -> None:
        self._middleware: List[Middleware] = middleware or []
        self._last_rejection: Optional[Tuple[str, Event]] = None

    def add(self, middleware: Middleware) -> None:
        """Append a middleware to the chain."""
        self._middleware.append(middleware)

    def remove(self, middleware: Middleware) -> bool:
        """Remove a middleware from the chain."""
        if middleware in self._middleware:
            self._middleware.remove(middleware)
            return True
        return False

    def execute(self, event: Event) -> Optional[Event]:
        """Run the event through every middleware in order.

        Returns the final event, or None if any middleware rejected it.
        """
        current = event
        for mw in self._middleware:
            result = mw.process(current)
            if result is None:
                self._last_rejection = (mw.__class__.__name__, event)
                return None
            current = result
        return current

    @property
    def length(self) -> int:
        """Number of middleware in the chain."""
        return len(self._middleware)

    @property
    def last_rejection(self) -> Optional[Tuple[str, Event]]:
        """The middleware class name and event of the last rejection, if any."""
        return self._last_rejection

    def _clear(self) -> None:
        """Remove all middleware. Internal/test use."""
        self._middleware.clear()
        self._last_rejection = None
