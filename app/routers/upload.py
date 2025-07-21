# app/routers/upload.py
from fastapi import APIRouter, File, UploadFile, HTTPException, status
from fastapi.responses import JSONResponse
from app.services.extract_text import extract_text_from_pdf
import os
from uuid import uuid4
from typing import Dict, Any
from app.utils.logger import get_logger

# 로깅 설정
logger = get_logger(__name__)

router = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 허용된 파일 형식
ALLOWED_EXTENSIONS = {".pdf"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

def validate_file(file: UploadFile) -> None:
    """파일 유효성 검증"""
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="파일명이 없습니다."
        )
    
    # 파일 확장자 검증
    file_extension = os.path.splitext(file.filename)[1].lower()
    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"지원하지 않는 파일 형식입니다. 허용된 형식: {', '.join(ALLOWED_EXTENSIONS)}"
        )

# PDF 파일을 업로드하고 텍스트를 추출합니다.
@router.post("/upload-pdf/")
async def upload_pdf(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    PDF 파일을 업로드하고 텍스트를 추출합니다.
    """
    try:
        # 파일 유효성 검증
        validate_file(file)
        
        # 파일 크기 검증
        file_content = await file.read()
        if len(file_content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"파일 크기가 너무 큽니다. 최대 크기: {MAX_FILE_SIZE // (1024*1024)}MB"
            )
        
        # 파일 저장
        file_id = str(uuid4())
        file_path = os.path.join(UPLOAD_DIR, f"{file_id}.pdf")
        
        try:
            with open(file_path, "wb") as f:
                f.write(file_content)
            logger.info(f"파일 업로드 성공: {file_id}")
        except IOError as e:
            logger.error(f"파일 저장 실패: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="파일 저장 중 오류가 발생했습니다."
            )
        
        # PDF 텍스트 추출
        try:
            pages = extract_text_from_pdf(file_path)
            logger.info(f"텍스트 추출 성공: {file_id}, 페이지 수: {len(pages)}")
        except Exception as e:
            logger.error(f"PDF 텍스트 추출 실패: {e}")
            # 업로드된 파일 삭제
            try:
                os.remove(file_path)
            except:
                pass
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="PDF 파일을 읽을 수 없습니다. 파일이 손상되었거나 암호화되어 있을 수 있습니다."
            )
        
        return {
            "file_id": file_id,
            "total_pages": len(pages),
            "content": pages,
            "filename": file.filename,
            "file_size": len(file_content)
        }
        
    except HTTPException:
        # HTTPException은 그대로 재발생
        raise
    except Exception as e:
        logger.error(f"예상치 못한 오류 발생: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="서버 내부 오류가 발생했습니다."
        )
