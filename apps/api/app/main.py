# -*- coding: utf-8 -*-
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import chat, docs

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


router = APIRouter()


@router.get("/health")
def check_health() -> dict:
    """
    Endpoint to check the health of the API.

    Returns:
        dict: A dictionary containing a boolean value indicating the health status.
    """
    return {"ok": True}


app.include_router(router)
