# -*- coding: utf-8 -*-
import asyncio
import httpx
from sqlalchemy.orm import Session
from datetime import datetime
from app.db import SessionLocal
from app.models import Crisis, JobPosting
import json

RELIEFWEB_BASE = "https://api.reliefweb.int/v1"


async def fetch_json(url: str, params=None):
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.get(url, params=params)
        r.raise_for_status()
        return r.json()


def upsert_crisis(db: Session, item: dict):
    sid = str(item.get("id"))
    fields = item.get("fields", {})
    title = fields.get("name") or fields.get("title") or ""
    countries = fields.get("country", [])
    country = ", ".join([c.get("name") for c in countries if c.get("name")]) if countries else None
    url = fields.get("url")
    pub = fields.get("date", {}).get("created") or fields.get("date", {}).get("original")
    published_at = datetime.fromisoformat(pub.replace("Z", "+00:00")) if pub else None

    row = db.query(Crisis).filter(Crisis.source=="reliefweb", Crisis.source_id==sid).first()
    if not row:
        row = Crisis(source="reliefweb", source_id=sid)
        db.add(row)
    row.title = title
    row.country = country
    row.url = url
    row.published_at = published_at
    row.raw = json.dumps(item)


def upsert_job(db: Session, item: dict):
    sid = str(item.get("id"))
    fields = item.get("fields", {})
    title = fields.get("title") or ""
    orgs = fields.get("source", [])
    org = ", ".join([o.get("name") for o in orgs if o.get("name")]) if orgs else None
    locs = fields.get("location", [])
    location = ", ".join([l.get("name") for l in locs if l.get("name")]) if locs else None
    url = fields.get("url")
    pub = fields.get("date", {}).get("posted")
    dl = fields.get("date", {}).get("closing")
    published_at = datetime.fromisoformat(pub.replace("Z", "+00:00")) if pub else None
    deadline = datetime.fromisoformat(dl.replace("Z", "+00:00")) if dl else None

    row = db.query(JobPosting).filter(JobPosting.source=="reliefweb", JobPosting.source_id==sid).first()
    if not row:
        row = JobPosting(source="reliefweb", source_id=sid)
        db.add(row)
    row.title = title
    row.org = org
    row.location = location
    row.url = url
    row.published_at = published_at
    row.deadline = deadline
    row.raw = json.dumps(item)


async def run():
    db = SessionLocal()
    try:
        # Crises
        crises = await fetch_json(f"{RELIEFWEB_BASE}/disasters", params={"appname":"romain","profile":"full","limit":50})
        for it in crises.get("data", []):
            upsert_crisis(db, it)
        # Jobs
        jobs = await fetch_json(f"{RELIEFWEB_BASE}/jobs", params={"appname":"romain","profile":"full","limit":50})
        for it in jobs.get("data", []):
            upsert_job(db, it)
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(run())
