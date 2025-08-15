# -*- coding: utf-8 -*-
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict
from sqlalchemy.orm import Session
from cryptography.fernet import Fernet, InvalidToken
import json

from app.config import settings
from app.models import OAuthToken


def _fernet() -> Optional[Fernet]:
    key = settings.OAUTH_ENCRYPTION_KEY.strip()
    if not key:
        return None
    try:
        return Fernet(key)
    except Exception:
        return None


def _enc(s: str) -> str:
    f = _fernet()
    if not f:
        return s
    return f.encrypt(s.encode("utf-8")).decode("utf-8")


def _dec(s: Optional[str]) -> Optional[str]:
    if s is None:
        return None
    f = _fernet()
    if not f:
        return s
    try:
        return f.decrypt(s.encode("utf-8")).decode("utf-8")
    except InvalidToken:
        # if key changed, fallback to raw
        return s


def save_oauth_token(db: Session, provider: str, subject: str | None, token: dict, user_id=None) -> OAuthToken:
    """Upsert OAuth token for provider (single-user for now)."""
    # Normalize
    access_token = token.get("access_token") or token.get("token")
    refresh_token = token.get("refresh_token")
    token_type = token.get("token_type")
    scope = token.get("scope") if isinstance(token.get("scope"), str) else " ".join(token.get("scope", []))
    expires_at: Optional[datetime] = None
    if token.get("expires_at"):
        # already absolute
        if isinstance(token["expires_at"], (int, float)):
            expires_at = datetime.fromtimestamp(token["expires_at"], tz=timezone.utc)
        else:
            # try parse RFC3339 or str
            try:
                expires_at = datetime.fromisoformat(token["expires_at"])  # may include tz
            except Exception:
                expires_at = None
    elif token.get("expires_in"):
        expires_at = datetime.now(tz=timezone.utc) + timedelta(seconds=int(token["expires_in"]))

    raw_json = json.dumps(token)

    q = db.query(OAuthToken).filter(OAuthToken.provider == provider)
    if user_id:
        q = q.filter(OAuthToken.user_id == user_id)
    row = q.order_by(OAuthToken.created_at.desc()).first()
    if not row:
        row = OAuthToken(provider=provider, user_id=user_id)
        db.add(row)
    row.subject = subject
    row.access_token = _enc(access_token or "")
    row.refresh_token = _enc(refresh_token) if refresh_token else None
    row.token_type = token_type
    row.scope = scope
    row.expires_at = expires_at
    row.raw = _enc(raw_json)
    db.commit()
    db.refresh(row)
    return row


def get_oauth_token(db: Session, provider: str, user_id=None) -> dict | None:
    q = db.query(OAuthToken).filter(OAuthToken.provider == provider)
    if user_id:
        q = q.filter(OAuthToken.user_id == user_id)
    row = q.order_by(OAuthToken.created_at.desc()).first()
    if not row:
        return None
    raw = _dec(row.raw) if row.raw else None
    try:
        return json.loads(raw) if raw else None
    except Exception:
        # reconstruct minimal payload
        return {
            "access_token": _dec(row.access_token),
            "refresh_token": _dec(row.refresh_token) if row.refresh_token else None,
            "token_type": row.token_type,
            "scope": row.scope,
            "expires_at": row.expires_at.timestamp() if row.expires_at else None,
        }


def needs_refresh(token: Dict, *, skew_seconds: int = 120) -> bool:
    now = datetime.now(tz=timezone.utc)
    # support both absolute and lib-specific fields
    if token.get("expires_at"):
        ts = token["expires_at"]
        if isinstance(ts, (int, float)):
            exp = datetime.fromtimestamp(ts, tz=timezone.utc)
        else:
            try:
                exp = datetime.fromisoformat(ts)
            except Exception:
                return False
        return exp - now < timedelta(seconds=skew_seconds)
    if token.get("expiry"):
        try:
            exp = datetime.fromisoformat(token["expiry"])  # google creds str
            return exp.replace(tzinfo=timezone.utc) - now < timedelta(seconds=skew_seconds)
        except Exception:
            return False
    if token.get("expires_in"):
        # if we only have relative expires_in from last fetch, assume refresh needed soon
        return True
    return False
