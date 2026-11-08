"""Prepare individual HTML email previews; this module never sends email."""
from __future__ import annotations
from dataclasses import dataclass
from html import escape
from pathlib import Path

@dataclass(frozen=True)
class EmailPreview:
    recipient: str
    subject: str
    html_body: str
    attachment: Path
    student_id: str
    school: str


def build_preview(student: dict[str, str], attachment: Path, school_logo: Path | None = None) -> EmailPreview:
    recipient = student["email"]
    student_id = escape(student["student_id"])
    school = escape(student["school"])
    logo_html = ""
    if school_logo and school_logo.is_file():
        # Embed a local logo only at rendering time in a later UI layer; do not expose filesystem paths.
        logo_html = '<p class="logo-placeholder">Logótipo da escola</p>'
    body = (
        '<!doctype html><html lang="pt"><meta charset="utf-8"><body>'
        '<main style="font-family:Arial,sans-serif;max-width:640px;margin:auto">'
        f'{logo_html}<h2>Comunicação escolar</h2>'
        f'<p>Exmo.(a) Encarregado(a) de Educação,</p>'
        f'<p>Segue em anexo o documento relativo ao aluno com o identificador <strong>{student_id}</strong>.</p>'
        f'<p>Escola: {school}</p><p>Com os melhores cumprimentos.</p>'
        '</main></body></html>'
    )
    return EmailPreview(recipient, "Documento escolar do aluno", body, attachment, student["student_id"], student["school"])
