"""Temporary script: send the real school document batch by Gmail."""

from config.settings import DOCUMENTS_PATH, EXCEL_PATH, GMAIL_CREDENTIALS_PATH, GMAIL_TOKEN_PATH
from database.database import insert_email_log, upsert_students
from services.document_matcher import find_student_document
from services.email_preview import build_preview
from services.email_sender import get_gmail_service, send_email
from services.student_import import load_students

SENDER = "provas@aetsm.pt"
SUBJECT = "Resultados das provas ModA 2026"

records = load_students(EXCEL_PATH)
upsert_students(
    [
        {
            "student_id": record["student_id"],
            "school": record["school"],
            "email": record["email"],
        }
        for record in records
    ]
)

service = get_gmail_service(GMAIL_CREDENTIALS_PATH, GMAIL_TOKEN_PATH)

previews = []
skipped = []
for record in records:
    match = find_student_document(
        DOCUMENTS_PATH,
        record["school"],
        record["student_id"],
    )
    if match.path is None:
        skipped.append(f"{record['student_id']} ({record['school']}): {match.error}")
        continue
    previews.append(
        build_preview(
            record,
            match.path,
            body_text="",
            subject=SUBJECT,
        )
    )

sent = 0
failed = []
for preview in previews:
    try:
        response = send_email(service, preview, SENDER)
        insert_email_log(
            student_number=preview.student_id,
            school=preview.school,
            recipient=preview.recipient,
            mode="production",
            status="sent",
            message_id=str(response.get("id")) if response else None,
        )
        sent += 1
        print("BATCH_SENT", preview.student_id, preview.school, preview.recipient, response.get("id"), flush=True)
    except Exception as error:
        insert_email_log(
            student_number=preview.student_id,
            school=preview.school,
            recipient=preview.recipient,
            mode="production",
            status="failed",
            error_message=str(error),
        )
        failed.append(f"{preview.recipient} ({preview.school}): {error}")
        print("BATCH_FAILED", preview.student_id, preview.school, preview.recipient, error, flush=True)

print("BATCH_SUMMARY", len(previews), "previews,", sent, "sent,", len(failed), "failed,", len(skipped), "skipped", flush=True)
for item in skipped:
    print("BATCH_SKIPPED", item, flush=True)
