"""
Chat API Endpoints
Gestisce conversazioni con l'LLM integrato con RAG e persistenza storico
"""
from uuid import UUID as PyUUID
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.ml.services.llm import llm_service
from src.ml.services.embedding import embedding_service
from src.ml.services.query_rewriter import rewrite_query
from src.database import get_db, AsyncSessionLocal
from src.models import Document, ChatSession, ChatMessage
from src.core.auth import verify_api_key
from src.core.rate_limit import limiter
from src.config import settings
from fastapi import Request

router = APIRouter()


# ============ SCHEMAS ============

class ChatRequest(BaseModel):
    """Richiesta di chat"""
    message: str
    session_id: PyUUID | None = None  # Se None, crea nuova sessione
    use_rag: bool = True
    system_prompt: str | None = None


class ChatResponse(BaseModel):
    """Risposta della chat"""
    session_id: PyUUID
    response: str
    rag_sources: list[str] = []


class SessionInfo(BaseModel):
    """Info sessione"""
    id: PyUUID
    title: str | None
    message_count: int


class MessageInfo(BaseModel):
    """Info messaggio"""
    id: PyUUID
    role: str
    content: str


# ============ SESSION ENDPOINTS ============

@router.get("/sessions", summary="Lista tutte le sessioni")
async def list_sessions(db: AsyncSession = Depends(get_db)) -> list[SessionInfo]:
    """Restituisce tutte le sessioni di chat ordinate per data."""
    from sqlalchemy import func
    
    # Subquery per contare messaggi per sessione (fix N+1)
    msg_count_subq = (
        select(ChatMessage.session_id, func.count().label("msg_count"))
        .group_by(ChatMessage.session_id)
        .subquery()
    )
    
    # Query principale con LEFT JOIN
    stmt = (
        select(ChatSession, func.coalesce(msg_count_subq.c.msg_count, 0).label("count"))
        .outerjoin(msg_count_subq, ChatSession.id == msg_count_subq.c.session_id)
        .order_by(ChatSession.created_at.desc())
    )
    
    result = await db.execute(stmt)
    rows = result.all()
    
    return [
        SessionInfo(
            id=PyUUID(str(row[0].id)),
            title=str(row[0].title) if row[0].title else None,
            message_count=int(row[1])
        )
        for row in rows
    ]


@router.post("/sessions", summary="Crea nuova sessione")
async def create_session(db: AsyncSession = Depends(get_db)) -> SessionInfo:
    """Crea una nuova sessione di chat vuota."""
    new_session = ChatSession(title="Nuova conversazione")
    db.add(new_session)
    await db.commit()
    await db.refresh(new_session)
    
    return SessionInfo(id=PyUUID(str(new_session.id)), title=str(new_session.title) if new_session.title else None, message_count=0)


@router.get("/sessions/{session_id}/history", summary="Storico messaggi")
async def get_session_history(
    session_id: PyUUID, 
    db: AsyncSession = Depends(get_db)
) -> list[MessageInfo]:
    """Restituisce tutti i messaggi di una sessione."""
    stmt = select(ChatMessage).where(
        ChatMessage.session_id == session_id
    ).order_by(ChatMessage.created_at)
    
    result = await db.execute(stmt)
    messages = result.scalars().all()
    
    return [
        MessageInfo(id=PyUUID(str(m.id)), role=str(m.role), content=str(m.content))
        for m in messages
    ]


@router.delete("/sessions/{session_id}", summary="Elimina sessione")
async def delete_session(session_id: PyUUID, db: AsyncSession = Depends(get_db)):
    """Elimina una sessione e tutti i suoi messaggi (cascade)."""
    stmt = select(ChatSession).where(ChatSession.id == session_id)
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Sessione non trovata")
    
    await db.delete(session)
    await db.commit()
    return {"status": "deleted", "session_id": str(session_id)}


# ============ CHAT ENDPOINTS ============

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


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Chat con l'IA",
    dependencies=[Depends(verify_api_key)]
)
@limiter.limit(settings.RATE_LIMIT_CHAT)
async def chat(request: ChatRequest, req: Request, db: AsyncSession = Depends(get_db)):
    """
    Invia un messaggio e ricevi una risposta dall'IA.
    - Se session_id è None, crea una nuova sessione
    - Salva automaticamente user message e assistant response
    - Se use_rag=True, cerca prima nel database vettoriale
    """
    # 1. Gestione sessione
    if request.session_id:
        stmt = select(ChatSession).where(ChatSession.id == request.session_id)
        result = await db.execute(stmt)
        session = result.scalar_one_or_none()
        if not session:
            raise HTTPException(status_code=404, detail="Sessione non trovata")
    else:
        # Crea nuova sessione con titolo dal primo messaggio
        title = request.message[:50] + "..." if len(request.message) > 50 else request.message
        session = ChatSession(title=title)
        db.add(session)
        await db.commit()
        await db.refresh(session)
    
    # 2. Salva messaggio utente
    user_msg = ChatMessage(
        session_id=session.id,
        role="user",
        content=request.message
    )
    db.add(user_msg)
    await db.commit()
    
    # 3. Carica storico chat (sliding window: ultimi 6)
    history_stmt = select(ChatMessage).where(
        ChatMessage.session_id == session.id
    ).order_by(ChatMessage.created_at.desc()).limit(6)
    
    history_result = await db.execute(history_stmt)
    history_messages = list(reversed(history_result.scalars().all()))
    
    chat_history = [
        {"role": str(m.role), "content": str(m.content)}
        for m in history_messages[:-1]  # Escludi l'ultimo (è la domanda corrente)
    ]
    
    # 4. RAG: Cerca documenti rilevanti con score e threshold
    context_docs: list[str] = []
    rag_sources: list[str] = []
    
    if request.use_rag:
        try:
            from src.config import settings
            
            # Query rewriting per query ambigue
            search_query = await rewrite_query(request.message, chat_history)
            query_vector = embedding_service.get_embedding(search_query)
            
            # Query con calcolo distanza
            distance_col = Document.embedding.cosine_distance(query_vector).label("distance")
            stmt = select(Document, distance_col).order_by(distance_col).limit(settings.RAG_TOP_K)
            result = await db.execute(stmt)
            rows = result.all()
            
            for row in rows:
                doc = row[0]
                distance = float(row[1])
                similarity = 1.0 - distance
                
                # Solo documenti sopra threshold
                if similarity >= settings.RAG_SIMILARITY_THRESHOLD:
                    context_docs.append(str(doc.content))
                    rag_sources.append(f"{doc.source_id}:{similarity:.2%}")
                    
        except Exception as e:
            print(f"⚠️ RAG fallito, procedo senza contesto: {e}")
    
    # 5. Genera risposta
    try:
        response_text = await llm_service.generate(
            user_message=request.message,
            system_prompt=request.system_prompt,
            context_docs=context_docs if context_docs else None,
            chat_history=chat_history if chat_history else None
        )
        
        # 6. Salva risposta assistant
        assistant_msg = ChatMessage(
            session_id=session.id,
            role="assistant",
            content=response_text
        )
        db.add(assistant_msg)
        await db.commit()
        
        return ChatResponse(
            session_id=PyUUID(str(session.id)),
            response=response_text,
            rag_sources=rag_sources
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore LLM: {str(e)}")


@router.get("/chat/stream", summary="Chat con streaming (SSE)")
async def chat_stream(
    message: str, 
    session_id: PyUUID | None = None,
    use_rag: bool = True
):
    """
    Chat con risposta in streaming (Server-Sent Events).
    I token vengono inviati uno alla volta per effetto "typing".
    """
    async def generate_stream():
        async with AsyncSessionLocal() as db:
            # Gestione sessione
            if session_id:
                stmt = select(ChatSession).where(ChatSession.id == session_id)
                result = await db.execute(stmt)
                session = result.scalar_one_or_none()
                if not session:
                    yield "data: [ERROR] Sessione non trovata\n\n"
                    return
            else:
                title = message[:50] + "..." if len(message) > 50 else message
                session = ChatSession(title=title)
                db.add(session)
                await db.commit()
                await db.refresh(session)
            
            # Salva messaggio utente
            user_msg = ChatMessage(session_id=session.id, role="user", content=message)
            db.add(user_msg)
            await db.commit()
            
            # Carica storico
            history_stmt = select(ChatMessage).where(
                ChatMessage.session_id == session.id
            ).order_by(ChatMessage.created_at.desc()).limit(6)
            history_result = await db.execute(history_stmt)
            history_messages = list(reversed(history_result.scalars().all()))
            
            chat_history = [
                {"role": str(m.role), "content": str(m.content)}
                for m in history_messages[:-1]
            ]
            
            # RAG con score e threshold
            context_docs: list[str] = []
            if use_rag:
                try:
                    from src.config import settings
                    query_vector = embedding_service.get_embedding(message)
                    distance_col = Document.embedding.cosine_distance(query_vector).label("distance")
                    stmt = select(Document, distance_col).order_by(distance_col).limit(settings.RAG_TOP_K)
                    result = await db.execute(stmt)
                    rows = result.all()
                    for row in rows:
                        doc = row[0]
                        distance = float(row[1])
                        similarity = 1.0 - distance
                        if similarity >= settings.RAG_SIMILARITY_THRESHOLD:
                            context_docs.append(str(doc.content))
                except Exception as e:
                    print(f"⚠️ RAG fallito: {e}")
            
            # Send session_id first
            yield f"data: {{\"session_id\": \"{session.id}\"}}\n\n"
            
            # Stream response
            full_response = ""
            try:
                async for token in llm_service.stream(
                    user_message=message,
                    context_docs=context_docs if context_docs else None,
                    chat_history=chat_history if chat_history else None
                ):
                    full_response += token
                    yield f"data: {token}\n\n"
                
                # Salva risposta completa
                assistant_msg = ChatMessage(
                    session_id=session.id, 
                    role="assistant", 
                    content=full_response
                )
                db.add(assistant_msg)
                await db.commit()
                
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


# Schema per POST streaming
class StreamChatRequest(BaseModel):
    """Richiesta per streaming POST"""
    message: str
    session_id: PyUUID | None = None
    use_rag: bool = True


@router.post("/chat/stream", summary="Chat con streaming (SSE) - POST")
async def chat_stream_post(request: StreamChatRequest):
    """
    Versione POST dello streaming per compatibilità frontend.
    Accetta JSON body invece di query parameters.
    """
    # Riutilizza la logica del GET
    return await chat_stream(
        message=request.message,
        session_id=request.session_id,
        use_rag=request.use_rag
    )
