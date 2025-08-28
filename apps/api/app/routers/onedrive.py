# -*- coding: utf-8 -*-
from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import RedirectResponse, JSONResponse
import os, time, json
import httpx
import msal
from sqlalchemy.orm import Session
from app.db import get_db
from app.services.oauth_tokens import save_oauth_token, get_oauth_token, needs_refresh
from app.services.session import get_or_create_current_user

router = APIRouter()

# DEV single-user token cache
_OD_CACHE = {"token": None, "expiry": 0}

# Config via env
MS_CLIENT_ID = os.getenv("MS_CLIENT_ID", "")
MS_CLIENT_SECRET = os.getenv("MS_CLIENT_SECRET", "")
MS_TENANT = os.getenv("MS_TENANT", "common")
MS_REDIRECT_URI = os.getenv("MS_REDIRECT_URI", "http://127.0.0.1:8000/api/integrations/onedrive/callback")

# Request offline_access to obtain refresh tokens; Files.Read covers user drive.
# Files.Read.All can be added if you need org-wide or shared items access (requires admin consent).
SCOPES = ["offline_access", "Files.Read"]
AUTHORITY = f"https://login.microsoftonline.com/{MS_TENANT}"


@router.get("/auth")
def start_auth(request: Request, db: Session = Depends(get_db)):
    user = get_or_create_current_user(db, request)
    if not MS_CLIENT_ID or not MS_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="OneDrive OAuth not configured")
    app = msal.ConfidentialClientApplication(
        MS_CLIENT_ID, authority=AUTHORITY, client_credential=MS_CLIENT_SECRET
    )
    auth_url = app.get_authorization_request_url(SCOPES, redirect_uri=MS_REDIRECT_URI)
    resp = RedirectResponse(auth_url)
    resp.set_cookie("ra_uid", str(user.id), httponly=False)
    return resp


@router.get("/callback")
def callback(request: Request, db: Session = Depends(get_db)):
    user = get_or_create_current_user(db, request)
    code = request.query_params.get("code")
    if not code:
        raise HTTPException(status_code=400, detail="Missing code")
    app = msal.ConfidentialClientApplication(
        MS_CLIENT_ID, authority=AUTHORITY, client_credential=MS_CLIENT_SECRET
    )
    token = app.acquire_token_by_authorization_code(code, scopes=SCOPES, redirect_uri=MS_REDIRECT_URI)
    if "access_token" not in token:
        raise HTTPException(status_code=400, detail=str(token))
    _OD_CACHE[str(user.id)] = token
    _OD_CACHE["expiry"] = time.time() + token.get("expires_in", 3600)
    save_oauth_token(db, provider="onedrive", subject=None, token=token, user_id=user.id)

    web_url = os.getenv("WEB_APP_URL", "http://127.0.0.1:5173")
    return RedirectResponse(f"{web_url}#onedrive=connected")


def _get_token(db: Session, request: Request) -> str:
    user = get_or_create_current_user(db, request)
    cache_key = str(user.id)
    tok = _OD_CACHE.get(cache_key)
    if not tok:
        stored = get_oauth_token(db, "onedrive", user_id=user.id)
        if not stored:
            raise HTTPException(status_code=401, detail="Not authenticated with OneDrive")
        _OD_CACHE[cache_key] = stored
        tok = stored
    # refresh if needed
    if needs_refresh(tok) and tok.get("refresh_token"):
        app = msal.ConfidentialClientApplication(
            MS_CLIENT_ID, authority=AUTHORITY, client_credential=MS_CLIENT_SECRET
        )
        refreshed = app.acquire_token_by_refresh_token(tok["refresh_token"], scopes=SCOPES)
        if "access_token" in refreshed:
            tok = refreshed
            _OD_CACHE[cache_key] = tok
            save_oauth_token(db, provider="onedrive", subject=None, token=tok, user_id=user.id)
    return tok["access_token"]


GRAPH_BASE = "https://graph.microsoft.com/v1.0"


@router.get("/list")
async def list_root(request: Request, q: str | None = None, db: Session = Depends(get_db)):
    token = _get_token(db, request)
    headers = {"Authorization": f"Bearer {token}"}
    # Use server-side search if a query is provided, otherwise list root children
    if q and q.strip():
        url = f"{GRAPH_BASE}/me/drive/root/search(q='{q.strip()}')"
    else:
        url = f"{GRAPH_BASE}/me/drive/root/children"
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(url, headers=headers)
        r.raise_for_status()
        data = r.json()
    items = data.get("value", [])
    # map minimal shape
    files = [
        {"id": it.get("id"), "name": it.get("name"), "mimeType": it.get("file", {}).get("mimeType", "folder"), "size": it.get("size")}
        for it in items
    ]
    return {"files": files}


@router.post("/import")
async def import_item(request: Request, id: str, db: Session = Depends(get_db)):
    token = _get_token(db, request)
    headers = {"Authorization": f"Bearer {token}"}
    url = f"{GRAPH_BASE}/me/drive/items/{id}/content"
    async with httpx.AsyncClient(timeout=None) as client:
        r = await client.get(url, headers=headers)
        if r.status_code >= 400:
            raise HTTPException(status_code=r.status_code, detail=r.text)
        data = r.content
    os.makedirs("uploads", exist_ok=True)
    # fetch name
    meta_url = f"{GRAPH_BASE}/me/drive/items/{id}"
    async with httpx.AsyncClient(timeout=30) as client:
        mr = await client.get(meta_url, headers=headers)
        mr.raise_for_status()
        name = mr.json().get("name", id)
    path = os.path.join("uploads", name)
    with open(path, "wb") as f:
        f.write(data)
    return {"ok": True, "name": name}
