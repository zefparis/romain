# -*- coding: utf-8 -*-
import asyncio
import httpx
from sqlalchemy.orm import Session
from datetime import datetime
from app.db import SessionLocal
from app.models import FundingRecord
import json

FTS_BASE = "https://api.hpc.tools/v1/public/fts/flow"


async def fetch_json(url: str, params=None):
    async with httpx.AsyncClient(timeout=120) as client:
        r = await client.get(url, params=params)
        r.raise_for_status()
        return r.json()


def upsert_funding(db: Session, it: dict, year: int):
    # FTS returns flows; we compose a source_id from attributes
    donor = it.get("donor", {}).get("name")
    recipient = it.get("recipient", {}).get("name")
    cluster = it.get("cluster", {}).get("name")
    country = it.get("location", {}).get("name")
    amount = it.get("amountUSD") or it.get("amount")
    currency = "USD"
    key = json.dumps({"d":donor,"r":recipient,"c":cluster,"y":year,"cty":country}, sort_keys=True)

    row = db.query(FundingRecord).filter(FundingRecord.source=="fts", FundingRecord.source_id==key).first()
    if not row:
        row = FundingRecord(source="fts", source_id=key)
        db.add(row)
    row.year = year
    row.country = country
    row.cluster = cluster
    row.donor = donor
    row.recipient = recipient
    row.amount = float(amount) if amount is not None else None
    row.currency = currency
    row.raw = json.dumps(it)


async def run(year: int | None = None):
    year = year or datetime.utcnow().year
    db = SessionLocal()
    try:
        # Basic query: top-level flows aggregated by donor/recipient/location/cluster
        params = {
            "year": year,
            "groupby": "donor,recipient,location,cluster",
            "size": 5000,
        }
        data = await fetch_json(FTS_BASE, params=params)
        for it in data.get("data", []):
            upsert_funding(db, it, year)
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(run())
