"""
LLM Service - Wrapper per Ollama + Llama 3.1
Gestisce generazione testo e streaming
"""
import httpx
from typing import AsyncGenerator
from src.config import settings


class LLMService:
    """
    Servizio per interagire con Llama 3.1 via Ollama.
    Supporta generazione sincrona e streaming.
    """
    
    def __init__(self):
        self.base_url = settings.OLLAMA_HOST
        self.model = settings.LLM_MODEL
        self.temperature = settings.LLM_TEMPERATURE
        self.max_tokens = settings.LLM_MAX_TOKENS
        
    def _build_prompt(
        self, 
        user_message: str, 
        system_prompt: str | None = None,
        context_docs: list[str] | None = None,
        chat_history: list[dict] | None = None
    ) -> str:
        """
        Costruisce il prompt in formato ChatML per Llama 3.1.
        Questo formato è FONDAMENTALE per far capire i ruoli al modello.
        """
        parts = ["<|begin_of_text|>"]
        
        # System Prompt
        system_content = system_prompt or "Sei ScuderieBot, un assistente AI esperto di moda italiana."
        
        if context_docs:
            docs_text = "\n\n".join([f"[DOCUMENTO {i+1}]: {doc}" for i, doc in enumerate(context_docs)])
            system_content += f"\n\nUsa SOLO i seguenti documenti per rispondere:\n{docs_text}"
        
        parts.append(f"<|start_header_id|>system<|end_header_id|>\n{system_content}<|eot_id|>")
        
        # Chat History (Sliding Window)
        if chat_history:
            for msg in chat_history[-6:]:  # Ultimi 6 messaggi
                role = msg.get("role", "user")
                content = msg.get("content", "")
                parts.append(f"<|start_header_id|>{role}<|end_header_id|>\n{content}<|eot_id|>")
        
        # Current User Message
        parts.append(f"<|start_header_id|>user<|end_header_id|>\n{user_message}<|eot_id|>")
        
        # Assistant turn start (il modello completerà da qui)
        parts.append("<|start_header_id|>assistant<|end_header_id|>\n")
        
        return "".join(parts)
    
    async def generate(
        self,
        user_message: str,
        system_prompt: str | None = None,
        context_docs: list[str] | None = None,
        chat_history: list[dict] | None = None
    ) -> str:
        """
        Genera una risposta completa (non-streaming).
        Usare per risposte brevi o quando serve il testo completo.
        """
        prompt = self._build_prompt(user_message, system_prompt, context_docs, chat_history)
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "num_predict": self.max_tokens,
            }
        }
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/api/generate",
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            return data.get("response", "")
    
    async def stream(
        self,
        user_message: str,
        system_prompt: str | None = None,
        context_docs: list[str] | None = None,
        chat_history: list[dict] | None = None
    ) -> AsyncGenerator[str, None]:
        """
        Genera risposta in streaming (token per token).
        Usare per chat UI con effetto "typing".
        """
        prompt = self._build_prompt(user_message, system_prompt, context_docs, chat_history)
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": self.temperature,
                "num_predict": self.max_tokens,
            }
        }
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/api/generate",
                json=payload
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line:
                        import json
                        data = json.loads(line)
                        token = data.get("response", "")
                        if token:
                            yield token
                        if data.get("done", False):
                            break
    
    async def health_check(self) -> bool:
        """Verifica se Ollama è raggiungibile e il modello è disponibile."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                if response.status_code == 200:
                    models = response.json().get("models", [])
                    model_names = [m.get("name", "") for m in models]
                    return self.model in model_names or any(self.model.split(":")[0] in m for m in model_names)
            return False
        except Exception:
            return False


# Singleton instance
llm_service = LLMService()
