"""SQLite storage backend.

Durable, file-based storage using Python's built-in ``sqlite3`` module.
Suitable for single-process applications that need event persistence
across restarts.
"""
from __future__ import annotations

import json
import sqlite3
from typing import List, Optional

from eventkit.core.event import Event
from eventkit.storage.base import StorageBackend
from eventkit.storage._serializer import _EventSerializer
from eventkit.utils._helpers import _validate_topic


class SQLiteStorage(StorageBackend):
    """Persist events in a local SQLite database.

    Args:
        db_path: Path to the SQLite file. Use ``:memory:`` for an
                 in-memory database (useful for tests).
    """

    # ── Class-level constants ───────────────────────────────────────
    TABLE_NAME = "events"
    SCHEMA_VERSION = 1

    def __init__(self, db_path: str = "events.db") -> None:
        self._db_path = db_path
        self._serializer = _EventSerializer()
        self._conn: Optional[sqlite3.Connection] = None
        self._ensure_schema()

    # ── StorageBackend interface ────────────────────────────────────

    def store(self, event: Event) -> None:
        """Insert an event into the database."""
        conn = self._get_connection()
        data = self._serializer.serialize(event)
        conn.execute(
            f"INSERT OR REPLACE INTO {self.TABLE_NAME} (event_id, topic, payload, priority, timestamp, raw) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                event.meta.event_id,
                event.topic,
                json.dumps(event.payload),
                event.priority.name,
                event.meta.timestamp.isoformat(),
                json.dumps(data),
            ),
        )
        conn.commit()

    def get(self, event_id: str) -> Optional[Event]:
        """Retrieve a single event by its ID."""
        conn = self._get_connection()
        row = conn.execute(
            f"SELECT raw FROM {self.TABLE_NAME} WHERE event_id = ?", (event_id,)
        ).fetchone()
        if row:
            return self._serializer.deserialize(json.loads(row[0]))
        return None

    def query(self, topic: Optional[str] = None, limit: int = 100) -> List[Event]:
        """Query events, optionally filtered by topic, newest first."""
        if topic is not None and not _validate_topic(topic):
            raise ValueError(f"invalid event topic: {topic!r}")
        conn = self._get_connection()
        if topic:
            rows = conn.execute(
                f"SELECT raw FROM {self.TABLE_NAME} WHERE topic = ? ORDER BY timestamp DESC LIMIT ?",
                (topic, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                f"SELECT raw FROM {self.TABLE_NAME} ORDER BY timestamp DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [self._serializer.deserialize(json.loads(r[0])) for r in rows]

    def count(self, topic: Optional[str] = None) -> int:
        """Count stored events."""
        conn = self._get_connection()
        if topic:
            row = conn.execute(
                f"SELECT COUNT(*) FROM {self.TABLE_NAME} WHERE topic = ?", (topic,)
            ).fetchone()
        else:
            row = conn.execute(f"SELECT COUNT(*) FROM {self.TABLE_NAME}").fetchone()
        return row[0] if row else 0

    def clear(self) -> int:
        """Delete all events."""
        conn = self._get_connection()
        count = self.count()
        conn.execute(f"DELETE FROM {self.TABLE_NAME}")
        conn.commit()
        return count

    # ── Extra public methods ────────────────────────────────────────

    def close(self) -> None:
        """Close the database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None

    @property
    def db_path(self) -> str:
        """The file path of the database."""
        return self._db_path

    # ── Private ─────────────────────────────────────────────────────

    def _get_connection(self) -> sqlite3.Connection:
        """Lazy-open the database connection."""
        if self._conn is None:
            self._conn = sqlite3.connect(self._db_path)
        return self._conn

    def _ensure_schema(self) -> None:
        """Create tables if they don't exist."""
        conn = self._get_connection()
        conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.TABLE_NAME} (
                event_id TEXT PRIMARY KEY,
                topic TEXT NOT NULL,
                payload TEXT,
                priority TEXT,
                timestamp TEXT,
                raw TEXT
            )
        """)
        conn.execute(
            f"CREATE INDEX IF NOT EXISTS idx_{self.TABLE_NAME}_topic "
            f"ON {self.TABLE_NAME}(topic)"
        )
        conn.commit()

    def _vacuum(self) -> None:
        """Reclaim disk space. Internal maintenance operation."""
        conn = self._get_connection()
        conn.execute("VACUUM")
