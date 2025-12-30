"""
Knowledge Base API Endpoints
Ingest and search documents with authentication
"""
import time
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.schemas import DocumentIngestRequest, SearchResponse, SearchResultItem
from src.ml.services.embedding import embedding_service
from src.database import get_db
from src.models import Document
from src.config import settings
from src.core.logging_config import logger
from src.core.auth import verify_api_key
from src.core.rate_limit import limiter
from fastapi import Request

router = APIRouter()


@router.post(
    "/ingest",
    summary="Carica e vettorializza un documento",
    dependencies=[Depends(verify_api_key)]
)
@limiter.limit(settings.RATE_LIMIT_INGEST)
async def ingest_document(
    payload: DocumentIngestRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Ingest a document into the knowledge base with automatic chunking."""
    from src.ml.services.chunker import chunk_text
    
    try:
        logger.info(f"Ingest started: {payload.source_id}")
        
        # Chunk document if too long
        chunks = chunk_text(payload.content, max_tokens=500, overlap=50)
        
        saved_ids = []
        for idx, chunk_content in enumerate(chunks):
            vector = embedding_service.get_embedding(chunk_content)
            
            new_doc = Document(
                source_id=f"{payload.source_id}_chunk_{idx}" if len(chunks) > 1 else payload.source_id,
                source_type=payload.source_type,
                content=chunk_content,
                chunk_index=idx,
                parent_id=payload.source_id if len(chunks) > 1 else None,
                embedding=vector
            )
            
            db.add(new_doc)
            await db.commit()
            await db.refresh(new_doc)
            saved_ids.append(new_doc.id)
        
        logger.info(f"Document saved: {len(saved_ids)} chunks ({payload.source_id})")
        
        return {
            "status": "success",
            "db_ids": saved_ids,
            "doc_id": payload.source_id,
            "chunks": len(chunks),
            "message": f"Vettorializzato in {len(chunks)} chunk(s)"
        }
    except Exception as e:
        logger.error(f"Ingest failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/search",
    response_model=SearchResponse,
    summary="Ricerca semantica nel DB",
    dependencies=[Depends(verify_api_key)]
)
async def search_knowledge(
    payload: DocumentIngestRequest,
    db: AsyncSession = Depends(get_db)
):
    """Search the knowledge base using semantic similarity."""
    start_time = time.time()
    
    logger.info(f"Search query: {payload.content[:50]}...")
    query_vector = embedding_service.get_embedding(payload.content)
    
    # Query with distance calculation
    distance_col = Document.embedding.cosine_distance(query_vector).label("distance")
    stmt = select(Document, distance_col).order_by(distance_col).limit(settings.RAG_TOP_K)
    
    result = await db.execute(stmt)
    rows = result.all()
    
    # Format results with threshold filtering
    results_list = []
    for row in rows:
        doc = row[0]
        distance = float(row[1])
        similarity = round(1.0 - distance, 4)
        
        if similarity >= settings.RAG_SIMILARITY_THRESHOLD:
            logger.debug(f"Match: {doc.source_id} ({similarity:.2%})")
            results_list.append(SearchResultItem(
                id=str(doc.source_id),
                content=str(doc.content),
                score=similarity
            ))
        else:
            logger.debug(f"Below threshold: {doc.source_id} ({similarity:.2%})")
    
    process_time = time.time() - start_time
    logger.info(f"Search completed: {len(results_list)} results in {process_time:.3f}s")
    
    return {
        "query": payload.content,
        "results": results_list,
        "processing_time": process_time
    }
