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
settings = Settings(_env_file=".env", _env_file_encoding="utf-8")
