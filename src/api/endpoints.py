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
    
    # 2. RICERCA NEL DB (La Magia)
    # Cerchiamo i 3 documenti con il vettore più simile (distanza coseno minore)
    # L'operatore 'cosine_distance' fa tutto il lavoro matematico pesante
    stmt = select(Document).order_by(Document.embedding.cosine_distance(query_vector)).limit(3)
    
    result = await db.execute(stmt)
    documents = result.scalars().all()
    
    # 3. Formattiamo i risultati
    results_list = []
    for doc in documents:
        print(f"   --> Trovato: {doc.source_id}")
        results_list.append(SearchResultItem(
            id=str(doc.source_id), #Agiunto str() per risoluzioni errori di tipizzazione 
            content=str(doc.content), #Agiunto str() per risoluzioni errori di tipizzazione 
            score=0.99 # Per ora fisso, nel prossimo step calcoleremo la % esatta
        ))
    
    process_time = time.time() - start_time
    
    return {
        "query": payload.content,
        "results": results_list,
        "processing_time": process_time
    }