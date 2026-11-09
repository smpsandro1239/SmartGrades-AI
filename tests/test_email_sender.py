import base64
from pathlib import Path
from unittest.mock import MagicMock

from services.email_preview import EmailPreview
from services.email_sender import build_raw_message, send_email


def _preview() -> EmailPreview:
    return EmailPreview(
        recipient="encarregado@example.com",
        subject="Documento escolar do aluno",
        html_body="<p>Exmo.(a) Encarregado(a) de Educação,</p>",
        attachment=Path("/tmp/12345.docx"),
        student_id="12345",
        school="Escola A",
    )


def test_build_raw_message_contains_headers_and_body():
    raw = build_raw_message(_preview(), "smpsandro1239@gmail.com")
    decoded = base64.urlsafe_b64decode(raw + "=" * (-len(raw) % 4)).decode("utf-8")
    assert "To: encarregado@example.com" in decoded
    assert "Subject: Documento escolar do aluno" in decoded
    assert "smpsandro1239@gmail.com" in decoded
    assert "Exmo.(a) Encarregado(a) de Educação," in decoded


def test_send_email_posts_to_gmail_api():
    service = MagicMock()
    send_mock = service.users().messages().send
    send_mock.return_value.execute.return_value = {"id": "msg-123"}
    result = send_email(service, _preview(), "smpsandro1239@gmail.com")
    assert result == {"id": "msg-123"}
    send_mock.assert_called_once()
