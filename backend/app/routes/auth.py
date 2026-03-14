from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse

from app.auth import (
    create_and_store_flow,
    get_pending_flow,
    store_credentials,
    load_credentials,
    clear_credentials,
)
from app.models import AuthStatus
from app.youtube import get_service

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.get("/login")
async def login():
    try:
        flow = create_and_store_flow()
    except FileNotFoundError:
        raise HTTPException(
            status_code=500,
            detail="client_secret.json not found. Place it in the backend/ directory.",
        )
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    return RedirectResponse(auth_url)


@router.get("/callback")
async def callback(code: str, state: str):
    flow = get_pending_flow(state)
    flow.fetch_token(code=code)
    await store_credentials(flow.credentials)
    return RedirectResponse("http://localhost:5173")


@router.get("/status", response_model=AuthStatus)
async def status():
    creds = await load_credentials()
    if not creds:
        return AuthStatus(authenticated=False)
    try:
        service = get_service(creds)
        resp = service.channels().list(part="snippet", mine=True).execute()
        items = resp.get("items", [])
        title = items[0]["snippet"]["title"] if items else None
        return AuthStatus(authenticated=True, channel_title=title)
    except Exception:
        return AuthStatus(authenticated=False)


@router.post("/logout")
async def logout():
    await clear_credentials()
    return {"ok": True}
