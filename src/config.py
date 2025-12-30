from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Scuderie AI Engine"
    API_V1_STR: str = "/api/v1"
    
    # Embedding Model
    MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    # LLM Configuration (Ollama + Llama 3.1)
    OLLAMA_HOST: str = "http://localhost:11434"
    LLM_MODEL: str = "llama3.1:latest"
    LLM_TEMPERATURE: float = 0.1  # Basso per RAG (precisione)
    LLM_MAX_TOKENS: int = 2048
    
    # RAG Configuration
    RAG_SIMILARITY_THRESHOLD: float = 0.5  # Minima similarità per includere (0-1)
    RAG_TOP_K: int = 3  # Massimo documenti da restituire
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_DEFAULT: str = "100/hour"
    RATE_LIMIT_CHAT: str = "10/minute"
    RATE_LIMIT_INGEST: str = "50/hour"
    RATE_LIMIT_SEARCH: str = "100/minute"
    REDIS_URL: str = "memory://"  # Prod: redis://redis:6379
    
    # --- MODIFICATO PER COMBACIARE COL VOSTRO DOCKER ---
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "scuderie_user"      # Era "postgres"
    POSTGRES_PASSWORD: str = "scuderie_password" # Era "password"
    POSTGRES_DB: str = "scuderie_db"          # Era "scuderie_vector_db"
    
    # Security
    API_KEY: str = "scuderie-dev-key-2024"  # Sovrascrivere in .env per produzione
    API_KEY_HEADER: str = "X-API-Key"

    class Config:
        env_file = ".env"

settings = Settings()