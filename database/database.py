"""SQLite connection and initial schema."""

import sqlite3
from pathlib import Path

from config.settings import DATABASE_PATH


def get_connection(database_path: Path = DATABASE_PATH) -> sqlite3.Connection:
    """Create the runtime directory and return a SQLite connection."""
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database(database_path: Path = DATABASE_PATH) -> None:
    """Create the initial tables if they do not already exist."""
    with get_connection(database_path) as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_number TEXT NOT NULL UNIQUE,
                full_name TEXT NOT NULL,
                student_email TEXT,
                guardian_email TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS grades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                subject TEXT NOT NULL,
                grade TEXT NOT NULL,
                academic_period TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES students(id)
                    ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS email_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                recipient TEXT NOT NULL,
                mode TEXT NOT NULL CHECK (
                    mode IN ('simulation', 'test', 'production')
                ),
                status TEXT NOT NULL CHECK (
                    status IN ('pending', 'sent', 'failed', 'simulated')
                ),
                message_id TEXT,
                error_message TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES students(id)
            );
            """
        )


def insert_email_log(
    database_path: Path = DATABASE_PATH,
    student_number: str = "",
    recipient: str = "",
    mode: str = "simulation",
    status: str = "simulated",
    error_message: str | None = None,
) -> None:
    """Persist a dispatch attempt for one recipient."""
    with get_connection(database_path) as connection:
        connection.execute(
            """
            INSERT INTO email_logs (student_id, recipient, mode, status, message_id, error_message)
            VALUES (
                (SELECT id FROM students WHERE student_number = ?),
                ?, ?, ?, NULL, ?
            )
            """,
            (student_number, recipient, mode, status, error_message),
        )


def list_email_logs(database_path: Path = DATABASE_PATH) -> list[dict[str, str]]:
    """Return the most recent dispatch attempts with the student number."""
    with get_connection(database_path) as connection:
        rows = connection.execute(
            """
            SELECT e.recipient, e.mode, e.status, e.error_message, e.created_at, s.student_number
            FROM email_logs e
            JOIN students s ON s.id = e.student_id
            ORDER BY e.created_at DESC
            LIMIT 100
            """
        ).fetchall()
        return [{key: row[key] for key in row.keys()} for row in rows]
