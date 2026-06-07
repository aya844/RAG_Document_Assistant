# backend/app/retrieval/reranker.py
import logging
from dataclasses import dataclass
from functools import lru_cache
from sentence_transformers import CrossEncoder
from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"


@lru_cache(maxsize=1)
def get_reranker() -> CrossEncoder:
    """
    Loaded once and cached — model is ~80MB, loading takes ~3s.
    lru_cache ensures single load across all requests.
    """
    logger.info(f"Loading reranker model: {RERANKER_MODEL}")
    model = CrossEncoder(RERANKER_MODEL, max_length=512)
    logger.info("Reranker loaded")
    return model


@dataclass
class RerankedResult:
    chunk_id: str
    parent_id: str
    document_id: str
    content: str        # child chunk content (kept for reference)
    page_number: int | None
    filename: str
    rerank_score: float
    rrf_score: float


def rerank(
    query: str,
    candidates: list,   # list[FusedResult]
    top_n: int,
) -> list[RerankedResult]:
    """
    Score each (query, chunk) pair with the cross-encoder.
    Returns top_n results sorted by rerank score descending.
    """
    if not candidates:
        return []

    reranker = get_reranker()

    pairs = [(query, c.content) for c in candidates]
    scores = reranker.predict(pairs)

    ranked = sorted(
        zip(candidates, scores),
        key=lambda x: x[1],
        reverse=True,
    )

    results = []
    for candidate, score in ranked[:top_n]:
        results.append(RerankedResult(
            chunk_id=candidate.chunk_id,
            parent_id=candidate.parent_id,
            document_id=candidate.document_id,
            content=candidate.content,
            page_number=candidate.page_number,
            filename=candidate.filename,
            rerank_score=float(score),
            rrf_score=candidate.rrf_score,
        ))

    logger.info(
        f"Reranked {len(candidates)} → top {len(results)} "
        f"(scores: {[round(r.rerank_score, 3) for r in results]})"
    )
    return results