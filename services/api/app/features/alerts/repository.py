"""SQLite data access for alert subscriptions and notification tracking."""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.core.config import settings


def get_sqlite_connection(db_path: str | Path | None = None) -> sqlite3.Connection:
    """Connect to SQLite and ensure alert tables exist."""
    path = Path(db_path or settings.app_db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS alert_subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            area_id TEXT NOT NULL,
            rule TEXT NOT NULL,
            lead_days INTEGER NOT NULL DEFAULT 14,
            confirmed BOOLEAN NOT NULL DEFAULT 0,
            unsubscribe_token TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS notifications_sent (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subscription_id INTEGER NOT NULL REFERENCES alert_subscriptions(id) ON DELETE CASCADE,
            rule TEXT NOT NULL,
            period TEXT NOT NULL,
            sent_at TEXT NOT NULL,
            UNIQUE(subscription_id, rule, period)
        )
        """
    )
    conn.commit()
    return conn


def create_subscription(
    email: str,
    area_id: str,
    rule: str,
    lead_days: int,
    unsubscribe_token: str,
    db_path: str | Path | None = None,
) -> int:
    """Insert an unconfirmed alert subscription."""
    conn = get_sqlite_connection(db_path)
    now_utc = datetime.now(UTC).isoformat()
    with conn:
        cursor = conn.execute(
            """
            INSERT INTO alert_subscriptions
            (email, area_id, rule, lead_days, confirmed, unsubscribe_token, created_at)
            VALUES (?, ?, ?, ?, 0, ?, ?)
            """,
            [email, area_id, rule, lead_days, unsubscribe_token, now_utc],
        )
        return int(cursor.lastrowid or 0)


def get_subscription_by_token(
    token: str,
    db_path: str | Path | None = None,
) -> dict[str, Any] | None:
    """Find a subscription by its unique token."""
    conn = get_sqlite_connection(db_path)
    cursor = conn.execute(
        """
        SELECT id, email, area_id, rule, lead_days, confirmed, unsubscribe_token, created_at
        FROM alert_subscriptions
        WHERE unsubscribe_token = ?
        LIMIT 1
        """,
        [token],
    )
    row = cursor.fetchone()
    if row is None:
        return None
    return {
        "id": row[0],
        "email": row[1],
        "area_id": row[2],
        "rule": row[3],
        "lead_days": row[4],
        "confirmed": bool(row[5]),
        "unsubscribe_token": row[6],
        "created_at": row[7],
    }


def confirm_subscription(
    token: str,
    db_path: str | Path | None = None,
) -> bool:
    """Mark a subscription confirmed given its token."""
    conn = get_sqlite_connection(db_path)
    with conn:
        cursor = conn.execute(
            """
            UPDATE alert_subscriptions
            SET confirmed = 1
            WHERE unsubscribe_token = ?
            """,
            [token],
        )
        return cursor.rowcount > 0


def delete_subscription_by_token(
    token: str,
    db_path: str | Path | None = None,
) -> bool:
    """Delete a subscription given its unsubscribe token."""
    conn = get_sqlite_connection(db_path)
    with conn:
        cursor = conn.execute(
            """
            DELETE FROM alert_subscriptions
            WHERE unsubscribe_token = ?
            """,
            [token],
        )
        return cursor.rowcount > 0


def list_confirmed_subscriptions(
    db_path: str | Path | None = None,
) -> list[dict[str, Any]]:
    """List all confirmed subscriptions for evaluation."""
    conn = get_sqlite_connection(db_path)
    cursor = conn.execute(
        """
        SELECT id, email, area_id, rule, lead_days, unsubscribe_token
        FROM alert_subscriptions
        WHERE confirmed = 1
        ORDER BY id
        """
    )
    return [
        {
            "id": row[0],
            "email": row[1],
            "area_id": row[2],
            "rule": row[3],
            "lead_days": row[4],
            "unsubscribe_token": row[5],
        }
        for row in cursor.fetchall()
    ]


def has_notification_been_sent(
    subscription_id: int,
    rule: str,
    period: str,
    db_path: str | Path | None = None,
) -> bool:
    """Check if notification has already been recorded for this subscription/rule/period."""
    conn = get_sqlite_connection(db_path)
    cursor = conn.execute(
        """
        SELECT 1 FROM notifications_sent
        WHERE subscription_id = ? AND rule = ? AND period = ?
        LIMIT 1
        """,
        [subscription_id, rule, period],
    )
    return cursor.fetchone() is not None


def record_notification_sent(
    subscription_id: int,
    rule: str,
    period: str,
    db_path: str | Path | None = None,
) -> bool:
    """Record a sent notification. Returns True if inserted, False if duplicate."""
    conn = get_sqlite_connection(db_path)
    now_utc = datetime.now(UTC).isoformat()
    try:
        with conn:
            conn.execute(
                """
                INSERT INTO notifications_sent
                (subscription_id, rule, period, sent_at)
                VALUES (?, ?, ?, ?)
                """,
                [subscription_id, rule, period, now_utc],
            )
            return True
    except sqlite3.IntegrityError:
        return False
