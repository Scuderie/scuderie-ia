from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# --- MODELLI DI INPUT (Cosa ci manda Laravel) ---

class DocumentIngestRequest(BaseModel):
    """
    Payload per caricare un nuovo documento.
    Laravel ci manderà questi dati.
    """
    source_type: str        # es. "ticket_assistenza", "manuale_pdf"
    source_id: str          # ID del record su Laravel
    content: str            # Il testo da imparare
    author: Optional[str] = None
    created_at_laravel: Optional[datetime] = None

# --- MODELLI DI OUTPUT (Come rispondiamo) ---

class SearchResultItem(BaseModel):
    id: int
    content_chunk: str      # Il pezzo di testo trovato
    similarity_score: float # Quanto è pertinente (0-1)
    source: str

class SearchResponse(BaseModel):
    query: str
    results: List[SearchResultItem]
    processing_time: float