from __future__ import annotations
import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from sqlalchemy import create_engine
from sqlalchemy.engine.url import make_url
from alembic import context

# This is the Alembic Config object, which provides access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Add app to path
import sys
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
APPS_API_DIR = os.path.abspath(os.path.join(BASE_DIR))
PROJECT_ROOT = os.path.abspath(os.path.join(APPS_API_DIR, '..', '..'))
sys.path.append(os.path.join(PROJECT_ROOT, 'apps', 'api'))

from app.models import Base  # noqa: E402
from app.config import settings  # noqa: E402

# Ensure sync URL for Alembic (convert asyncpg to psycopg if needed)
url = settings.DATABASE_URL
try:
    parsed = make_url(url)
    driver = parsed.drivername or ''
    if '+asyncpg' in driver:
        url = url.replace('+asyncpg', '+psycopg')
except Exception:
    pass

config.set_main_option('sqlalchemy.url', url)

target_metadata = Base.metadata

def run_migrations_offline() -> None:
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True, dialect_opts={"paramstyle": "named"})
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    connectable = create_engine(url, poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
