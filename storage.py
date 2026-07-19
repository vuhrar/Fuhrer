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
