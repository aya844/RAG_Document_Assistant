import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.storage.database import init_db
from app.dependencies import ensure_collection
from app.api import documents, chat

from app.retrieval.sparse import get_bm25_index

from app.api import retrieval

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    os.makedirs(settings.upload_dir, exist_ok=True)
    os.makedirs(os.path.dirname(settings.sqlite_path), exist_ok=True)
    await init_db()
    await ensure_collection()
    get_bm25_index()
    yield
    # Shutdown — nothing needed


app = FastAPI(title="RAG Assistant", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents.router, prefix="/api/documents", tags=["documents"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(retrieval.router, prefix="/api/retrieval", tags=["retrieval"])

@app.get("/health")
async def health():
    return {"status": "ok"}