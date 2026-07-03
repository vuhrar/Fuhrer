# storage.py
"""
إدارة الجلسات والإعدادات على قاعدة بيانات Supabase.
نظام تخزين سحابي مجاني (500MB storage, 2GB bandwidth).
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv

# تحميل متغيرات البيئة
load_dotenv()

# تهيئة Supabase
try:
    from supabase import create_client, Client
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    if SUPABASE_URL and SUPABASE_KEY:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        USE_SUPABASE = True
    else:
        supabase = None
        USE_SUPABASE = False
except ImportError:
    supabase = None
    USE_SUPABASE = False

# النظام المحلي (fallback)
DATA_DIR = "fuehrer_data"
SESSIONS_DIR = os.path.join(DATA_DIR, "sessions")
SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")

# إنشاء المجلدات
for d in (DATA_DIR, SESSIONS_DIR):
    os.makedirs(d, exist_ok=True)

def _load_json(path: str, default: Any = None) -> Any:
    """تحميل ملف JSON"""
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return default

def _save_json(path: str, data: Any) -> bool:
    """حفظ ملف JSON"""
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False

# ============ وظائف Supabase ============
def _create_sessions_table():
    """إنشاء جدول الجلسات في Supabase"""
    if not USE_SUPABASE:
        return False
    try:
        response = supabase.table("sessions").select("*").limit(1).execute()
        return True
    except Exception as e:
        print(f"⚠️  خطأ في إنشاء جدول الجلسات: {e}")
        return False

def _create_cases_table():
    """إنشاء جدول القضايا في Supabase"""
    if not USE_SUPABASE:
        return False
    try:
        response = supabase.table("cases").select("*").limit(1).execute()
        return True
    except Exception as e:
        print(f"⚠️  خطأ في إنشاء جدول القضايا: {e}")
        return False

if USE_SUPABASE:
    _create_sessions_table()
    _create_cases_table()

# ============ وظائف الجلسات ============
def load_settings() -> Dict:
    """تحميل الإعدادات"""
    if USE_SUPABASE:
        try:
            response = supabase.table("settings").select("*").limit(1).execute()
            if response.data:
                return response.data[0]["data"]
            return {}
        except Exception as e:
            print(f"⚠️  خطأ في تحميل الإعدادات من Supabase: {e}")
            return _load_json(SETTINGS_FILE, {})
    else:
        return _load_json(SETTINGS_FILE, {})

def save_settings(settings: Dict) -> bool:
    """حفظ الإعدادات (بدون مفتاح API)"""
    safe_settings = {k: v for k, v in settings.items() if k != "api_key"}
    if USE_SUPABASE:
        try:
            response = supabase.table("settings").update({
                "data": safe_settings,
                "updated_at": datetime.now().isoformat()
            }).eq("id", 1).execute()
            if not response.data:
                response = supabase.table("settings").insert({
                    "id": 1,
                    "data": safe_settings,
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }).execute()
            return True
        except Exception as e:
            print(f"⚠️  خطأ في حفظ الإعدادات إلى Supabase: {e}")
            return _save_json(SETTINGS_FILE, safe_settings)
    else:
        return _save_json(SETTINGS_FILE, safe_settings)

def list_sessions(user_id: str = "default") -> List[Dict]:
    """قائمة الجلسات"""
    if USE_SUPABASE:
        try:
            response = supabase.table("sessions").select(
                "id, data->name, data->messages, data->persona, created_at"
            ).eq("user_id", user_id).order("created_at", desc=True).limit(20).execute()
            sessions = []
            for session in response.data:
                sessions.append({
                    "id": session["id"],
                    "name": session["data"]["name"] if session["data"] else "جلسة جديدة",
                    "count": len(session["data"]["messages"]) if session["data"] and "messages" in session["data"] else 0,
                    "persona": session["data"]["persona"] if session["data"] else "lawyer",
                    "created_at": session["created_at"]
                })
            return sessions
        except Exception as e:
            print(f"⚠️  خطأ في تحميل الجلسات من Supabase: {e}")
            return _list_sessions_local()
    else:
        return _list_sessions_local()

def _list_sessions_local() -> List[Dict]:
    """قائمة الجلسات من النظام المحلي"""
    out = []
    try:
        for f in sorted(os.listdir(SESSIONS_DIR), reverse=True)[:20]:
            if f.endswith(".json"):
                d = _load_json(os.path.join(SESSIONS_DIR, f), {})
                out.append({
                    "id": f[:-5],
                    "name": d.get("name", "جلسة"),
                    "count": len(d.get("messages", [])),
                    "persona": d.get("persona", "lawyer"),
                    "created_at": d.get("updated", "")
                })
    except Exception:
        pass
    return out

def load_session(sid: str) -> Dict:
    """تحميل جلسة"""
    if USE_SUPABASE:
        try:
            response = supabase.table("sessions").select("data").eq("id", sid).single().execute()
            if response.data and "data" in response.data:
                return response.data["data"]
            return {"name": "جلسة جديدة", "messages": [], "persona": "lawyer"}
        except Exception as e:
            print(f"⚠️  خطأ في تحميل الجلسة من Supabase: {e}")
            return _load_session_local(sid)
    else:
        return _load_session_local(sid)

def _load_session_local(sid: str) -> Dict:
    """تحميل جلسة من النظام المحلي"""
    return _load_json(
        os.path.join(SESSIONS_DIR, f"{sid}.json"),
        {"name": "جلسة جديدة", "messages": [], "persona": "lawyer"}
    )

def save_session(sid: str, data: Dict) -> bool:
    """حفظ جلسة"""
    data["updated"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    if USE_SUPABASE:
        try:
            existing = supabase.table("sessions").select("id").eq("id", sid).execute()
            if existing.data:
                response = supabase.table("sessions").update({
                    "data": data,
                    "updated_at": datetime.now().isoformat()
                }).eq("id", sid).execute()
            else:
                response = supabase.table("sessions").insert({
                    "id": sid,
                    "user_id": "default",
                    "data": data,
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }).execute()
            return True
        except Exception as e:
            print(f"⚠️  خطأ في حفظ الجلسة إلى Supabase: {e}")
            return _save_session_local(sid, data)
    else:
        return _save_session_local(sid, data)

def _save_session_local(sid: str, data: Dict) -> bool:
    """حفظ جلسة في النظام المحلي"""
    return _save_json(os.path.join(SESSIONS_DIR, f"{sid}.json"), data)

def delete_session(sid: str) -> bool:
    """حذف جلسة"""
    if USE_SUPABASE:
        try:
            response = supabase.table("sessions").delete().eq("id", sid).execute()
            return True
        except Exception as e:
            print(f"⚠️  خطأ في حذف الجلسة من Supabase: {e}")
            return _delete_session_local(sid)
    else:
        return _delete_session_local(sid)

def _delete_session_local(sid: str) -> bool:
    """حذف جلسة من النظام المحلي"""
    path = os.path.join(SESSIONS_DIR, f"{sid}.json")
    if os.path.exists(path):
        os.remove(path)
        return True
    return False

def new_session_id() -> str:
    """إنشاء معرف جلسة جديد"""
    return datetime.now().strftime("%Y%m%d_%H%M%S")

# ============ وظائف القضايا ============
def create_case(case_data: Dict, user_id: str = "default") -> str:
    """إنشاء قضية جديدة"""
    case_id = f"CASE-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    case_data["id"] = case_id
    case_data["user_id"] = user_id
    case_data["created_at"] = datetime.now().isoformat()
    case_data["status"] = "مفتوحة"
    case_data["updates"] = []
    if USE_SUPABASE:
        try:
            response = supabase.table("cases").insert(case_data).execute()
            return case_id
        except Exception as e:
            print(f"⚠️  خطأ في إنشاء القضية في Supabase: {e}")
            return _create_case_local(case_data, case_id)
    else:
        return _create_case_local(case_data, case_id)

def _create_case_local(case_data: Dict, case_id: str) -> str:
    """إنشاء قضية في النظام المحلي"""
    CASES_DIR = os.path.join(DATA_DIR, "cases")
    os.makedirs(CASES_DIR, exist_ok=True)
    _save_json(os.path.join(CASES_DIR, f"{case_id}.json"), case_data)
    return case_id

def list_cases(user_id: str = "default") -> List[Dict]:
    """قائمة القضايا"""
    if USE_SUPABASE:
        try:
            response = supabase.table("cases").select(
                "id, user_id, status, created_at, data->title"
            ).eq("user_id", user_id).order("created_at", desc=True).limit(20).execute()
            cases = []
            for case in response.data:
                cases.append({
                    "id": case["id"],
                    "title": case["data"]["title"] if case["data"] and "title" in case["data"] else "قضية جديدة",
                    "status": case["status"],
                    "created_at": case["created_at"]
                })
            return cases
        except Exception as e:
            print(f"⚠️  خطأ في تحميل القضايا من Supabase: {e}")
            return _list_cases_local(user_id)
    else:
        return _list_cases_local(user_id)

def _list_cases_local(user_id: str = "default") -> List[Dict]:
    """قائمة القضايا من النظام المحلي"""
    CASES_DIR = os.path.join(DATA_DIR, "cases")
    cases = []
    try:
        for f in sorted(os.listdir(CASES_DIR), reverse=True)[:20]:
            if f.endswith(".json"):
                path = os.path.join(CASES_DIR, f)
                case_data = _load_json(path, {})
                if case_data.get("user_id") == user_id:
                    cases.append({
                        "id": f[:-5],
                        "title": case_data.get("title", "قضية جديدة"),
                        "status": case_data.get("status", "مفتوحة"),
                        "created_at": case_data.get("created_at", "")
                    })
    except Exception:
        pass
    return cases

def clear_all_sessions(user_id: str = "default") -> bool:
    """مسح جميع الجلسات"""
    if USE_SUPABASE:
        try:
            response = supabase.table("sessions").delete().eq("user_id", user_id).execute()
            return True
        except Exception as e:
            print(f"⚠️  خطأ في مسح الجلسات من Supabase: {e}")
            return _clear_all_sessions_local(user_id)
    else:
        return _clear_all_sessions_local(user_id)

def _clear_all_sessions_local(user_id: str = "default") -> bool:
    """مسح جميع الجلسات من النظام المحلي"""
    try:
        for f in os.listdir(SESSIONS_DIR):
            if f.endswith(".json"):
                path = os.path.join(SESSIONS_DIR, f)
                case_data = _load_json(path, {})
                if case_data.get("user_id") == user_id:
                    os.remove(path)
        return True
    except Exception:
        return False