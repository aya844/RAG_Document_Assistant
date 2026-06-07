from functools import lru_cache
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams
from app.config import get_settings

settings = get_settings()

EMBEDDING_DIM = 768  # nomic-embed-text output dimension


@lru_cache
def get_qdrant_client() -> AsyncQdrantClient:
    return AsyncQdrantClient(
        host=settings.qdrant_host,
        port=settings.qdrant_port,
    )


async def ensure_collection():
    client = get_qdrant_client()
    exists = await client.collection_exists(settings.qdrant_collection)
    if not exists:
        await client.create_collection(
            collection_name=settings.qdrant_collection,
            vectors_config=VectorParams(
                size=EMBEDDING_DIM,
                distance=Distance.COSINE,
            ),
        )