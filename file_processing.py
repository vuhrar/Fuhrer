# file_processing.py
"""
معالجة الملفات والمستندات القانونية — نسخة CLI
تمت إزالة واجهات Streamlit. توجد الآن دوال مساعدة لتشغيل المعالجة من CLI أو من كود آخر.
"""

import io
import os
import json
import logging
import re
import statistics
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

DATE_PATTERN = re.compile(r"(?:\d{1,4}[/-]\d{1,2}[/-]\d{1,4}|\d{1,2}\s+(?:يناير|فبراير|مارس|أبريل|مايو|يونيو|يوليو|أغسطس|سبتمبر|أكتوبر|نوفمبر|ديسمبر)\s+\d{4})")
AMOUNT_PATTERN = re.compile(r"(?:\d[\d,\.]*\s*(?:ريال|ر\.س|ر\.س\.?|SAR)|(?:راتب|أجر|مبلغ|خصم)[^؛.\n]{0,80})", re.IGNORECASE)
EMAIL_PATTERN = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.IGNORECASE)
PHONE_PATTERN = re.compile(r"(?:\+?966|05)\s*[- ]?\d{8,9}")
ARTICLE_PATTERN = re.compile(r"(?:المادة|مادة)\s*\(?\s*\d{1,3}\s*\)?")


def extract_structured_signals(text: str) -> Dict[str, Any]:
    """استخراج إشارات قابلة للمراجعة؛ لا تُعامل كحقائق مثبتة أو تفسير قانوني."""
    clean = text or ""
    def unique(pattern: re.Pattern[str]) -> list[str]:
        return list(dict.fromkeys(m.group(0).strip() for m in pattern.finditer(clean)))
    return {
        "dates": unique(DATE_PATTERN),
        "amounts_or_pay_terms": unique(AMOUNT_PATTERN),
        "emails": unique(EMAIL_PATTERN),
        "phones": unique(PHONE_PATTERN),
        "legal_article_mentions": unique(ARTICLE_PATTERN),
        "characters": len(clean),
        "words_approx": len(clean.split()),
        "needs_human_verification": True,
    }


def _ocr_image(image) -> tuple[str, Optional[float]]:
    """OCR عربي/إنجليزي مع تحسينات محافظة وإرجاع متوسط الثقة إن أمكن."""
    import pytesseract
    from PIL import ImageOps, ImageFilter
    image = ImageOps.exif_transpose(image).convert("L")
    if image.width < 1600:
        scale = 1600 / max(1, image.width)
        image = image.resize((int(image.width * scale), int(image.height * scale)))
    image = ImageOps.autocontrast(image).filter(ImageFilter.SHARPEN)
    config = "--oem 3 --psm 6"
    try:
        data = pytesseract.image_to_data(image, lang="ara+eng", config=config, output_type=pytesseract.Output.DICT)
        words = [x for x in data.get("text", []) if x and x.strip()]
        confidences = []
        for value in data.get("conf", []):
            try:
                number = float(value)
                if number >= 0:
                    confidences.append(number)
            except (TypeError, ValueError):
                continue
        return " ".join(words).strip(), round(statistics.mean(confidences) / 100, 3) if confidences else None
    except Exception:
        return pytesseract.image_to_string(image, lang="ara+eng", config=config).strip(), None


def _pdf_pages(content: bytes) -> tuple[list[dict], list[dict]]:
    """استخراج صفحات PDF، مع OCR للصفحات التي لا تحتوي نصًا، دون إسقاط الصفحة."""
    import fitz
    from PIL import Image
    doc = fitz.open(stream=content, filetype="pdf")
    pages, tables = [], []
    for number, page in enumerate(doc, 1):
        text = (page.get_text("text") or "").strip()
        method, confidence = "text", None
        if not text or len(text) < 20:
            pix = page.get_pixmap(matrix=fitz.Matrix(2.2, 2.2), alpha=False)
            image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            text, confidence = _ocr_image(image)
            method = "ocr" if text else "ocr_failed"
        pages.append({"page": number, "text": text, "method": method, "ocr_confidence": confidence, "characters": len(text)})
        try:
            for table in page.find_tables().tables:
                rows = table.extract()
                if rows:
                    tables.append({"page": number, "source": "pdf_table", "rows": [[str(cell or "").strip() for cell in row] for row in rows]})
        except Exception:
            pass
    return pages, tables


# (ابقينا الدوال الأساسية لاستخراج النص كما كانت)

def extract_text_from_file(uploaded_file) -> dict:
    """
    استخراج النص من ملف.
    المدخل: كائن ملف ثنائي مع خاصية .name و .read().
    """
    filename = getattr(uploaded_file, 'name', 'unknown')
    ext = os.path.splitext(filename)[1].lower()
    result = {"success": False, "text": "", "filename": filename, "pages": 0, "error": "", "signals": {}}

    try:
        if ext == ".txt":
            content = uploaded_file.read()
            for enc in ("utf-8", "windows-1256", "utf-16", "latin-1"):
                try:
                    text = content.decode(enc)
                    text = text.strip()
                    result.update({"success": True, "text": text, "pages": 1, "signals": extract_structured_signals(text)})
                    return result
                except Exception:
                    continue
            result["error"] = "تعذّر قراءة الملف النصي — ترميز غير معروف"
            return result
        elif ext == ".pdf":
            content = uploaded_file.read()
            try:
                pages, tables = _pdf_pages(content)
                text = "\n\n".join(x["text"] for x in pages if x["text"]).strip()
                confidence_values = [x["ocr_confidence"] for x in pages if x.get("ocr_confidence") is not None]
                result.update({"success": bool(text), "text": text, "pages": len(pages), "signals": extract_structured_signals(text), "page_records": pages, "tables": tables, "extraction_method": "mixed_text_ocr" if any(x["method"] != "text" for x in pages) else "text", "ocr_confidence": round(statistics.mean(confidence_values), 3) if confidence_values else None})
                if result["success"]:
                    return result
            except Exception:
                pass
            result["error"] = "تعذّر استخراج النص من ملف PDF"
            return result
        elif ext in ('.docx', '.doc'):
            try:
                from docx import Document
                doc = Document(io.BytesIO(uploaded_file.read()))
                paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
                tables = []
                for table in doc.tables:
                    for row in table.rows:
                        tables.append(" | ".join(cell.text.strip() for cell in row.cells))
                text = "\n".join(paragraphs + tables)
                result.update({"success": True, "text": text, "pages": 1, "signals": extract_structured_signals(text), "page_records": [{"page": 1, "text": text, "method": "text", "ocr_confidence": None, "characters": len(text)}], "tables": [{"page": 1, "source": "docx_table", "rows": [row.split(" | ") for row in tables]}] if tables else [], "extraction_method": "text_tables" if tables else "text"})
                return result
            except Exception as e:
                result['error'] = f"خطأ في قراءة DOCX: {e}"
                return result
        elif ext == '.json':
            try:
                data = json.loads(uploaded_file.read().decode('utf-8'))
                text = json.dumps(data, ensure_ascii=False, indent=2)
                result.update({"success": True, "text": text, "pages": 1, "signals": extract_structured_signals(text), "page_records": [{"page": 1, "text": text, "method": "text", "ocr_confidence": None, "characters": len(text)}], "tables": [], "extraction_method": "text"})
                return result
            except Exception as e:
                result['error'] = f"خطأ في قراءة JSON: {e}"
                return result
        elif ext == '.csv':
            try:
                import csv
                content = uploaded_file.read().decode('utf-8', errors='replace')
                reader = csv.reader(content.splitlines())
                rows = ["\t".join(row) for row in reader]
                text = "\n".join(rows)
                result.update({"success": True, "text": text, "pages": 1, "signals": extract_structured_signals(text), "page_records": [{"page": 1, "text": text, "method": "text", "ocr_confidence": None, "characters": len(text)}], "tables": [{"page": 1, "source": "csv", "rows": [row.split("\t") for row in rows]}], "extraction_method": "table"})
                return result
            except Exception as e:
                result['error'] = f"خطأ في قراءة CSV: {e}"
                return result
        elif ext in ('.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp'):
            try:
                from PIL import Image
                img = Image.open(io.BytesIO(uploaded_file.read()))
                text, confidence = _ocr_image(img)
                result.update({"success": True, "text": text.strip(), "pages": 1, "signals": extract_structured_signals(text), "page_records": [{"page": 1, "text": text.strip(), "method": "ocr", "ocr_confidence": confidence, "characters": len(text.strip())}], "tables": [], "extraction_method": "ocr", "ocr_confidence": confidence})
                return result
            except Exception as e:
                result['error'] = f"خطأ في OCR: {e}"
                return result
        else:
            result['error'] = f"نوع الملف غير مدعوم: {ext}"
            return result
    except Exception as e:
        result['error'] = f"خطأ في معالجة الملف: {e}"
        logger.error(f"Error processing {filename}: {e}", exc_info=True)
        return result


def process_multiple_files(file_objects: list) -> dict:
    """معالجة قائمة من كائنات الملفات الثنائية وإرجاع ملخص ونصوص جاهزة للـ AI."""
    texts = []
    results = []
    success_count = 0
    failed_count = 0

    for f in file_objects:
        res = extract_text_from_file(f)
        results.append(res)
        if res["success"] and res["text"]:
            texts.append(f"=== {res['filename']} ===\n{res['text']}")
            success_count += 1
        else:
            failed_count += 1

    return {
        "texts": [truncate_for_ai(t, 3000) for t in texts],
        "results": results,
        "total": len(file_objects),
        "success": success_count,
        "failed": failed_count,
    }


def truncate_for_ai(text: str, max_chars: int = 4000) -> str:
    if len(text) <= max_chars:
        return text
    half = max_chars // 2
    return (
        text[:half]
        + f"\n\n[... تم حذف {len(text) - max_chars} حرف للاختصار ...]\n\n"
        + text[-half:]
    )
