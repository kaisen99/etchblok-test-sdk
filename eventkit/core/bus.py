"""EventBus — the central publish/subscribe dispatcher.

The bus receives events via ``emit()``, passes them through the
middleware pipeline, then delivers to all matching handlers sorted
by priority.
"""
from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING

from eventkit.core.event import Event, Priority
from eventkit.core.handler import Handler
from eventkit.core._registry import _HandlerRegistry

if TYPE_CHECKING:
    from eventkit.middleware.base import Middleware
    from eventkit.storage.base import StorageBackend


class EventBus:
    """Central event dispatcher.

    Manages handler registration, middleware pipelines, and optional
    event persistence via a storage backend.

    Args:
        storage: Optional storage backend for persisting events.
        max_dead_letters: Maximum dead-letter queue size before oldest are discarded.

    Example::

        bus = EventBus()

        @bus.on("order.placed")
        def handle_order(event):
            print(event.payload)

        bus.emit("order.placed", payload={"item": "widget"})
    """

    def __init__(
        self,
        storage: Optional["StorageBackend"] = None,
        max_dead_letters: int = 1000,
    ) -> None:
        self._registry = _HandlerRegistry()
        self._middleware: List["Middleware"] = []
        self._storage = storage
        self._dead_letters: List[Event] = []
        self._max_dead_letters = max_dead_letters
        self._event_count = 0

    # ── Public API ──────────────────────────────────────────────────

    def on(self, *topics: str, priority: Priority = Priority.NORMAL) -> Callable:
        """Decorator to register a handler for one or more topics.

        Args:
            *topics: Topic patterns to subscribe to.
            priority: Handler priority.

        Returns:
            Decorator that registers the function.
        """
        def decorator(fn: Callable[[Event], None]) -> Callable[[Event], None]:
            h = Handler(fn=fn, topics=set(topics), priority=priority)
            self._registry.register(h)
            return fn
        return decorator

    def register(self, handler: Handler) -> None:
        """Explicitly register a Handler instance.

        Args:
            handler: The handler to register.
        """
        self._registry.register(handler)

    def unregister(self, handler: Handler) -> bool:
        """Remove a handler. Returns True if it was registered.

        Args:
            handler: The handler to remove.
        """
        return self._registry.unregister(handler)

    def emit(self, topic: str, payload: Optional[Dict[str, Any]] = None, priority: Priority = Priority.NORMAL) -> Event:
        """Create and dispatch an event.

        The event flows through middleware (in registration order), then
        to all matching handlers (sorted by priority).

        Args:
            topic: The event topic.
            payload: Event data dictionary.
            priority: Event priority.

        Returns:
            The dispatched Event instance.
        """
        event = Event(topic=topic, payload=payload or {}, priority=priority)
        return self.dispatch(event)

    def dispatch(self, event: Event) -> Event:
        """Dispatch a pre-built event through the pipeline.

        Args:
            event: The event to dispatch.

        Returns:
            The event (potentially modified by middleware).
        """
        processed = self._run_middleware(event)
        if processed is None:
            return event  # Middleware rejected the event

        if self._storage:
            self._storage.store(processed)

        handlers = self._registry.get_handlers(processed.topic)
        handlers.sort(key=lambda h: h.priority)

        delivered = False
        for h in handlers:
            if h.invoke(processed):
                delivered = True

        if not delivered:
            self._add_dead_letter(processed)

        self._event_count += 1
        return processed

    def use(self, middleware: "Middleware") -> None:
        """Add a middleware to the pipeline.

        Middleware are executed in the order they are added.

        Args:
            middleware: The middleware instance to add.
        """
        self._middleware.append(middleware)

    @property
    def storage(self) -> Optional["StorageBackend"]:
        """The attached storage backend, if any."""
        return self._storage

    @property
    def handler_count(self) -> int:
        """Total number of registered handlers."""
        return self._registry.count

    @property
    def dead_letters(self) -> List[Event]:
        """Events that had no matching handler."""
        return list(self._dead_letters)

    @property
    def event_count(self) -> int:
        """Total number of events dispatched."""
        return self._event_count

    def clear_dead_letters(self) -> int:
        """Clear the dead letter queue. Returns the number removed."""
        count = len(self._dead_letters)
        self._dead_letters.clear()
        return count

    # ── Private ─────────────────────────────────────────────────────

    def _run_middleware(self, event: Event) -> Optional[Event]:
        """Pass the event through each middleware in order.

        If any middleware returns None, the event is rejected.
        """
        current = event
        for mw in self._middleware:
            result = mw.process(current)
            if result is None:
                return None
            current = result
        return current

    def _add_dead_letter(self, event: Event) -> None:
        """Enqueue an undeliverable event."""
        self._dead_letters.append(event)
        if len(self._dead_letters) > self._max_dead_letters:
            self._dead_letters = self._dead_letters[-self._max_dead_letters:]

    def __repr__(self) -> str:
        return f"EventBus(handlers={self.handler_count}, events={self._event_count})"
