import pytest

from database.database import (
    get_connection,
    initialize_database,
    insert_email_log,
    list_email_logs,
    upsert_students,
)


def test_initialize_database_creates_expected_tables(tmp_path):
    database_path = tmp_path / "test.sqlite3"
    initialize_database(database_path)

    with get_connection(database_path) as connection:
        rows = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()

    table_names = {row["name"] for row in rows}

    assert {"students", "grades", "email_logs"}.issubset(table_names)


def test_same_student_number_is_allowed_in_different_schools(tmp_path):
    database_path = tmp_path / "students.sqlite3"
    initialize_database(database_path)

    records = [
        {
            "student_id": "123",
            "school": "Escola A",
            "email": "a@example.com",
        },
        {
            "student_id": "123",
            "school": "Escola B",
            "email": "b@example.com",
        },
    ]

    assert upsert_students(records, database_path) == 2

    with get_connection(database_path) as connection:
        count = connection.execute(
            "SELECT COUNT(*) FROM students WHERE student_number = ?",
            ("123",),
        ).fetchone()[0]

    assert count == 2


def test_upsert_updates_guardian_email_without_duplicate(tmp_path):
    database_path = tmp_path / "upsert.sqlite3"
    initialize_database(database_path)

    first_record = {
        "student_id": "123",
        "school": "Escola A",
        "email": "a@example.com",
    }

    updated_record = {
        "student_id": "123",
        "school": "Escola A",
        "email": "novo@example.com",
    }

    upsert_students([first_record], database_path)
    upsert_students([updated_record], database_path)

    with get_connection(database_path) as connection:
        rows = connection.execute(
            "SELECT * FROM students"
        ).fetchall()

    assert len(rows) == 1
    assert rows[0]["guardian_email"] == "novo@example.com"


def test_insert_and_list_email_logs(tmp_path):
    database_path = tmp_path / "logs.sqlite3"
    initialize_database(database_path)

    upsert_students(
        [
            {
                "student_id": "12345",
                "school": "Escola A",
                "email": "encarregado@example.com",
            }
        ],
        database_path,
    )

    insert_email_log(
        database_path=database_path,
        student_number="12345",
        school="Escola A",
        recipient="encarregado@example.com",
        mode="simulation",
        status="simulated",
        message_id="msg-test-123",
    )

    logs = list_email_logs(database_path)

    assert len(logs) == 1
    assert logs[0]["student_number"] == "12345"
    assert logs[0]["school"] == "Escola A"
    assert logs[0]["recipient"] == "encarregado@example.com"
    assert logs[0]["mode"] == "simulation"
    assert logs[0]["status"] == "simulated"
    assert logs[0]["message_id"] == "msg-test-123"


def test_email_log_rejects_unknown_student(tmp_path):
    database_path = tmp_path / "unknown.sqlite3"
    initialize_database(database_path)

    with pytest.raises(ValueError, match="não existe"):
        insert_email_log(
            database_path=database_path,
            student_number="999",
            school="Escola A",
            recipient="encarregado@example.com",
        )


def test_upsert_rejects_empty_required_fields(tmp_path):
    database_path = tmp_path / "invalid.sqlite3"
    initialize_database(database_path)

    with pytest.raises(ValueError):
        upsert_students(
            [
                {
                    "student_id": "123",
                    "school": "",
                    "email": "a@example.com",
                }
            ],
            database_path,
        )
