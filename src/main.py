from fastapi import FastAPI
from src.config import settings
from src.api.endpoints import router as api_router
from src.api.chat import router as chat_router

app = FastAPI(title=settings.PROJECT_NAME)

# Colleghiamo le rotte
app.include_router(api_router, prefix="/api/v1", tags=["Knowledge Base"])
app.include_router(chat_router, prefix="/api/v1", tags=["Chat AI"])

@app.get("/")
def read_root():
    return {"status": "online", "system": "Scuderie AI Engine"}