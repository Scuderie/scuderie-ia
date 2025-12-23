
from fastapi import APIRouter
from src.schemas import DocumentIngestRequest, SearchResponse, SearchResultItem

router = APIRouter()

@router.post("/ingest", summary="Carica un documento")
async def ingest_document(payload: DocumentIngestRequest):
    print(f"--> [MOCK] Ricevuto documento ID {payload.source_id} ({payload.source_type})")
    return {
        "status": "received",
        "doc_id": payload.source_id,
        "message": "Documento in coda per vettorializzazione"
    }

@router.post("/search", response_model=SearchResponse, summary="Cerca nella Knowledge Base")
async def search_knowledge(payload: DocumentIngestRequest):
    return {
        "query": "Test Query",
        "results": [
            SearchResultItem(
                id=1,
                content_chunk="Questa è una risposta di prova generata dalle API Python.",
                similarity_score=0.99,
                source="Sistema Test"
            )
        ],
        "processing_time": 0.01
    }
