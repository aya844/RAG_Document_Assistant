import logging
from fastapi import APIRouter
from pydantic import BaseModel
from app.agent.graph import agent_graph

router = APIRouter()
logger = logging.getLogger(__name__)


class ChatRequest(BaseModel):
    message: str
    document_ids: list[str] | None = None
    session_id: str | None = None


class Citation(BaseModel):
    filename: str
    page_number: int | None
    rerank_score: float | None = None
    excerpt: str | None = None


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation]
    grounded: bool
    intent: str


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    logger.info(f"Chat request: '{request.message[:80]}' | "
                f"doc_filter: {request.document_ids}")

    initial_state = {
        "query": request.message,
        "document_ids": request.document_ids or [],
        "intent": "unknown",
        "retrieval_result": {},
        "summarize_result": {},
        "answer": "",
        "citations": [],
        "grounded": False,
    }

    final_state = await agent_graph.ainvoke(initial_state)

    return ChatResponse(
        answer=final_state["answer"],
        citations=[Citation(**c) for c in final_state["citations"]],
        grounded=final_state["grounded"],
        intent=final_state["intent"],
    )