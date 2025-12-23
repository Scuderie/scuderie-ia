"""
Chat API Endpoints
Gestisce conversazioni con l'LLM integrato con RAG
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from src.ml.services.llm import llm_service
from src.ml.services.embedding import embedding_service
from sqlalchemy import select
from src.database import AsyncSessionLocal
from src.models import Document

router = APIRouter()


class ChatRequest(BaseModel):
    """Richiesta di chat"""
    message: str
    use_rag: bool = True  # Se True, cerca nel DB vettoriale prima di rispondere
    system_prompt: str | None = None


class ChatResponse(BaseModel):
    """Risposta della chat"""
    response: str
    rag_sources: list[str] = []


@router.get("/health", summary="Verifica stato LLM")
async def llm_health():
    """Controlla se Ollama e Llama 3.1 sono raggiungibili."""
    is_healthy = await llm_service.health_check()
    if is_healthy:
        return {"status": "ok", "model": llm_service.model}
    else:
        raise HTTPException(
            status_code=503,
            detail="LLM non raggiungibile. Assicurati che Ollama sia in esecuzione."
        )


@router.post("/chat", response_model=ChatResponse, summary="Chat con l'IA")
async def chat(request: ChatRequest):
    """
    Invia un messaggio e ricevi una risposta dall'IA.
    Se use_rag=True, cerca prima nel database vettoriale.
    """
    context_docs: list[str] = []
    rag_sources: list[str] = []
    
    # RAG: Cerca documenti rilevanti
    if request.use_rag:
        try:
            query_vector = embedding_service.get_embedding(request.message)
            
            async with AsyncSessionLocal() as db:
                stmt = select(Document).order_by(
                    Document.embedding.cosine_distance(query_vector)
                ).limit(3)
                result = await db.execute(stmt)
                documents = result.scalars().all()
                
                for doc in documents:
                    context_docs.append(str(doc.content))
                    rag_sources.append(str(doc.source_id))
                    
        except Exception as e:
            print(f"⚠️ RAG fallito, procedo senza contesto: {e}")
    
    # Genera risposta
    try:
        response_text = await llm_service.generate(
            user_message=request.message,
            system_prompt=request.system_prompt,
            context_docs=context_docs if context_docs else None
        )
        
        return ChatResponse(
            response=response_text,
            rag_sources=rag_sources
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore LLM: {str(e)}")


@router.get("/chat/stream", summary="Chat con streaming (SSE)")
async def chat_stream(message: str, use_rag: bool = True):
    """
    Chat con risposta in streaming (Server-Sent Events).
    I token vengono inviati uno alla volta per effetto "typing".
    """
    context_docs: list[str] = []
    
    # RAG: Cerca documenti rilevanti
    if use_rag:
        try:
            query_vector = embedding_service.get_embedding(message)
            
            async with AsyncSessionLocal() as db:
                stmt = select(Document).order_by(
                    Document.embedding.cosine_distance(query_vector)
                ).limit(3)
                result = await db.execute(stmt)
                documents = result.scalars().all()
                
                for doc in documents:
                    context_docs.append(str(doc.content))
                    
        except Exception as e:
            print(f"⚠️ RAG fallito, procedo senza contesto: {e}")
    
    async def generate_stream():
        try:
            async for token in llm_service.stream(
                user_message=message,
                context_docs=context_docs if context_docs else None
            ):
                yield f"data: {token}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: [ERROR] {str(e)}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
