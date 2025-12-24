import time
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.schemas import DocumentIngestRequest, SearchResponse, SearchResultItem
from src.ml.services.embedding import embedding_service
from src.database import get_db
from src.models import Document

router = APIRouter()

@router.post("/ingest", summary="Carica e vettorializza un documento")
async def ingest_document(
    payload: DocumentIngestRequest, 
    db: AsyncSession = Depends(get_db)
):
    try:
        print(f"--- 🧠 AI ENGINE: Inizio elaborazione doc {payload.source_id} ---")
        
        vector = embedding_service.get_embedding(payload.content)
        
        new_doc = Document(
            source_id=payload.source_id,
            source_type=payload.source_type,
            content=payload.content,
            embedding=vector
        )
        
        db.add(new_doc)
        await db.commit()
        await db.refresh(new_doc)
        
        print(f"💾 Documento salvato nel DB con ID: {new_doc.id}")
        
        return {
            "status": "success",
            "db_id": new_doc.id,
            "doc_id": payload.source_id,
            "message": "Vettorializzato e Salvato nella Memoria a Lungo Termine"
        }
    except Exception as e:
        print(f"❌ ERRORE CRITICO: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search", response_model=SearchResponse, summary="Ricerca semantica nel DB")
async def search_knowledge(
    payload: DocumentIngestRequest,
    db: AsyncSession = Depends(get_db)
):
    start_time = time.time()
    
    # 1. Vettorializziamo la domanda dell'utente
    print(f"🔎 Domanda utente: {payload.content}")
    query_vector = embedding_service.get_embedding(payload.content)
    
    # 2. RICERCA NEL DB con calcolo distanza
    # cosine_distance: 0 = identico, 2 = opposto
    # similarity = 1 - distance (range: -1 a 1, ma per vettori normalizzati: 0 a 1)
    from src.config import settings
    
    distance_col = Document.embedding.cosine_distance(query_vector).label("distance")
    stmt = select(Document, distance_col).order_by(distance_col).limit(settings.RAG_TOP_K)
    
    result = await db.execute(stmt)
    rows = result.all()
    
    # 3. Formattiamo i risultati con score reale e threshold
    results_list = []
    for row in rows:
        doc = row[0]  # Document object
        distance = float(row[1])  # Distance value
        similarity = round(1.0 - distance, 4)  # Convert to similarity
        
        # Applica threshold
        if similarity >= settings.RAG_SIMILARITY_THRESHOLD:
            print(f"   ✅ {doc.source_id} (similarity: {similarity:.2%})")
            results_list.append(SearchResultItem(
                id=str(doc.source_id),
                content=str(doc.content),
                score=similarity
            ))
        else:
            print(f"   ❌ {doc.source_id} sotto threshold (similarity: {similarity:.2%})")
    
    process_time = time.time() - start_time
    
    return {
        "query": payload.content,
        "results": results_list,
        "processing_time": process_time
    }