"""Abstract base class for middleware.

All middleware must subclass ``Middleware`` and implement ``process()``.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from eventkit.core.event import Event


class Middleware(ABC):
    """Base class for event middleware.

    Middleware intercepts events as they flow through the bus. Each
    middleware can inspect, modify, or reject an event.

    Subclasses must implement :meth:`process`. Returning ``None``
    from ``process`` rejects the event and halts the pipeline.
    """

    @abstractmethod
    def process(self, event: Event) -> Optional[Event]:
        """Process an event.

        Args:
            event: The event to process.

        Returns:
            The (possibly modified) event, or None to reject it.
        """
        ...

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"
