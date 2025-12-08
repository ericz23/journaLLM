"""
WHOOP OAuth 2.0 endpoints for authorization and token management.
"""

import secrets
from typing import Optional

import httpx
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from backend.core.config import (
    WHOOP_CLIENT_ID,
    WHOOP_CLIENT_SECRET,
    WHOOP_REDIRECT_URI,
    WHOOP_AUTH_URL,
    WHOOP_TOKEN_URL,
    WHOOP_SCOPES,
)

router = APIRouter(prefix="/api/whoop", tags=["whoop"])

# In-memory token storage (replace with database storage in production)
_token_storage: dict = {}


class TokenInfo(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    expires_in: int
    token_type: str
    scope: str


class TokenStatus(BaseModel):
    authenticated: bool
    scopes: Optional[str] = None


def _generate_state() -> str:
    """Generate a random 8-character state string for CSRF protection."""
    return secrets.token_urlsafe(6)[:8]


@router.get("/login")
async def whoop_login():
    """
    Initiates the WHOOP OAuth flow by redirecting the user to WHOOP's authorization page.
    """
    if not WHOOP_CLIENT_ID:
        raise HTTPException(
            status_code=500,
            detail="WHOOP_CLIENT_ID not configured. Please set it in your .env file."
        )

    state = _generate_state()
    _token_storage["oauth_state"] = state

    # Build authorization URL with required parameters
    auth_params = {
        "client_id": WHOOP_CLIENT_ID,
        "redirect_uri": WHOOP_REDIRECT_URI,
        "response_type": "code",
        "scope": WHOOP_SCOPES,
        "state": state,
    }

    query_string = "&".join(f"{k}={v}" for k, v in auth_params.items())
    authorization_url = f"{WHOOP_AUTH_URL}?{query_string}"

    return RedirectResponse(url=authorization_url)


@router.get("/callback")
async def whoop_callback(
    code: str = Query(..., description="Authorization code from WHOOP"),
    state: str = Query(..., description="State parameter for CSRF validation"),
):
    """
    Handles the OAuth callback from WHOOP after user authorization.
    Exchanges the authorization code for access and refresh tokens.
    """
    # Validate state to prevent CSRF attacks
    stored_state = _token_storage.get("oauth_state")
    if not stored_state or state != stored_state:
        raise HTTPException(
            status_code=400,
            detail="Invalid state parameter. Possible CSRF attack."
        )

    # Clear the used state
    _token_storage.pop("oauth_state", None)

    # Exchange authorization code for tokens
    token_data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": WHOOP_REDIRECT_URI,
        "client_id": WHOOP_CLIENT_ID,
        "client_secret": WHOOP_CLIENT_SECRET,
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            WHOOP_TOKEN_URL,
            data=token_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to exchange code for token: {response.text}"
            )

        tokens = response.json()

    # Store tokens (in production, save to database with user association)
    _token_storage["access_token"] = tokens.get("access_token")
    _token_storage["refresh_token"] = tokens.get("refresh_token")
    _token_storage["expires_in"] = tokens.get("expires_in")
    _token_storage["scope"] = tokens.get("scope")

    # Redirect to frontend with success message
    return RedirectResponse(url="/?whoop_connected=true")


@router.post("/refresh")
async def refresh_token():
    """
    Refreshes the WHOOP access token using the stored refresh token.
    """
    refresh_token = _token_storage.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=401,
            detail="No refresh token available. Please re-authenticate."
        )

    token_data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": WHOOP_CLIENT_ID,
        "client_secret": WHOOP_CLIENT_SECRET,
        "scope": "offline",
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            WHOOP_TOKEN_URL,
            data=token_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to refresh token: {response.text}"
            )

        tokens = response.json()

    # Update stored tokens
    _token_storage["access_token"] = tokens.get("access_token")
    _token_storage["refresh_token"] = tokens.get("refresh_token")
    _token_storage["expires_in"] = tokens.get("expires_in")
    _token_storage["scope"] = tokens.get("scope")

    return {"message": "Token refreshed successfully", "expires_in": tokens.get("expires_in")}


@router.get("/status", response_model=TokenStatus)
async def token_status():
    """
    Returns the current authentication status.
    """
    access_token = _token_storage.get("access_token")
    return TokenStatus(
        authenticated=bool(access_token),
        scopes=_token_storage.get("scope") if access_token else None,
    )


@router.post("/logout")
async def logout():
    """
    Clears the stored tokens (local logout).
    """
    _token_storage.clear()
    return {"message": "Logged out successfully"}


def get_access_token() -> Optional[str]:
    """
    Helper function to get the current access token for use in other modules.
    """
    return _token_storage.get("access_token")
