# -*- coding: utf-8 -*-
from __future__ import annotations
import uuid
from sqlalchemy.orm import Session
from fastapi import Request
from app.models import User

COOKIE_NAME = "ra_uid"


def get_current_user(db: Session, request: Request) -> User | None:
    """Return current user from cookie, or None if absent/invalid."""
    uid = request.cookies.get(COOKIE_NAME)
    if not uid:
        return None
    try:
        return db.query(User).filter(User.id == uuid.UUID(uid)).first()
    except Exception:
        return None


def get_or_create_current_user(db: Session, request: Request) -> User:
    """Resolve a current user; create one if none exists (used during /auth)."""
    user = get_current_user(db, request)
    if user:
        return user
    user = User()
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
