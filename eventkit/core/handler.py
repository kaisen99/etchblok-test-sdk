"""Handler definitions and the ``@handler`` decorator.

A handler is any callable that accepts an ``Event``. This module
provides both a Protocol for type checking and a decorator for
convenient registration.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional, Protocol, Set, runtime_checkable

from eventkit.core.event import Event, Priority


# ── Public protocol ─────────────────────────────────────────────────

@runtime_checkable
class HandlerProtocol(Protocol):
    """Structural type for anything that can handle events."""

    def __call__(self, event: Event) -> None: ...


# ── Handler wrapper ─────────────────────────────────────────────────

@dataclass
class Handler:
    """Wraps a callable with handler-specific metadata.

    Attributes:
        fn: The underlying callable.
        topics: Set of topic patterns this handler subscribes to.
        priority: Execution priority relative to other handlers.
        name: Human-readable label (defaults to the function name).
        max_retries: How many times delivery should be retried on failure.
        enabled: Whether this handler is currently active.
    """

    fn: Callable[[Event], None]
    topics: Set[str] = field(default_factory=set)
    priority: Priority = Priority.NORMAL
    name: str = ""
    max_retries: int = 0
    enabled: bool = True

    def __post_init__(self) -> None:
        if not self.name:
            self.name = getattr(self.fn, "__name__", "anonymous")

    # ── Public API ──────────────────────────────────────────────────

    def invoke(self, event: Event) -> bool:
        """Deliver an event to this handler.

        Args:
            event: The event to deliver.

        Returns:
            True if the handler executed successfully, False on error.
        """
        if not self.enabled:
            return False
        if not self._matches_topic(event.topic):
            return False
        try:
            self.fn(event)
            return True
        except Exception:
            return False

    def disable(self) -> None:
        """Temporarily disable this handler."""
        self.enabled = False

    def enable(self) -> None:
        """Re-enable this handler."""
        self.enabled = True

    @property
    def is_wildcard(self) -> bool:
        """Whether the handler subscribes to all topics via ``*``."""
        return "*" in self.topics

    # ── Dunder ──────────────────────────────────────────────────────

    def __repr__(self) -> str:
        return f"Handler(name={self.name!r}, topics={self.topics}, enabled={self.enabled})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Handler):
            return NotImplemented
        return self.fn is other.fn and self.topics == other.topics

    def __hash__(self) -> int:
        return id(self.fn)

    # ── Private ─────────────────────────────────────────────────────

    def _matches_topic(self, topic: str) -> bool:
        """Check if the event topic matches any of the handler's patterns.

        Supports:
        - Exact match: ``user.created``
        - Wildcard suffix: ``user.*``
        - Global wildcard: ``*``
        """
        if "*" in self.topics:
            return True
        if topic in self.topics:
            return True
        prefix = topic.rsplit(".", 1)[0] + ".*"
        return prefix in self.topics

    def __validate_fn(self) -> bool:
        """Verify the wrapped callable has the expected signature. Name-mangled."""
        import inspect
        sig = inspect.signature(self.fn)
        params = list(sig.parameters.values())
        return len(params) >= 1


# ── Decorator ───────────────────────────────────────────────────────

def handler(
    *topics: str,
    priority: Priority = Priority.NORMAL,
    max_retries: int = 0,
) -> Callable:
    """Decorator to mark a function as an event handler.

    Args:
        *topics: One or more topic patterns to subscribe to.
        priority: Execution priority.
        max_retries: Retry count on failure.

    Returns:
        A decorator that wraps the function in a ``Handler`` instance.

    Example::

        @handler("user.created", "user.updated", priority=Priority.HIGH)
        def on_user_change(event: Event):
            print(event.payload)
    """
    def decorator(fn: Callable[[Event], None]) -> Handler:
        return Handler(
            fn=fn,
            topics=set(topics),
            priority=priority,
            max_retries=max_retries,
        )
    return decorator
