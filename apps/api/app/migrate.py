# -*- coding: utf-8 -*-
import os
import sys
from alembic.config import Config
from alembic import command

# Resolve absolute paths based on known repo layout
# This file lives in /app/apps/api/app/migrate.py in the container
HERE = os.path.abspath(os.path.dirname(__file__))
API_ROOT = os.path.abspath(os.path.join(HERE, '..'))  # /app/apps/api
ALEMBIC_INI = os.path.join(API_ROOT, 'alembic.ini')
SCRIPTS_DIR = os.path.join(API_ROOT, 'alembic')

if __name__ == '__main__':
    if not os.path.exists(ALEMBIC_INI):
        print(f"[ERROR] alembic.ini not found at {ALEMBIC_INI}", file=sys.stderr)
        sys.exit(1)
    if not os.path.isdir(SCRIPTS_DIR):
        print(f"[ERROR] alembic scripts dir not found at {SCRIPTS_DIR}", file=sys.stderr)
        sys.exit(1)

    cfg = Config(ALEMBIC_INI)
    # Force script_location to absolute directory to avoid relative path confusion
    cfg.set_main_option('script_location', SCRIPTS_DIR)

    try:
        command.upgrade(cfg, 'head')
        print('[INFO] Alembic migrations applied successfully')
    except Exception as e:
        print(f"[ERROR] Alembic migration failed: {e}", file=sys.stderr)
        sys.exit(1)
