# -*- coding: utf-8 -*-
from pydantic_settings import BaseSettings
class Settings(BaseSettings):
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4-turbo"
    EMBED_MODEL: str = "text-embedding-3-large"
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/romain"
    REDIS_URL: str = "redis://localhost:6379/0"
    CORS_ORIGINS: str = "http://localhost:5173"
    OAUTH_ENCRYPTION_KEY: str = ""  # Fernet key base64, optional in dev
    ENABLE_DB_BOOTSTRAP: bool = False
    # --- Frontend URLs ---
    WEB_APP_URL: str = "http://127.0.0.1:5173"
    PUBLIC_FRONTEND_URL: str = ""
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    # --- Microsoft / OneDrive OAuth ---
    MS_CLIENT_ID: str = ""
    MS_CLIENT_SECRET: str = ""
    MS_TENANT: str = "common"
    MS_REDIRECT_URI: str = "http://127.0.0.1:8000/api/integrations/onedrive/callback"
settings = Settings(_env_file=".env", _env_file_encoding="utf-8")
