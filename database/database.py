"""SQLite connection and database operations."""

import sqlite3
from pathlib import Path
from typing import Iterable

from config.settings import DATABASE_PATH


def get_connection(
    database_path: Path = DATABASE_PATH,
) -> sqlite3.Connection:
    """Create the runtime directory and return a SQLite connection."""

    database_path = Path(database_path)
    database_path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    return connection


def initialize_database(
    database_path: Path = DATABASE_PATH,
) -> None:
    """Create the application database schema."""

    with get_connection(database_path) as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_number TEXT NOT NULL,
                school TEXT NOT NULL,
                full_name TEXT,
                student_email TEXT,
                guardian_email TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(student_number, school)
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

            CREATE INDEX IF NOT EXISTS idx_email_logs_created_at
            ON email_logs(created_at);

            CREATE INDEX IF NOT EXISTS idx_students_school_number
            ON students(school, student_number);
            """
        )


def upsert_students(
    records: Iterable[dict[str, str]],
    database_path: Path = DATABASE_PATH,
) -> int:
    """Insert students or update their guardian email addresses."""

    records = list(records)

    if not records:
        return 0

    with get_connection(database_path) as connection:
        for record in records:
            student_number = record["student_id"].strip()
            school = record["school"].strip()
            guardian_email = record["email"].strip()

            if not student_number or not school or not guardian_email:
                raise ValueError(
                    "Os dados do aluno contêm campos obrigatórios vazios."
                )

            connection.execute(
                """
                INSERT INTO students (
                    student_number,
                    school,
                    guardian_email
                )
                VALUES (?, ?, ?)

                ON CONFLICT(student_number, school)
                DO UPDATE SET
                    guardian_email = excluded.guardian_email
                """,
                (
                    student_number,
                    school,
                    guardian_email,
                ),
            )

    return len(records)


def insert_email_log(
    database_path: Path = DATABASE_PATH,
    student_number: str = "",
    school: str = "",
    recipient: str = "",
    mode: str = "simulation",
    status: str = "simulated",
    message_id: str | None = None,
    error_message: str | None = None,
) -> None:
    """Persist an individual email dispatch attempt."""

    if not student_number or not school:
        raise ValueError(
            "É obrigatório indicar o ID do aluno e a escola."
        )

    with get_connection(database_path) as connection:
        student = connection.execute(
            """
            SELECT id
            FROM students
            WHERE student_number = ? AND school = ?
            """,
            (student_number, school),
        ).fetchone()

        if student is None:
            raise ValueError(
                "O aluno não existe na base de dados. "
                "Importa primeiro os alunos."
            )

        connection.execute(
            """
            INSERT INTO email_logs (
                student_id,
                recipient,
                mode,
                status,
                message_id,
                error_message
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                student["id"],
                recipient,
                mode,
                status,
                message_id,
                error_message,
            ),
        )


def list_email_logs(
    database_path: Path = DATABASE_PATH,
) -> list[dict]:
    """Return the most recent dispatch attempts."""

    with get_connection(database_path) as connection:
        rows = connection.execute(
            """
            SELECT
                e.recipient,
                e.mode,
                e.status,
                e.message_id,
                e.error_message,
                e.created_at,
                s.student_number,
                s.school
            FROM email_logs e
            JOIN students s ON s.id = e.student_id
            ORDER BY e.created_at DESC, e.id DESC
            LIMIT 100
            """
        ).fetchall()

        return [
            {key: row[key] for key in row.keys()}
            for row in rows
        ]
