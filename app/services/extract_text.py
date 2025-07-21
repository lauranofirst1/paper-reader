# app/services/extract_text.py

import fitz  # PyMuPDF
import re
import os
from typing import List, Dict, Any
from app.utils.logger import get_logger

# 로깅 설정
logger = get_logger(__name__)

class PDFExtractionError(Exception):
    """PDF 추출 관련 커스텀 예외"""
    pass

def extract_text_from_pdf(pdf_path: str) -> List[Dict[str, Any]]:
    """
    PDF 파일에서 텍스트를 추출합니다.
    
    Args:
        pdf_path: PDF 파일 경로
        
    Returns:
        페이지별 텍스트 정보가 담긴 리스트
        
    Raises:
        PDFExtractionError: PDF 처리 중 오류 발생 시
        FileNotFoundError: 파일이 존재하지 않을 때
    """
    # 파일 존재 확인
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF 파일을 찾을 수 없습니다: {pdf_path}")
    
    # 파일 크기 확인
    file_size = os.path.getsize(pdf_path)
    if file_size == 0:
        raise PDFExtractionError("PDF 파일이 비어있습니다.")
    
    if file_size > 100 * 1024 * 1024:  # 100MB
        raise PDFExtractionError("PDF 파일이 너무 큽니다. 최대 100MB까지 지원합니다.")
    
    try:
        # PDF 문서 열기
        doc = fitz.open(pdf_path)
        logger.info(f"PDF 열기 성공: {pdf_path}, 페이지 수: {len(doc)}")
        
        if len(doc) == 0:
            raise PDFExtractionError("PDF 파일에 페이지가 없습니다.")
        
        pages = []
        
        for i, page in enumerate(doc):
            try:
                # 페이지 텍스트 추출
                text = page.get_text("text")
                
                if not text or not text.strip():
                    logger.warning(f"페이지 {i+1}에서 텍스트를 추출할 수 없습니다.")
                    pages.append({
                        "page": i + 1,
                        "paragraphs": [],
                        "error": "텍스트를 추출할 수 없습니다."
                    })
                    continue
                
                # 문장 분리
                sentences = split_into_sentences(text)
                
                if not sentences:
                    logger.warning(f"페이지 {i+1}에서 유효한 문장을 찾을 수 없습니다.")
                    pages.append({
                        "page": i + 1,
                        "paragraphs": [],
                        "error": "유효한 문장을 찾을 수 없습니다."
                    })
                    continue
                
                pages.append({
                    "page": i + 1,
                    "paragraphs": sentences,
                    "text_length": len(text),
                    "sentence_count": len(sentences)
                })
                
                logger.debug(f"페이지 {i+1} 처리 완료: {len(sentences)}개 문장")
                
            except Exception as e:
                logger.error(f"페이지 {i+1} 처리 중 오류: {e}")
                pages.append({
                    "page": i + 1,
                    "paragraphs": [],
                    "error": f"페이지 처리 중 오류: {str(e)}"
                })
        
        doc.close()
        
        # 성공적으로 추출된 페이지가 있는지 확인
        successful_pages = [p for p in pages if "error" not in p]
        if not successful_pages:
            raise PDFExtractionError("모든 페이지에서 텍스트 추출에 실패했습니다.")
        
        logger.info(f"PDF 텍스트 추출 완료: {len(successful_pages)}/{len(pages)} 페이지 성공")
        return pages
        
    except fitz.FileDataError as e:
        logger.error(f"PDF 파일 데이터 오류: {e}")
        raise PDFExtractionError("PDF 파일이 손상되었거나 읽을 수 없습니다.")
    except fitz.PasswordError as e:
        logger.error(f"PDF 암호 오류: {e}")
        raise PDFExtractionError("PDF 파일이 암호로 보호되어 있습니다.")
    except Exception as e:
        logger.error(f"PDF 처리 중 예상치 못한 오류: {e}")
        raise PDFExtractionError(f"PDF 처리 중 오류가 발생했습니다: {str(e)}")

def split_into_sentences(text: str) -> List[str]:
    """
    텍스트를 문장 단위로 분리합니다.
    
    Args:
        text: 분리할 텍스트
        
    Returns:
        문장 리스트
    """
    try:
        # 줄바꿈 제거하고, 공백 하나로 정리
        text = re.sub(r'\s*\n\s*', ' ', text).strip()
        
        if not text:
            return []
        
        # 마침표, 느낌표, 물음표 기준으로 문장 분리
        raw_sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z가-힣])', text)
        
        # 문장이 너무 짧거나 의미 없는 건 제외
        sentences = [s.strip() for s in raw_sentences if len(s.strip()) > 10]
        
        # 문장들을 단락 단위로 묶기 (2문장씩)
        paragraphs = []
        temp = []
        for s in sentences:
            temp.append(s)
            if len(temp) >= 2:  # 2문장씩 묶어서 하나의 단락
                paragraphs.append(' '.join(temp))
                temp = []
        if temp:
            paragraphs.append(' '.join(temp))

        return paragraphs
        
    except Exception as e:
        logger.error(f"문장 분리 중 오류: {e}")
        return []

# 텍스트 추출과 요약은 별도 서비스에서 처리하도록 분리
