"""
LLM Service - Wrapper per Ollama + Llama 3.1
Gestisce generazione testo e streaming con retry logic
"""
import json
import httpx
from typing import AsyncGenerator
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from src.config import settings
from src.core.logging_config import logger


class LLMService:
    """
    Servizio per interagire con Llama 3.1 via Ollama.
    Supporta generazione sincrona e streaming con retry automatico.
    """
    
    def __init__(self):
        self.base_url = settings.OLLAMA_HOST
        self.model = settings.LLM_MODEL
        self.temperature = settings.LLM_TEMPERATURE
        self.max_tokens = settings.LLM_MAX_TOKENS
        logger.info(f"LLM Service initialized: {self.model} @ {self.base_url}")
        
    def _build_prompt(
        self, 
        user_message: str, 
        system_prompt: str | None = None,
        context_docs: list[str] | None = None,
        chat_history: list[dict] | None = None
    ) -> str:
        """
        Costruisce il prompt in formato ChatML per Llama 3.1.
        Include personalità ScuderieBot + RAG context + chat history.
        """
        parts = ["<|begin_of_text|>"]
        
        # DEFINIZIONE DELLA PERSONALITÀ (Soft Fine-Tuning via Prompt)
        default_system = """Sei ScuderieBot, il Senior Fashion Consultant delle Scuderie AI.
Il tuo stile è: Sofisticato, Tecnico ma Accogliente, Essenziale (Silent Luxury).

REGOLE DI RISPOSTA:
1. Usa ESCLUSIVAMENTE le informazioni fornite nel CONTESTO qui sotto, se presente.
2. Se il CONTESTO non contiene la risposta, dì chiaramente: "Mi dispiace, non ho informazioni specifiche su questo nei miei cataloghi attuali." NON inventare.
3. Cita sempre i materiali e i dettagli tecnici se presenti.
4. Non iniziare mai con "In base al contesto...". Rispondi direttamente come un esperto.
5. Mantieni un tono professionale ma amichevole, come un consulente di alta moda."""
        
        system_content = system_prompt or default_system
        
        # Inietta contesto RAG nel system prompt
        if context_docs:
            docs_text = "\n\n".join([f"[DOCUMENTO {i+1}]: {doc}" for i, doc in enumerate(context_docs)])
            system_content += f"\n\nCONTESTO RECUPERATO DAL DATABASE:\n{docs_text}"
        
        parts.append(f"<|start_header_id|>system<|end_header_id|>\n\n{system_content}<|eot_id|>")
        
        # Chat History (Sliding Window - ultimi 6 messaggi)
        if chat_history:
            for msg in chat_history[-6:]:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                parts.append(f"<|start_header_id|>{role}<|end_header_id|>\n\n{content}<|eot_id|>")
        
        # Current User Message
        parts.append(f"<|start_header_id|>user<|end_header_id|>\n\n{user_message}<|eot_id|>")
        
        # Assistant generation trigger
        parts.append("<|start_header_id|>assistant<|end_header_id|>\n\n")
        
        return "".join(parts)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.ConnectError, httpx.TimeoutException)),
        before_sleep=lambda retry_state: logger.warning(
            f"LLM retry #{retry_state.attempt_number} after error"
        )
    )
    async def generate(
        self,
        user_message: str,
        system_prompt: str | None = None,
        context_docs: list[str] | None = None,
        chat_history: list[dict] | None = None
    ) -> str:
        """
        Genera una risposta completa (non-streaming).
        Retry automatico in caso di errori di connessione.
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
        
        logger.debug(f"LLM generate request: {user_message[:50]}...")
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/api/generate",
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            result = data.get("response", "")
            logger.info(f"LLM response generated: {len(result)} chars")
            return result
    
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
        
        logger.debug(f"LLM stream request: {user_message[:50]}...")
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/api/generate",
                json=payload
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line:
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
                    is_available = self.model in model_names or any(
                        self.model.split(":")[0] in m for m in model_names
                    )
                    logger.info(f"LLM health check: {'OK' if is_available else 'FAIL'}")
                    return is_available
            return False
        except Exception as e:
            logger.error(f"LLM health check failed: {e}")
            return False


# Singleton instance
llm_service = LLMService()

