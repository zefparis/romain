# -*- coding: utf-8 -*-
"""
Modèles de base de données pour l'assistant Romain
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

Base = declarative_base()

class Conversation(Base):
    """Modèle pour les conversations"""
    __tablename__ = "conversations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_archived = Column(Boolean, default=False)
    
    # Relations
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")

class Message(Base):
    """Modèle pour les messages dans les conversations"""
    __tablename__ = "messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False)
    role = Column(String(20), nullable=False)  # 'user', 'assistant', 'system'
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Métadonnées pour la recherche sémantique
    embedding = Column(Text)  # Stockage JSON de l'embedding
    
    # Relations
    conversation = relationship("Conversation", back_populates="messages")

class Document(Base):
    """Modèle pour les documents gérés par l'assistant"""
    __tablename__ = "documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(50), nullable=False)  # 'pdf', 'docx', 'xlsx', etc.
    file_size = Column(Integer, nullable=False)
    
    # Métadonnées
    title = Column(String(255))
    description = Column(Text)
    tags = Column(Text)  # JSON array de tags
    
    # Dates
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Statut
    is_processed = Column(Boolean, default=False)
    processing_status = Column(String(50), default='pending')  # 'pending', 'processing', 'completed', 'error'

class AgendaEvent(Base):
    """Modèle pour les événements de l'agenda"""
    __tablename__ = "agenda_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Dates et heures
    start_datetime = Column(DateTime, nullable=False)
    end_datetime = Column(DateTime)
    is_all_day = Column(Boolean, default=False)
    
    # Localisation
    location = Column(String(255))
    
    # Rappels
    reminder_minutes = Column(Integer, default=15)  # Rappel X minutes avant
    is_reminder_sent = Column(Boolean, default=False)
    
    # Récurrence
    is_recurring = Column(Boolean, default=False)
    recurrence_pattern = Column(String(50))  # 'daily', 'weekly', 'monthly', 'yearly'
    recurrence_end_date = Column(DateTime)
    
    # Métadonnées
    priority = Column(String(20), default='medium')  # 'low', 'medium', 'high', 'urgent'
    category = Column(String(100))  # 'meeting', 'task', 'personal', etc.
    
    # Dates
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Statut
    status = Column(String(20), default='scheduled')  # 'scheduled', 'completed', 'cancelled'

class Memory(Base):
    """Modèle pour la mémoire à long terme de l'assistant"""
    __tablename__ = "memories"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content = Column(Text, nullable=False)
    context = Column(Text)  # Contexte dans lequel cette information a été apprise
    
    # Classification
    category = Column(String(100))  # 'personal', 'work', 'preferences', 'facts', etc.
    importance = Column(Float, default=1.0)  # Score d'importance (0.0 à 1.0)
    
    # Métadonnées pour la recherche
    keywords = Column(Text)  # JSON array de mots-clés
    embedding = Column(Text)  # Embedding pour la recherche sémantique
    
    # Dates
    created_at = Column(DateTime, default=datetime.utcnow)
    last_accessed = Column(DateTime, default=datetime.utcnow)
    access_count = Column(Integer, default=0)
    
    # Relations optionnelles
    related_conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"))
    related_document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"))

class UserPreference(Base):
    """Modèle pour les préférences utilisateur"""
    __tablename__ = "user_preferences"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key = Column(String(100), nullable=False, unique=True)
    value = Column(Text, nullable=False)
    description = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
