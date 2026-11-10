"""Central application settings.

Sensitive credentials and real student data must never be stored
inside the Git repository.
"""

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# External folders
USER_DATA_ROOT = PROJECT_ROOT.parent
PRIVATE_ROOT = USER_DATA_ROOT / "SmartGrades-Private"
PRIVATE_CREDENTIALS_DIR = PRIVATE_ROOT / "credentials"

# Application data outside the Git repository
LOCAL_APP_DATA = Path(
    os.environ.get(
        "LOCALAPPDATA",
        str(Path.home() / "AppData" / "Local")
    )
)

RUNTIME_DIR = LOCAL_APP_DATA / "SmartGrades-AI"
DATABASE_PATH = RUNTIME_DIR / "smartgrades.sqlite3"
LOG_DIR = RUNTIME_DIR / "logs"

# Google OAuth credentials
_credentials_candidates = sorted(
    PRIVATE_CREDENTIALS_DIR.glob("client_secret*.json"),
    key=lambda path: path.stat().st_mtime,
)

GMAIL_CREDENTIALS_PATH = (
    _credentials_candidates[-1]
    if _credentials_candidates
    else PRIVATE_CREDENTIALS_DIR / "client_secret.json"
)

# OAuth token must remain outside the repository
GMAIL_TOKEN_DIR = RUNTIME_DIR / "secrets"
GMAIL_TOKEN_PATH = GMAIL_TOKEN_DIR / "token.json"

# Student data
EXCEL_PATH = USER_DATA_ROOT / "Livro1.xlsx"
DOCUMENTS_PATH = USER_DATA_ROOT

APP_NAME = "SmartGrades-AI"
APP_VERSION = "0.1.0"

# Safe default: never send real emails automatically
DEFAULT_EMAIL_MODE = "production"
ALLOWED_EMAIL_MODES = {"simulation", "test", "production"}

MAX_SEND_PER_RUN = 250
