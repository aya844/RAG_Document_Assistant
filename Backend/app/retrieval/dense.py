import logging
from dataclasses import dataclass
from app.config import get_settings
from app.dependencies import get_qdrant_client
from app.ingestion.embedder import embed_single

settings = get_settings()
logger = logging.getLogger(__name__)


@dataclass
class DenseResult:
    chunk_id: str
    parent_id: str
    document_id: str
    content: str
    page_number: int | None
    filename: str
    score: float


async def dense_search(query: str, top_k: int) -> list[DenseResult]:
    """
    Embed the query and search Qdrant for nearest child chunks.
    """
    query_vector = await embed_single(query)
    qdrant = get_qdrant_client()

    results = await qdrant.search(
        collection_name=settings.qdrant_collection,
        query_vector=query_vector,
        limit=top_k,
        with_payload=True,
    )

    hits = []
    for r in results:
        p = r.payload
        hits.append(DenseResult(
            chunk_id=str(r.id),
            parent_id=p.get("parent_id", ""),
            document_id=p.get("document_id", ""),
            content=p.get("content", ""),
            page_number=p.get("page_number"),
            filename=p.get("filename", ""),
            score=r.score,
        ))

    logger.info(f"Dense search returned {len(hits)} results")
    return hits