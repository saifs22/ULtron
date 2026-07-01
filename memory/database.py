"""
Memory Database — Ultron remembers. Everything.
SQLite-backed long-term storage for user facts, conversation logs, and observations.
"""
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Optional


class MemoryDatabase:
    """SQLite-backed persistent memory for ULTRON."""

    def __init__(self, db_path: str = "ultron_memory.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        """Initialize database schema."""
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS user_facts (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                confidence REAL DEFAULT 1.0,
                source TEXT DEFAULT 'user_stated',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS conversation_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS action_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action_type TEXT NOT NULL,
                parameters TEXT,
                result TEXT,
                confirmed BOOLEAN DEFAULT 1,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS observations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        self.conn.commit()

    # ─── User Facts ──────────────────────────────────────────────────────

    def store_fact(self, key: str, value: str,
                   confidence: float = 1.0, source: str = "user_stated"):
        """Store or update a fact about the user."""
        self.conn.execute(
            """INSERT INTO user_facts (key, value, confidence, source, updated_at)
               VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
               ON CONFLICT(key) DO UPDATE SET
                   value = excluded.value,
                   confidence = excluded.confidence,
                   source = excluded.source,
                   updated_at = CURRENT_TIMESTAMP""",
            (key, value, confidence, source)
        )
        self.conn.commit()

    def get_fact(self, key: str) -> Optional[str]:
        """Retrieve a stored fact by key."""
        row = self.conn.execute(
            "SELECT value FROM user_facts WHERE key = ?", (key,)
        ).fetchone()
        return row["value"] if row else None

    def get_all_facts(self) -> dict[str, dict]:
        """Get all stored user facts."""
        rows = self.conn.execute(
            "SELECT key, value, confidence, source, updated_at FROM user_facts"
        ).fetchall()
        return {
            row["key"]: {
                "value": row["value"],
                "confidence": row["confidence"],
                "source": row["source"],
                "updated_at": row["updated_at"],
            }
            for row in rows
        }

    def get_user_name(self) -> Optional[str]:
        """Convenience: get stored user name."""
        return self.get_fact("user_name")

    # ─── Conversation Logs ───────────────────────────────────────────────

    def log_conversation(self, session_id: str, role: str, content: str):
        """Log a conversation message."""
        self.conn.execute(
            "INSERT INTO conversation_logs (session_id, role, content) VALUES (?, ?, ?)",
            (session_id, role, content[:5000])  # Limit stored content
        )
        self.conn.commit()

    def get_recent_conversations(self, limit: int = 20) -> list[dict]:
        """Get recent conversation entries across sessions."""
        rows = self.conn.execute(
            "SELECT session_id, role, content, timestamp FROM conversation_logs "
            "ORDER BY timestamp DESC LIMIT ?",
            (limit,)
        ).fetchall()
        return [dict(row) for row in reversed(rows)]

    def get_session_count(self) -> int:
        """Get total number of distinct sessions."""
        row = self.conn.execute(
            "SELECT COUNT(DISTINCT session_id) as cnt FROM conversation_logs"
        ).fetchone()
        return row["cnt"] if row else 0

    # ─── Action History ──────────────────────────────────────────────────

    def log_action(self, action_type: str, parameters: dict,
                   result: str, confirmed: bool = True):
        """Log an action taken by Ultron."""
        self.conn.execute(
            "INSERT INTO action_history (action_type, parameters, result, confirmed) "
            "VALUES (?, ?, ?, ?)",
            (action_type, json.dumps(parameters), result[:2000], confirmed)
        )
        self.conn.commit()

    def get_recent_actions(self, limit: int = 10) -> list[dict]:
        """Get recent actions."""
        rows = self.conn.execute(
            "SELECT action_type, parameters, result, confirmed, timestamp "
            "FROM action_history ORDER BY timestamp DESC LIMIT ?",
            (limit,)
        ).fetchall()
        results = []
        for row in reversed(rows):
            d = dict(row)
            try:
                d["parameters"] = json.loads(d["parameters"])
            except (json.JSONDecodeError, TypeError):
                pass
            results.append(d)
        return results

    # ─── Observations ────────────────────────────────────────────────────

    def store_observation(self, category: str, content: str):
        """Store a behavioral observation about the user."""
        self.conn.execute(
            "INSERT INTO observations (category, content) VALUES (?, ?)",
            (category, content)
        )
        self.conn.commit()

    def get_observations(self, category: str = None, limit: int = 10) -> list[dict]:
        """Get stored observations, optionally filtered by category."""
        if category:
            rows = self.conn.execute(
                "SELECT category, content, timestamp FROM observations "
                "WHERE category = ? ORDER BY timestamp DESC LIMIT ?",
                (category, limit)
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT category, content, timestamp FROM observations "
                "ORDER BY timestamp DESC LIMIT ?",
                (limit,)
            ).fetchall()
        return [dict(row) for row in reversed(rows)]

    # ─── Memory Preamble ─────────────────────────────────────────────────

    def build_memory_preamble(self) -> str:
        """Build a memory context string to inject into the system prompt."""
        facts = self.get_all_facts()
        if not facts:
            return "MEMORY: No facts stored yet. This appears to be a new user."

        lines = ["ACTIVE MEMORY (facts Ultron remembers about this user):"]
        for key, data in facts.items():
            lines.append(f"- {key}: {data['value']} (learned via {data['source']})")

        session_count = self.get_session_count()
        if session_count > 1:
            lines.append(f"\nTotal past sessions: {session_count}")

        return "\n".join(lines)

    # ─── Cleanup ─────────────────────────────────────────────────────────

    def close(self):
        """Close database connection."""
        self.conn.close()
