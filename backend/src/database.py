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
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS escalations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reference_id TEXT UNIQUE NOT NULL,
                who_needs_help TEXT NOT NULL,
                caller_id TEXT,
                what_happened TEXT NOT NULL,
                agent_checks TEXT,
                urgency TEXT DEFAULT 'medium',
                language_preference TEXT DEFAULT 'English',
                preferred_followup TEXT DEFAULT 'call-back',
                status TEXT DEFAULT 'open',
                created_at TEXT NOT NULL
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


# ── Escalation helpers ────────────────────────────────────────────────────────

def _generate_reference_id() -> str:
    """Generate a unique escalation reference ID like ESC-20260812-0003."""
    date_str = datetime.now().strftime("%Y%m%d")
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM escalations WHERE reference_id LIKE ?",
            (f"ESC-{date_str}-%",),
        )
        count = cursor.fetchone()[0]
    seq = count + 1
    return f"ESC-{date_str}-{seq:04d}"


def create_escalation(
    who_needs_help: str,
    caller_id: str,
    what_happened: str,
    agent_checks: str,
    urgency: str = "medium",
    language_preference: str = "English",
    preferred_followup: str = "call-back",
) -> str:
    """Store an escalation request and return its reference ID."""
    reference_id = _generate_reference_id()
    created_at = datetime.now().isoformat()

    logger.info(
        f"Creating escalation {reference_id} for '{who_needs_help}' "
        f"(urgency={urgency}): {what_happened}"
    )

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO escalations
                (reference_id, who_needs_help, caller_id, what_happened,
                 agent_checks, urgency, language_preference,
                 preferred_followup, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'open', ?)
            """,
            (
                reference_id,
                who_needs_help,
                caller_id,
                what_happened,
                agent_checks,
                urgency,
                language_preference,
                preferred_followup,
                created_at,
            ),
        )
        conn.commit()

    return reference_id


def get_open_escalations() -> list[dict]:
    """Return all escalation requests with status 'open'."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT reference_id, who_needs_help, caller_id, what_happened,
                   agent_checks, urgency, language_preference,
                   preferred_followup, status, created_at
            FROM escalations
            WHERE status = 'open'
            ORDER BY created_at DESC
            """
        )
        rows = cursor.fetchall()

    return [
        {
            "reference_id": r[0],
            "who_needs_help": r[1],
            "caller_id": r[2],
            "what_happened": r[3],
            "agent_checks": r[4],
            "urgency": r[5],
            "language_preference": r[6],
            "preferred_followup": r[7],
            "status": r[8],
            "created_at": r[9],
        }
        for r in rows
    ]


def get_all_escalations() -> list[dict]:
    """Return all escalation requests (open and resolved)."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT reference_id, who_needs_help, caller_id, what_happened,
                   agent_checks, urgency, language_preference,
                   preferred_followup, status, created_at
            FROM escalations
            ORDER BY created_at DESC
            """
        )
        rows = cursor.fetchall()

    return [
        {
            "reference_id": r[0],
            "who_needs_help": r[1],
            "caller_id": r[2],
            "what_happened": r[3],
            "agent_checks": r[4],
            "urgency": r[5],
            "language_preference": r[6],
            "preferred_followup": r[7],
            "status": r[8],
            "created_at": r[9],
        }
        for r in rows
    ]


def resolve_escalation(reference_id: str) -> bool:
    """Mark an escalation as resolved. Returns True if a row was updated."""
    logger.info(f"Resolving escalation {reference_id}")
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE escalations SET status = 'resolved' WHERE reference_id = ? AND status = 'open'",
            (reference_id,),
        )
        conn.commit()
        return cursor.rowcount > 0

