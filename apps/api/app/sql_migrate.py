# -*- coding: utf-8 -*-
import os
import sys
import time
from datetime import datetime
from typing import List
from urllib.parse import urlparse

import psycopg

from app.config import settings

HERE = os.path.abspath(os.path.dirname(__file__))
API_ROOT = os.path.abspath(os.path.join(HERE, '..'))  # /app/apps/api
MIGRATIONS_DIR = os.path.join(API_ROOT, 'migrations')

SCHEMA_MIGRATIONS_SQL = (
    """
    CREATE TABLE IF NOT EXISTS schema_migrations (
        version TEXT PRIMARY KEY,
        applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    """
)


def _list_migration_files() -> List[str]:
    if not os.path.isdir(MIGRATIONS_DIR):
        os.makedirs(MIGRATIONS_DIR, exist_ok=True)
    files = [f for f in os.listdir(MIGRATIONS_DIR) if f.lower().endswith('.sql')]
    files.sort()
    return [os.path.join(MIGRATIONS_DIR, f) for f in files]


def _load_applied_versions(conn) -> set:
    with conn.cursor() as cur:
        cur.execute("SELECT version FROM schema_migrations")
        return {row[0] for row in cur.fetchall()}


def _apply_sql_file(conn, path: str) -> None:
    with open(path, 'r', encoding='utf-8') as f:
        sql = f.read().strip()
    if not sql:
        return
    # Naive splitter: works for simple statements
    statements = [s.strip() for s in sql.split(';') if s.strip()]
    with conn.cursor() as cur:
        for stmt in statements:
            cur.execute(stmt)


def main() -> int:
    dsn = settings.DATABASE_URL
    # Only Postgres supported in this simple runner
    if not dsn.startswith('postgresql') and not dsn.startswith('postgres'):
        print('[sql_migrate] Non-Postgres DATABASE_URL detected; skipping SQL migrations.')
        return 0

    try:
        with psycopg.connect(dsn, autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute(SCHEMA_MIGRATIONS_SQL)

            applied = _load_applied_versions(conn)
            files = _list_migration_files()
            for path in files:
                version = os.path.basename(path)
                if version in applied:
                    continue
                print(f"[sql_migrate] Applying {version} ...")
                _apply_sql_file(conn, path)
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO schema_migrations(version, applied_at) VALUES (%s, %s)",
                        (version, datetime.utcnow()),
                    )
                print(f"[sql_migrate] Applied {version}")
        print('[sql_migrate] All migrations up to date.')
        return 0
    except Exception as e:
        print(f"[sql_migrate] ERROR: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
