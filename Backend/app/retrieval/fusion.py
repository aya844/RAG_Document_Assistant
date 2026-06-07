import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

RRF_K = 60  # Standard constant — dampens rank differences


@dataclass
class FusedResult:
    chunk_id: str
    parent_id: str
    document_id: str
    content: str
    page_number: int | None
    filename: str
    rrf_score: float
    dense_rank: int | None
    sparse_rank: int | None


def reciprocal_rank_fusion(
        dense_results: list,  # list[DenseResult]
        sparse_results: list,  # list[tuple[BM25Document, float]]
        top_k: int,
) -> list[FusedResult]:
    """
    RRF formula: score(d) = Σ 1 / (k + rank(d))

    Each list contributes independently.
    Documents appearing in both lists get scores from both.
    """
    # Build lookup: chunk_id → rank (1-indexed)
    dense_ranks: dict[str, int] = {
        r.chunk_id: i + 1 for i, r in enumerate(dense_results)
    }
    sparse_ranks: dict[str, int] = {
        doc.chunk_id: i + 1 for i, (doc, _) in enumerate(sparse_results)
    }

    # Collect all unique chunk IDs
    all_ids = set(dense_ranks.keys()) | set(sparse_ranks.keys())

    # Build a lookup for metadata from both result lists
    meta: dict[str, dict] = {}
    for r in dense_results:
        meta[r.chunk_id] = {
            "parent_id": r.parent_id,
            "document_id": r.document_id,
            "content": r.content,
            "page_number": r.page_number,
            "filename": r.filename,
        }
    for doc, _ in sparse_results:
        if doc.chunk_id not in meta:
            meta[doc.chunk_id] = {
                "parent_id": doc.parent_id,
                "document_id": doc.document_id,
                "content": doc.content,
                "page_number": doc.page_number,
                "filename": "",
            }

    # Compute RRF scores
    fused = []
    for chunk_id in all_ids:
        d_rank = dense_ranks.get(chunk_id)
        s_rank = sparse_ranks.get(chunk_id)

        score = 0.0
        if d_rank is not None:
            score += 1.0 / (RRF_K + d_rank)
        if s_rank is not None:
            score += 1.0 / (RRF_K + s_rank)

        m = meta[chunk_id]
        fused.append(FusedResult(
            chunk_id=chunk_id,
            parent_id=m["parent_id"],
            document_id=m["document_id"],
            content=m["content"],
            page_number=m["page_number"],
            filename=m["filename"],
            rrf_score=score,
            dense_rank=d_rank,
            sparse_rank=s_rank,
        ))

    fused.sort(key=lambda x: x.rrf_score, reverse=True)
    top = fused[:top_k]
    logger.info(f"RRF fusion: {len(all_ids)} unique chunks → top {len(top)}")
    return top