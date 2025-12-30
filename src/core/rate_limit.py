"""
Rate Limiting Core Module
Configurazione centralizzata del rate limiter con strategia multi-key.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import Request
import logging

logger = logging.getLogger("scuderie")


def get_api_key_or_ip(request: Request) -> str:
    """
    Key function per rate limiting: usa API Key se presente, altrimenti IP.
    
    Strategia:
    - Se header X-API-Key presente → usa "apikey:<key>"
    - Altrimenti → usa IP address
    
    Questo permette di avere limiti separati per chiavi autenticate vs traffico anonimo.
    """
    api_key = request.headers.get("X-API-Key")
    
    if api_key:
        # Limiti per API Key (più generosi per utenti autenticati)
        return f"apikey:{api_key}"
    
    # Limiti per IP (più restrittivi per traffico anonimo)
    return get_remote_address(request)


# Configurazione Limiter
# Storage: memory:// per sviluppo locale
# Production: usare Redis con storage_uri="redis://redis:6379"
limiter = Limiter(
    key_func=get_api_key_or_ip,
    default_limits=["100/hour"],  # Default: 100 req/ora
    storage_uri="memory://",
    headers_enabled=True,  # Abilita headers X-RateLimit-*
)

logger.info("Rate limiter initialized (storage: memory://)")
