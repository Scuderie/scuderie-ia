from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector  # type: ignore
from src.database import Base
import uuid


class Document(Base):
    """Documento vettorializzato per RAG"""
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(String, index=True)      # Es: "doc_01"
    source_type = Column(String)                # Es: "manuale_pdf"
    content = Column(Text)                      # Il testo originale
    
    # Vettore a 384 dimensioni (per il modello MiniLM)
    embedding = Column(Vector(384))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ChatSession(Base):
    """Sessione di chat (una conversazione)"""
    __tablename__ = "chat_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=True)  # Titolo auto-generato
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relazione con i messaggi (cascade delete)
    messages = relationship(
        "ChatMessage", 
        back_populates="session", 
        cascade="all, delete-orphan",
        order_by="ChatMessage.created_at"
    )


class ChatMessage(Base):
    """Singolo messaggio in una chat"""
    __tablename__ = "chat_messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id"), index=True)
    role = Column(String)  # 'user' o 'assistant'
    content = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relazione inversa
    session = relationship("ChatSession", back_populates="messages")