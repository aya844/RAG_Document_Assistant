# backend/app/retrieval/dense.py
import logging
from dataclasses import dataclass
from qdrant_client.models import Filter, FieldCondition, MatchAny
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


async def dense_search(
    query: str,
    top_k: int,
    document_ids: list[str] | None = None,
) -> list[DenseResult]:

    query_vector = await embed_single(query)
    qdrant = get_qdrant_client()

    # Build filter only when IDs are explicitly provided
    query_filter = None
    if document_ids:
        query_filter = Filter(
            must=[
                FieldCondition(
                    key="document_id",
                    match=MatchAny(any=document_ids),  # matches any of the IDs
                )
            ]
        )

    results = await qdrant.query_points(
        collection_name=settings.qdrant_collection,
        query=query_vector,
        limit=top_k,
        with_payload=True,
        query_filter=query_filter,
    )

    hits = []
    for r in results.points:
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

    logger.info(f"Dense: {len(hits)} results | filter={document_ids or 'all'}")
    return hits