# file_processing.py
"""
استخراج النص من الملفات المنقولة (PDF, DOCX, TXT, صور).
يدعم:
- PDF (مع OCR إذا لزم الأمر)
- DOCX
- TXT
- صور (PNG, JPG) مع OCR
"""

import io
import re
import logging
from typing import List, Dict
from PIL import Image
import pytesseract

logger = logging.getLogger("file_processing")

def extract_text_from_file(uploaded_file) -> str:
    """استخراج نص من أي ملف مدعوم."""
    name = uploaded_file.name.lower()
    raw = uploaded_file.read()
    uploaded_file.seek(0)

    if name.endswith(".txt"):
        return _extract_text_from_txt(raw)
    elif name.endswith(".pdf"):
        return _extract_text_from_pdf(raw, name)
    elif name.endswith(".docx"):
        return _extract_text_from_docx(raw)
    elif name.endswith(".json"):
        return _extract_text_from_json(raw)
    elif name.endswith((".png", ".jpg", ".jpeg", ".bmp", ".tiff")):
        return _extract_text_from_image(raw)
    else:
        try:
            return raw.decode("utf-8", errors="replace")[:5000]
        except:
            return "⚠️  نوع ملف غير مدعوم."

def _extract_text_from_txt(raw: bytes) -> str:
    """استخراج نص من ملف TXT"""
    for enc in ["utf-8", "utf-8-sig", "cp1256", "latin-1", "iso-8859-6"]:
        try:
            return raw.decode(enc)
        except Exception:
            continue
    return raw.decode("utf-8", errors="replace")

def _extract_text_from_pdf(raw: bytes, filename: str) -> str:
    """استخراج نص من ملف PDF"""
    # محاولة 1: PyMuPDF (الأفضل للنص العربي)
    try:
        import fitz
        doc = fitz.open(stream=raw, filetype="pdf")
        text = "\n".join(page.get_text("text") for page in doc)
        if len(text.strip()) > 50:
            return text
    except Exception as e:
        logger.warning(f"PyMuPDF failed: {e}")

    # محاولة 2: pypdf
    try:
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(raw))
        text = "\n".join(p.extract_text() or "" for p in reader.pages)
        if len(text.strip()) > 50:
            return text
    except Exception as e:
        logger.warning(f"pypdf failed: {e}")

    # محاولة 3: OCR إذا كان PDF صورة
    try:
        images = _convert_pdf_to_images(raw)
        full_text = ""
        for img in images:
            text = pytesseract.image_to_string(img, lang='ara+eng')
            full_text += text + "\n"
        if len(full_text.strip()) > 50:
            return full_text
    except Exception as e:
        logger.warning(f"OCR failed: {e}")

    return "⚠️  لم يتم استخراج نص من هذا الملف (قد يكون ملفاً مسحوباً يحتاج OCR)."

def _extract_text_from_docx(raw: bytes) -> str:
    """استخراج نص من ملف DOCX"""
    try:
        from docx import Document
        doc = Document(io.BytesIO(raw))
        text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
        if len(text.strip()) > 10:
            return text
    except Exception as e:
        logger.warning(f"docx extraction failed: {e}")
    return "⚠️  خطأ في قراءة ملف DOCX. تأكد من أن الملف ليس من نوع DOC القديم."

def _extract_text_from_json(raw: bytes) -> str:
    """استخراج نص من ملف JSON"""
    try:
        import json
        data = json.loads(raw)
        return json.dumps(data, ensure_ascii=False, indent=2)[:8000]
    except Exception:
        return raw.decode("utf-8", errors="replace")[:8000]

def _extract_text_from_image(raw: bytes) -> str:
    """استخراج نص من صورة باستخدام OCR"""
    try:
        img = Image.open(io.BytesIO(raw))
        text = pytesseract.image_to_string(img, lang='ara+eng')
        if len(text.strip()) > 10:
            return text
        return "⚠️  لم يتم العثور على نص في الصورة."
    except Exception as e:
        logger.warning(f"Image OCR failed: {e}")
        return "⚠️  خطأ في استخراج النص من الصورة."

def _convert_pdf_to_images(pdf_bytes: bytes, dpi: int = 300, first_page: int = 1, last_page: int = 5):
    """تحويل صفحات PDF إلى صور"""
    try:
        from pdf2image import convert_from_bytes
        images = convert_from_bytes(pdf_bytes, dpi=dpi, first_page=first_page, last_page=last_page)
        return images
    except ImportError:
        logger.warning("pdf2image not installed. Install with: pip install pdf2image")
        return []
    except Exception as e:
        logger.warning(f"PDF to image conversion failed: {e}")
        return []

def process_multiple_files(uploaded_files) -> List[Dict]:
    """معالجة ملفات متعددة."""
    results = []
    for uploaded_file in uploaded_files:
        try:
            text = extract_text_from_file(uploaded_file)
            results.append({
                "filename": uploaded_file.name,
                "size": len(uploaded_file.read()),
                "text": text,
                "success": len(text.strip()) > 10
            })
            uploaded_file.seek(0)
        except Exception as e:
            results.append({
                "filename": uploaded_file.name,
                "error": str(e),
                "text": "",
                "success": False
            })
    return results