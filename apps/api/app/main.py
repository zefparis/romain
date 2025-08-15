# -*- coding: utf-8 -*-
import os
import time
import logging
from typing import List, Set
from fastapi import FastAPI, APIRouter, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, RedirectResponse, JSONResponse
from starlette.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import BaseModel, constr
from app.routers import chat, docs, conversations, agenda, gdrive, onedrive, humdata
from app.db import init_db, ensure_database_and_extensions

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("app")

app = FastAPI(title="Romain Assistant API", version="0.1.0")

# --- CORS (env-driven) ---
raw_origins: List[str] = []
public_frontend = (os.getenv("PUBLIC_FRONTEND_URL", "").strip() or None)
allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").strip()
if public_frontend:
    raw_origins.append(public_frontend)
if allowed_origins_env:
    raw_origins.extend([o.strip() for o in allowed_origins_env.split(",") if o.strip()])
origins: Set[str] = set(raw_origins)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(origins) if origins else ["http://localhost:5173"],
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
STATIC_DIR = os.getenv("STATIC_DIR", "static")
if os.path.isdir(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    logger.info(f"Static mounted at /static from '{STATIC_DIR}'")
else:
    logger.warning(f"Static directory '{STATIC_DIR}' not found. Skipping mount.")


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    """Serve favicon from /static if available, otherwise return 204."""
    path = os.path.join(STATIC_DIR, "favicon.ico")
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

# Additional healthz endpoint for external health checks
@app.get("/healthz")
def healthz():
    return {"status": "ok"}


# --- Simple items endpoint with pagination ---
MOCK_ITEMS = [{"id": i, "name": f"Item {i}"} for i in range(1, 101)]

@app.get("/api/items")
def list_items(limit: int = 20, offset: int = 0):
    limit = max(1, min(100, limit))
    offset = max(0, offset)
    data = MOCK_ITEMS[offset: offset + limit]
    return {
        "items": data,
        "count": len(MOCK_ITEMS),
        "limit": limit,
        "offset": offset,
    }


# --- Request logging middleware ---
class RequestLoggerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.time()
        try:
            response = await call_next(request)
            return response
        finally:
            duration_ms = int((time.time() - start) * 1000)
            logger.info({
                "method": request.method,
                "path": request.url.path,
                "status": getattr(response, 'status_code', None),
                "duration_ms": duration_ms,
            })

app.add_middleware(RequestLoggerMiddleware)


# --- Global exception handlers ---
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(Exception)
async def unhandled_exceptions(request: Request, exc: Exception):
    logger.exception("Unhandled error")
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})


app.include_router(router)

# Root endpoint: redirect to frontend if configured and different host; else /docs
@app.get("/", include_in_schema=False)
def root_index(request: Request):
    from urllib.parse import urlparse

    web_app_url = os.getenv("WEB_APP_URL", "").strip()
    public_frontend = os.getenv("PUBLIC_FRONTEND_URL", "").strip()
    target = web_app_url or public_frontend

    if target and (target.startswith("http://") or target.startswith("https://")):
        try:
            target_host = urlparse(target).netloc
            current_host = request.url.netloc
            if target_host and target_host.lower() != current_host.lower():
                return RedirectResponse(url=target, status_code=307)
        except Exception:
            pass
    return RedirectResponse(url="/docs", status_code=307)
