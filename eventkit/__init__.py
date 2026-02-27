"""EventKit — lightweight event bus for Python applications.

Public API re-exports. Internal modules (prefixed with ``_``) are not
part of the stable interface.
"""
from eventkit.core.event import Event, EventMeta, Priority
from eventkit.core.bus import EventBus
from eventkit.core.handler import Handler, handler

__all__ = [
    "Event",
    "EventMeta",
    "Priority",
    "EventBus",
    "Handler",
    "handler",
]

__version__ = "0.1.0"
