# -*- coding: utf-8 -*-
import os
from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, RedirectResponse
from starlette.staticfiles import StaticFiles
from app.routers import chat, docs, conversations, agenda, gdrive, onedrive, humdata
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
# Also mount chat under /api/chat to match frontend client
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(docs.router, prefix="/docs", tags=["docs"])
# Also mount docs under /api/docs to match frontend paths
app.include_router(docs.router, prefix="/api/docs", tags=["docs"])
app.include_router(conversations.router, prefix="/api", tags=["conversations"])
app.include_router(agenda.router, prefix="/api/agenda", tags=["agenda"])
app.include_router(gdrive.router, prefix="/api/integrations/google", tags=["integrations:google"])
app.include_router(onedrive.router, prefix="/api/integrations/onedrive", tags=["integrations:onedrive"])
app.include_router(humdata.router, prefix="/api", tags=["humdata"])


router = APIRouter()


@app.on_event("startup")
def on_startup():
    """Initialize database tables on startup (safe if already created)."""
    ensure_database_and_extensions()
    init_db()

# Serve static files if present (Docker copies web dist into ./static)
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    """Serve favicon from /static if available, otherwise return 204."""
    path = os.path.join("static", "favicon.ico")
    if os.path.exists(path):
        return RedirectResponse(url="/static/favicon.ico")
    return Response(status_code=204)


@router.get("/health")
def check_health() -> dict:
    """
    Endpoint to check the health of the API.

    Returns:
        dict: A dictionary containing a boolean value indicating the health status.
    """
    return {"ok": True}


app.include_router(router)
