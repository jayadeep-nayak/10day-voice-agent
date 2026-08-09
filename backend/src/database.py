import json
import logging
import os
import sqlite3
from datetime import datetime

logger = logging.getLogger("database")

DB_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "voice_agent.db")
)


def get_connection():
    return sqlite3.connect(DB_PATH)


def initialize_db():
    logger.info(f"Initializing SQLite database at {DB_PATH}")
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS callers (
                user_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                language_preference TEXT,
                facts TEXT,
                last_interaction TEXT
            )
        """
        )
        conn.commit()


def lookup_caller(user_id: str) -> dict | None:
    logger.info(f"Looking up caller with user_id: {user_id}")
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT user_id, name, language_preference, facts, last_interaction FROM callers WHERE user_id = ?",
            (user_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None

        facts_json = row[3]
        facts = {}
        if facts_json:
            try:
                facts = json.loads(facts_json)
            except Exception as e:
                logger.error(f"Error decoding facts JSON for {user_id}: {e}")

        return {
            "user_id": row[0],
            "name": row[1],
            "language_preference": row[2],
            "facts": facts,
            "last_interaction": row[4],
        }


def lookup_caller_by_name(name: str) -> dict | None:
    logger.info(f"Looking up caller with name: {name}")
    with get_connection() as conn:
        cursor = conn.cursor()
        # Case insensitive lookup
        cursor.execute(
            "SELECT user_id, name, language_preference, facts, last_interaction FROM callers WHERE LOWER(name) = LOWER(?)",
            (name.strip(),),
        )
        row = cursor.fetchone()
        if not row:
            return None

        facts_json = row[3]
        facts = {}
        if facts_json:
            try:
                facts = json.loads(facts_json)
            except Exception as e:
                logger.error(f"Error decoding facts JSON for name {name}: {e}")

        return {
            "user_id": row[0],
            "name": row[1],
            "language_preference": row[2],
            "facts": facts,
            "last_interaction": row[4],
        }


def save_caller(user_id: str, name: str, language_preference: str, facts: dict) -> None:
    logger.info(f"Saving caller {name} (ID: {user_id}) with facts: {facts}")
    last_interaction = datetime.now().isoformat()
    facts_json = json.dumps(facts)
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO callers (user_id, name, language_preference, facts, last_interaction)
            VALUES (?, ?, ?, ?, ?)
        """,
            (user_id, name, language_preference, facts_json, last_interaction),
        )
        conn.commit()


def delete_caller(user_id: str) -> bool:
    logger.info(f"Deleting caller record for user_id: {user_id}")
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM callers WHERE user_id = ?", (user_id,))
        conn.commit()
        return cursor.rowcount > 0


def clear_all_callers() -> int:
    logger.info("Clearing all caller records from database")
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM callers")
        conn.commit()
        return cursor.rowcount


def lookup_most_recent_caller() -> dict | None:
    logger.info("Looking up most recent caller in database")
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT user_id, name, language_preference, facts, last_interaction FROM callers ORDER BY last_interaction DESC LIMIT 1"
        )
        row = cursor.fetchone()
        if not row:
            return None

        facts_json = row[3]
        facts = {}
        if facts_json:
            try:
                facts = json.loads(facts_json)
            except Exception as e:
                logger.error(f"Error decoding facts JSON: {e}")

        return {
            "user_id": row[0],
            "name": row[1],
            "language_preference": row[2],
            "facts": facts,
            "last_interaction": row[4],
        }

