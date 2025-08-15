# -*- coding: utf-8 -*-
"""
API endpoints pour la gestion de l'agenda
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, date, timedelta
import uuid

from app.db import get_db
from app.models import AgendaEvent

router = APIRouter()

# Modèles Pydantic
class AgendaEventCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    start_datetime: datetime
    end_datetime: Optional[datetime] = None
    is_all_day: bool = False
    location: Optional[str] = None
    reminder_minutes: int = 15
    is_recurring: bool = False
    recurrence_pattern: Optional[str] = None  # 'daily', 'weekly', 'monthly', 'yearly'
    recurrence_end_date: Optional[datetime] = None
    priority: str = Field(default='medium', pattern='^(low|medium|high|urgent)$')
    category: Optional[str] = None

class AgendaEventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    start_datetime: Optional[datetime] = None
    end_datetime: Optional[datetime] = None
    is_all_day: Optional[bool] = None
    location: Optional[str] = None
    reminder_minutes: Optional[int] = None
    priority: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None

class AgendaEventResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: Optional[str]
    start_datetime: datetime
    end_datetime: Optional[datetime]
    is_all_day: bool
    location: Optional[str]
    reminder_minutes: int
    is_reminder_sent: bool
    is_recurring: bool
    recurrence_pattern: Optional[str]
    recurrence_end_date: Optional[datetime]
    priority: str
    category: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime

@router.post("/events", response_model=AgendaEventResponse)
def create_event(
    event_data: AgendaEventCreate,
    db: Session = Depends(get_db)
):
    """Crée un nouvel événement dans l'agenda"""
    
    # Validation des dates
    if event_data.end_datetime and event_data.end_datetime <= event_data.start_datetime:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La date de fin doit être postérieure à la date de début"
        )
    
    event = AgendaEvent(
        title=event_data.title,
        description=event_data.description,
        start_datetime=event_data.start_datetime,
        end_datetime=event_data.end_datetime,
        is_all_day=event_data.is_all_day,
        location=event_data.location,
        reminder_minutes=event_data.reminder_minutes,
        is_recurring=event_data.is_recurring,
        recurrence_pattern=event_data.recurrence_pattern,
        recurrence_end_date=event_data.recurrence_end_date,
        priority=event_data.priority,
        category=event_data.category
    )
    
    db.add(event)
    db.commit()
    db.refresh(event)
    
    return AgendaEventResponse(**event.__dict__)

@router.get("/events", response_model=List[AgendaEventResponse])
def get_events(
    start_date: Optional[date] = Query(None, description="Date de début (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="Date de fin (YYYY-MM-DD)"),
    category: Optional[str] = Query(None, description="Filtrer par catégorie"),
    priority: Optional[str] = Query(None, description="Filtrer par priorité"),
    status: str = Query("scheduled", description="Statut des événements"),
    limit: int = Query(100, le=500, description="Nombre maximum d'événements"),
    db: Session = Depends(get_db)
):
    """Récupère les événements de l'agenda avec filtres optionnels"""
    
    query = db.query(AgendaEvent).filter(AgendaEvent.status == status)
    
    # Filtres de date
    if start_date:
        start_datetime = datetime.combine(start_date, datetime.min.time())
        query = query.filter(AgendaEvent.start_datetime >= start_datetime)
    
    if end_date:
        end_datetime = datetime.combine(end_date, datetime.max.time())
        query = query.filter(AgendaEvent.start_datetime <= end_datetime)
    
    # Autres filtres
    if category:
        query = query.filter(AgendaEvent.category == category)
    
    if priority:
        query = query.filter(AgendaEvent.priority == priority)
    
    events = query.order_by(AgendaEvent.start_datetime).limit(limit).all()
    
    return [AgendaEventResponse(**event.__dict__) for event in events]

@router.get("/events/today", response_model=List[AgendaEventResponse])
def get_today_events(db: Session = Depends(get_db)):
    """Récupère les événements d'aujourd'hui"""
    today = date.today()
    start_datetime = datetime.combine(today, datetime.min.time())
    end_datetime = datetime.combine(today, datetime.max.time())
    
    events = db.query(AgendaEvent).filter(
        AgendaEvent.start_datetime >= start_datetime,
        AgendaEvent.start_datetime <= end_datetime,
        AgendaEvent.status == "scheduled"
    ).order_by(AgendaEvent.start_datetime).all()
    
    return [AgendaEventResponse(**event.__dict__) for event in events]

@router.get("/events/upcoming", response_model=List[AgendaEventResponse])
def get_upcoming_events(
    days: int = Query(7, ge=1, le=30, description="Nombre de jours à venir"),
    db: Session = Depends(get_db)
):
    """Récupère les événements à venir"""
    start_datetime = datetime.now()
    end_datetime = start_datetime + timedelta(days=days)
    
    events = db.query(AgendaEvent).filter(
        AgendaEvent.start_datetime >= start_datetime,
        AgendaEvent.start_datetime <= end_datetime,
        AgendaEvent.status == "scheduled"
    ).order_by(AgendaEvent.start_datetime).limit(20).all()
    
    return [AgendaEventResponse(**event.__dict__) for event in events]

@router.get("/events/{event_id}", response_model=AgendaEventResponse)
def get_event(
    event_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """Récupère un événement spécifique"""
    event = db.query(AgendaEvent).filter(AgendaEvent.id == event_id).first()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Événement non trouvé"
        )
    
    return AgendaEventResponse(**event.__dict__)

@router.put("/events/{event_id}", response_model=AgendaEventResponse)
def update_event(
    event_id: uuid.UUID,
    event_data: AgendaEventUpdate,
    db: Session = Depends(get_db)
):
    """Met à jour un événement"""
    event = db.query(AgendaEvent).filter(AgendaEvent.id == event_id).first()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Événement non trouvé"
        )
    
    # Mettre à jour les champs modifiés
    update_data = event_data.dict(exclude_unset=True)
    
    # Validation des dates si modifiées
    if 'start_datetime' in update_data or 'end_datetime' in update_data:
        start_dt = update_data.get('start_datetime', event.start_datetime)
        end_dt = update_data.get('end_datetime', event.end_datetime)
        
        if end_dt and end_dt <= start_dt:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La date de fin doit être postérieure à la date de début"
            )
    
    for field, value in update_data.items():
        setattr(event, field, value)
    
    event.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(event)
    
    return AgendaEventResponse(**event.__dict__)

@router.delete("/events/{event_id}")
def delete_event(
    event_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """Supprime un événement"""
    event = db.query(AgendaEvent).filter(AgendaEvent.id == event_id).first()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Événement non trouvé"
        )
    
    db.delete(event)
    db.commit()
    
    return {"message": "Événement supprimé avec succès"}

@router.put("/events/{event_id}/complete")
def complete_event(
    event_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """Marque un événement comme terminé"""
    event = db.query(AgendaEvent).filter(AgendaEvent.id == event_id).first()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Événement non trouvé"
        )
    
    event.status = "completed"
    event.updated_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Événement marqué comme terminé"}

@router.get("/stats/summary")
def get_agenda_summary(db: Session = Depends(get_db)):
    """Récupère un résumé statistique de l'agenda"""
    today = datetime.now().date()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    
    # Événements d'aujourd'hui
    today_events = db.query(AgendaEvent).filter(
        AgendaEvent.start_datetime >= datetime.combine(today, datetime.min.time()),
        AgendaEvent.start_datetime <= datetime.combine(today, datetime.max.time()),
        AgendaEvent.status == "scheduled"
    ).count()
    
    # Événements de la semaine
    week_events = db.query(AgendaEvent).filter(
        AgendaEvent.start_datetime >= datetime.combine(week_start, datetime.min.time()),
        AgendaEvent.start_datetime <= datetime.combine(week_end, datetime.max.time()),
        AgendaEvent.status == "scheduled"
    ).count()
    
    # Événements en retard (passés mais non terminés)
    overdue_events = db.query(AgendaEvent).filter(
        AgendaEvent.start_datetime < datetime.now(),
        AgendaEvent.status == "scheduled"
    ).count()
    
    return {
        "today_events": today_events,
        "week_events": week_events,
        "overdue_events": overdue_events,
        "summary_date": today.isoformat()
    }
