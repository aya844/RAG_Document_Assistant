from fastapi import APIRouter
from pydantic import BaseModel
from app.retrieval.pipeline import run_retrieval_pipeline
from app.config import get_settings

settings = get_settings()
router = APIRouter()


class SearchRequest(BaseModel):
    query: str


@router.post("/search")
async def search(request: SearchRequest):
    """
    Temporary endpoint to validate the retrieval pipeline.
    Will be removed in Phase 5 — the agent handles retrieval internally.
    """
    contexts = await run_retrieval_pipeline(request.query)

    return {
        "query": request.query,
        "results_count": len(contexts),
        "grounding_score_threshold": settings.grounding_score_threshold,
        "results": [
            {
                "filename": c.filename,
                "page_number": c.page_number,
                "rerank_score": round(c.rerank_score, 4),
                "child_content": c.child_content[:200] + "..."
                    if len(c.child_content) > 200 else c.child_content,
                "parent_content_preview": c.parent_content[:300] + "..."
                    if len(c.parent_content) > 300 else c.parent_content,
            }
            for c in contexts
        ],
    }