"""Tests for the SQLite database layer."""

import sqlite3

from database.database import get_connection, initialize_database


def test_initialize_database_creates_expected_tables(tmp_path):
    database_path = tmp_path / "test.sqlite3"

    initialize_database.__globals__["get_connection"] = lambda: get_connection(database_path)
    try:
        initialize_database()
    finally:
        from config.settings import DATABASE_PATH
        initialize_database.__globals__["get_connection"] = lambda: get_connection(DATABASE_PATH)

    with get_connection(database_path) as connection:
        rows = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()

    table_names = {row["name"] for row in rows}
    assert {"students", "grades", "email_logs"}.issubset(table_names)


def test_student_number_must_be_unique(tmp_path):
    database_path = tmp_path / "unique.sqlite3"
    with get_connection(database_path) as connection:
        connection.execute(
            "CREATE TABLE students (id INTEGER PRIMARY KEY, student_number TEXT UNIQUE)"
        )
        connection.execute(
            "INSERT INTO students (student_number) VALUES (?)", ("A001",)
        )
        try:
            connection.execute(
                "INSERT INTO students (student_number) VALUES (?)", ("A001",)
            )
        except sqlite3.IntegrityError:
            pass
        else:
            raise AssertionError("A duplicação do número de aluno devia ser impedida.")
