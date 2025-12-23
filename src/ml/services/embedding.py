from sentence_transformers import SentenceTransformer
import torch
from src.config import settings

class EmbeddingService:
    def __init__(self):
        if torch.backends.mps.is_available():
            self.device = "mps"
            # CORREZIONE: Tolta la 'f'
            print("--- 🚀 AI ENGINE: Caricamento su Apple Metal (GPU) ---")
        elif torch.cuda.is_available():
            self.device = "cuda"
            # CORREZIONE: Tolta la 'f'
            print("--- 🚀 AI ENGINE: Caricamento su CUDA (GPU) ---")
        else:
            self.device = "cpu"
            # CORREZIONE: Tolta la 'f'
            print("--- 🐢 AI ENGINE: Caricamento su CPU (Slow Mode) ---")

        self.model = SentenceTransformer(settings.MODEL_NAME, device=self.device)

    def get_embedding(self, text: str) -> list[float]:
        cleaned_text = text.replace("\n", " ").strip()
        embedding = self.model.encode(cleaned_text)
        return embedding.tolist()

embedding_service = EmbeddingService()