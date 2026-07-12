# storage.py
"""
طبقة التخزين الموحدة — النسخة الاحترافية v2.0
تدعم: Supabase (سحابي) + JSON محلي (Fallback)
المبادئ: Repository Pattern, Clean Error Handling, Unified Data Model
"""

import json
import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any

from dotenv import load_dotenv

load_dotenv()

# ============================================================
# تهيئة Supabase
# ============================================================
try:
    from supabase import create_client, Client
    _SUPABASE_URL = os.getenv("SUPABASE_URL", "")
    _SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
    if _SUPABASE_URL and _SUPABASE_KEY:
        _supabase: Optional[Client] = create_client(_SUPABASE_URL, _SUPABASE_KEY)
        USE_SUPABASE = True
    else:
        _supabase = None
        USE_SUPABASE = False
except Exception:
    _supabase = None
    USE_SUPABASE = False

# ============================================================
# إعداد التخزين المحلي
# ============================================================
_DATA_DIR      = os.path.join(os.path.expanduser("~"), "fuhrer_data")
_SESSIONS_DIR  = os.path.join(_DATA_DIR, "sessions")
_CASES_DIR     = os.path.join(_DATA_DIR, "cases")
_SETTINGS_FILE = os.path.join(_DATA_DIR, "settings.json")

for _d in (_DATA_DIR, _SESSIONS_DIR, _CASES_DIR):
    os.makedirs(_d, exist_ok=True)


# ============================================================
# أدوات JSON المحلية
# ============================================================
def _load_json(path: str, default: Any = None) -> Any:
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return default if default is not None else {}


def _save_json(path: str, data: Any) -> bool:
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


def _now_iso() -> str:
    return datetime.now().isoformat()


def _now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


# ============================================================
# معرّفات فريدة
# ============================================================
def new_session_id() -> str:
    """إنشاء معرّف جلسة فريد."""
    return f"sess_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"


def new_case_id() -> str:
    """إنشاء معرّف قضية فريد."""
    return f"case_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"


# ============================================================
# الإعدادات (Settings)
# ============================================================
def load_settings() -> Dict:
    """تحميل إعدادات التطبيق."""
    if USE_SUPABASE:
        try:
            resp = _supabase.table("settings").select("*").eq("id", 1).limit(1).execute()
            if resp.data:
                return resp.data[0].get("data", {})
        except Exception:
            pass
    return _load_json(_SETTINGS_FILE, {})


def save_settings(settings: Dict) -> bool:
    """حفظ الإعدادات (يستثني مفتاح API من الحفظ الدائم)."""
    safe = {k: v for k, v in settings.items() if k != "api_key"}
    if USE_SUPABASE:
        try:
            resp = _supabase.table("settings").upsert({
                "id": 1, "data": safe, "updated_at": _now_iso()
            }).execute()
            return True
        except Exception:
            pass
    return _save_json(_SETTINGS_FILE, safe)


# ============================================================
# الجلسات (Sessions)
# ============================================================
def save_session(session_id: str, data: Dict) -> bool:
    """حفظ جلسة محادثة."""
    data["id"] = session_id
    data.setdefault("created_at", _now_str())
    data["updated_at"] = _now_str()

    if USE_SUPABASE:
        try:
            _supabase.table("sessions").upsert({
                "id": session_id,
                "name": data.get("name", "جلسة"),
                "persona": data.get("persona", "lawyer"),
                "messages": data.get("messages", []),
                "created_at": data.get("created_at"),
                "updated_at": data["updated_at"],
            }).execute()
            return True
        except Exception:
            pass
    return _save_json(os.path.join(_SESSIONS_DIR, f"{session_id}.json"), data)


def load_session(session_id: str) -> Dict:
    """تحميل جلسة محادثة."""
    if USE_SUPABASE:
        try:
            resp = _supabase.table("sessions").select("*").eq("id", session_id).limit(1).execute()
            if resp.data:
                return resp.data[0]
        except Exception:
            pass
    return _load_json(os.path.join(_SESSIONS_DIR, f"{session_id}.json"), {})


def list_sessions(limit: int = 30) -> List[Dict]:
    """قائمة الجلسات المحفوظة."""
    if USE_SUPABASE:
        try:
            resp = _supabase.table("sessions").select(
                "id, name, persona, updated_at, created_at"
            ).order("updated_at", desc=True).limit(limit).execute()
            return [
                {
                    "id": s["id"],
                    "name": s.get("name", "جلسة"),
                    "persona": s.get("persona", "lawyer"),
                    "count": len(s.get("messages", [])) if isinstance(s.get("messages"), list) else 0,
                    "created_at": s.get("created_at", ""),
                    "updated_at": s.get("updated_at", ""),
                }
                for s in resp.data
            ]
        except Exception:
            pass

    # Fallback محلي
    sessions = []
    try:
        files = sorted(
            [f for f in os.listdir(_SESSIONS_DIR) if f.endswith(".json")],
            key=lambda f: os.path.getmtime(os.path.join(_SESSIONS_DIR, f)),
            reverse=True
        )[:limit]
        for fname in files:
            d = _load_json(os.path.join(_SESSIONS_DIR, fname), {})
            if d:
                sessions.append({
                    "id": d.get("id", fname[:-5]),
                    "name": d.get("name", "جلسة"),
                    "persona": d.get("persona", "lawyer"),
                    "count": len(d.get("messages", [])),
                    "created_at": d.get("created_at", ""),
                    "updated_at": d.get("updated_at", ""),
                })
    except Exception:
        pass
    return sessions


def delete_session(session_id: str) -> bool:
    """حذف جلسة."""
    if USE_SUPABASE:
        try:
            _supabase.table("sessions").delete().eq("id", session_id).execute()
            return True
        except Exception:
            pass
    path = os.path.join(_SESSIONS_DIR, f"{session_id}.json")
    if os.path.exists(path):
        os.remove(path)
        return True
    return False


def clear_all_sessions() -> bool:
    """مسح جميع الجلسات."""
    if USE_SUPABASE:
        try:
            _supabase.table("sessions").delete().neq("id", "").execute()
            return True
        except Exception:
            pass
    try:
        for f in os.listdir(_SESSIONS_DIR):
            if f.endswith(".json"):
                os.remove(os.path.join(_SESSIONS_DIR, f))
        return True
    except Exception:
        return False


# ============================================================
# القضايا (Cases)
# ============================================================
def create_case(case_data: Dict) -> str:
    """إنشاء قضية جديدة وإعادة معرّفها."""
    case_id = new_case_id()
    full_data = {
        "id": case_id,
        "title": case_data.get("title", "قضية جديدة"),
        "description": case_data.get("description", ""),
        "status": "مفتوحة",
        "persona": case_data.get("persona", "lawyer"),
        "category": case_data.get("category", "عام"),
        "notes": [],
        "documents": [],
        "created_at": _now_str(),
        "updated_at": _now_str(),
    }
    if USE_SUPABASE:
        try:
            _supabase.table("cases").insert(full_data).execute()
            return case_id
        except Exception:
            pass
    _save_json(os.path.join(_CASES_DIR, f"{case_id}.json"), full_data)
    return case_id


def load_case(case_id: str) -> Dict:
    """تحميل قضية."""
    if USE_SUPABASE:
        try:
            resp = _supabase.table("cases").select("*").eq("id", case_id).limit(1).execute()
            if resp.data:
                return resp.data[0]
        except Exception:
            pass
    return _load_json(os.path.join(_CASES_DIR, f"{case_id}.json"), {})


def update_case(case_id: str, updates: Dict) -> bool:
    """تحديث بيانات قضية."""
    updates["updated_at"] = _now_str()
    if USE_SUPABASE:
        try:
            _supabase.table("cases").update(updates).eq("id", case_id).execute()
            return True
        except Exception:
            pass
    # محلي
    path = os.path.join(_CASES_DIR, f"{case_id}.json")
    data = _load_json(path, {})
    data.update(updates)
    return _save_json(path, data)


def list_cases(limit: int = 30) -> List[Dict]:
    """قائمة القضايا المحفوظة."""
    if USE_SUPABASE:
        try:
            resp = _supabase.table("cases").select(
                "id, title, status, category, persona, created_at, updated_at"
            ).order("updated_at", desc=True).limit(limit).execute()
            return resp.data or []
        except Exception:
            pass

    cases = []
    try:
        files = sorted(
            [f for f in os.listdir(_CASES_DIR) if f.endswith(".json")],
            key=lambda f: os.path.getmtime(os.path.join(_CASES_DIR, f)),
            reverse=True
        )[:limit]
        for fname in files:
            d = _load_json(os.path.join(_CASES_DIR, fname), {})
            if d:
                cases.append({
                    "id": d.get("id", fname[:-5]),
                    "title": d.get("title", "قضية"),
                    "status": d.get("status", "مفتوحة"),
                    "category": d.get("category", "عام"),
                    "persona": d.get("persona", "lawyer"),
                    "created_at": d.get("created_at", ""),
                    "updated_at": d.get("updated_at", ""),
                })
    except Exception:
        pass
    return cases


def delete_case(case_id: str) -> bool:
    """حذف قضية."""
    if USE_SUPABASE:
        try:
            _supabase.table("cases").delete().eq("id", case_id).execute()
            return True
        except Exception:
            pass
    path = os.path.join(_CASES_DIR, f"{case_id}.json")
    if os.path.exists(path):
        os.remove(path)
        return True
    return False


def add_case_note(case_id: str, note: str) -> bool:
    """إضافة ملاحظة لقضية."""
    case = load_case(case_id)
    if not case:
        return False
    notes = case.get("notes", [])
    notes.append({"text": note, "timestamp": _now_str()})
    return update_case(case_id, {"notes": notes})


# ============================================================
# إحصائيات عامة
# ============================================================
def get_stats() -> Dict:
    """إحصائيات عامة للتطبيق."""
    return {
        "sessions": len(list_sessions()),
        "cases": len(list_cases()),
        "storage": "Supabase ☁️" if USE_SUPABASE else "محلي 💾",
    }
