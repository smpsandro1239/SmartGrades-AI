"""Temporary script: run Google OAuth local server flow for Gmail send."""

import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs

import webbrowser

from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from wsgiref.simple_server import make_server

from config.settings import GMAIL_CREDENTIALS_PATH, GMAIL_TOKEN_PATH
from services.email_sender import GMAIL_SEND_SCOPE

_client_config = json.loads(
    Path(str(GMAIL_CREDENTIALS_PATH)).read_text(encoding="utf-8")
)

flow = InstalledAppFlow.from_client_config(
    _client_config,
    scopes=[
        GMAIL_SEND_SCOPE,
        "https://www.googleapis.com/auth/gmail.readonly",
    ],
)
flow.redirect_uri = "http://localhost:8080/"
flow.prompt = "consent"

captured = {"uri": ""}
received = threading.Event()


def wsgi_app(environ, start_response):
    path = environ.get("PATH_INFO", "/")
    query = environ.get("QUERY_STRING", "")
    captured["uri"] = (
        f"{environ.get('wsgi.url_scheme', 'http')}"
        f"://{environ.get('HTTP_HOST', 'localhost')}"
        f"{path}?{query}"
    )
    if path == "/" and "code" in parse_qs(query):
        received.set()
    start_response("200 OK", [("Content-Type", "text/plain; charset=utf-8")])
    return [b"ok"]


server = make_server("127.0.0.1", 8080, wsgi_app)
thread = threading.Thread(target=server.serve_forever, daemon=True)
thread.start()

authorization_url, _ = flow.authorization_url()
print("AUTH_URL=" + authorization_url, flush=True)
webbrowser.open(authorization_url)
received.wait(600)
authorization_response = captured["uri"].replace("http", "https")
token = flow.fetch_token(
    authorization_response=authorization_response
)
_client = _client_config.get("web") or _client_config.get("installed")
_expires_at = token.get("expires_at")
if isinstance(_expires_at, (int, float)):
    _expires_at = datetime.fromtimestamp(
        _expires_at, tz=timezone.utc
    ).replace(tzinfo=None)

credentials = Credentials(
    token=token["access_token"],
    refresh_token=token.get("refresh_token"),
    token_uri=token.get("token_uri", "https://oauth2.googleapis.com/token"),
    client_id=_client["client_id"],
    client_secret=_client["client_secret"],
    scopes=[
        GMAIL_SEND_SCOPE,
        "https://www.googleapis.com/auth/gmail.readonly",
    ],
    expiry=_expires_at,
)
server.shutdown()
GMAIL_TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
GMAIL_TOKEN_PATH.write_text(credentials.to_json(), encoding="utf-8")
print("TOKEN_OK", flush=True)
