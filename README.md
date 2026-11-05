# EventKit

A lightweight Python event bus library for building event-driven applications. Supports typed events, middleware pipelines, pluggable storage backends, and async-friendly design.

## Features

- **Typed events** — Define events as dataclasses with automatic validation
- **Middleware pipeline** — Intercept, transform, or reject events before delivery
- **Pluggable storage** — In-memory, SQLite, or bring your own backend
- **Priority routing** — Control handler execution order with priorities
- **Dead letter queue** — Capture undeliverable events for inspection

## Quick Start

```python
from eventkit import EventBus, Event

bus = EventBus()

@bus.on("user.created")
def handle_user_created(event: Event):
    print(f"New user: {event.payload['name']}")

bus.emit("user.created", payload={"name": "Alice"})
```

## Architecture

EventKit is composed of four layers:

1. **Core** — `EventBus`, `Event`, and `Handler` definitions
2. **Middleware** — Processing pipeline (logging, retry, rate limiting)
3. **Storage** — Persistence backends for event sourcing
4. **Utils** — Type definitions and internal helpers

## Adding Middleware

```python
from eventkit.middleware import LoggingMiddleware, RetryMiddleware

bus = EventBus()
bus.use(LoggingMiddleware())
bus.use(RetryMiddleware(max_retries=3))
```

## Storage Backends

```python
from eventkit.storage import SQLiteStorage

bus = EventBus(storage=SQLiteStorage("events.db"))
bus.emit("order.placed", payload={"order_id": 42})

# Replay events
events = bus.storage.query(topic="order.placed")
```

## Quick start

```python
from eventkit import EventBus

bus = EventBus()
bus.emit("orders.created", {"id": 1})
```
