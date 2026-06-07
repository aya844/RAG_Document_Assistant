from fastapi import APIRouter, UploadFile, File, HTTPException
from app.storage.database import get_all_documents

router = APIRouter()


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    # Implemented in Phase 2
    return {"message": "not implemented yet"}


@router.get("/")
async def list_documents():
    return await get_all_documents()