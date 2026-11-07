"""Tests for the SQLite database layer."""

import sqlite3

from database.database import get_connection, initialize_database


def test_initialize_database_creates_expected_tables(tmp_path):
    database_path = tmp_path / "test.sqlite3"
    initialize_database(database_path)

    with get_connection(database_path) as connection:
        rows = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()

    table_names = {row["name"] for row in rows}
    assert {"students", "grades", "email_logs"}.issubset(table_names)


def test_student_number_must_be_unique(tmp_path):
    database_path = tmp_path / "unique.sqlite3"
    initialize_database(database_path)

    with get_connection(database_path) as connection:
        connection.execute(
            """
            INSERT INTO students (student_number, full_name)
            VALUES (?, ?)
            """,
            ("A001", "Aluno de teste"),
        )

        try:
            connection.execute(
                """
                INSERT INTO students (student_number, full_name)
                VALUES (?, ?)
                """,
                ("A001", "Outro aluno"),
            )
        except sqlite3.IntegrityError:
            pass
        else:
            raise AssertionError("A duplicação do número de aluno devia ser impedida.")
