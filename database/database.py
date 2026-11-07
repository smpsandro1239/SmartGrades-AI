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
