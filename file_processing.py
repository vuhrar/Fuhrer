# file_processing.py
"""
معالجة الملفات والمستندات القانونية — النسخة الاحترافية v2.0
يدعم: PDF, DOCX, TXT, PNG/JPG (OCR), JSON, CSV
"""

import io
import os
import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)


# ============================================================
# استخراج النص من الملفات
# ============================================================

def extract_text_from_file(uploaded_file) -> dict:
    """
    استخراج النص من ملف مرفوع.
    يعيد: {"success": bool, "text": str, "filename": str, "pages": int, "error": str}
    """
    filename = uploaded_file.name
    ext = os.path.splitext(filename)[1].lower()
    result = {"success": False, "text": "", "filename": filename, "pages": 0, "error": ""}

    try:
        if ext == ".txt":
            result = _extract_txt(uploaded_file, result)
        elif ext == ".pdf":
            result = _extract_pdf(uploaded_file, result)
        elif ext in (".docx", ".doc"):
            result = _extract_docx(uploaded_file, result)
        elif ext == ".json":
            result = _extract_json(uploaded_file, result)
        elif ext == ".csv":
            result = _extract_csv(uploaded_file, result)
        elif ext in (".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp"):
            result = _extract_image_ocr(uploaded_file, result)
        else:
            result["error"] = f"نوع الملف غير مدعوم: {ext}"
    except Exception as e:
        result["error"] = f"خطأ في معالجة الملف: {str(e)}"
        logger.error(f"Error processing {filename}: {e}", exc_info=True)

    return result


def _extract_txt(uploaded_file, result: dict) -> dict:
    """استخراج نص من ملف TXT."""
    content = uploaded_file.read()
    # محاولة UTF-8 ثم Windows-1256 (عربي)
    for enc in ("utf-8", "windows-1256", "utf-16", "latin-1"):
        try:
            text = content.decode(enc)
            result.update({"success": True, "text": text.strip(), "pages": 1})
            return result
        except (UnicodeDecodeError, LookupError):
            continue
    result["error"] = "تعذّر قراءة الملف النصي — ترميز غير معروف"
    return result


def _extract_pdf(uploaded_file, result: dict) -> dict:
    """استخراج نص من PDF — يجرب pymupdf ثم pypdf ثم OCR."""
    content = uploaded_file.read()

    # ── المحاولة 1: PyMuPDF (fitz) ──────────────────────────
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(stream=content, filetype="pdf")
        pages_text = []
        for page in doc:
            pages_text.append(page.get_text())
        text = "\n\n".join(pages_text).strip()
        if text:
            result.update({"success": True, "text": text, "pages": len(doc)})
            return result
    except ImportError:
        pass
    except Exception as e:
        logger.warning(f"PyMuPDF failed: {e}")

    # ── المحاولة 2: pypdf ────────────────────────────────────
    try:
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(content))
        pages_text = []
        for page in reader.pages:
            pages_text.append(page.extract_text() or "")
        text = "\n\n".join(pages_text).strip()
        if text:
            result.update({"success": True, "text": text, "pages": len(reader.pages)})
            return result
    except ImportError:
        pass
    except Exception as e:
        logger.warning(f"pypdf failed: {e}")

    # ── المحاولة 3: OCR عبر pdf2image + pytesseract ──────────
    try:
        from pdf2image import convert_from_bytes
        import pytesseract
        images = convert_from_bytes(content, dpi=200)
        pages_text = []
        for img in images:
            pages_text.append(pytesseract.image_to_string(img, lang="ara+eng"))
        text = "\n\n".join(pages_text).strip()
        if text:
            result.update({"success": True, "text": text, "pages": len(images)})
            return result
    except ImportError:
        pass
    except Exception as e:
        logger.warning(f"OCR failed: {e}")

    result["error"] = "تعذّر استخراج النص من ملف PDF"
    return result


def _extract_docx(uploaded_file, result: dict) -> dict:
    """استخراج نص من DOCX."""
    try:
        from docx import Document
        doc = Document(io.BytesIO(uploaded_file.read()))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        text = "\n".join(paragraphs)
        result.update({"success": True, "text": text, "pages": 1})
    except ImportError:
        result["error"] = "مكتبة python-docx غير مثبّتة"
    except Exception as e:
        result["error"] = f"خطأ في قراءة DOCX: {e}"
    return result


def _extract_json(uploaded_file, result: dict) -> dict:
    """استخراج نص من JSON."""
    try:
        data = json.loads(uploaded_file.read().decode("utf-8"))
        text = json.dumps(data, ensure_ascii=False, indent=2)
        result.update({"success": True, "text": text, "pages": 1})
    except Exception as e:
        result["error"] = f"خطأ في قراءة JSON: {e}"
    return result


def _extract_csv(uploaded_file, result: dict) -> dict:
    """استخراج نص من CSV."""
    try:
        import csv
        content = uploaded_file.read().decode("utf-8", errors="replace")
        reader = csv.reader(content.splitlines())
        rows = ["\t".join(row) for row in reader]
        text = "\n".join(rows)
        result.update({"success": True, "text": text, "pages": 1})
    except Exception as e:
        result["error"] = f"خطأ في قراءة CSV: {e}"
    return result


def _extract_image_ocr(uploaded_file, result: dict) -> dict:
    """استخراج نص من صورة عبر OCR."""
    try:
        import pytesseract
        from PIL import Image
        img = Image.open(io.BytesIO(uploaded_file.read()))
        text = pytesseract.image_to_string(img, lang="ara+eng")
        result.update({"success": True, "text": text.strip(), "pages": 1})
    except ImportError:
        result["error"] = "مكتبة pytesseract أو Pillow غير مثبّتة"
    except Exception as e:
        result["error"] = f"خطأ في OCR: {e}"
    return result


# ============================================================
# معالجة ملفات متعددة
# ============================================================

def process_multiple_files(uploaded_files: list) -> dict:
    """
    معالجة قائمة من الملفات المرفوعة.
    يعيد: {"texts": [str], "results": [dict], "total": int, "success": int, "failed": int}
    """
    texts = []
    results = []
    success_count = 0
    failed_count = 0

    for f in uploaded_files:
        res = extract_text_from_file(f)
        results.append(res)
        if res["success"] and res["text"]:
            texts.append(f"=== {res['filename']} ===\n{res['text']}")
            success_count += 1
        else:
            failed_count += 1

    return {
        "texts": texts,
        "results": results,
        "total": len(uploaded_files),
        "success": success_count,
        "failed": failed_count,
    }


# ============================================================
# تقليص النص للذكاء الاصطناعي
# ============================================================

def truncate_for_ai(text: str, max_chars: int = 4000) -> str:
    """
    تقليص النص ليناسب نافذة السياق.
    يحتفظ بالبداية والنهاية لأنهما الأكثر أهمية في الوثائق القانونية.
    """
    if len(text) <= max_chars:
        return text
    half = max_chars // 2
    return (
        text[:half]
        + f"\n\n[... تم حذف {len(text) - max_chars} حرف للاختصار ...]\n\n"
        + text[-half:]
    )


# ============================================================
# واجهة Streamlit لرفع الملفات
# ============================================================

def render_file_upload_widget() -> list:
    """
    عرض واجهة رفع الملفات في Streamlit.
    يعيد قائمة نصوص المستندات المستخرجة.
    """
    import streamlit as st

    st.markdown("### 📎 رفع المستندات القانونية")
    st.markdown(
        "<div class='info-box'>يمكنك رفع عقود العمل، الرسائل، القرارات، أو أي وثيقة قانونية "
        "لتحليلها بالذكاء الاصطناعي. الصيغ المدعومة: PDF, DOCX, TXT, PNG, JPG, JSON</div>",
        unsafe_allow_html=True,
    )

    uploaded = st.file_uploader(
        "اختر الملفات:",
        type=["pdf", "docx", "doc", "txt", "png", "jpg", "jpeg", "json", "csv"],
        accept_multiple_files=True,
        key="doc_uploader",
    )

    if not uploaded:
        return []

    with st.spinner(f"جاري معالجة {len(uploaded)} ملف..."):
        batch = process_multiple_files(uploaded)

    if batch["success"] > 0:
        st.success(f"✅ تم استخراج النص من {batch['success']} ملف بنجاح")
    if batch["failed"] > 0:
        st.warning(f"⚠️ فشل استخراج {batch['failed']} ملف")

    for res in batch["results"]:
        icon = "✅" if res["success"] else "❌"
        label = f"{icon} {res['filename']}"
        if res["success"]:
            with st.expander(label):
                preview = res["text"][:500] + ("..." if len(res["text"]) > 500 else "")
                st.markdown(f"**الصفحات:** {res['pages']} | **الأحرف:** {len(res['text']):,}")
                st.text_area("معاينة:", value=preview, height=120, disabled=True, key=f"prev_{res['filename']}")
        else:
            st.error(f"{label}: {res['error']}")

    return [truncate_for_ai(t, 3000) for t in batch["texts"]]
