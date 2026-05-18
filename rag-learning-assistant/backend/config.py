"""
Configuration globale du projet RAG Learning Assistant
"""
from pydantic_settings import BaseSettings
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    # Ollama
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2:3b"           # Modèle principal (chat)
    OLLAMA_EMBED_MODEL: str = "nomic-embed-text"  # Modèle d'embeddings

    # Chemins
    UPLOAD_DIR: Path = BASE_DIR / "data" / "uploads"
    VECTORSTORE_DIR: Path = BASE_DIR / "data" / "vectorstore"

    # RAG
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 64
    TOP_K: int = 5                          # Nombre de chunks récupérés

    # Mémoire conversationnelle
    MAX_HISTORY_TURNS: int = 10             # Nb de tours conservés

    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    CORS_ORIGINS: list[str] = ["*"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

# Créer les dossiers si absents
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.VECTORSTORE_DIR.mkdir(parents=True, exist_ok=True)
