release: alembic -c apps/api/alembic.ini upgrade head
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
