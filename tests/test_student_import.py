import pytest
from services.document_matcher import find_student_document
from services.student_import import load_students


def test_loads_valid_csv(tmp_path):
    file = tmp_path / "alunos.csv"
    file.write_text("E-mail,ID_Aluno,Escola\na@example.com,123,Escola A\n", encoding="utf-8")
    assert load_students(file) == [{"email": "a@example.com", "student_id": "123", "school": "Escola A"}]


def test_rejects_duplicate_ids(tmp_path):
    file = tmp_path / "alunos.csv"
    file.write_text("E-mail,ID_Aluno,Escola\na@example.com,123,Escola A\nb@example.com,123,Escola B\n", encoding="utf-8")
    with pytest.raises(ValueError, match="duplicado"):
        load_students(file)


def test_rejects_missing_columns(tmp_path):
    file = tmp_path / "alunos.csv"
    file.write_text("E-mail,Escola\na@example.com,Escola A\n", encoding="utf-8")
    with pytest.raises(ValueError, match="ID_Aluno"):
        load_students(file)


def test_dummy_flow_reports_found_and_missing_documents(tmp_path):
    file = tmp_path / "alunos_ficticios.csv"
    file.write_text(
        "E-mail,ID_Aluno,Escola\nencarregado_a@example.com,12345,Escola A\nencarregado_b@example.com,54321,Escola B\n",
        encoding="utf-8",
    )
    records = load_students(file)
    assert len(records) == 2

    (tmp_path / "Escola A").mkdir()
    (tmp_path / "Escola A" / "12345.docx").write_bytes(b"fake-docx-for-dummy-flow")

    found = find_student_document(tmp_path, records[0]["school"], records[0]["student_id"])
    missing = find_student_document(tmp_path, records[1]["school"], records[1]["student_id"])

    assert found.path is not None
    assert missing.path is None
