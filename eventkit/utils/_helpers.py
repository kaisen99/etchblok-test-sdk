"""Internal helper functions.

NOT part of the public API. These are used by core and middleware
modules for common operations.
"""
from __future__ import annotations

import re
from typing import List, Set


# ── Topic utilities ─────────────────────────────────────────────────

_TOPIC_RE = re.compile(r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)*(\.\*)?$")


def _validate_topic(topic: str) -> bool:
    """Check that a topic string is well-formed.

    Valid topics are dot-separated lowercase identifiers, optionally
    ending with ``.*`` for wildcard patterns.

    Examples:
        - ``user.created`` → valid
        - ``order.item.added`` → valid
        - ``user.*`` → valid (wildcard)
        - ``*`` → valid (global wildcard)
        - ``User.Created`` → invalid (uppercase)
        - ``user..created`` → invalid (empty segment)
    """
    if topic == "*":
        return True
    return bool(_TOPIC_RE.match(topic))


def _expand_wildcard(pattern: str, known_topics: Set[str]) -> List[str]:
    """Expand a wildcard topic pattern against known topics.

    Args:
        pattern: A topic pattern, possibly ending in ``.*``.
        known_topics: Set of all known concrete topics.

    Returns:
        List of matching concrete topics.
    """
    if pattern == "*":
        return sorted(known_topics)
    if not pattern.endswith(".*"):
        return [pattern] if pattern in known_topics else []
    prefix = pattern[:-2]  # Strip ".*"
    return sorted(t for t in known_topics if t.startswith(prefix + "."))


def _generate_event_id() -> str:
    """Generate a unique event ID. Internal use only."""
    import uuid
    return uuid.uuid4().hex


def _truncate(text: str, max_length: int = 200) -> str:
    """Truncate a string for logging. Internal helper."""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


def _topic_depth(topic: str) -> int:
    """How many dot-separated levels a topic has ("orders.created" is 2). Internal helper."""
    return len([part for part in topic.split(".") if part])
