"""مخزن عمل قانوني محلي وآمن نسبيًا لمستخدم واحد باستخدام SQLite."""
from __future__ import annotations

import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.getenv("FUHRER_DATA_DIR", os.path.join(os.path.expanduser("~"), "fuhrer_data"))
os.makedirs(DATA_DIR, exist_ok=True)
DB_PATH = os.path.join(DATA_DIR, "workspace.sqlite3")


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db() -> None:
    with connect() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS matters (
          id TEXT PRIMARY KEY, title TEXT NOT NULL, matter_type TEXT NOT NULL DEFAULT 'عام',
          status TEXT NOT NULL DEFAULT 'مفتوحة', priority TEXT NOT NULL DEFAULT 'متوسطة',
          client_name TEXT NOT NULL DEFAULT '', opposing_party TEXT NOT NULL DEFAULT '',
          jurisdiction TEXT NOT NULL DEFAULT '', description TEXT NOT NULL DEFAULT '',
          created_at TEXT NOT NULL, updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS tasks (
          id TEXT PRIMARY KEY, matter_id TEXT NOT NULL, title TEXT NOT NULL,
          status TEXT NOT NULL DEFAULT 'مفتوحة', priority TEXT NOT NULL DEFAULT 'متوسطة',
          due_date TEXT, owner TEXT NOT NULL DEFAULT 'المستخدم الوحيد', notes TEXT NOT NULL DEFAULT '',
          created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
          FOREIGN KEY(matter_id) REFERENCES matters(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS documents (
          id TEXT PRIMARY KEY, matter_id TEXT, filename TEXT NOT NULL, kind TEXT NOT NULL DEFAULT 'مستند',
          extracted_text TEXT NOT NULL DEFAULT '', source_hash TEXT NOT NULL DEFAULT '',
          created_at TEXT NOT NULL,
          FOREIGN KEY(matter_id) REFERENCES matters(id) ON DELETE SET NULL
        );
        CREATE TABLE IF NOT EXISTS audit_events (
          id INTEGER PRIMARY KEY AUTOINCREMENT, entity_type TEXT NOT NULL, entity_id TEXT NOT NULL,
          action TEXT NOT NULL, metadata TEXT NOT NULL DEFAULT '{}', created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS parties (
          id TEXT PRIMARY KEY, matter_id TEXT NOT NULL, name TEXT NOT NULL, role TEXT NOT NULL,
          contact TEXT NOT NULL DEFAULT '', notes TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL,
          FOREIGN KEY(matter_id) REFERENCES matters(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS facts (
          id TEXT PRIMARY KEY, matter_id TEXT NOT NULL, event_date TEXT, title TEXT NOT NULL,
          description TEXT NOT NULL DEFAULT '', certainty TEXT NOT NULL DEFAULT 'غير متحقق',
          source_document_id TEXT, created_at TEXT NOT NULL,
          FOREIGN KEY(matter_id) REFERENCES matters(id) ON DELETE CASCADE,
          FOREIGN KEY(source_document_id) REFERENCES documents(id) ON DELETE SET NULL
        );
        CREATE TABLE IF NOT EXISTS claims (
          id TEXT PRIMARY KEY, matter_id TEXT NOT NULL, title TEXT NOT NULL,
          position TEXT NOT NULL DEFAULT 'مقترح', legal_basis TEXT NOT NULL DEFAULT '',
          status TEXT NOT NULL DEFAULT 'قيد التحقق', notes TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL,
          FOREIGN KEY(matter_id) REFERENCES matters(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS claim_evidence (
          claim_id TEXT NOT NULL, document_id TEXT NOT NULL, matter_id TEXT NOT NULL,
          note TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL,
          PRIMARY KEY (claim_id, document_id),
          FOREIGN KEY(claim_id) REFERENCES claims(id) ON DELETE CASCADE,
          FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE,
          FOREIGN KEY(matter_id) REFERENCES matters(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS deadlines (
          id TEXT PRIMARY KEY, matter_id TEXT NOT NULL, title TEXT NOT NULL, due_date TEXT,
          status TEXT NOT NULL DEFAULT 'مفتوح', source TEXT NOT NULL DEFAULT '', notes TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL,
          FOREIGN KEY(matter_id) REFERENCES matters(id) ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_facts_matter_date ON facts(matter_id, event_date);
        CREATE INDEX IF NOT EXISTS idx_claims_matter ON claims(matter_id);
        CREATE INDEX IF NOT EXISTS idx_deadlines_matter_due ON deadlines(matter_id, due_date);
        CREATE INDEX IF NOT EXISTS idx_tasks_matter ON tasks(matter_id);
        CREATE INDEX IF NOT EXISTS idx_tasks_due ON tasks(due_date);
        CREATE INDEX IF NOT EXISTS idx_audit_entity ON audit_events(entity_type, entity_id);
        """)


def audit(db: sqlite3.Connection, entity_type: str, entity_id: str, action: str, metadata: Optional[Dict[str, Any]] = None) -> None:
    db.execute("INSERT INTO audit_events(entity_type, entity_id, action, metadata, created_at) VALUES(?,?,?,?,?)", (entity_type, entity_id, action, json.dumps(metadata or {}, ensure_ascii=False), now()))


def create_matter(payload: Dict[str, Any]) -> Dict[str, Any]:
    matter_id, stamp = _id("matter"), now()
    values = (matter_id, payload["title"].strip(), payload.get("matter_type", "عام"), payload.get("status", "مفتوحة"), payload.get("priority", "متوسطة"), payload.get("client_name", ""), payload.get("opposing_party", ""), payload.get("jurisdiction", ""), payload.get("description", ""), stamp, stamp)
    with connect() as db:
        db.execute("INSERT INTO matters VALUES(?,?,?,?,?,?,?,?,?,?,?)", values)
        audit(db, "matter", matter_id, "created", {"title": values[1]})
    return get_matter(matter_id)


def list_matters(status: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
    with connect() as db:
        if status:
            rows = db.execute("SELECT * FROM matters WHERE status=? ORDER BY updated_at DESC LIMIT ?", (status, limit)).fetchall()
        else:
            rows = db.execute("SELECT * FROM matters ORDER BY updated_at DESC LIMIT ?", (limit,)).fetchall()
        return [dict(row) for row in rows]


def get_matter(matter_id: str) -> Dict[str, Any]:
    with connect() as db:
        row = db.execute("SELECT * FROM matters WHERE id=?", (matter_id,)).fetchone()
        if not row:
            raise KeyError(matter_id)
        result = dict(row)
        result["tasks"] = [dict(x) for x in db.execute("SELECT * FROM tasks WHERE matter_id=? ORDER BY due_date IS NULL, due_date", (matter_id,)).fetchall()]
        result["documents"] = [dict(x) for x in db.execute("SELECT id,matter_id,filename,kind,source_hash,created_at FROM documents WHERE matter_id=? ORDER BY created_at DESC", (matter_id,)).fetchall()]
        result["parties"] = [dict(x) for x in db.execute("SELECT * FROM parties WHERE matter_id=? ORDER BY created_at", (matter_id,)).fetchall()]
        result["facts"] = [dict(x) for x in db.execute("SELECT * FROM facts WHERE matter_id=? ORDER BY event_date IS NULL, event_date, created_at", (matter_id,)).fetchall()]
        result["claims"] = [dict(x) for x in db.execute("SELECT * FROM claims WHERE matter_id=? ORDER BY created_at", (matter_id,)).fetchall()]
        result["claim_evidence"] = [dict(x) for x in db.execute("SELECT ce.*, c.title AS claim_title, d.filename FROM claim_evidence ce JOIN claims c ON c.id=ce.claim_id JOIN documents d ON d.id=ce.document_id WHERE ce.matter_id=? ORDER BY ce.created_at", (matter_id,)).fetchall()]
        result["deadlines"] = [dict(x) for x in db.execute("SELECT * FROM deadlines WHERE matter_id=? ORDER BY due_date IS NULL, due_date", (matter_id,)).fetchall()]
        result["audit"] = [dict(x) for x in db.execute("SELECT * FROM audit_events WHERE entity_id=? ORDER BY created_at DESC LIMIT 100", (matter_id,)).fetchall()]
        return result


def update_matter(matter_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    allowed = {key: payload[key] for key in ("title", "matter_type", "status", "priority", "client_name", "opposing_party", "jurisdiction", "description") if key in payload}
    if not allowed:
        return get_matter(matter_id)
    fields = ", ".join(f"{key}=?" for key in allowed)
    values = list(allowed.values()) + [now(), matter_id]
    with connect() as db:
        cur = db.execute(f"UPDATE matters SET {fields}, updated_at=? WHERE id=?", values)
        if cur.rowcount == 0:
            raise KeyError(matter_id)
        audit(db, "matter", matter_id, "updated", {"fields": list(allowed)})
    return get_matter(matter_id)


def create_task(matter_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    task_id, stamp = _id("task"), now()
    with connect() as db:
        if not db.execute("SELECT 1 FROM matters WHERE id=?", (matter_id,)).fetchone():
            raise KeyError(matter_id)
        db.execute("INSERT INTO tasks VALUES(?,?,?,?,?,?,?,?,?,?)", (task_id, matter_id, payload["title"].strip(), payload.get("status", "مفتوحة"), payload.get("priority", "متوسطة"), payload.get("due_date"), payload.get("owner", "المستخدم الوحيد"), payload.get("notes", ""), stamp, stamp))
        db.execute("UPDATE matters SET updated_at=? WHERE id=?", (stamp, matter_id))
        audit(db, "matter", matter_id, "task_created", {"task_id": task_id})
    return get_matter(matter_id)


def update_task(task_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    allowed = {key: payload[key] for key in ("title", "status", "priority", "due_date", "owner", "notes") if key in payload}
    if not allowed:
        return {"task_id": task_id}
    with connect() as db:
        row = db.execute("SELECT matter_id FROM tasks WHERE id=?", (task_id,)).fetchone()
        if not row:
            raise KeyError(task_id)
        fields = ", ".join(f"{key}=?" for key in allowed)
        db.execute(f"UPDATE tasks SET {fields}, updated_at=? WHERE id=?", [*allowed.values(), now(), task_id])
        audit(db, "matter", row["matter_id"], "task_updated", {"task_id": task_id, "fields": list(allowed)})
    return get_matter(row["matter_id"])


def add_document(matter_id: Optional[str], filename: str, kind: str, extracted_text: str, source_hash: str) -> Dict[str, Any]:
    document_id, stamp = _id("doc"), now()
    with connect() as db:
        if matter_id and not db.execute("SELECT 1 FROM matters WHERE id=?", (matter_id,)).fetchone():
            raise KeyError(matter_id)
        db.execute("INSERT INTO documents VALUES(?,?,?,?,?,?,?)", (document_id, matter_id, filename, kind, extracted_text, source_hash, stamp))
        if matter_id:
            audit(db, "matter", matter_id, "document_added", {"document_id": document_id, "filename": filename})
    return {"id": document_id, "matter_id": matter_id, "filename": filename, "kind": kind, "source_hash": source_hash, "created_at": stamp}


def dashboard() -> Dict[str, Any]:
    with connect() as db:
        counts = {"matters": db.execute("SELECT COUNT(*) FROM matters").fetchone()[0], "open_matters": db.execute("SELECT COUNT(*) FROM matters WHERE status NOT IN ('مغلقة','مؤرشفة')").fetchone()[0], "open_tasks": db.execute("SELECT COUNT(*) FROM tasks WHERE status NOT IN ('مكتملة','ملغاة')").fetchone()[0], "documents": db.execute("SELECT COUNT(*) FROM documents").fetchone()[0]}
        upcoming = [dict(x) for x in db.execute("SELECT tasks.*, matters.title AS matter_title FROM tasks JOIN matters ON matters.id=tasks.matter_id WHERE tasks.status NOT IN ('مكتملة','ملغاة') ORDER BY due_date IS NULL, due_date LIMIT 10").fetchall()]
        return {"counts": counts, "upcoming_tasks": upcoming, "recent_matters": list_matters(limit=8)}


init_db()


def _ensure_matter(db: sqlite3.Connection, matter_id: str) -> None:
    if not db.execute("SELECT 1 FROM matters WHERE id=?", (matter_id,)).fetchone():
        raise KeyError(matter_id)


def add_party(matter_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    party_id, stamp = _id("party"), now()
    with connect() as db:
        _ensure_matter(db, matter_id)
        row = (party_id, matter_id, payload["name"].strip(), payload["role"].strip(), payload.get("contact", ""), payload.get("notes", ""), stamp)
        db.execute("INSERT INTO parties VALUES(?,?,?,?,?,?,?)", row)
        audit(db, "matter", matter_id, "party_added", {"party_id": party_id})
    return get_matter(matter_id)


def add_fact(matter_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    fact_id, stamp = _id("fact"), now()
    with connect() as db:
        _ensure_matter(db, matter_id)
        row = (fact_id, matter_id, payload.get("event_date"), payload["title"].strip(), payload.get("description", ""), payload.get("certainty", "غير متحقق"), payload.get("source_document_id"), stamp)
        db.execute("INSERT INTO facts VALUES(?,?,?,?,?,?,?,?)", row)
        audit(db, "matter", matter_id, "fact_added", {"fact_id": fact_id, "certainty": row[5]})
    return get_matter(matter_id)


def add_claim(matter_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    claim_id, stamp = _id("claim"), now()
    with connect() as db:
        _ensure_matter(db, matter_id)
        row = (claim_id, matter_id, payload["title"].strip(), payload.get("position", "مقترح"), payload.get("legal_basis", ""), payload.get("status", "قيد التحقق"), payload.get("notes", ""), stamp)
        db.execute("INSERT INTO claims VALUES(?,?,?,?,?,?,?,?)", row)
        audit(db, "matter", matter_id, "claim_added", {"claim_id": claim_id})
    return get_matter(matter_id)


def link_claim_evidence(matter_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    stamp = now()
    with connect() as db:
        _ensure_matter(db, matter_id)
        claim = db.execute("SELECT 1 FROM claims WHERE id=? AND matter_id=?", (payload["claim_id"], matter_id)).fetchone()
        document = db.execute("SELECT 1 FROM documents WHERE id=? AND matter_id=?", (payload["document_id"], matter_id)).fetchone()
        if not claim or not document:
            raise KeyError(matter_id)
        db.execute("INSERT OR REPLACE INTO claim_evidence(claim_id, document_id, matter_id, note, created_at) VALUES(?,?,?,?,?)", (payload["claim_id"], payload["document_id"], matter_id, payload.get("note", ""), stamp))
        audit(db, "matter", matter_id, "claim_evidence_linked", {"claim_id": payload["claim_id"], "document_id": payload["document_id"]})
    return get_matter(matter_id)


def add_deadline(matter_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    deadline_id, stamp = _id("deadline"), now()
    with connect() as db:
        _ensure_matter(db, matter_id)
        row = (deadline_id, matter_id, payload["title"].strip(), payload.get("due_date"), payload.get("status", "مفتوح"), payload.get("source", ""), payload.get("notes", ""), stamp)
        db.execute("INSERT INTO deadlines VALUES(?,?,?,?,?,?,?,?)", row)
        audit(db, "matter", matter_id, "deadline_added", {"deadline_id": deadline_id})
    return get_matter(matter_id)
