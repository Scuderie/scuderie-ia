from sentence_transformers import SentenceTransformer
import torch
from src.config import settings

class EmbeddingService:
    def __init__(self):
        # Configurazione specifica per Mac (MPS = Metal Performance Shaders)
        if torch.backends.mps.is_available():
            self.device = "mps"
            print(f"--- 🚀 AI ENGINE: Caricamento su Apple Metal (GPU) ---")
        elif torch.cuda.is_available():
            self.device = "cuda"
            print(f"--- 🚀 AI ENGINE: Caricamento su CUDA (GPU) ---")
        else:
            self.device = "cpu"
            print(f"--- 🐢 AI ENGINE: Caricamento su CPU (Slow Mode) ---")

        # Carica il modello (lo scaricherà la prima volta)
        self.model = SentenceTransformer(settings.MODEL_NAME, device=self.device)

    def get_embedding(self, text: str) -> list[float]:
        # Pulizia e calcolo
        cleaned_text = text.replace("\n", " ").strip()
        embedding = self.model.encode(cleaned_text)
        return embedding.tolist()

embedding_service = EmbeddingService()