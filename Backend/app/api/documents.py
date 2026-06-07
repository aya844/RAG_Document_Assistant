import os
import uuid
import logging
from fastapi import APIRouter, UploadFile, File, HTTPException
from qdrant_client.models import PointStruct

from app.config import get_settings
from app.dependencies import get_qdrant_client
from app.storage.database import (
    insert_document,
    insert_parent_chunk,
    get_all_documents,
)
from app.ingestion.parser import parse_file
from app.ingestion.chunker import create_parent_child_chunks
from app.ingestion.embedder import embed_texts
from app.retrieval.sparse import get_bm25_index, BM25Document

settings = get_settings()
router = APIRouter()
logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".pdf", ".txt"}


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    # --- Validate ---
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")

    # --- Save file ---
    doc_id = str(uuid.uuid4())
    save_path = os.path.join(settings.upload_dir, f"{doc_id}{ext}")
    content = await file.read()
    with open(save_path, "wb") as f:
        f.write(content)

    try:
        # --- Parse ---
        logger.info(f"Parsing {file.filename}")
        pages = parse_file(save_path)
        if not pages:
            raise HTTPException(status_code=422, detail="Could not extract text from document")

        # --- Chunk ---
        logger.info(f"Chunking document {doc_id}")
        parents, children = create_parent_child_chunks(pages, doc_id)
        logger.info(f"Created {len(parents)} parents, {len(children)} children")

        # --- Embed children ---
        logger.info(f"Embedding {len(children)} child chunks...")
        child_texts = [c.content for c in children]
        embeddings = await embed_texts(child_texts)

        # --- Store parents in SQLite ---
        await insert_document(doc_id, file.filename, ext.lstrip("."))
        for parent in parents:
            await insert_parent_chunk(
                chunk_id=parent.id,
                document_id=parent.document_id,
                content=parent.content,
                chunk_index=parent.chunk_index,
                page_number=parent.page_number,
            )

        # --- Store child chunks in Qdrant ---
        qdrant = get_qdrant_client()
        points = [
            PointStruct(
                id=child.id,
                vector=embeddings[i],
                payload={
                    "document_id": child.document_id,
                    "parent_id": child.parent_id,
                    "content": child.content,
                    "chunk_index": child.chunk_index,
                    "page_number": child.page_number,
                    "filename": file.filename,
                },
            )
            for i, child in enumerate(children)
        ]
        await qdrant.upsert(
            collection_name=settings.qdrant_collection,
            points=points,
        )

        # --- Update BM25 index ---
        bm25_index = get_bm25_index()
        bm25_docs = [
            BM25Document(
                chunk_id=child.id,
                parent_id=child.parent_id,
                document_id=child.document_id,
                content=child.content,
                page_number=child.page_number,
            )
            for child in children
        ]
        bm25_index.add_documents(bm25_docs)
        bm25_index.save()

        logger.info(f"Document {doc_id} ingested successfully")
        return {
            "document_id": doc_id,
            "filename": file.filename,
            "pages": len(pages),
            "parent_chunks": len(parents),
            "child_chunks": len(children),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Ingestion failed for {file.filename}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def list_documents():
    return await get_all_documents()