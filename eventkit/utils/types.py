"""Public type aliases and protocols used across EventKit.

These types can be used by consumers for type annotations when
building handlers and middleware.
"""
from __future__ import annotations

from typing import Callable, Protocol, Sequence, Union, runtime_checkable

from eventkit.core.event import Event


# ── Type aliases ────────────────────────────────────────────────────

EventCallback = Callable[[Event], None]
"""Callable that receives and processes a single event."""

TopicFilter = Union[str, Sequence[str]]
"""A single topic pattern or a list of topic patterns."""

EventPredicate = Callable[[Event], bool]
"""A function that tests whether an event matches some criteria."""


# ── Protocols ───────────────────────────────────────────────────────

@runtime_checkable
class Emitter(Protocol):
    """Anything that can emit events."""

    def emit(self, topic: str, **kwargs) -> Event: ...


@runtime_checkable
class Subscriber(Protocol):
    """Anything that can subscribe to events."""

    def on(self, *topics: str) -> Callable: ...


@runtime_checkable
class EventStore(Protocol):
    """Structural type for read-only event storage access."""

    def get(self, event_id: str) -> Event | None: ...
    def query(self, topic: str | None = None, limit: int = 100) -> list[Event]: ...
    def count(self, topic: str | None = None) -> int: ...
