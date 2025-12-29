"""
Embedding Service
Generates vector embeddings with LRU caching for performance.
"""
from functools import lru_cache
from sentence_transformers import SentenceTransformer
from src.config import settings
from src.core.logging_config import logger


class EmbeddingService:
    """
    Servizio per embedding vettoriale con cache LRU.
    Usa CPU per liberare GPU per il LLM (più pesante).
    """
    
    def __init__(self):
        self.device = "cpu"
        logger.info("Embedding service loading on CPU (GPU reserved for LLM)")
        self.model = SentenceTransformer(settings.MODEL_NAME, device=self.device)
        self._cache_hits = 0
        self._cache_misses = 0
    
    def _compute_embedding(self, text: str) -> tuple[float, ...]:
        """Compute embedding and return as tuple (hashable for cache)."""
        cleaned_text = text.replace("\n", " ").strip()
        embedding = self.model.encode(cleaned_text)
        return tuple(embedding.tolist())
    
    @lru_cache(maxsize=1000)
    def get_embedding_cached(self, text: str) -> tuple[float, ...]:
        """Cached embedding - returns tuple for hashability."""
        self._cache_misses += 1
        return self._compute_embedding(text)
    
    def get_embedding(self, text: str) -> list[float]:
        """Get embedding with cache support."""
        # Normalize text for cache key
        cache_key = text.replace("\n", " ").strip()[:500]  # Limit key size
        
        # Check if in cache (by calling cached method)
        result = self.get_embedding_cached(cache_key)
        
        # Log cache stats periodically
        total = self._cache_hits + self._cache_misses
        if total > 0 and total % 50 == 0:
            hit_rate = self._cache_hits / total * 100
            logger.info(f"Embedding cache: {hit_rate:.1f}% hit rate ({self._cache_hits}/{total})")
        
        return list(result)
    
    def get_cache_info(self) -> dict:
        """Return cache statistics."""
        info = self.get_embedding_cached.cache_info()
        return {
            "hits": info.hits,
            "misses": info.misses,
            "size": info.currsize,
            "maxsize": info.maxsize
        }


embedding_service = EmbeddingService()