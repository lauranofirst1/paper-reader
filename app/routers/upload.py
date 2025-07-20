# app/routers/upload.py
from fastapi import APIRouter, File, UploadFile
from app.services.extract_text import extract_text_from_pdf
import os
from uuid import uuid4

router = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload-pdf/")
async def upload_pdf(file: UploadFile = File(...)):
    file_id = str(uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{file_id}.pdf")

    with open(file_path, "wb") as f:
        f.write(await file.read())

    pages = extract_text_from_pdf(file_path)

    return {
        "file_id": file_id,
        "total_pages": len(pages),
        "content": pages
    }
