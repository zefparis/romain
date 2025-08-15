# -*- coding: utf-8 -*-
from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import RedirectResponse, JSONResponse
from app.config import settings
from app.db import get_db
from sqlalchemy.orm import Session
from app.services.oauth_tokens import save_oauth_token, get_oauth_token, needs_refresh
from app.services.session import get_or_create_current_user
import os, time
from typing import Optional

# Google auth
from google.oauth2.credentials import Credentials
import json
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request as GoogleRequest

router = APIRouter()

# In dev, we keep a single-user token cache in memory
_OAUTH_CACHE = {}

GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/drive.readonly",
]

# Expect these env vars to be set
CLIENT_ID = os.getenv("GOOGLE_OAUTH_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET", "")
REDIRECT_URI = os.getenv("GOOGLE_OAUTH_REDIRECT_URI", "http://127.0.0.1:8000/api/integrations/google/callback")


def _build_flow(state: Optional[str] = None) -> Flow:
    if not CLIENT_ID or not CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="Google OAuth not configured")
    return Flow.from_client_config(
        {
            "web": {
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "redirect_uris": [REDIRECT_URI],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=GOOGLE_SCOPES,
        state=state,
    )


@router.get("/auth")
def start_auth(request: Request, db: Session = Depends(get_db)):
    # Ensure a user exists; set cookie on redirect
    user = get_or_create_current_user(db, request)
    flow = _build_flow()
    flow.redirect_uri = REDIRECT_URI
    auth_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    # store state in memory (single-user dev). In prod, tie to user session/DB.
    request.app.state.g_state = state
    resp = RedirectResponse(auth_url)
    # propagate user id cookie to front-end so it returns on callback
    resp.set_cookie("ra_uid", str(user.id), httponly=False)
    return resp


@router.get("/callback")
def oauth_callback(request: Request, db: Session = Depends(get_db)):
    user = get_or_create_current_user(db, request)
    state = getattr(request.app.state, "g_state", None)
    flow = _build_flow(state=state)
    flow.redirect_uri = REDIRECT_URI

    # Exchange code
    try:
        flow.fetch_token(authorization_response=str(request.url))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"OAuth exchange failed: {e}")

    creds = flow.credentials
    # Persist securely
    save_oauth_token(db, provider="google", subject=None, token=json.loads(creds.to_json()), user_id=user.id)
    _OAUTH_CACHE[str(user.id)] = creds.to_json()

    # Redirect back to web app (Documents tab)
    web_url = os.getenv("WEB_APP_URL", "http://127.0.0.1:5173")
    return RedirectResponse(f"{web_url}#gdrive=connected")


def _get_creds(db: Session, request: Request | None = None) -> Credentials:
    # resolve user
    if request is None:
        # may be passed explicitly in handlers
        user = None
    else:
        user = get_or_create_current_user(db, request)
    user_key = str(user.id) if user else "default"
    token_json = _OAUTH_CACHE.get(user_key)
    if not token_json:
        stored = get_oauth_token(db, "google", user_id=user.id if user else None)
        if not stored:
            raise HTTPException(status_code=401, detail="Not authenticated with Google Drive")
        token_json = json.dumps(stored)
        _OAUTH_CACHE[user_key] = token_json
    data = json.loads(token_json)
    creds = Credentials.from_authorized_user_info(data)
    # Refresh if needed and we have a refresh token
    if getattr(creds, "expired", False) and getattr(creds, "refresh_token", None):
        try:
            creds.refresh(GoogleRequest())
            # Save updated token
            _OAUTH_CACHE[user_key] = creds.to_json()
            save_oauth_token(db, provider="google", subject=None, token=json.loads(creds.to_json()), user_id=user.id if user else None)
        except Exception:
            pass
    return creds


@router.get("/list")
def list_drive_files(q: Optional[str] = None, page_token: Optional[str] = None, db: Session = Depends(get_db), request: Request = None):
    creds = _get_creds(db, request)
    service = build("drive", "v3", credentials=creds)
    resp = service.files().list(
        q=q or None,
        pageSize=25,
        pageToken=page_token or None,
        fields="nextPageToken, files(id, name, mimeType, size)"
    ).execute()
    return JSONResponse(resp)


@router.get("/download")
def download_drive_file(id: str, db: Session = Depends(get_db), request: Request = None):
    creds = _get_creds(db, request)
    service = build("drive", "v3", credentials=creds)
    try:
        request = service.files().get_media(fileId=id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

    # Stream to bytes
    from googleapiclient.http import MediaIoBaseDownload
    import io
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
    fh.seek(0)

    return JSONResponse({"ok": True, "size": len(fh.getvalue())})


@router.post("/import")
def import_drive_file(id: str, db: Session = Depends(get_db), request: Request = None):
    """Download a file from Drive and store it in local uploads directory."""
    import os, io
    from googleapiclient.http import MediaIoBaseDownload
    from fastapi.responses import FileResponse

    creds = _get_creds(db, request)
    service = build("drive", "v3", credentials=creds)
    meta = service.files().get(fileId=id, fields="id,name, mimeType").execute()

    request = service.files().get_media(fileId=id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
    fh.seek(0)

    os.makedirs("uploads", exist_ok=True)
    path = os.path.join("uploads", meta["name"])  # naive: may overwrite
    with open(path, "wb") as f:
        f.write(fh.getvalue())

    return {"ok": True, "name": meta["name"]}
