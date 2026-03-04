"""Simple SQLite helpers for chat state storage."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


# Database file is stored next to this module.
DB_PATH = Path(__file__).with_name("train_count_bot.db")


def _get_connection() -> sqlite3.Connection:
    """Create a SQLite connection with row access by column name."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _row_to_chat(row: sqlite3.Row | None) -> dict[str, Any] | None:
    """Convert a SQLite row to a regular Python dict."""
    if row is None:
        return None
    return {
        "chat_id": row["chat_id"],
        "trainer_id": row["trainer_id"],
        "balance": row["balance"],
        "message_id": row["message_id"],
    }


def init_db() -> None:
    """Create required tables if they do not exist."""
    with _get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS chats (
                chat_id INTEGER PRIMARY KEY,
                trainer_id INTEGER,
                balance INTEGER,
                message_id INTEGER
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS private_instructions (
                user_id INTEGER PRIMARY KEY
            )
            """
        )
        conn.commit()


def get_chat(chat_id: int) -> dict[str, Any] | None:
    """Get chat data by chat_id. Returns None if chat is missing."""
    with _get_connection() as conn:
        row = conn.execute(
            """
            SELECT chat_id, trainer_id, balance, message_id
            FROM chats
            WHERE chat_id = ?
            """,
            (chat_id,),
        ).fetchone()
    return _row_to_chat(row)


def create_chat(chat_id: int, trainer_id: int) -> dict[str, Any]:
    """
    Create chat row if it doesn't exist and return chat data.

    Default values:
    - balance: 0
    - message_id: NULL
    """
    with _get_connection() as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO chats (chat_id, trainer_id, balance, message_id)
            VALUES (?, ?, 0, NULL)
            """,
            (chat_id, trainer_id),
        )
        conn.commit()

        row = conn.execute(
            """
            SELECT chat_id, trainer_id, balance, message_id
            FROM chats
            WHERE chat_id = ?
            """,
            (chat_id,),
        ).fetchone()

    # Row always exists here because we inserted or it already existed.
    return _row_to_chat(row) or {
        "chat_id": chat_id,
        "trainer_id": trainer_id,
        "balance": 0,
        "message_id": None,
    }


def update_balance(chat_id: int, balance: int) -> dict[str, Any] | None:
    """Update chat balance and return updated chat dict (or None)."""
    with _get_connection() as conn:
        conn.execute(
            """
            UPDATE chats
            SET balance = ?
            WHERE chat_id = ?
            """,
            (balance, chat_id),
        )
        conn.commit()

    return get_chat(chat_id)


def update_message_id(chat_id: int, message_id: int) -> dict[str, Any] | None:
    """Update stored message_id and return updated chat dict (or None)."""
    with _get_connection() as conn:
        conn.execute(
            """
            UPDATE chats
            SET message_id = ?
            WHERE chat_id = ?
            """,
            (message_id, chat_id),
        )
        conn.commit()

    return get_chat(chat_id)


def has_seen_private_instruction(user_id: int) -> bool:
    """Return True if instruction was already shown in private chat."""
    with _get_connection() as conn:
        row = conn.execute(
            """
            SELECT 1
            FROM private_instructions
            WHERE user_id = ?
            """,
            (user_id,),
        ).fetchone()
    return row is not None


def mark_private_instruction_seen(user_id: int) -> None:
    """Mark private instruction as shown for this user."""
    with _get_connection() as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO private_instructions (user_id)
            VALUES (?)
            """,
            (user_id,),
        )
        conn.commit()