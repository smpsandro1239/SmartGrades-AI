"""Prepare individual HTML email previews; this module never sends email."""
import re
from dataclasses import dataclass
from html import escape, unescape
from pathlib import Path
from zipfile import ZipFile

@dataclass(frozen=True)
class EmailPreview:
    recipient: str
    subject: str
    html_body: str
    attachment: Path
    student_id: str
    school: str


def extract_docx_text(path: Path) -> str:
    """Extract readable plain text from a Word document."""
    with ZipFile(path) as archive:
        xml = archive.read("word/document.xml").decode("utf-8")
    text = re.sub(r"</w:p>", "\n", xml)
    text = re.sub(r"<[^>]+>", "", text)
    return unescape(text).strip()


def build_preview(
    student: dict[str, str],
    attachment: Path,
    school_logo: Path | None = None,
    body_text: str | None = None,
    subject: str = "Documento escolar do aluno",
) -> EmailPreview:
    recipient = student["email"]
    student_id = escape(student["student_id"])
    school = escape(student["school"])
    logo_html = ""
    if school_logo and school_logo.is_file():
        # Embed a local logo only at rendering time in a later UI layer; do not expose filesystem paths.
        logo_html = '<p class="logo-placeholder">Logótipo da escola</p>'
    source = body_text if body_text and body_text.strip() else extract_docx_text(attachment)
    if body_text and body_text.strip():
        content = (
            body_text
            if "<" in body_text and ">" in body_text
            else "<br>".join(escape(line) for line in body_text.replace("\r\n", "\n").split("\n"))
        )
    elif source and source.strip():
        content = escape(source)
    else:
        content = (
            "Exmo.(a) Encarregado(a) de Educação,"
            f"<br>Segue em anexo o documento relativo ao aluno com o identificador <strong>{student_id}</strong>.<br>"
            f"Escola: {school}<br>"
            f"Com os melhores cumprimentos."
        )
    body = (
        '<!doctype html><html lang="pt"><meta charset="utf-8"><body>'
        '<main style="font-family:Arial,sans-serif;max-width:640px;margin:auto">'
        f'{logo_html}<h2 style="font-size:28px;margin:0 0 16px;">{escape(subject)}</h2>'
        f'<p>{content}</p>'
        '</main></body></html>'
    )
    return EmailPreview(
        recipient,
        subject,
        body,
        attachment,
        student["student_id"],
        student["school"],
    )
