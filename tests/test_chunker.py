"""
Tests for Document Chunker Service
"""
from src.ml.services.chunker import chunk_text, estimate_tokens


class TestChunkText:
    """Tests for chunk_text function."""
    
    def test_empty_text(self):
        """Empty text should return empty list."""
        assert chunk_text("") == []
        assert chunk_text("   ") == []
    
    def test_short_text(self):
        """Short text (under max_tokens) should return single chunk."""
        text = "Questo è un testo breve."
        chunks = chunk_text(text, max_tokens=500)
        assert len(chunks) == 1
        assert chunks[0] == "Questo è un testo breve."
    
    def test_long_text_creates_multiple_chunks(self):
        """Long text should be split into multiple chunks."""
        # Create text with 100 words
        words = ["parola"] * 100
        text = " ".join(words)
        
        chunks = chunk_text(text, max_tokens=30, overlap=5)
        
        assert len(chunks) > 1
        # Each chunk should have at most max_tokens words
        for chunk in chunks:
            assert len(chunk.split()) <= 30
    
    def test_overlap_works(self):
        """Chunks should have overlapping content."""
        words = ["word" + str(i) for i in range(50)]
        text = " ".join(words)
        
        chunks = chunk_text(text, max_tokens=20, overlap=5)
        
        assert len(chunks) >= 2
        # Check overlap exists between consecutive chunks
        if len(chunks) >= 2:
            chunk1_words = chunks[0].split()[-5:]
            chunk2_words = chunks[1].split()[:5]
            # At least some words should overlap
            overlap = set(chunk1_words) & set(chunk2_words)
            assert len(overlap) > 0


class TestEstimateTokens:
    """Tests for estimate_tokens function."""
    
    def test_empty_text(self):
        """Empty text should have 0 tokens."""
        assert estimate_tokens("") == 0
    
    def test_token_estimation(self):
        """Token count should be roughly 0.75x word count."""
        text = "one two three four"  # 4 words
        tokens = estimate_tokens(text)
        assert tokens == 3  # 4 * 0.75 = 3
