"""Resolve each student's DOCX attachment inside the matching school folder."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DocumentMatch:
    student_id: str
    school: str
    path: Path | None
    error: str | None = None


def find_student_document(documents_root: str | Path, school: str, student_id: str) -> DocumentMatch:
    """Find exactly '<student_id>.docx' under '<root>/<school>/'.

    School and ID are treated as single path components to prevent traversal.
    Ambiguous case-insensitive matches are rejected rather than guessed.
    """
    root = Path(documents_root).expanduser().resolve()
    if not school.strip() or school in {".", ".."} or Path(school).name != school:
        return DocumentMatch(student_id, school, None, "Nome de escola inválido.")
    if not student_id.strip() or student_id in {".", ".."} or Path(student_id).name != student_id:
        return DocumentMatch(student_id, school, None, "ID de aluno inválido.")

    school_dir = (root / school).resolve()
    if root not in school_dir.parents:
        return DocumentMatch(student_id, school, None, "Caminho da escola inválido.")
    if not school_dir.is_dir():
        return DocumentMatch(student_id, school, None, "Pasta da escola não encontrada.")

    expected = f"{student_id}.docx"
    matches = [p for p in school_dir.iterdir() if p.is_file() and p.name.casefold() == expected.casefold()]
    if len(matches) == 0:
        return DocumentMatch(student_id, school, None, f"Documento {expected} não encontrado.")
    if len(matches) > 1:
        return DocumentMatch(student_id, school, None, f"Existem vários documentos correspondentes a {expected}.")
    resolved = matches[0].resolve()
    if school_dir not in resolved.parents or resolved.suffix.lower() != ".docx":
        return DocumentMatch(student_id, school, None, "Anexo fora da pasta autorizada.")
    return DocumentMatch(student_id, school, resolved)
