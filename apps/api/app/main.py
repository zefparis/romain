# -*- coding: utf-8 -*-
from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from app.routers import chat, docs, conversations, agenda
from app.db import init_db, ensure_database_and_extensions

app = FastAPI(title="Romain Assistant API", version="0.1.0")

# DEV: autorise localhost/127.0.0.1 sur n'importe quel port
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d{1,5})?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/chat", tags=["chat"])
app.include_router(docs.router, prefix="/docs", tags=["docs"])
app.include_router(conversations.router, prefix="/api/conversations", tags=["conversations"])
app.include_router(agenda.router, prefix="/api/agenda", tags=["agenda"])


router = APIRouter()


@app.on_event("startup")
def on_startup():
    """Initialize database tables on startup (safe if already created)."""
    ensure_database_and_extensions()
    init_db()


@router.get("/health")
def check_health() -> dict:
    """
    Endpoint to check the health of the API.

    Returns:
        dict: A dictionary containing a boolean value indicating the health status.
    """
    return {"ok": True}


app.include_router(router)
