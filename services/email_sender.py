"""Gmail API integration for sending individualized school documents."""

from __future__ import annotations

import base64
import json
from email.message import EmailMessage
from email.utils import formataddr
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import Resource, build

from config.settings import GMAIL_SENDER_NAME
from services.email_preview import EmailPreview

GMAIL_SEND_SCOPE = "https://www.googleapis.com/auth/gmail.send"
GMAIL_USER_ID = "me"

DOCX_MIME_TYPE = (
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
)


def get_gmail_credentials(
    credentials_path: str | Path,
    token_path: str | Path
) -> Credentials:
    """Load existing Gmail credentials and refresh them when necessary."""

    token_file = Path(token_path)

    if not token_file.is_file():
        raise FileNotFoundError(
            "Token Gmail não encontrado. É necessário realizar "
            "a autenticação OAuth primeiro."
        )

    token_data = json.loads(
        token_file.read_text(encoding="utf-8")
    )
    token_data.setdefault("refresh_token", None)

    credentials = Credentials.from_authorized_user_info(
        token_data,
        [GMAIL_SEND_SCOPE]
    )

    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())

        token_file.parent.mkdir(parents=True, exist_ok=True)
        token_file.write_text(
            credentials.to_json(),
            encoding="utf-8"
        )

    if not credentials.valid:
        raise RuntimeError(
            "As credenciais Gmail são inválidas. "
            "É necessário autenticar novamente."
        )

    return credentials


def get_gmail_service(
    credentials_path: str | Path,
    token_path: str | Path
) -> Resource:
    """Create an authenticated Gmail API service."""

    credentials_file = Path(credentials_path)

    if not credentials_file.is_file():
        raise FileNotFoundError(
            f"Ficheiro de credenciais Google não encontrado: "
            f"{credentials_file}"
        )

    credentials = get_gmail_credentials(
        credentials_file,
        token_path
    )

    return build(
        "gmail",
        "v1",
        credentials=credentials
    )


def build_raw_message(
    preview: EmailPreview,
    sender: str = ""
) -> str:
    """Build an individualized email with its DOCX attachment."""

    attachment_path = Path(preview.attachment)

    if not attachment_path.is_file():
        raise FileNotFoundError(
            f"Documento Word não encontrado: {attachment_path.name}"
        )

    if attachment_path.suffix.lower() != ".docx":
        raise ValueError(
            "O anexo tem de ser um documento Word com extensão .docx."
        )

    message = EmailMessage()

    if sender:
        message["From"] = formataddr(
            (GMAIL_SENDER_NAME, sender)
        )

    message["To"] = preview.recipient
    message["Subject"] = preview.subject

    message.set_content(
        preview.html_body,
        subtype="html",
        charset="utf-8"
    )

    message.add_attachment(
        attachment_path.read_bytes(),
        maintype="application",
        subtype=(
            "vnd.openxmlformats-officedocument."
            "wordprocessingml.document"
        ),
        filename=attachment_path.name
    )

    return base64.urlsafe_b64encode(
        message.as_bytes()
    ).decode("ascii")


def send_email(
    service: Resource,
    preview: EmailPreview,
    sender: str = ""
) -> dict:
    """Send one individualized email through the Gmail API."""

    raw = build_raw_message(preview, sender)

    return (
        service.users()
        .messages()
        .send(
            userId=GMAIL_USER_ID,
            body={"raw": raw}
        )
        .execute()
    )


def get_sender_address(service: Resource) -> str:
    """Do not query the Gmail profile with the gmail.send-only scope."""

    return ""
