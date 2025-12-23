from fastapi import FastAPI
from src.config import settings
from src.api.endpoints import router as api_router

# ECCO IL PEZZO CHE MANCAVA: La definizione di 'app'
app = FastAPI(title=settings.PROJECT_NAME)

# Colleghiamo le rotte
app.include_router(api_router, prefix="/api/v1", tags=["Knowledge Base"])

@app.get("/")
def read_root():
    return {"status": "online", "system": "Scuderie AI Engine"}