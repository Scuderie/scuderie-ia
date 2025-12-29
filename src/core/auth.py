"""
Authentication Module
API Key verification for securing endpoints
"""
from fastapi import HTTPException, Security, Depends
from fastapi.security import APIKeyHeader
from src.config import settings

# Header name for API key
api_key_header = APIKeyHeader(name=settings.API_KEY_HEADER, auto_error=False)


async def verify_api_key(api_key: str | None = Security(api_key_header)) -> str:
    """
    Verifica che la richiesta contenga un API key valido.
    
    Usage:
        @router.post("/endpoint", dependencies=[Depends(verify_api_key)])
    """
    if api_key is None:
        raise HTTPException(
            status_code=401,
            detail="API Key mancante. Usa header X-API-Key"
        )
    
    if api_key != settings.API_KEY:
        raise HTTPException(
            status_code=401,
            detail="API Key non valido"
        )
    
    return api_key


# Optional: dependency for endpoints that need the key value
def get_api_key_dependency():
    """Returns the verify_api_key dependency for use in routers."""
    return Depends(verify_api_key)
