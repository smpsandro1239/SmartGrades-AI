from services.document_matcher import find_student_document


def test_finds_document_by_school_and_student_id(tmp_path):
    school = tmp_path / "Escola A"
    school.mkdir()
    document = school / "12345.docx"
    document.write_bytes(b"fake-docx-for-path-test")
    result = find_student_document(tmp_path, "Escola A", "12345")
    assert result.path == document
    assert result.error is None


def test_missing_document_is_reported(tmp_path):
    (tmp_path / "Escola A").mkdir()
    result = find_student_document(tmp_path, "Escola A", "999")
    assert result.path is None
    assert "não encontrado" in result.error


def test_rejects_path_traversal(tmp_path):
    result = find_student_document(tmp_path, "../outside", "123")
    assert result.path is None
    assert result.error
