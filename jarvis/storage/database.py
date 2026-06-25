"""SQLite persistence for settings, sessions, chat history, and the action log.

Uses the standard library ``sqlite3`` (no heavy ORM). The database is created
on first use under the user's app-data directory (overridable for tests).
"""
from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from .models import (
    ActionLogEntry,
    ChatMessage,
    MessageRole,
    RiskLevel,
    Session,
)


def default_db_path() -> Path:
    """Return the default database path under the user's home/app-data dir."""
    base = Path.home() / ".jarvis"
    base.mkdir(parents=True, exist_ok=True)
    return base / "jarvis.db"


class Database:
    """Thin, thread-safe wrapper around a SQLite connection."""

    def __init__(self, path: Optional[Path | str] = None) -> None:
        self.path = str(path) if path is not None else str(default_db_path())
        # check_same_thread=False because the Qt worker thread also logs.
        self._conn = sqlite3.connect(self.path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._lock = threading.Lock()
        self._create_schema()

    # -- schema --------------------------------------------------------------
    def _create_schema(self) -> None:
        with self._lock:
            self._conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS settings (
                    key   TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS sessions (
                    id         INTEGER PRIMARY KEY AUTOINCREMENT,
                    title      TEXT NOT NULL DEFAULT 'Session',
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS messages (
                    id         INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
                    role       TEXT NOT NULL,
                    content    TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS action_log (
                    id                INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id        INTEGER NOT NULL,
                    created_at        TEXT NOT NULL,
                    user_request      TEXT NOT NULL DEFAULT '',
                    plan              TEXT NOT NULL DEFAULT '',
                    tool_name         TEXT NOT NULL DEFAULT '',
                    tool_args_summary TEXT NOT NULL DEFAULT '',
                    risk_level        TEXT NOT NULL DEFAULT 'low',
                    confirmation      TEXT NOT NULL DEFAULT '',
                    result            TEXT NOT NULL DEFAULT '',
                    error             TEXT NOT NULL DEFAULT '',
                    screenshot_meta   TEXT
                );
                """
            )
            self._conn.commit()

    # -- settings ------------------------------------------------------------
    def get_setting(self, key: str, default: Any = None) -> Any:
        with self._lock:
            cur = self._conn.execute(
                "SELECT value FROM settings WHERE key = ?", (key,)
            )
            row = cur.fetchone()
        if row is None:
            return default
        try:
            return json.loads(row["value"])
        except (json.JSONDecodeError, TypeError):
            return row["value"]

    def set_setting(self, key: str, value: Any) -> None:
        payload = json.dumps(value)
        with self._lock:
            self._conn.execute(
                "INSERT INTO settings(key, value) VALUES(?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (key, payload),
            )
            self._conn.commit()

    def all_settings(self) -> dict[str, Any]:
        with self._lock:
            cur = self._conn.execute("SELECT key, value FROM settings")
            rows = cur.fetchall()
        result: dict[str, Any] = {}
        for row in rows:
            try:
                result[row["key"]] = json.loads(row["value"])
            except (json.JSONDecodeError, TypeError):
                result[row["key"]] = row["value"]
        return result

    # -- sessions ------------------------------------------------------------
    def create_session(self, title: str = "Session") -> Session:
        created = datetime.now().isoformat()
        with self._lock:
            cur = self._conn.execute(
                "INSERT INTO sessions(title, created_at) VALUES(?, ?)",
                (title, created),
            )
            self._conn.commit()
            session_id = int(cur.lastrowid)
        return Session(id=session_id, title=title, created_at=datetime.fromisoformat(created))

    def list_sessions(self, limit: int = 50) -> list[Session]:
        with self._lock:
            cur = self._conn.execute(
                "SELECT * FROM sessions ORDER BY id DESC LIMIT ?", (limit,)
            )
            rows = cur.fetchall()
        return [
            Session(
                id=r["id"],
                title=r["title"],
                created_at=datetime.fromisoformat(r["created_at"]),
            )
            for r in rows
        ]

    # -- messages ------------------------------------------------------------
    def add_message(self, session_id: int, role: MessageRole, content: str) -> ChatMessage:
        created = datetime.now().isoformat()
        with self._lock:
            cur = self._conn.execute(
                "INSERT INTO messages(session_id, role, content, created_at) "
                "VALUES(?, ?, ?, ?)",
                (session_id, role.value, content, created),
            )
            self._conn.commit()
            msg_id = int(cur.lastrowid)
        return ChatMessage(
            id=msg_id,
            session_id=session_id,
            role=role,
            content=content,
            created_at=datetime.fromisoformat(created),
        )

    def get_messages(self, session_id: int, limit: int = 200) -> list[ChatMessage]:
        with self._lock:
            cur = self._conn.execute(
                "SELECT * FROM messages WHERE session_id = ? ORDER BY id ASC LIMIT ?",
                (session_id, limit),
            )
            rows = cur.fetchall()
        return [
            ChatMessage(
                id=r["id"],
                session_id=r["session_id"],
                role=MessageRole(r["role"]),
                content=r["content"],
                created_at=datetime.fromisoformat(r["created_at"]),
            )
            for r in rows
        ]

    # -- action log ----------------------------------------------------------
    def log_action(self, entry: ActionLogEntry) -> ActionLogEntry:
        with self._lock:
            cur = self._conn.execute(
                """
                INSERT INTO action_log(
                    session_id, created_at, user_request, plan, tool_name,
                    tool_args_summary, risk_level, confirmation, result, error,
                    screenshot_meta
                ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    entry.session_id,
                    entry.created_at.isoformat(),
                    entry.user_request,
                    entry.plan,
                    entry.tool_name,
                    entry.tool_args_summary,
                    entry.risk_level.value,
                    entry.confirmation,
                    entry.result,
                    entry.error,
                    entry.screenshot_meta,
                ),
            )
            self._conn.commit()
            entry.id = int(cur.lastrowid)
        return entry

    def get_action_log(self, session_id: Optional[int] = None, limit: int = 200) -> list[ActionLogEntry]:
        with self._lock:
            if session_id is None:
                cur = self._conn.execute(
                    "SELECT * FROM action_log ORDER BY id DESC LIMIT ?", (limit,)
                )
            else:
                cur = self._conn.execute(
                    "SELECT * FROM action_log WHERE session_id = ? "
                    "ORDER BY id DESC LIMIT ?",
                    (session_id, limit),
                )
            rows = cur.fetchall()
        return [
            ActionLogEntry(
                id=r["id"],
                session_id=r["session_id"],
                created_at=datetime.fromisoformat(r["created_at"]),
                user_request=r["user_request"],
                plan=r["plan"],
                tool_name=r["tool_name"],
                tool_args_summary=r["tool_args_summary"],
                risk_level=RiskLevel(r["risk_level"]),
                confirmation=r["confirmation"],
                result=r["result"],
                error=r["error"],
                screenshot_meta=r["screenshot_meta"],
            )
            for r in rows
        ]

    def close(self) -> None:
        with self._lock:
            self._conn.close()
