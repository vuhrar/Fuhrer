# file_processing.py
"""
معالجة الملفات والمستندات القانونية — نسخة CLI
تمت إزالة واجهات Streamlit. توجد الآن دوال مساعدة لتشغيل المعالجة من CLI أو من كود آخر.
"""

import io
import os
import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)


# (ابقينا الدوال الأساسية لاستخراج النص كما كانت)

def extract_text_from_file(uploaded_file) -> dict:
    """
    استخراج النص من ملف.
    المدخل: كائن ملف ثنائي مع خاصية .name و .read().
    """
    filename = getattr(uploaded_file, 'name', 'unknown')
    ext = os.path.splitext(filename)[1].lower()
    result = {"success": False, "text": "", "filename": filename, "pages": 0, "error": ""}

    try:
        if ext == ".txt":
            content = uploaded_file.read()
            for enc in ("utf-8", "windows-1256", "utf-16", "latin-1"):
                try:
                    text = content.decode(enc)
                    result.update({"success": True, "text": text.strip(), "pages": 1})
                    return result
                except Exception:
                    continue
            result["error"] = "تعذّر قراءة الملف النصي — ترميز غير معروف"
            return result
        elif ext == ".pdf":
            # استنساخ من النسخة السابقة: استخدام PyMuPDF ثم pypdf ثم OCR
            content = uploaded_file.read()
            try:
                import fitz
                doc = fitz.open(stream=content, filetype='pdf')
                pages_text = [p.get_text() for p in doc]
                text = "\n\n".join(pages_text).strip()
                if text:
                    result.update({"success": True, "text": text, "pages": len(doc)})
                    return result
            except Exception:
                pass
            try:
                from pypdf import PdfReader
                reader = PdfReader(io.BytesIO(content))
                pages_text = [p.extract_text() or "" for p in reader.pages]
                text = "\n\n".join(pages_text).strip()
                if text:
                    result.update({"success": True, "text": text, "pages": len(reader.pages)})
                    return result
            except Exception:
                pass
            try:
                from pdf2image import convert_from_bytes
                import pytesseract
                from PIL import Image
                images = convert_from_bytes(content, dpi=200)
                pages_text = [pytesseract.image_to_string(img, lang='ara+eng') for img in images]
                text = "\n\n".join(pages_text).strip()
                if text:
                    result.update({"success": True, "text": text, "pages": len(images)})
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
                text = "\n".join(paragraphs)
                result.update({"success": True, "text": text, "pages": 1})
                return result
            except Exception as e:
                result['error'] = f"خطأ في قراءة DOCX: {e}"
                return result
        elif ext == '.json':
            try:
                data = json.loads(uploaded_file.read().decode('utf-8'))
                text = json.dumps(data, ensure_ascii=False, indent=2)
                result.update({"success": True, "text": text, "pages": 1})
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
                result.update({"success": True, "text": text, "pages": 1})
                return result
            except Exception as e:
                result['error'] = f"خطأ في قراءة CSV: {e}"
                return result
        elif ext in ('.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp'):
            try:
                import pytesseract
                from PIL import Image
                img = Image.open(io.BytesIO(uploaded_file.read()))
                text = pytesseract.image_to_string(img, lang='ara+eng')
                result.update({"success": True, "text": text.strip(), "pages": 1})
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
