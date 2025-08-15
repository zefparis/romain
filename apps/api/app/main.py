from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers import chat, docs
app = FastAPI(title="Romain Assistant API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(chat.router, prefix="/chat", tags=["chat"])
app.include_router(docs.router, prefix="/docs", tags=["docs"])
@app.get("/health")
def health():
    return {"ok": True}
