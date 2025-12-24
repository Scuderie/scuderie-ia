import asyncio
from src.database import engine, Base
from src.models import Document, ChatSession, ChatMessage  # Import all models
from sqlalchemy import text

async def init_db():
    async with engine.begin() as conn:
        print("--- 🔌 Connessione al Database... ---")
        
        # 1. Attiviamo l'estensione vettoriale (Fondamentale!)
        print("--- 🧠 Attivazione estensione pgvector ---")
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        
        # 2. Creiamo le tabelle definite in models.py
        print("--- 🏗️ Creazione tabelle (documents, chat_sessions, chat_messages) ---")
        await conn.run_sync(Base.metadata.create_all)
    
    print("✅ TUTTO FATTO! Database pronto all'uso.")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(init_db())