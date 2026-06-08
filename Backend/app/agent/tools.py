# backend/app/agent/tools.py
import logging
import aiosqlite
from app.retrieval.pipeline import run_retrieval_pipeline
from app.storage.database import get_all_documents
from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


async def retrieve_tool(
    query: str,
    document_ids: list[str] | None = None,
) -> dict:
    """
    Tool 1: Hybrid retrieval.
    document_ids: restrict retrieval to these documents.
                  Empty list or None = search all documents.
    """
    contexts = await run_retrieval_pipeline(
        query=query,
        document_ids=document_ids or [],
    )

    if not contexts:
        return {"grounded": False, "reason": "no_results", "contexts": []}

    top_score = contexts[0].rerank_score
    grounded = top_score >= settings.grounding_score_threshold

    logger.info(f"retrieve_tool: {len(contexts)} contexts | "
                f"top={top_score:.3f} | grounded={grounded}")

    return {
        "grounded": grounded,
        "top_score": top_score,
        "contexts": [
            {
                "filename": c.filename,
                "page_number": c.page_number,
                "parent_content": c.parent_content,
                "child_content": c.child_content,
                "rerank_score": c.rerank_score,
            }
            for c in contexts
        ],
    }


async def summarize_tool(
    document_ids: list[str] | None = None,
) -> dict:
    """
    Tool 2: Summarize selected documents.
    document_ids: restrict to these documents.
                  Empty list or None = summarize all.
    """
    all_documents = await get_all_documents()

    if not all_documents:
        return {"error": "No documents available", "content": []}

    # Filter if specific IDs provided
    if document_ids:
        docs_to_summarize = [d for d in all_documents if d["id"] in document_ids]
        if not docs_to_summarize:
            return {"error": "Selected documents not found", "content": []}
    else:
        docs_to_summarize = all_documents

    content_blocks = []
    async with aiosqlite.connect(settings.sqlite_path) as db:
        db.row_factory = aiosqlite.Row
        for doc in docs_to_summarize:
            async with db.execute(
                "SELECT content FROM parent_chunks "
                "WHERE document_id = ? ORDER BY chunk_index",
                (doc["id"],),
            ) as cursor:
                rows = await cursor.fetchall()
                full_text = " ".join(r["content"] for r in rows)[:3000]

            content_blocks.append({
                "document_id": doc["id"],
                "filename": doc["filename"],
                "content": full_text,
            })

    return {"content": content_blocks}