import json
import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
import time
import random

from dotenv import load_dotenv

load_dotenv()

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

_DATA_DIR      = os.path.join(os.path.expanduser("~"), "fuhrer_data")
_SESSIONS_DIR  = os.path.join(_DATA_DIR, "sessions")
_CASES_DIR     = os.path.join(_DATA_DIR, "cases")
_SETTINGS_FILE = os.path.join(_DATA_DIR, "settings.json")

for _d in (_DATA_DIR, _SESSIONS_DIR, _CASES_DIR):
    os.makedirs(_d, exist_ok=True)


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


def new_session_id() -> str:
    return f"sess_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"


def new_case_id() -> str:
    return f"case_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"


def _execute_with_retry(query_func, max_retries=3, base_delay=1.0):
    for attempt in range(max_retries):
        try:
            return query_func()
        except Exception as e:
            if "429" in str(e) and attempt < max_retries - 1:
                time.sleep(base_delay * (2 ** attempt) + random.uniform(0, 1))
                continue
            raise e


def load_settings() -> Dict:
    if USE_SUPABASE and _supabase:
        try:
            func = lambda: _supabase.table("settings").select("*").eq("id", 1).limit(1).execute()
            resp = _execute_with_retry(func)
            if resp and resp.data:
                return resp.data[0].get("data", {})
        except Exception:
            pass
    return _load_json(_SETTINGS_FILE, {})


def save_settings(settings: Dict) -> bool:
    if USE_SUPABASE and _supabase:
        try:
            payload = {"id": 1, "data": settings, "updated_at": _now_iso()}
            func = lambda: _supabase.table("settings").upsert(payload).execute()
            _execute_with_retry(func)
            return True
        except Exception:
            pass
    return _save_json(_SETTINGS_FILE, settings)


def save_session(session_id: str, data: Dict) -> bool:
    data["id"] = session_id
    data.setdefault("created_at", _now_str())
    data["updated_at"] = _now_str()
    if USE_SUPABASE and _supabase:
        try:
            payload = {
                "id": session_id,
                "name": data.get("name", "جلسة"),
                "persona": data.get("persona", "lawyer"),
                "messages": data.get("messages", []),
                "created_at": data.get("created_at"),
                "updated_at": data["updated_at"],
            }
            func = lambda: _supabase.table("sessions").upsert(payload).execute()
            _execute_with_retry(func)
            return True
        except Exception:
            pass
    return _save_json(os.path.join(_SESSIONS_DIR, f"{session_id}.json"), data)


def load_session(session_id: str) -> Dict:
    if USE_SUPABASE and _supabase:
        try:
            func = lambda: _supabase.table("sessions").select("*").eq("id", session_id).limit(1).execute()
            resp = _execute_with_retry(func)
            if resp and resp.data:
                return resp.data[0]
        except Exception:
            pass
    return _load_json(os.path.join(_SESSIONS_DIR, f"{session_id}.json"), {})


def list_sessions(limit: int = 30) -> List[Dict]:
    if USE_SUPABASE and _supabase:
        try:
            func = lambda: _supabase.table("sessions").select(
                "id, name, persona, updated_at, created_at, messages"
            ).order("updated_at", desc=True).limit(limit).execute()
            resp = _execute_with_retry(func)
            if resp and resp.data:
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
    if USE_SUPABASE and _supabase:
        try:
            func = lambda: _supabase.table("sessions").delete().eq("id", session_id).execute()
            _execute_with_retry(func)
            return True
        except Exception:
            pass
    path = os.path.join(_SESSIONS_DIR, f"{session_id}.json")
    if os.path.exists(path):
        os.remove(path)
        return True
    return False


def clear_all_sessions() -> bool:
    if USE_SUPABASE and _supabase:
        try:
            func = lambda: _supabase.table("sessions").delete().neq("id", "").execute()
            _execute_with_retry(func)
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


def create_case(case_data: Dict) -> str:
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
    if USE_SUPABASE and _supabase:
        try:
            func = lambda: _supabase.table("cases").insert(full_data).execute()
            _execute_with_retry(func)
            return case_id
        except Exception:
            pass
    _save_json(os.path.join(_CASES_DIR, f"{case_id}.json"), full_data)
    return case_id


def save_case(case_id: str, data: Dict) -> bool:
    data["id"] = case_id
    data["updated_at"] = _now_str()
    if USE_SUPABASE and _supabase:
        try:
            func = lambda: _supabase.table("cases").upsert(data).execute()
            _execute_with_retry(func)
            return True
        except Exception:
            pass
    return _save_json(os.path.join(_CASES_DIR, f"{case_id}.json"), data)


def load_case(case_id: str) -> Dict:
    if USE_SUPABASE and _supabase:
        try:
            func = lambda: _supabase.table("cases").select("*").eq("id", case_id).limit(1).execute()
            resp = _execute_with_retry(func)
            if resp and resp.data:
                return resp.data[0]
        except Exception:
            pass
    return _load_json(os.path.join(_CASES_DIR, f"{case_id}.json"), {})


def list_cases(limit: int = 30) -> List[Dict]:
    if USE_SUPABASE and _supabase:
        try:
            func = lambda: _supabase.table("cases").select("*").order("updated_at", desc=True).limit(limit).execute()
            resp = _execute_with_retry(func)
            if resp and resp.data:
                return resp.data
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
                cases.append(d)
    except Exception:
        pass
    return cases


def delete_case(case_id: str) -> bool:
    if USE_SUPABASE and _supabase:
        try:
            func = lambda: _supabase.table("cases").delete().eq("id", case_id).execute()
            _execute_with_retry(func)
            return True
        except Exception:
            pass
    path = os.path.join(_CASES_DIR, f"{case_id}.json")
    if os.path.exists(path):
        os.remove(path)
        return True
    return False
