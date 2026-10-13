"""مكتبة أنظمة المستخدم: رفع، استخراج، تشفير، وفهرسة نصوص الأنظمة."""
from __future__ import annotations

import hashlib
import json
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import file_processing
import workspace_store

DATA_DIR = Path(workspace_store.DATA_DIR)
LIBRARY_DIR = DATA_DIR / "legal_library"
LIBRARY_DIR.mkdir(parents=True, exist_ok=True)
INDEX_PATH = LIBRARY_DIR / "index.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load() -> List[Dict[str, Any]]:
    if not INDEX_PATH.exists():
        return []
    try:
        return json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []


def _save(items: List[Dict[str, Any]]) -> None:
    temp = INDEX_PATH.with_suffix(".tmp")
    temp.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
    os.chmod(temp, 0o600)
    temp.replace(INDEX_PATH)


def _safe_name(value: str) -> str:
    return re.sub(r"[^\w\-.ء-ي]+", "_", value, flags=re.UNICODE)[:100] or "source"


def add_source(filename: str, raw_bytes: bytes, *, title: str = "", authority: str = "", status: str = "يحتاج تحقق", notes: str = "") -> Dict[str, Any]:
    if not raw_bytes:
        raise ValueError("الملف فارغ")
    file_obj = __import__("io").BytesIO(raw_bytes)
    file_obj.name = filename
    extracted = file_processing.extract_text_from_file(file_obj)
    if not extracted.get("success") or not extracted.get("text", "").strip():
        raise ValueError(extracted.get("error") or "تعذر استخراج نص النظام")
    source_id = f"law_{uuid.uuid4().hex[:14]}"
    source_hash = hashlib.sha256(raw_bytes).hexdigest()
    blob_path = LIBRARY_DIR / f"{source_id}.bin.enc"
    text_path = LIBRARY_DIR / f"{source_id}.txt.enc"
    blob_path.write_bytes(workspace_store.encrypt_bytes(raw_bytes))
    text_path.write_bytes(workspace_store.encrypt_bytes(extracted["text"].encode("utf-8")))
    os.chmod(blob_path, 0o600)
    os.chmod(text_path, 0o600)
    item = {
        "id": source_id,
        "title": (title or Path(filename).stem).strip()[:300],
        "authority": authority.strip()[:200],
        "status": status.strip()[:80] or "يحتاج تحقق",
        "notes": notes.strip()[:2000],
        "filename": filename,
        "mime_type": extracted.get("mime_type", "") or "application/octet-stream",
        "source_hash": source_hash,
        "byte_size": len(raw_bytes),
        "characters": len(extracted["text"]),
        "extraction_method": extracted.get("extraction_method", "text"),
        "created_at": _now(),
        "blob_path": str(blob_path),
        "text_path": str(text_path),
        "needs_human_verification": True,
    }
    items = _load()
    items.insert(0, item)
    _save(items)
    return {key: value for key, value in item.items() if key not in {"blob_path", "text_path"}}


def list_sources() -> List[Dict[str, Any]]:
    return [{key: value for key, value in item.items() if key not in {"blob_path", "text_path"}} for item in _load()]


def _tokens(text: str) -> List[str]:
    return [token for token in re.findall(r"[\wء-ي]{2,}", text.lower()) if token not in {"من", "على", "إلى", "هذا", "هذه", "التي", "الذي"}]


def search(query: str, max_results: int = 10) -> List[Dict[str, Any]]:
    query_tokens = _tokens(query)
    if not query_tokens:
        return []
    results = []
    for item in _load():
        try:
            text = workspace_store.decrypt_bytes(Path(item["text_path"]).read_bytes()).decode("utf-8", errors="replace")
        except (OSError, ValueError):
            continue
        haystack = text.lower()
        hits = sum(haystack.count(token) for token in query_tokens)
        if not hits:
            continue
        score = round(min(0.99, 0.10 + hits / max(10, len(query_tokens) * 20)), 4)
        first = min((haystack.find(token) for token in query_tokens if haystack.find(token) >= 0), default=0)
        start = max(0, first - 180)
        results.append({
            "source_type": "user_library",
            "source_id": item["id"],
            "title": item["title"],
            "authority": item["authority"],
            "status": item["status"],
            "filename": item["filename"],
            "source_hash": item["source_hash"],
            "score": score,
            "text": text[start:start + 700],
            "needs_human_verification": True,
        })
    return sorted(results, key=lambda row: row["score"], reverse=True)[:max_results]


def source_text(source_id: str) -> str:
    item = next((x for x in _load() if x["id"] == source_id), None)
    if not item:
        raise KeyError(source_id)
    return workspace_store.decrypt_bytes(Path(item["text_path"]).read_bytes()).decode("utf-8", errors="replace")
