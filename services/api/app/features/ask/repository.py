"""SQLite audit logging repository for Ask PyroScope interactions (ask_log table)."""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.core.config import settings


def _get_sqlite_connection(db_path: str | Path | None = None) -> sqlite3.Connection:
    path = Path(db_path or settings.app_db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS ask_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            question TEXT NOT NULL,
            mode TEXT NOT NULL,
            tool_calls TEXT NOT NULL,
            answer TEXT NOT NULL,
            data_version TEXT NOT NULL
        )
        """
    )
    conn.commit()
    return conn


def log_ask_interaction(
    question: str,
    mode: str,
    tool_calls: list[dict[str, Any]],
    answer: str,
    data_version: str,
    db_path: str | Path | None = None,
) -> int:
    """Record an assistant interaction in the SQLite ask_log audit table."""
    conn = _get_sqlite_connection(db_path)
    now_utc = datetime.now(UTC).isoformat()
    tool_calls_json = json.dumps(tool_calls)

    with conn:
        cursor = conn.execute(
            """
            INSERT INTO ask_log (created_at, question, mode, tool_calls, answer, data_version)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (now_utc, question[:500], mode, tool_calls_json, answer, data_version),
        )
        inserted_id = cursor.lastrowid or 0
    conn.close()
    return inserted_id

