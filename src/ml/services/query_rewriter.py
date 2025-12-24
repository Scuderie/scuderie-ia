"""
Query Rewriter Service
Riscrive query ambigue usando il contesto della chat history.
"""
from src.ml.services.llm import llm_service


async def rewrite_query(
    query: str,
    chat_history: list[dict] | None = None
) -> str:
    """
    Riscrive una query ambigua in modo completo e autonomo.
    
    Esempi:
        "E di rosso?" → "Scarpe rosse della collezione primavera 2024"
        "parlami di quello" → "Parlami del vestito Versace menzionato"
    
    Args:
        query: La domanda originale dell'utente
        chat_history: Storico messaggi recenti
        
    Returns:
        Query riscritta o originale se non serve riscrittura
    """
    # Se non c'è storico, la query è già autonoma
    if not chat_history:
        return query
    
    # Indicatori di query che necessita riscrittura
    ambiguous_indicators = [
        "quello", "quella", "questi", "queste",
        "e di", "anche", "invece", "pure",
        "lo stesso", "la stessa", "gli stessi",
        "dimmi di più", "continua", "approfondisci"
    ]
    
    query_lower = query.lower()
    needs_rewrite = any(ind in query_lower for ind in ambiguous_indicators)
    
    if not needs_rewrite:
        return query
    
    # Costruisci prompt per riscrittura
    recent_history = chat_history[-4:]  # Ultimi 4 messaggi per contesto
    history_text = "\n".join([
        f"{msg['role'].upper()}: {msg['content'][:200]}"
        for msg in recent_history
    ])
    
    rewrite_prompt = f"""Riscrivi la seguente domanda in modo che sia completa e autonoma, 
senza riferimenti impliciti alla conversazione precedente.

STORICO CONVERSAZIONE:
{history_text}

DOMANDA ORIGINALE: {query}

REGOLE:
- Riscrivi solo la domanda, nient'altro
- Mantieni lo stesso intento dell'utente
- Includi i riferimenti espliciti mancanti
- Se la domanda è già chiara, riscrivila identica

DOMANDA RISCRITTA:"""

    try:
        rewritten = await llm_service.generate(
            user_message=rewrite_prompt,
            system_prompt="Sei un assistente che riscrive domande ambigue in modo chiaro."
        )
        # Pulisci la risposta
        rewritten = rewritten.strip().strip('"').strip("'")
        print(f"🔄 Query rewrite: '{query}' → '{rewritten}'")
        return rewritten
    except Exception as e:
        print(f"⚠️ Query rewrite fallito: {e}")
        return query
