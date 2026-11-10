"""Central application settings.

Sensitive credentials and real student data must never be stored here
or committed to the repository.
"""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_DIR = PROJECT_ROOT / "runtime_data"
DATABASE_PATH = RUNTIME_DIR / "smartgrades.sqlite3"
LOG_DIR = RUNTIME_DIR / "logs"
GMAIL_CREDENTIALS_PATH = PROJECT_ROOT / "credentials.json"
GMAIL_TOKEN_PATH = PROJECT_ROOT / "token.json"
DOCUMENTS_PATH = PROJECT_ROOT / "documents"

APP_NAME = "SmartGrades-AI"
APP_VERSION = "0.1.0"
DEFAULT_EMAIL_MODE = "production"
ALLOWED_EMAIL_MODES = {"simulation", "test", "production"}
MAX_SEND_PER_RUN = 10
