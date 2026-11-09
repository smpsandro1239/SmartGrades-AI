"""Tests for the SQLite database layer."""

import sqlite3

from database.database import get_connection, initialize_database, insert_email_log, list_email_logs


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


def test_insert_and_list_email_logs(tmp_path):
    database_path = tmp_path / "logs.sqlite3"
    initialize_database(database_path)

    with get_connection(database_path) as connection:
        connection.execute(
            "INSERT INTO students (student_number, full_name) VALUES (?, ?)",
            ("12345", "Aluno de teste"),
        )

    insert_email_log(database_path, "12345", "encarregado@example.com", "simulation", "simulated")
    logs = list_email_logs(database_path)

    assert len(logs) == 1
    assert logs[0]["recipient"] == "encarregado@example.com"
    assert logs[0]["mode"] == "simulation"
    assert logs[0]["status"] == "simulated"
