from fastapi import APIRouter, HTTPException
from src.schemas import DocumentIngestRequest, SearchResponse, SearchResultItem
# Qui importiamo il TUO servizio di intelligenza artificiale
from src.ml.services.embedding import embedding_service

router = APIRouter()

@router.post("/ingest", summary="Carica e vettorializza un documento")
async def ingest_document(payload: DocumentIngestRequest):
    """
    1. Riceve il testo.
    2. Usa la GPU (Metal/MPS) per calcolare il vettore.
    3. Restituisce il risultato (in futuro lo salverà su DB).
    """
    try:
        print(f"\n--- 🧠 AI ENGINE: Inizio elaborazione doc {payload.source_id} ---")
        
        # QUESTA È LA MAGIA: Il testo diventa numeri
        vector = embedding_service.get_embedding(payload.content)
        
        print(f"✅ Vettore calcolato con successo!")
        print(f"📊 Dimensioni vettore: {len(vector)}")
        print(f"👀 Primi 5 valori: {vector[:5]}...")
        
        # TODO: Prossimo step -> Salvare 'vector' su Postgres con pgvector
        
        return {
            "status": "success",
            "doc_id": payload.source_id,
            "vector_dim": len(vector),
            "message": "Vettorializzazione completata su Chip Apple Silicon"
        }
    except Exception as e:
        print(f"❌ ERRORE CRITICO: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search", response_model=SearchResponse)
async def search_knowledge(payload: DocumentIngestRequest):
    # Simuliamo una ricerca usando il motore per trasformare la query
    query_vector = embedding_service.get_embedding(payload.content)
    
    return {
        "query": payload.content,
        "results": [], # Per ora vuoto, collegheremo il DB nel prossimo step
        "processing_time": 0.1
    }