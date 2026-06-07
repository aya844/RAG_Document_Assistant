import logging
from app.retrieval.pipeline import run_retrieval_pipeline, RetrievalContext
from app.storage.database import get_all_documents, get_parent_chunk
from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


async def retrieve_tool(query: str) -> dict:
    """
    Tool 1: Hybrid retrieval pipeline.
    Returns contexts and a grounding flag.
    """
    contexts = await run_retrieval_pipeline(query)

    if not contexts:
        return {
            "grounded": False,
            "reason": "no_results",
            "contexts": [],
        }

    top_score = contexts[0].rerank_score
    grounded = top_score >= settings.grounding_score_threshold

    logger.info(
        f"retrieve_tool: {len(contexts)} contexts, "
        f"top_score={top_score:.3f}, grounded={grounded}"
    )

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


async def summarize_tool(document_id: str | None = None) -> dict:
    documents = await get_all_documents()

    if not documents:
        return {"error": "No documents available", "content": []}

    if document_id:
        docs_to_summarize = [d for d in documents if d["id"] == document_id]
        if not docs_to_summarize:
            return {"error": f"Document {document_id} not found", "content": []}
    else:
        docs_to_summarize = documents

    content_blocks = []
    async with __import__('aiosqlite').connect(settings.sqlite_path) as db:
        db.row_factory = __import__('aiosqlite').Row
        for doc in docs_to_summarize:
            async with db.execute(
                "SELECT content FROM parent_chunks "
                "WHERE document_id = ? ORDER BY chunk_index",
                (doc["id"],)
            ) as cursor:
                rows = await cursor.fetchall()
                # Joins tous les chunks en un seul texte, cap à 3000 chars
                full_text = " ".join(r["content"] for r in rows)[:3000]

            content_blocks.append({
                "document_id": doc["id"],
                "filename": doc["filename"],
                "content": full_text,       # un seul bloc par document
            })

    return {"content": content_blocks}