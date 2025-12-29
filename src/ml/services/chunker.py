"""
Document Chunker Service
Splits long documents into smaller chunks for better RAG retrieval.
"""
from src.core.logging_config import logger


def chunk_text(
    text: str,
    max_tokens: int = 500,
    overlap: int = 50
) -> list[str]:
    """
    Split text into overlapping chunks.
    
    Args:
        text: Input text to chunk
        max_tokens: Maximum words per chunk (approximate tokens)
        overlap: Number of overlapping words between chunks
        
    Returns:
        List of text chunks
    """
    if not text or not text.strip():
        return []
    
    # Clean and split into words
    words = text.replace("\n", " ").split()
    
    # If text is small enough, return as single chunk
    if len(words) <= max_tokens:
        return [" ".join(words)]
    
    chunks = []
    step = max_tokens - overlap
    
    for i in range(0, len(words), step):
        chunk_words = words[i:i + max_tokens]
        chunk = " ".join(chunk_words)
        chunks.append(chunk)
        
        # Stop if we've reached the end
        if i + max_tokens >= len(words):
            break
    
    logger.debug(f"Chunked text: {len(words)} words -> {len(chunks)} chunks")
    return chunks


def estimate_tokens(text: str) -> int:
    """Estimate token count (rough approximation: ~0.75 tokens per word)."""
    words = len(text.split())
    return int(words * 0.75)
