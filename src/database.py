from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from src.config import settings

# Costruiamo l'indirizzo del database usando i dati del config
DATABASE_URL = f"postgresql+asyncpg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_SERVER}/{settings.POSTGRES_DB}"

# Creiamo il motore (echo=True ci farà vedere le query SQL nel terminale, utile per debug)
engine = create_async_engine(DATABASE_URL, echo=True)

# La fabbrica di sessioni async (async_sessionmaker è la versione moderna per async)
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()

# Funzione che useremo nelle API per prendere la sessione
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session