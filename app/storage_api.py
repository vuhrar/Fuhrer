from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
import storage

router = APIRouter()

@router.get("/sessions")
def list_sessions():
    try:
        s = storage.list_sessions()
        return {"ok": True, "sessions": s}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sessions")
def create_session(payload: Dict[str, Any]):
    try:
        sid = storage.new_session_id()
        data = {
            "name": payload.get("name", f"جلسة {sid}"),
            "messages": payload.get("messages", []),
            "persona": payload.get("persona", "lawyer")
        }
        storage.save_session(sid, data)
        return {"ok": True, "id": sid}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sessions/{sid}")
def get_session(sid: str):
    try:
        data = storage.load_session(sid)
        if data is None:
            raise HTTPException(status_code=404, detail="session not found")
        return {"ok": True, "session": data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/sessions/{sid}")
def delete_session(sid: str):
    try:
        storage.delete_session(sid)
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Cases
@router.get("/cases")
def list_cases():
    try:
        c = storage.list_cases()
        return {"ok": True, "cases": c}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cases")
def create_case(payload: Dict[str, Any]):
    try:
        cid = storage.create_case(payload)
        return {"ok": True, "id": cid}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/cases/{cid}")
def get_case(cid: str):
    try:
        data = storage.load_case(cid)
        if data is None:
            raise HTTPException(status_code=404, detail="case not found")
        return {"ok": True, "case": data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/cases/{cid}")
def delete_case(cid: str):
    try:
        storage.delete_case(cid)
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
