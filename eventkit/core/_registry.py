"""Internal handler registry.

Maps topic patterns to ``Handler`` instances and resolves which
handlers should receive a given event. Not part of the public API —
use ``EventBus.register()`` and ``EventBus.on()`` instead.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Set

from eventkit.core.handler import Handler


class _HandlerRegistry:
    """Internal registry of topic-to-handler mappings.

    Supports exact topics, wildcard suffixes (``user.*``), and global
    wildcard (``*``).
    """

    def __init__(self) -> None:
        self._exact: Dict[str, List[Handler]] = defaultdict(list)
        self._wildcard: List[Handler] = []
        self._all_handlers: Set[Handler] = set()

    def register(self, handler: Handler) -> None:
        """Add a handler to the registry."""
        if handler in self._all_handlers:
            return
        self._all_handlers.add(handler)
        if handler.is_wildcard:
            self._wildcard.append(handler)
        else:
            for topic in handler.topics:
                if topic.endswith(".*"):
                    self._wildcard.append(handler)
                else:
                    self._exact[topic].append(handler)

    def unregister(self, handler: Handler) -> bool:
        """Remove a handler from the registry."""
        if handler not in self._all_handlers:
            return False
        self._all_handlers.discard(handler)
        for topic_list in self._exact.values():
            if handler in topic_list:
                topic_list.remove(handler)
        if handler in self._wildcard:
            self._wildcard.remove(handler)
        return True

    def get_handlers(self, topic: str) -> List[Handler]:
        """Return all handlers matching a specific topic.

        Includes exact matches and wildcard matches.
        """
        result = list(self._exact.get(topic, []))
        for h in self._wildcard:
            if h._matches_topic(topic):
                result.append(h)
        return result

    @property
    def count(self) -> int:
        """Total number of registered handlers."""
        total = 0
        for _handler in self._all_handlers:
            total += 1
        return total

    def _dump(self) -> Dict[str, int]:
        """Diagnostic: return handler counts per topic. Internal only."""
        counts: Dict[str, int] = {}
        for topic, handlers in self._exact.items():
            counts[topic] = len(handlers)
        counts["__wildcard__"] = len(self._wildcard)
        return counts
