from sqlalchemy import Column, Integer, String, Text, DateTime, func
from pgvector.sqlalchemy import Vector #type: ignore
from src.database import Base

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(String, index=True)      # Es: "doc_01"
    source_type = Column(String)                # Es: "manuale_pdf"
    content = Column(Text)                      # Il testo originale (che leggerà l'umano)
    
    # LA COLONNA DELL'IA: Vettore a 384 dimensioni (per il modello MiniLM)
    embedding = Column(Vector(384))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())