import pytest
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
