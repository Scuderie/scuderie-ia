from sentence_transformers import SentenceTransformer
from src.config import settings


class EmbeddingService:
    """
    Servizio per embedding vettoriale.
    Usa CPU per liberare GPU per il LLM (più pesante).
    """
    def __init__(self):
        # FORCE CPU: MiniLM è piccolo (22M params), gira bene su CPU
        # Questo libera la GPU per Llama 3.1 (8B params)
        self.device = "cpu"
        print("--- 📊 EMBEDDING: Caricamento su CPU (GPU riservata a LLM) ---")
        
        self.model = SentenceTransformer(settings.MODEL_NAME, device=self.device)

    def get_embedding(self, text: str) -> list[float]:
        """Genera embedding vettoriale per un testo."""
        cleaned_text = text.replace("\n", " ").strip()
        embedding = self.model.encode(cleaned_text)
        return embedding.tolist()


embedding_service = EmbeddingService()