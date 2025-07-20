# app/services/extract_text.py
# import fitz  # PyMuPDF

# def extract_text_from_pdf(file_path: str):
#     doc = fitz.open(file_path)
#     result = []

#     for page_num, page in enumerate(doc, start=1):
#         text = page.get_text()
#         result.append({
#             "page": page_num,
#             "text": text.strip()
#         })

#     return result

# if __name__ == "__main__":
#     result = extract_text_from_pdf("uploads/sample.pdf")
#     for page in result:
#         print(f"\n--- Page {page['page']} ---\n{page['text'][:500]}")

import fitz  # PyMuPDF
import re

def extract_text_by_page(pdf_path):
    doc = fitz.open(pdf_path)
    pages = []

    for i, page in enumerate(doc):
        text = page.get_text("text")
        sentences = split_into_sentences(text)
        pages.append({
            "page": i + 1,
            "paragraphs": sentences
        })

    return pages

def split_into_sentences(text):
    # 줄바꿈 제거하고, 공백 하나로 정리
    text = re.sub(r'\s*\n\s*', ' ', text).strip()
    
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


if __name__ == "__main__":
    pdf_path = "uploads/sample.pdf"  # 너가 테스트하는 PDF 경로
    result = extract_text_by_page(pdf_path)

    for page in result:
        print(f"[Page {page['page']}]")
        for idx, para in enumerate(page["paragraphs"], start=1):
            print(f"[Paragraph {idx}]\n{para}\n")
