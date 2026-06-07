from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


@router.post("/")
async def chat(request: ChatRequest):
    # Implemented in Phase 4
    return {"answer": "not implemented yet", "citations": []}