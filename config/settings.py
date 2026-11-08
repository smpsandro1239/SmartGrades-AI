"""Central application settings.

Sensitive credentials and real student data must never be stored here
or committed to the repository. Runtime files live in the user's local
application-data directory so they survive PyInstaller one-file extraction.
"""

import os
from pathlib import Path

APP_NAME = "SmartGrades-AI"
APP_VERSION = "0.1.0"
DEFAULT_EMAIL_MODE = "simulation"
ALLOWED_EMAIL_MODES = {"simulation", "test", "production"}

LOCAL_APP_DATA = Path(
    os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local"))
)
RUNTIME_DIR = LOCAL_APP_DATA / APP_NAME / "runtime_data"
DATABASE_PATH = RUNTIME_DIR / "smartgrades.sqlite3"
LOG_DIR = RUNTIME_DIR / "logs"

# The source root is useful for development-only resources, not writable data.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
