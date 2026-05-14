"""SQLite persistence for Devin remediation sessions."""
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = os.getenv("DB_PATH", "/data/sessions.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    issue_number        INTEGER NOT NULL,
    cve_id              TEXT    NOT NULL,
    package             TEXT,
    fixed_version       TEXT,
    severity            TEXT,
    devin_session_id    TEXT    UNIQUE NOT NULL,
    devin_session_url   TEXT,
    status              TEXT    NOT NULL DEFAULT 'pending',
    pr_url              TEXT,
    error_message       TEXT,
    created_at          TEXT    NOT NULL,
    completed_at        TEXT
);
CREATE INDEX IF NOT EXISTS idx_status ON sessions(status);
CREATE INDEX IF NOT EXISTS idx_issue  ON sessions(issue_number);
"""


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def get_conn(db_path: str = DB_PATH):
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db(db_path: str = DB_PATH) -> None:
    with get_conn(db_path) as conn:
        conn.executescript(SCHEMA)


def insert_session(
    *,
    issue_number: int,
    cve_id: str,
    package: str,
    fixed_version: str,
    severity: str,
    devin_session_id: str,
    devin_session_url: str,
    db_path: str = DB_PATH,
) -> None:
    with get_conn(db_path) as conn:
        conn.execute(
            """INSERT OR IGNORE INTO sessions
               (issue_number, cve_id, package, fixed_version, severity,
                devin_session_id, devin_session_url, status, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?)""",
            (issue_number, cve_id, package, fixed_version, severity,
             devin_session_id, devin_session_url, _now_iso()),
        )


def update_status(
    devin_session_id: str,
    status: str,
    *,
    pr_url: str | None = None,
    error_message: str | None = None,
    db_path: str = DB_PATH,
) -> None:
    completed_at = _now_iso() if status in ("completed", "failed") else None
    with get_conn(db_path) as conn:
        conn.execute(
            """UPDATE sessions
               SET status = ?,
                   pr_url = COALESCE(?, pr_url),
                   error_message = COALESCE(?, error_message),
                   completed_at = COALESCE(?, completed_at)
               WHERE devin_session_id = ?""",
            (status, pr_url, error_message, completed_at, devin_session_id),
        )


def get_active_sessions(db_path: str = DB_PATH) -> list[dict]:
    with get_conn(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM sessions WHERE status IN ('pending', 'running', 'blocked')"
        ).fetchall()
    return [dict(r) for r in rows]


def get_all_sessions(db_path: str = DB_PATH) -> list[dict]:
    with get_conn(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM sessions ORDER BY created_at DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def session_exists_for_issue(
    issue_number: int, cve_id: str, db_path: str = DB_PATH
) -> bool:
    """Idempotency guard — webhooks fire duplicates."""
    with get_conn(db_path) as conn:
        row = conn.execute(
            "SELECT 1 FROM sessions WHERE issue_number = ? AND cve_id = ? LIMIT 1",
            (issue_number, cve_id),
        ).fetchone()
    return row is not None
