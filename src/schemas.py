from pydantic import BaseModel
from typing import List, Optional

# Modello per ricevere i dati (Ingest)
class DocumentIngestRequest(BaseModel):
    source_id: str
    source_type: str
    content: str

# Modello per il singolo risultato trovato
class SearchResultItem(BaseModel):
    id: str
    content: str
    score: float  # <--- Questo è il campo che probabilmente mancava!

# Modello per la risposta completa della ricerca
class SearchResponse(BaseModel):
    query: str
    results: List[SearchResultItem]
    processing_time: float