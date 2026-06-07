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
    """
    Final unit passed to the agent/LLM.
    Contains parent chunk text (wide context) + child metadata (for citations).
    """
    parent_id: str
    document_id: str
    filename: str
    page_number: int | None
    parent_content: str     # wide context for LLM
    child_content: str      # precise match (for citation display)
    rerank_score: float


async def run_retrieval_pipeline(query: str) -> list[RetrievalContext]:
    top_k = settings.retrieval_top_k
    top_n = settings.rerank_top_n

    # --- Step 1: Dense ---
    dense_results = await dense_search(query, top_k)

    # --- Step 2: Sparse ---
    bm25_index = get_bm25_index()
    sparse_results = bm25_index.search(query, top_k)

    # --- Guard: nothing indexed ---
    if not dense_results and not sparse_results:
        logger.warning("No results from either dense or sparse search")
        return []  # ← retourne [] pas None

    # --- Step 3: RRF Fusion ---
    fused = reciprocal_rank_fusion(dense_results, sparse_results, top_k)

    # --- Step 4: Rerank ---
    reranked = rerank(query, fused, top_n)

    # --- Guard: reranker returned nothing ---
    if not reranked:
        logger.warning("Reranker returned no results")
        return []  # ← retourne [] pas None

    # --- Step 5: Fetch parent chunks ---
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
    logger.info(
        f"Pipeline complete: {len(contexts)} contexts "
        f"(top score: {top_score:.3f})"
    )
    return contexts