# -*- coding: utf-8 -*-
"""
Service pour la gestion des conversations et de la mémoire
"""
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from app.models import Conversation, Message, Memory
from app.db import get_db
from typing import List, Optional, Dict
import json
from datetime import datetime, timedelta
import uuid

class ConversationService:
    """Service pour gérer les conversations et la mémoire contextuelle"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_conversation(self, title: str = None) -> Conversation:
        """Crée une nouvelle conversation"""
        if not title:
            title = f"Conversation du {datetime.now().strftime('%d/%m/%Y à %H:%M')}"
        
        conversation = Conversation(title=title)
        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)
        return conversation
    
    def get_conversation(self, conversation_id: uuid.UUID) -> Optional[Conversation]:
        """Récupère une conversation par son ID"""
        return self.db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
    
    def get_conversations(self, limit: int = 50, archived: bool = False) -> List[Conversation]:
        """Récupère la liste des conversations"""
        return self.db.query(Conversation).filter(
            Conversation.is_archived == archived
        ).order_by(desc(Conversation.updated_at)).limit(limit).all()
    
    def add_message(self, conversation_id: uuid.UUID, role: str, content: str) -> Message:
        """Ajoute un message à une conversation"""
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content
        )
        self.db.add(message)
        
        # Mettre à jour la date de dernière modification de la conversation
        conversation = self.get_conversation(conversation_id)
        if conversation:
            conversation.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(message)
        return message
    
    def get_conversation_messages(self, conversation_id: uuid.UUID, limit: int = 100) -> List[Message]:
        """Récupère les messages d'une conversation"""
        return self.db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at).limit(limit).all()
    
    def get_conversation_context(self, conversation_id: uuid.UUID, max_messages: int = 20) -> List[Dict]:
        """Récupère le contexte d'une conversation pour GPT"""
        messages = self.get_conversation_messages(conversation_id, max_messages)
        
        context = []
        for message in messages[-max_messages:]:  # Prendre les derniers messages
            context.append({
                "role": message.role,
                "content": message.content
            })
        
        return context
    
    def search_conversations(self, query: str, limit: int = 10) -> List[Conversation]:
        """Recherche dans les conversations"""
        return self.db.query(Conversation).filter(
            Conversation.title.ilike(f"%{query}%")
        ).order_by(desc(Conversation.updated_at)).limit(limit).all()
    
    def archive_conversation(self, conversation_id: uuid.UUID) -> bool:
        """Archive une conversation"""
        conversation = self.get_conversation(conversation_id)
        if conversation:
            conversation.is_archived = True
            self.db.commit()
            return True
        return False
    
    def delete_conversation(self, conversation_id: uuid.UUID) -> bool:
        """Supprime une conversation et tous ses messages"""
        conversation = self.get_conversation(conversation_id)
        if conversation:
            self.db.delete(conversation)
            self.db.commit()
            return True
        return False
    
    def update_conversation_title(self, conversation_id: uuid.UUID, title: str) -> bool:
        """Met à jour le titre d'une conversation"""
        conversation = self.get_conversation(conversation_id)
        if conversation:
            conversation.title = title
            conversation.updated_at = datetime.utcnow()
            self.db.commit()
            return True
        return False

class MemoryService:
    """Service pour la gestion de la mémoire à long terme"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def store_memory(self, content: str, context: str = None, category: str = None, 
                    importance: float = 1.0, keywords: List[str] = None,
                    conversation_id: uuid.UUID = None) -> Memory:
        """Stocke une nouvelle information en mémoire"""
        memory = Memory(
            content=content,
            context=context,
            category=category,
            importance=importance,
            keywords=json.dumps(keywords) if keywords else None,
            related_conversation_id=conversation_id
        )
        
        self.db.add(memory)
        self.db.commit()
        self.db.refresh(memory)
        return memory
    
    def get_relevant_memories(self, query: str = None, category: str = None, 
                            limit: int = 10) -> List[Memory]:
        """Récupère les mémoires pertinentes"""
        query_filter = self.db.query(Memory)
        
        if category:
            query_filter = query_filter.filter(Memory.category == category)
        
        if query:
            query_filter = query_filter.filter(
                Memory.content.ilike(f"%{query}%")
            )
        
        return query_filter.order_by(
            desc(Memory.importance),
            desc(Memory.last_accessed)
        ).limit(limit).all()
    
    def access_memory(self, memory_id: uuid.UUID) -> Optional[Memory]:
        """Accède à une mémoire et met à jour les statistiques d'accès"""
        memory = self.db.query(Memory).filter(Memory.id == memory_id).first()
        if memory:
            memory.last_accessed = datetime.utcnow()
            memory.access_count += 1
            self.db.commit()
        return memory
    
    def update_memory_importance(self, memory_id: uuid.UUID, importance: float) -> bool:
        """Met à jour l'importance d'une mémoire"""
        memory = self.db.query(Memory).filter(Memory.id == memory_id).first()
        if memory:
            memory.importance = max(0.0, min(1.0, importance))  # Clamp entre 0 et 1
            self.db.commit()
            return True
        return False
    
    def get_memories_by_category(self, category: str, limit: int = 20) -> List[Memory]:
        """Récupère les mémoires par catégorie"""
        return self.db.query(Memory).filter(
            Memory.category == category
        ).order_by(desc(Memory.importance)).limit(limit).all()
    
    def cleanup_old_memories(self, days_threshold: int = 90, importance_threshold: float = 0.3):
        """Nettoie les anciennes mémoires peu importantes"""
        cutoff_date = datetime.utcnow() - timedelta(days=days_threshold)
        
        old_memories = self.db.query(Memory).filter(
            and_(
                Memory.last_accessed < cutoff_date,
                Memory.importance < importance_threshold
            )
        ).all()
        
        for memory in old_memories:
            self.db.delete(memory)
        
        self.db.commit()
        return len(old_memories)
