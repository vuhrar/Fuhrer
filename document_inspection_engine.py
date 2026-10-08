"""فحص حتمي قابل للتدقيق للمرفقات القانونية.

يفحص كل ملف عبر file_processing، ويحوّل النتيجة إلى سجل تغطية واضح.
لا يعتبر الملف مفحوصًا بالكامل إذا فشل استخراج النص أو كان النص فارغًا.
"""
from __future__ import annotations

import hashlib
import re
from typing import Any, Dict, Iterable, List

from file_processing import extract_structured_signals, extract_text_from_file

SUPPORTED_EXTENSIONS = {".txt", ".pdf", ".docx", ".doc", ".json", ".csv", ".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp"}


def _excerpt(text: str, start: int, end: int, radius: int = 110) -> str:
    left = max(0, start - radius)
    right = min(len(text), end + radius)
    return " ".join(text[left:right].split())


def _find_occurrences(text: str, terms: Iterable[str], limit: int = 8) -> List[Dict[str, Any]]:
    found: List[Dict[str, Any]] = []
    clean = text or ""
    for term in terms:
        if not term:
            continue
        for match in re.finditer(re.escape(term), clean, flags=re.IGNORECASE):
            found.append({"term": term, "start": match.start(), "end": match.end(), "excerpt": _excerpt(clean, match.start(), match.end())})
            if len(found) >= limit:
                return found
    return found


def inspect_file(file_object: Any, raw_bytes: bytes | None = None) -> Dict[str, Any]:
    filename = getattr(file_object, "name", "unknown")
    extension = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if raw_bytes is None:
        position = file_object.tell() if hasattr(file_object, "tell") else 0
        raw_bytes = file_object.read()
        if hasattr(file_object, "seek"):
            file_object.seek(position)
    digest = hashlib.sha256(raw_bytes or b"").hexdigest()
    result = extract_text_from_file(file_object)
    text = result.get("text", "") or ""
    signals = result.get("signals") or extract_structured_signals(text)
    readable = bool(result.get("success") and text.strip())
    status = "مقروء" if readable else ("امتداد غير مدعوم" if extension not in SUPPORTED_EXTENSIONS else "فشل الفحص")
    if readable and result.get("pages") == 0:
        status = "مقروء جزئيًا"
    issues = []
    if not readable:
        issues.append(result.get("error") or "لم يتم استخراج نص قابل للفحص")
    if extension in {".pdf", ".docx", ".doc"} and readable and len(text.strip()) < 40:
        status = "مقروء جزئيًا"
        issues.append("النص المستخرج قصير وقد يكون الملف مصورًا أو يحتوي جداول لم تُقرأ بالكامل")
    return {
        "filename": filename,
        "extension": extension,
        "mime_type": getattr(file_object, "content_type", "") or "",
        "byte_size": len(raw_bytes or b""),
        "source_hash": digest,
        "inspection_status": status,
        "readable": readable,
        "full_text_available": bool(text.strip()),
        "text": text,
        "pages": result.get("pages", 0),
        "characters_scanned": len(text),
        "words_approx": len(text.split()),
        "signals": signals,
        "errors": issues,
        "manual_review_required": status != "مقروء",
        "keyword_occurrences": {
            "dates": _find_occurrences(text, signals.get("dates", [])),
            "amounts": _find_occurrences(text, signals.get("amounts_or_pay_terms", [])),
            "articles": _find_occurrences(text, signals.get("legal_article_mentions", [])),
        },
    }


def inspect_batch(file_objects: List[Any]) -> Dict[str, Any]:
    results = []
    for file_object in file_objects:
        try:
            results.append(inspect_file(file_object))
        except Exception as exc:
            results.append({
                "filename": getattr(file_object, "name", "unknown"), "extension": "", "byte_size": 0,
                "source_hash": "", "inspection_status": "فشل الفحص", "readable": False,
                "full_text_available": False, "text": "", "pages": 0, "characters_scanned": 0,
                "words_approx": 0, "signals": {}, "errors": [str(exc)], "manual_review_required": True,
                "keyword_occurrences": {},
            })
    return coverage_summary(results) | {"results": results}


def coverage_summary(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    readable = [x for x in results if x.get("readable")]
    unreadable = [x for x in results if not x.get("readable")]
    partial = [x for x in results if x.get("inspection_status") == "مقروء جزئيًا"]
    return {
        "documents_total": len(results),
        "documents_read": len(readable),
        "documents_partial": len(partial),
        "documents_unreadable": len(unreadable),
        "documents_fully_inspected": len([x for x in results if x.get("inspection_status") == "مقروء"]),
        "characters_scanned": sum(x.get("characters_scanned", 0) for x in results),
        "pages_scanned": sum(x.get("pages", 0) for x in results),
        "unsupported_extensions": sorted({x.get("extension") for x in results if x.get("inspection_status") == "امتداد غير مدعوم"}),
        "manual_review_required": any(x.get("manual_review_required") for x in results),
        "status": "مكتمل ضمن الملفات القابلة للقراءة" if not unreadable else "غير مكتمل — توجد ملفات لم تُقرأ بالكامل",
    }
