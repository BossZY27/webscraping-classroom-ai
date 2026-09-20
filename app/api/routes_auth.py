import logging
from typing import Optional
from urllib.parse import urlencode

from fastapi import APIRouter
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from app.auth.google_oauth import (
    OAuthConfigError,
    OAuthStateError,
    create_authorization_url,
    finish_login,
    get_auth_status,
    logout,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])

APP_URL = "/static/index.html"


class AuthStatus(BaseModel):
    authenticated: bool
    has_credentials: bool
    redirect_uri: Optional[str] = None
    client_type: Optional[str] = None
    error: Optional[str] = None


def _back_to_app(**params: str) -> RedirectResponse:
    """Send the browser back to the UI, carrying the outcome of the login."""
    query = f"?{urlencode(params)}" if params else ""
    return RedirectResponse(url=f"{APP_URL}{query}", status_code=302)


@router.get("/status", response_model=AuthStatus)
def check_auth_status():
    """Check if the user is authenticated with Google."""
    return get_auth_status()


@router.get("/login")
def login():
    """Redirect the browser to Google's consent screen.

    Returns immediately: the worker is never blocked waiting for the user.
    """
    try:
        return RedirectResponse(url=create_authorization_url(), status_code=302)
    except OAuthConfigError as exc:
        logger.error("Google OAuth is not configured: %s", exc)
        return _back_to_app(auth_error=str(exc))
    except Exception as exc:
        logger.exception("Could not build the Google authorization URL")
        return _back_to_app(auth_error=f"Could not start Google login: {exc}")


@router.get("/callback")
def callback(
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
):
    """Where Google sends the user back after they approve or deny access."""
    if error:
        return _back_to_app(auth_error=f"Google returned an error: {error}")

    if not code or not state:
        return _back_to_app(
            auth_error="Google callback was missing the authorization code."
        )

    try:
        finish_login(code, state)
    except OAuthStateError as exc:
        return _back_to_app(auth_error=str(exc))
    except Exception as exc:
        logger.exception("Google token exchange failed")
        return _back_to_app(auth_error=f"Could not complete Google login: {exc}")

    return _back_to_app(auth="success")


@router.post("/logout")
def sign_out():
    """Delete the stored token so the next login starts fresh."""
    logout()
    return {"status": "success", "message": "Signed out of Google"}
