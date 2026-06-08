# backend/app/retrieval/pipeline.py
import logging
from dataclasses import dataclass
from app.config import get_settings
from app.retrieval.dense import dense_search
from app.retrieval.sparse import get_bm25_index
from app.retrieval.fusion import reciprocal_rank_fusion
from app.retrieval.reranker import rerank
from app.storage.database import get_parent_chunk

settings = get_settings()
logger = logging.getLogger(__name__)


@dataclass
class RetrievalContext:
    parent_id: str
    document_id: str
    filename: str
    page_number: int | None
    parent_content: str
    child_content: str
    rerank_score: float


async def run_retrieval_pipeline(
    query: str,
    document_ids: list[str] | None = None,   # ← empty or None = all docs
) -> list[RetrievalContext]:

    top_k = settings.retrieval_top_k
    top_n = settings.rerank_top_n
    filter_ids = document_ids if document_ids else []

    dense_results = await dense_search(query, top_k, document_ids=filter_ids)

    bm25_index = get_bm25_index()
    sparse_results = bm25_index.search(query, top_k, document_ids=filter_ids)

    if not dense_results and not sparse_results:
        logger.warning("No results from either retriever")
        return []

    fused = reciprocal_rank_fusion(dense_results, sparse_results, top_k)
    if not fused:
        return []

    reranked = rerank(query, fused, top_n)
    if not reranked:
        return []

    contexts: list[RetrievalContext] = []
    seen_parents: set[str] = set()
    seen_content: set[str] = set()

    for result in reranked:
        if result.parent_id in seen_parents:
            continue
        content_key = result.content[:100]
        if content_key in seen_content:
            continue
        seen_parents.add(result.parent_id)
        seen_content.add(content_key)

        parent = await get_parent_chunk(result.parent_id)
        if not parent:
            logger.warning(f"Parent chunk not found: {result.parent_id}")
            continue

        contexts.append(RetrievalContext(
            parent_id=result.parent_id,
            document_id=result.document_id,
            filename=result.filename,
            page_number=result.page_number,
            parent_content=parent["content"],
            child_content=result.content,
            rerank_score=result.rerank_score,
        ))

    top_score = contexts[0].rerank_score if contexts else 0.0
    logger.info(f"Pipeline: {len(contexts)} contexts | top={top_score:.3f} | "
                f"filter={filter_ids or 'all'}")
    return contexts