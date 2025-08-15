# -*- coding: utf-8 -*-
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine.url import make_url
import psycopg
import os

from app.config import settings
from app.models import Base


def _build_sync_engine_from_url(db_url: str):
    """Return a synchronous SQLAlchemy engine from possibly async URL.

    - Converts postgresql+asyncpg -> postgresql+psycopg (or psycopg2 fallback)
    - Keeps SQLite as-is and sets proper connect args
    - Falls back to local SQLite file if driver missing
    """
    try:
        url = make_url(db_url)
    except Exception:
        # Fallback to SQLite file if URL is malformed
        return create_engine("sqlite:///./romain.db", echo=False, future=True, connect_args={"check_same_thread": False})

    driver = url.drivername or ""

    # SQLite
    if driver.startswith("sqlite"):
        return create_engine(db_url, echo=False, future=True, connect_args={"check_same_thread": False})

    # Postgres: coerce async driver to sync
    sync_url = db_url
    if "+asyncpg" in driver:
        sync_url = db_url.replace("+asyncpg", "+psycopg")

    # Try psycopg (v3)
    try:
        return create_engine(sync_url, echo=False, future=True)
    except ModuleNotFoundError:
        # Try psycopg2
        try:
            sync_url_psycopg2 = sync_url.replace("+psycopg", "+psycopg2")
            return create_engine(sync_url_psycopg2, echo=False, future=True)
        except ModuleNotFoundError:
            # Final fallback to SQLite file with a loud warning
            print("[WARN] psycopg/psycopg2 not installed. Falling back to SQLite ./romain.db")
            return create_engine("sqlite:///./romain.db", echo=False, future=True, connect_args={"check_same_thread": False})


# Create synchronous SQLAlchemy engine (compatible with current routers/services)
engine = _build_sync_engine_from_url(settings.DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """FastAPI dependency that yields a DB session and ensures proper close."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create database tables if they do not exist yet."""
    Base.metadata.create_all(bind=engine)


def ensure_database_and_extensions() -> None:
    """Ensure target PostgreSQL database exists and enable pgvector extension.

    - If the URL points to PostgreSQL, connect to the server-level 'postgres' DB
      and create the target database if missing.
    - Then connect to the target DB and CREATE EXTENSION IF NOT EXISTS vector.
    - No-op for SQLite or non-Postgres URLs.
    """
    # Production-safe: only run when explicitly enabled (local dev)
    if os.getenv("ENABLE_DB_BOOTSTRAP", "false").lower() not in {"1", "true", "yes"}:
        return
    try:
        url = make_url(settings.DATABASE_URL)
    except Exception:
        return

    if not url.drivername.startswith("postgresql"):
        return

    db_name = url.database or "postgres"
    # Server-level connection URL (connect to 'postgres' database)
    server_url = url.set(database="postgres")

    # Build psycopg connection strings
    server_dsn = str(server_url)
    target_dsn = str(url)

    try:
        # Create database if it doesn't exist
        with psycopg.connect(server_dsn, autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
                exists = cur.fetchone() is not None
                if not exists:
                    cur.execute(f'CREATE DATABASE "{db_name}"')
    except Exception as e:
        print(f"[WARN] Could not ensure database exists: {e}")

    try:
        # Enable pgvector extension in target DB (requires superuser or privileges)
        with psycopg.connect(target_dsn, autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    except Exception as e:
        print(f"[WARN] Could not enable pgvector extension: {e}")
