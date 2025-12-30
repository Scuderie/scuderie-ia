from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware # <--- FONDAMENTALE
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from src.config import settings
from src.api.endpoints import router as api_router
from src.api.chat import router as chat_router
from src.core.rate_limit import limiter

app = FastAPI(title=settings.PROJECT_NAME)

# Rate Limiter State
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# --- CONFIGURAZIONE CORS (Il passaporto per Angular) ---
# Senza questo, il browser di Lorenzo bloccherà le richieste
origins = [
    "http://localhost:4200",    # Angular Default
    "http://127.0.0.1:4200",
    "http://192.168.0.182:8000",  
    "*"                         # Utile per testare se stessi
    # Se Lorenzo è su un altro PC nella stessa rete, aggiungi qui il suo IP
    # es: "http://192.168.1.XX:4200"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Permetti GET, POST, OPTIONS, tutto
    allow_headers=["*"], # Permetti invio di JSON e token
)
# -------------------------------------------------------

# Colleghiamo le rotte
app.include_router(api_router, prefix="/api/v1", tags=["Knowledge Base"])
app.include_router(chat_router, prefix="/api/v1", tags=["Chat AI"])

@app.get("/")
def read_root():
    return {"status": "online", "system": "Scuderie AI Engine"}