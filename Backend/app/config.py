
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Qdrant
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_collection: str = "rag_chunks"

    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    embed_model: str = "nomic-embed-text"
    llm_model: str = "qwen2.5:7b-instruct"

    # Chunking
    child_chunk_size: int = 300
    child_chunk_overlap: int = 50
    parent_chunk_size: int = 1200

    # Retrieval
    retrieval_top_k: int = 15
    rerank_top_n: int = 5
    grounding_score_threshold: float = 0.25

    # Storage
    sqlite_path: str = "data/rag.db"
    bm25_index_path: str = "data/bm25_index.pkl"
    upload_dir: str = "data/uploads"

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()