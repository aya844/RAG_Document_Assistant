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
    """
    Full pipeline:
    1. Dense search (Qdrant)       → top_k results
    2. Sparse search (BM25)        → top_k results
    3. RRF fusion                  → top_k unified
    4. Cross-encoder reranking     → top_n results
    5. Fetch parent chunks         → final context list

    Returns empty list if no documents are indexed.
    """
    top_k = settings.retrieval_top_k   # 15
    top_n = settings.rerank_top_n      # 5

    # --- Step 1: Dense ---
    dense_results = await dense_search(query, top_k)

    # --- Step 2: Sparse ---
    bm25_index = get_bm25_index()
    sparse_results = bm25_index.search(query, top_k)

    # --- Guard: nothing indexed yet ---
    if not dense_results and not sparse_results:
        logger.warning("No results from either dense or sparse search")
        return []

    # --- Step 3: RRF Fusion ---
    fused = reciprocal_rank_fusion(dense_results, sparse_results, top_k)

    # --- Step 4: Rerank ---
    reranked = rerank(query, fused, top_n)

    # --- Step 5: Fetch parent chunks from SQLite ---
    contexts: list[RetrievalContext] = []
    seen_parents: set[str] = set()

    for result in reranked:
        # Deduplicate: multiple children can share the same parent
        if result.parent_id in seen_parents:
            continue
        seen_parents.add(result.parent_id)

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

    logger.info(
        f"Pipeline complete: {len(contexts)} contexts "
        f"(top score: {contexts[0].rerank_score:.3f} if contexts else 'n/a')"
    )
    return contexts