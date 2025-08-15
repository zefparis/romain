FROM node:20-alpine AS web
WORKDIR /app/web
COPY apps/web/package*.json ./
RUN npm ci
COPY apps/web .
RUN npm run build

FROM python:3.11-slim AS api
ENV PYTHONUNBUFFERED=1
WORKDIR /app
RUN apt-get update && apt-get install -y libpangocairo-1.0-0 libpangoft2-1.0-0 libcairo2 && rm -rf /var/lib/apt/lists/*
COPY apps/api/requirements.txt ./
RUN pip install -r requirements.txt
COPY apps/api ./apps/api
COPY --from=web /app/web/dist ./static
WORKDIR /app/apps/api
ENV PORT=8000
# Run DB migrations on startup via module to avoid PATH issues, then launch the API.
CMD ["/bin/sh", "-c", "python -m alembic -c alembic.ini upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
