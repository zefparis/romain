# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import Crisis, JobPosting, FundingRecord
from typing import Optional, List

router = APIRouter(prefix="/humdata", tags=["humdata"])


@router.get("/crises")
def list_crises(
    db: Session = Depends(get_db),
    source: Optional[str] = Query(None),
    q: Optional[str] = Query(None, description="search in title"),
    country: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    qry = db.query(Crisis).order_by(Crisis.published_at.desc().nullslast())
    if source:
        qry = qry.filter(Crisis.source == source)
    if q:
        like = f"%{q}%"
        qry = qry.filter(Crisis.title.ilike(like))
    if country:
        likec = f"%{country}%"
        qry = qry.filter(Crisis.country.ilike(likec))
    rows = qry.offset(offset).limit(limit).all()
    return [
        {
            "id": str(r.id),
            "source": r.source,
            "source_id": r.source_id,
            "title": r.title,
            "country": r.country,
            "url": r.url,
            "published_at": r.published_at,
        }
        for r in rows
    ]


@router.get("/jobs")
def list_jobs(
    db: Session = Depends(get_db),
    source: Optional[str] = Query(None),
    q: Optional[str] = Query(None, description="search in title"),
    org: Optional[str] = Query(None),
    country: Optional[str] = Query(None, description="search in location"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    qry = db.query(JobPosting).order_by(JobPosting.published_at.desc().nullslast())
    if source:
        qry = qry.filter(JobPosting.source == source)
    if q:
        like = f"%{q}%"
        qry = qry.filter(JobPosting.title.ilike(like))
    if org:
        likeo = f"%{org}%"
        qry = qry.filter(JobPosting.org.ilike(likeo))
    if country:
        likec = f"%{country}%"
        qry = qry.filter(JobPosting.location.ilike(likec))
    rows = qry.offset(offset).limit(limit).all()
    return [
        {
            "id": str(r.id),
            "source": r.source,
            "source_id": r.source_id,
            "title": r.title,
            "org": r.org,
            "location": r.location,
            "url": r.url,
            "published_at": r.published_at,
            "deadline": r.deadline,
        }
        for r in rows
    ]


@router.get("/funding")
def list_funding(
    db: Session = Depends(get_db),
    year: Optional[int] = Query(None),
    country: Optional[str] = Query(None),
    cluster: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    q = db.query(FundingRecord)
    if year:
        q = q.filter(FundingRecord.year == year)
    if country:
        q = q.filter(FundingRecord.country.ilike(f"%{country}%"))
    if cluster:
        q = q.filter(FundingRecord.cluster.ilike(f"%{cluster}%"))
    q = q.order_by(FundingRecord.amount.desc().nullslast())
    rows = q.offset(offset).limit(limit).all()
    return [
        {
            "id": str(r.id),
            "year": r.year,
            "country": r.country,
            "cluster": r.cluster,
            "donor": r.donor,
            "recipient": r.recipient,
            "amount": r.amount,
            "currency": r.currency,
        }
        for r in q.limit(limit).all()
    ]
