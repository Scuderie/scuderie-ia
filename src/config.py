from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Scuderie AI Engine"
    API_V1_STR: str = "/api/v1"
    
    # Configurazione Modello IA
    MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    # Configurazione Database (Default per sviluppo locale)
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_DB: str = "scuderie_vector_db"

    class Config:
        env_file = ".env"

# QUESTA È LA RIGA CHE MANCAVA: Creiamo l'istanza che main.py sta cercando
settings = Settings()