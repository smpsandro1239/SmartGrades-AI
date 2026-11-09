"""Gmail API integration for sending individualized school documents."""

from __future__ import annotations

import base64
from email.message import EmailMessage
from email.utils import formataddr
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import Resource, build

from services.email_preview import EmailPreview

GMAIL_SEND_SCOPE = "https://www.googleapis.com/auth/gmail.send"
GMAIL_USER_ID = "me"


def get_gmail_credentials(credentials_path: str | Path, token_path: str | Path) -> Credentials:
    credentials = Credentials.from_authorized_user_file(token_path, [GMAIL_SEND_SCOPE])
    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
    return credentials


def get_gmail_service(credentials_path: str | Path, token_path: str | Path) -> Resource:
    credentials = get_gmail_credentials(credentials_path, token_path)
    return build("gmail", "v1", credentials=credentials)


def build_raw_message(preview: EmailPreview, sender: str) -> str:
    message = EmailMessage()
    message["From"] = formataddr(("SmartGrades-AI", sender))
    message["To"] = formataddr(("", preview.recipient))
    message["Subject"] = preview.subject
    message["MIME-Version"] = "1.0"
    message.set_content(preview.html_body, subtype="html")
    return base64.urlsafe_b64encode(message.as_bytes()).decode("ascii")


def send_email(service: Resource, preview: EmailPreview, sender: str) -> dict:
    raw = build_raw_message(preview, sender)
    return service.users().messages().send(userId=GMAIL_USER_ID, body={"raw": raw}).execute()


def get_sender_address(service: Resource) -> str:
    profile = service.users().getProfile(userId=GMAIL_USER_ID).execute()
    return profile.get("emailAddress", "")
