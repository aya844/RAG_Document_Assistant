import httpx
import numpy as np
from app.config import get_settings

settings = get_settings()

OLLAMA_EMBED_URL = f"{settings.ollama_base_url}/api/embeddings"


async def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Calls Ollama embeddings endpoint.
    Batches individually — Ollama doesn't support true batching yet.
    """
    embeddings = []
    async with httpx.AsyncClient(timeout=60.0) as client:
        for text in texts:
            response = await client.post(
                OLLAMA_EMBED_URL,
                json={"model": settings.embed_model, "prompt": text},
            )
            response.raise_for_status()
            data = response.json()
            embeddings.append(data["embedding"])
    return embeddings


async def embed_single(text: str) -> list[float]:
    results = await embed_texts([text])
    return results[0]