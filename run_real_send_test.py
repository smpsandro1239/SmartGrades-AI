"""Temporary script: real Gmail send + receive verification test."""

import base64

from config.settings import DOCUMENTS_PATH, GMAIL_CREDENTIALS_PATH, GMAIL_TOKEN_PATH
from services.document_matcher import find_student_document
from services.email_preview import build_preview
from services.email_sender import get_gmail_service, send_email

service = get_gmail_service(GMAIL_CREDENTIALS_PATH, GMAIL_TOKEN_PATH)

record = {
    "email": "smpsandro1239@gmail.com",
    "student_id": "123456",
    "school": "Escola Prado",
}

match = find_student_document(DOCUMENTS_PATH, record["school"], record["student_id"])

if match.path is None:
    raise RuntimeError(f"Documento não encontrado: {match.error}")

preview = build_preview(
    record,
    match.path,
    body_text=(
        "Exmo.(a) Encarregado(a) de Educação,\n\n"
        f"Segue em anexo o documento relativo ao aluno com o identificador "
        f"<strong>{record['student_id']}</strong>.\n\n"
        f"Escola: {record['school']}\n\n"
        "Com os melhores cumprimentos."
    ),
    subject="Resultados das provas ModA 2026",
)

result = send_email(service, preview, "provas@aetsm.pt")
print("SEND_OK", result.get("id"), flush=True)

message = (
    service.users()
    .messages()
    .get(userId="me", id=str(result.get("id")))
    .execute()
)

payload = message.get("payload") or {}
parts = payload.get("parts") or [payload]

attachment_names = []
bodies = []
for part in parts:
    if part.get("filename"):
        attachment_names.append(part["filename"])
    body = part.get("body") or {}
    data = body.get("data") or ""
    if data and part.get("mimeType") in {"text/html", "text/plain"}:
        bodies.append(base64.b64decode(data).decode("utf-8", "ignore"))

print("MSG_ID", message.get("id"))
print("SUBJECT", message.get("subject"))
print("FROM", message.get("from"))
print("TO", message.get("to"))
print("ATTACHMENTS", attachment_names)
for body in bodies:
    print("BODY", body[:200].replace("\n", " "))

if not attachment_names:
    raise RuntimeError("Sem partes encontradas no e-mail recebido.")
print("REAL_SEND_TEST_OK", flush=True)
