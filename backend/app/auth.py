import json
import os
import secrets
from pathlib import Path
from typing import Annotated

from fastapi import Depends, HTTPException
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request

from app.database import get_db

SCOPES = ["https://www.googleapis.com/auth/youtube"]
CLIENT_SECRET_FILE = os.getenv("GOOGLE_CLIENT_SECRET_FILE", "client_secret.json")
REDIRECT_URI = "http://localhost:8000/api/auth/callback"

# In-memory OAuth flow state (persisted between login and callback)
_pending_flow: Flow | None = None


def _get_client_secret_path() -> Path:
    p = Path(CLIENT_SECRET_FILE)
    if not p.is_absolute():
        p = Path(__file__).parent.parent / p
    return p


def create_flow(state: str | None = None) -> Flow:
    flow = Flow.from_client_secrets_file(
        str(_get_client_secret_path()),
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
        state=state,
    )
    return flow


def create_and_store_flow() -> Flow:
    """Create a new OAuth flow, store it for the callback, return it."""
    global _pending_flow
    state = secrets.token_urlsafe(32)
    _pending_flow = create_flow(state=state)
    return _pending_flow


def get_pending_flow(state: str) -> Flow:
    """Retrieve the stored flow and verify the state token. Single-use."""
    global _pending_flow
    if _pending_flow is None:
        raise HTTPException(status_code=400, detail="No pending OAuth flow")
    # Verify CSRF state
    flow_state = _pending_flow.oauth2session._state
    if not secrets.compare_digest(flow_state, state):
        _pending_flow = None
        raise HTTPException(status_code=400, detail="Invalid OAuth state (possible CSRF)")
    flow = _pending_flow
    _pending_flow = None
    return flow


async def store_credentials(creds: Credentials):
    db = await get_db()
    try:
        token_json = creds.to_json()
        await db.execute(
            "INSERT OR REPLACE INTO tokens (id, token_json) VALUES (1, ?)",
            (token_json,),
        )
        await db.commit()
    finally:
        await db.close()


async def load_credentials() -> Credentials | None:
    db = await get_db()
    try:
        cursor = await db.execute("SELECT token_json FROM tokens WHERE id = 1")
        row = await cursor.fetchone()
        if not row:
            return None

        creds = Credentials.from_authorized_user_info(json.loads(row["token_json"]), SCOPES)

        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            await store_credentials(creds)

        if not creds.valid:
            return None

        return creds
    finally:
        await db.close()


async def clear_credentials():
    db = await get_db()
    try:
        await db.execute("DELETE FROM tokens WHERE id = 1")
        await db.commit()
    finally:
        await db.close()


async def require_credentials() -> Credentials:
    """FastAPI dependency — returns valid credentials or raises 401."""
    creds = await load_credentials()
    if not creds:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return creds


# Type alias for use in route signatures
RequireCreds = Annotated[Credentials, Depends(require_credentials)]
