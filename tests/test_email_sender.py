import base64
from email import policy
from email.parser import BytesParser
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from services.email_preview import EmailPreview
from services.email_sender import build_raw_message, send_email


def _preview(attachment: Path) -> EmailPreview:
    return EmailPreview(
        recipient="encarregado@example.com",
        subject="Documento escolar do aluno",
        html_body="<p>Comunicação escolar</p>",
        attachment=attachment,
        student_id="123456",
        school="Escola Prado",
    )


def _decode_message(raw: str):
    decoded = base64.urlsafe_b64decode(
        raw + "=" * (-len(raw) % 4)
    )
    return BytesParser(policy=policy.default).parsebytes(decoded)


def test_build_raw_message_contains_headers_and_body(tmp_path):
    attachment = tmp_path / "123456.docx"
    attachment.write_bytes(b"conteudo-word-ficticio")

    raw = build_raw_message(
        _preview(attachment),
        "sender@example.com"
    )

    message = _decode_message(raw)

    assert message["To"] == "encarregado@example.com"
    assert message["Subject"] == "Documento escolar do aluno"
    assert message["From"] is not None

    html_part = message.get_body(preferencelist=("html",))
    assert html_part is not None
    assert "Comunicação escolar" in html_part.get_content()


def test_build_raw_message_contains_docx_attachment(tmp_path):
    attachment_content = b"conteudo-word-ficticio"
    attachment = tmp_path / "123456.docx"
    attachment.write_bytes(attachment_content)

    raw = build_raw_message(_preview(attachment))
    message = _decode_message(raw)

    attachments = list(message.iter_attachments())

    assert len(attachments) == 1
    assert attachments[0].get_filename() == "123456.docx"
    assert attachments[0].get_content_type() == (
        "application/vnd.openxmlformats-officedocument."
        "wordprocessingml.document"
    )
    assert attachments[0].get_payload(decode=True) == attachment_content


def test_build_raw_message_rejects_missing_attachment(tmp_path):
    attachment = tmp_path / "inexistente.docx"

    with pytest.raises(FileNotFoundError):
        build_raw_message(_preview(attachment))


def test_send_email_posts_to_gmail_api(tmp_path):
    attachment = tmp_path / "123456.docx"
    attachment.write_bytes(b"conteudo-word-ficticio")

    service = MagicMock()
    send_mock = service.users().messages().send
    send_mock.return_value.execute.return_value = {"id": "msg-123"}

    result = send_email(service, _preview(attachment))

    assert result == {"id": "msg-123"}
    send_mock.assert_called_once()

    request_body = send_mock.call_args.kwargs["body"]
    message = _decode_message(request_body["raw"])

    assert message["To"] == "encarregado@example.com"
    assert len(list(message.iter_attachments())) == 1
