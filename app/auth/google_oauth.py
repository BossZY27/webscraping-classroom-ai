"""Google OAuth 2.0 using the Web Application (redirect) flow.

The browser is sent to Google's consent screen and Google redirects back to
``/api/auth/callback``.  Nothing here blocks a server worker, so the UI stays
responsive while the user signs in.
"""
import json
import logging
import os
import threading
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urlparse

from google.auth.exceptions import RefreshError, TransportError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow

from app.config import settings

logger = logging.getLogger(__name__)

# Google routinely grants a superset of the requested scopes; without this
# oauthlib rejects the token exchange with "Scope has changed".
os.environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "1"

# If modifying these scopes, delete credentials/token.json and sign in again.
SCOPES = [
    'https://www.googleapis.com/auth/classroom.courses.readonly',
    'https://www.googleapis.com/auth/classroom.coursework.me.readonly',
    'https://www.googleapis.com/auth/classroom.announcements.readonly',
    'https://www.googleapis.com/auth/drive.readonly'
]

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CREDENTIALS_DIR = PROJECT_ROOT / "credentials"
TOKEN_FILE = CREDENTIALS_DIR / "token.json"
CLIENT_SECRET_FILE = CREDENTIALS_DIR / "client_secret.json"

DEFAULT_REDIRECT_PATH = "/api/auth/callback"
STATE_TTL_SECONDS = 600
LOOPBACK_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})


class OAuthError(RuntimeError):
    """Base class for every failure in the sign-in flow."""


class OAuthConfigError(OAuthError):
    """client_secret.json is missing or malformed."""


class OAuthStateError(OAuthError):
    """The callback carried a state value we did not hand out."""


class NotAuthenticatedError(OAuthError):
    """No usable Google credentials are stored yet."""


# Pending logins: state -> {"code_verifier": str, "created_at": float}.
# The PKCE verifier is generated while building the authorization URL and has
# to survive until Google redirects the user back to the callback.
_pending_lock = threading.Lock()
_pending_states: Dict[str, Dict[str, Any]] = {}

_creds_lock = threading.Lock()
_cached_creds: Optional[Credentials] = None
_creds_version = 0


def get_redirect_uri() -> str:
    """The callback URL Google sends the user back to.

    This exact value must be registered on the OAuth client in Google Cloud
    Console (Credentials > OAuth 2.0 Client IDs > Authorized redirect URIs).
    """
    configured = (settings.OAUTH_REDIRECT_URI or "").strip()
    if configured:
        return configured

    host = settings.HOST
    if host in ("0.0.0.0", "::", ""):
        host = "localhost"
    return f"http://{host}:{settings.PORT}{DEFAULT_REDIRECT_PATH}"


def _enable_insecure_transport_for_loopback(redirect_uri: str) -> None:
    """oauthlib refuses plain http, which Google's loopback redirect requires."""
    parsed = urlparse(redirect_uri)
    if parsed.scheme == "http" and (parsed.hostname or "") in LOOPBACK_HOSTS:
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"


def _load_client_config() -> Tuple[Dict[str, Any], str]:
    """Read client_secret.json and report whether it is a web or desktop client."""
    if not CLIENT_SECRET_FILE.exists():
        raise OAuthConfigError(
            f"Missing {CLIENT_SECRET_FILE}. Download the OAuth client JSON from "
            "Google Cloud Console and save it there."
        )

    try:
        config = json.loads(CLIENT_SECRET_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise OAuthConfigError(f"Could not read {CLIENT_SECRET_FILE}: {exc}") from exc

    for client_type in ("web", "installed"):
        if client_type in config:
            return config, client_type

    raise OAuthConfigError(
        "client_secret.json must contain a 'web' or 'installed' client entry."
    )


def _build_flow(state: Optional[str] = None) -> Flow:
    config, _ = _load_client_config()
    redirect_uri = get_redirect_uri()
    _enable_insecure_transport_for_loopback(redirect_uri)
    return Flow.from_client_config(
        config, scopes=SCOPES, state=state, redirect_uri=redirect_uri
    )


def _purge_expired_states(now: float) -> None:
    """Drop abandoned logins. The caller must hold _pending_lock."""
    stale = [s for s, entry in _pending_states.items()
             if now - entry["created_at"] > STATE_TTL_SECONDS]
    for state in stale:
        del _pending_states[state]


def create_authorization_url() -> str:
    """Build the Google consent-screen URL and remember the pending login."""
    flow = _build_flow()
    auth_url, state = flow.authorization_url(
        access_type="offline",  # ask for a refresh token...
        prompt="consent",       # ...even when this account consented before
    )

    now = time.time()
    with _pending_lock:
        _purge_expired_states(now)
        _pending_states[state] = {
            "code_verifier": flow.code_verifier,
            "created_at": now,
        }

    return auth_url


def _consume_state(state: str) -> Dict[str, Any]:
    now = time.time()
    with _pending_lock:
        _purge_expired_states(now)
        entry = _pending_states.pop(state, None)

    if entry is None:
        raise OAuthStateError(
            "This login link has expired or was not started here. "
            "Please click Authorize Access again."
        )
    return entry


def finish_login(code: str, state: str) -> Credentials:
    """Exchange the authorization code from the callback for a token."""
    entry = _consume_state(state)

    flow = _build_flow(state=state)
    # PKCE: reuse the verifier that produced the challenge in the auth URL.
    flow.code_verifier = entry["code_verifier"]
    flow.fetch_token(code=code)

    creds = flow.credentials
    _save_token(creds)
    _bump_credentials_version()
    logger.info("Google sign-in completed; token saved to %s", TOKEN_FILE)
    return creds


def _save_token(creds: Credentials) -> None:
    global _cached_creds
    CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)
    TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")
    with _creds_lock:
        _cached_creds = creds


def _bump_credentials_version() -> None:
    """Signal that a different account (or none) is now signed in."""
    global _creds_version
    with _creds_lock:
        _creds_version += 1


def credentials_version() -> int:
    """Callers that cache a Google API client rebuild it when this changes."""
    with _creds_lock:
        return _creds_version


def _load_stored_credentials() -> Optional[Credentials]:
    if not TOKEN_FILE.exists():
        return None
    try:
        return Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    except (OSError, ValueError) as exc:
        logger.warning("Ignoring unreadable token file %s: %s", TOKEN_FILE, exc)
        return None


def get_credentials() -> Credentials:
    """Return stored credentials, refreshing them when they have expired.

    Never opens a browser and never blocks: callers get NotAuthenticatedError
    when the user still has to go through /api/auth/login.
    """
    with _creds_lock:
        cached = _cached_creds
    if cached and cached.valid:
        return cached

    creds = _load_stored_credentials()
    if creds is None:
        raise NotAuthenticatedError(
            "Not signed in with Google. Open the app and click Authorize Access."
        )

    if creds.valid:
        _save_token(creds)
        return creds

    if creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
        except (RefreshError, TransportError, Exception) as exc:
            raise NotAuthenticatedError(
                f"Google session expired or network error ({exc}). "
                "Please sign in again."
            ) from exc
        _save_token(creds)
        return creds

    raise NotAuthenticatedError(
        "Stored Google token is not usable. Please sign in again."
    )


def logout() -> None:
    """Forget the current Google session."""
    global _cached_creds
    with _creds_lock:
        _cached_creds = None
    TOKEN_FILE.unlink(missing_ok=True)
    with _pending_lock:
        _pending_states.clear()
    _bump_credentials_version()


def get_auth_status() -> Dict[str, Any]:
    status: Dict[str, Any] = {
        "authenticated": False,
        "has_credentials": CLIENT_SECRET_FILE.exists(),
        "redirect_uri": get_redirect_uri(),
        "client_type": None,
        "error": None,
    }

    try:
        _, status["client_type"] = _load_client_config()
    except OAuthConfigError as exc:
        status["error"] = str(exc)
        return status

    # Never signed in yet is a normal state, not an error worth showing.
    if not TOKEN_FILE.exists():
        return status

    try:
        get_credentials()
        status["authenticated"] = True
    except (NotAuthenticatedError, OAuthError, Exception) as exc:
        status["authenticated"] = False
        status["error"] = str(exc)

    return status
