"""مخزن عمل قانوني محلي وآمن نسبيًا لمستخدم واحد باستخدام SQLite."""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import tempfile
import zipfile
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.getenv("FUHRER_DATA_DIR", os.path.join(os.path.expanduser("~"), "fuhrer_data"))
os.makedirs(DATA_DIR, exist_ok=True)
BLOB_DIR = os.path.join(DATA_DIR, "document_blobs")
os.makedirs(BLOB_DIR, exist_ok=True)
DB_PATH = os.path.join(DATA_DIR, "workspace.sqlite3")


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


PROCEDURE_STEPS = [
    ("intake", "استيعاب النزاع وتحديد النطاق"),
    ("evidence", "جمع الأدلة وفحصها وربطها بالوقائع"),
    ("legal_review", "البحث والتكييف القانوني والتحقق من المصادر"),
    ("amicable_settlement", "التسوية الودية وتوثيق الجلسات والنتيجة"),
    ("referral", "محضر التعذر أو الإحالة للمرحلة التالية"),
    ("lawsuit", "تجهيز صحيفة الدعوى والمرفقات"),
    ("hearings", "إدارة الجلسات والردود والمذكرات"),
    ("judgment", "الحكم وقراءة أسبابه ومواعيد الاعتراض"),
    ("enforcement", "التنفيذ أو التسوية النهائية"),
    ("closed", "إغلاق الملف وأرشفة السجل"),
]

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
          byte_size INTEGER NOT NULL DEFAULT 0, mime_type TEXT NOT NULL DEFAULT '',
          storage_path TEXT NOT NULL DEFAULT '', retention_class TEXT NOT NULL DEFAULT 'حساس',
          integrity_status TEXT NOT NULL DEFAULT 'سليم', metadata_json TEXT NOT NULL DEFAULT '{}', created_at TEXT NOT NULL,
          FOREIGN KEY(matter_id) REFERENCES matters(id) ON DELETE SET NULL
        );
        CREATE TABLE IF NOT EXISTS custody_events (
          id TEXT PRIMARY KEY, document_id TEXT NOT NULL, matter_id TEXT,
          event_type TEXT NOT NULL, actor TEXT NOT NULL DEFAULT 'المستخدم الوحيد',
          details TEXT NOT NULL DEFAULT '{}', event_hash TEXT NOT NULL,
          created_at TEXT NOT NULL,
          FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE,
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
        CREATE TABLE IF NOT EXISTS procedure_steps (
          id TEXT PRIMARY KEY, matter_id TEXT NOT NULL, step_key TEXT NOT NULL,
          title TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'غير مكتملة',
          started_at TEXT, completed_at TEXT, notes TEXT NOT NULL DEFAULT '',
          created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
          UNIQUE(matter_id, step_key), FOREIGN KEY(matter_id) REFERENCES matters(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS document_inspections (
          id TEXT PRIMARY KEY, document_id TEXT NOT NULL, matter_id TEXT,
          inspection_status TEXT NOT NULL, readable INTEGER NOT NULL DEFAULT 0,
          full_text_available INTEGER NOT NULL DEFAULT 0, pages INTEGER NOT NULL DEFAULT 0,
          characters_scanned INTEGER NOT NULL DEFAULT 0, words_approx INTEGER NOT NULL DEFAULT 0,
          signals_json TEXT NOT NULL DEFAULT '{}', coverage_json TEXT NOT NULL DEFAULT '{}',
          errors_json TEXT NOT NULL DEFAULT '[]', inspected_at TEXT NOT NULL,
          FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE,
          FOREIGN KEY(matter_id) REFERENCES matters(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS discovered_rights (
          id TEXT PRIMARY KEY, matter_id TEXT NOT NULL, right_key TEXT NOT NULL,
          label TEXT NOT NULL, status TEXT NOT NULL, trigger_count INTEGER NOT NULL DEFAULT 0,
          reason TEXT NOT NULL DEFAULT '', elements_json TEXT NOT NULL DEFAULT '[]',
          evidence_json TEXT NOT NULL DEFAULT '[]', missing_json TEXT NOT NULL DEFAULT '[]',
          triggers_json TEXT NOT NULL DEFAULT '[]', source_refs_json TEXT NOT NULL DEFAULT '[]',
          human_review_required INTEGER NOT NULL DEFAULT 1, created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL, UNIQUE(matter_id, right_key),
          FOREIGN KEY(matter_id) REFERENCES matters(id) ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_facts_matter_date ON facts(matter_id, event_date);
        CREATE INDEX IF NOT EXISTS idx_claims_matter ON claims(matter_id);
        CREATE INDEX IF NOT EXISTS idx_deadlines_matter_due ON deadlines(matter_id, due_date);
        CREATE INDEX IF NOT EXISTS idx_tasks_matter ON tasks(matter_id);
        CREATE INDEX IF NOT EXISTS idx_tasks_due ON tasks(due_date);
        CREATE INDEX IF NOT EXISTS idx_audit_entity ON audit_events(entity_type, entity_id);
        CREATE INDEX IF NOT EXISTS idx_custody_document ON custody_events(document_id, created_at);
        CREATE INDEX IF NOT EXISTS idx_document_inspections_matter ON document_inspections(matter_id, inspected_at);
        CREATE INDEX IF NOT EXISTS idx_discovered_rights_matter ON discovered_rights(matter_id, status);
        """)


def audit(db: sqlite3.Connection, entity_type: str, entity_id: str, action: str, metadata: Optional[Dict[str, Any]] = None) -> None:
    db.execute("INSERT INTO audit_events(entity_type, entity_id, action, metadata, created_at) VALUES(?,?,?,?,?)", (entity_type, entity_id, action, json.dumps(metadata or {}, ensure_ascii=False), now()))


def create_matter(payload: Dict[str, Any]) -> Dict[str, Any]:
    matter_id, stamp = _id("matter"), now()
    values = (matter_id, payload["title"].strip(), payload.get("matter_type", "عام"), payload.get("status", "مفتوحة"), payload.get("priority", "متوسطة"), payload.get("client_name", ""), payload.get("opposing_party", ""), payload.get("jurisdiction", ""), payload.get("description", ""), stamp, stamp)
    with connect() as db:
        db.execute("INSERT INTO matters VALUES(?,?,?,?,?,?,?,?,?,?,?)", values)
        steps = [(f"step_{uuid.uuid4().hex[:12]}", matter_id, key, title, "جارية" if index == 0 else "غير مكتملة", stamp if index == 0 else None, None, "", stamp, stamp) for index, (key, title) in enumerate(PROCEDURE_STEPS)]
        db.executemany("INSERT INTO procedure_steps VALUES(?,?,?,?,?,?,?,?,?,?)", steps)
        audit(db, "matter", matter_id, "created", {"title": values[1], "procedure_steps": len(steps)})
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
        result["documents"] = [dict(x) for x in db.execute("SELECT id,matter_id,filename,kind,extracted_text,source_hash,byte_size,mime_type,storage_path,retention_class,integrity_status,metadata_json,created_at FROM documents WHERE matter_id=? ORDER BY created_at DESC", (matter_id,)).fetchall()]
        result["custody_events"] = [dict(x) for x in db.execute("SELECT * FROM custody_events WHERE matter_id=? ORDER BY created_at", (matter_id,)).fetchall()]
        result["parties"] = [dict(x) for x in db.execute("SELECT * FROM parties WHERE matter_id=? ORDER BY created_at", (matter_id,)).fetchall()]
        result["facts"] = [dict(x) for x in db.execute("SELECT * FROM facts WHERE matter_id=? ORDER BY event_date IS NULL, event_date, created_at", (matter_id,)).fetchall()]
        result["claims"] = [dict(x) for x in db.execute("SELECT * FROM claims WHERE matter_id=? ORDER BY created_at", (matter_id,)).fetchall()]
        result["claim_evidence"] = [dict(x) for x in db.execute("SELECT ce.*, c.title AS claim_title, d.filename FROM claim_evidence ce JOIN claims c ON c.id=ce.claim_id JOIN documents d ON d.id=ce.document_id WHERE ce.matter_id=? ORDER BY ce.created_at", (matter_id,)).fetchall()]
        result["deadlines"] = [dict(x) for x in db.execute("SELECT * FROM deadlines WHERE matter_id=? ORDER BY due_date IS NULL, due_date", (matter_id,)).fetchall()]
        result["audit"] = [dict(x) for x in db.execute("SELECT * FROM audit_events WHERE entity_id=? ORDER BY created_at DESC LIMIT 100", (matter_id,)).fetchall()]
        result["procedure_steps"] = [dict(x) for x in db.execute("SELECT * FROM procedure_steps WHERE matter_id=? ORDER BY rowid", (matter_id,)).fetchall()]
        result["document_inspections"] = [dict(x) for x in db.execute("SELECT * FROM document_inspections WHERE matter_id=? ORDER BY inspected_at DESC", (matter_id,)).fetchall()]
        result["discovered_rights"] = [dict(x) for x in db.execute("SELECT * FROM discovered_rights WHERE matter_id=? ORDER BY updated_at DESC", (matter_id,)).fetchall()]
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


def update_procedure_step(matter_id: str, step_key: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    allowed = {key: payload[key] for key in ("status", "notes") if key in payload}
    stamp = now()
    if payload.get("status") == "جارية": allowed.update(started_at=stamp, completed_at=None)
    elif payload.get("status") == "مكتملة": allowed.update(completed_at=stamp, started_at=stamp)
    if not allowed:
        allowed = {}
    with connect() as db:
        row = db.execute("SELECT 1 FROM procedure_steps WHERE matter_id=? AND step_key=?", (matter_id, step_key)).fetchone()
        if not row: raise KeyError(step_key)
        if allowed:
            fields = ", ".join(f"{k}=?" for k in allowed)
            db.execute(f"UPDATE procedure_steps SET {fields}, updated_at=? WHERE matter_id=? AND step_key=?", [*allowed.values(), stamp, matter_id, step_key])
        db.execute("UPDATE matters SET updated_at=? WHERE id=?", (stamp, matter_id))
        audit(db, "procedure_step", f"{matter_id}:{step_key}", "updated", {"status": payload.get("status")})
        return dict(db.execute("SELECT * FROM procedure_steps WHERE matter_id=? AND step_key=?", (matter_id, step_key)).fetchone())

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


def add_document(matter_id: Optional[str], filename: str, kind: str, extracted_text: str, source_hash: str, byte_size: int = 0, mime_type: str = "", storage_path: str = "", metadata: Optional[Dict[str, Any]] = None, raw_bytes: Optional[bytes] = None) -> Dict[str, Any]:
    document_id, stamp = _id("doc"), now()
    if raw_bytes is not None:
        actual_hash = hashlib.sha256(raw_bytes).hexdigest()
        if source_hash and source_hash != actual_hash:
            raise ValueError("بصمة الملف الأصلي لا تطابق البيانات المرفوعة")
        source_hash = actual_hash
        byte_size = len(raw_bytes)
    payload = {"filename": filename, "source_hash": source_hash, "byte_size": byte_size, "mime_type": mime_type, "kind": kind}
    event_hash = hashlib.sha256(json.dumps({"document_id": document_id, "event_type": "ingested", "payload": payload, "created_at": stamp}, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
    if raw_bytes is not None:
        os.makedirs(BLOB_DIR, exist_ok=True)
        storage_path = os.path.join(BLOB_DIR, f"{document_id}.bin")
        with open(storage_path, "wb") as blob:
            blob.write(raw_bytes)
    with connect() as db:
        if matter_id and not db.execute("SELECT 1 FROM matters WHERE id=?", (matter_id,)).fetchone():
            raise KeyError(matter_id)
        db.execute("INSERT INTO documents(id,matter_id,filename,kind,extracted_text,source_hash,byte_size,mime_type,storage_path,retention_class,integrity_status,metadata_json,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)", (document_id, matter_id, filename, kind, extracted_text, source_hash, byte_size, mime_type, storage_path, "حساس", "سليم", json.dumps(metadata or {}, ensure_ascii=False), stamp))
        db.execute("INSERT INTO custody_events(id,document_id,matter_id,event_type,actor,details,event_hash,created_at) VALUES(?,?,?,?,?,?,?,?)", (_id("custody"), document_id, matter_id, "ingested", "المستخدم الوحيد", json.dumps(payload, ensure_ascii=False), event_hash, stamp))
        if matter_id:
            audit(db, "matter", matter_id, "document_added", {"document_id": document_id, "filename": filename, "source_hash": source_hash, "event_hash": event_hash, "metadata": metadata or {}})
    return {"id": document_id, "matter_id": matter_id, "filename": filename, "kind": kind, "source_hash": source_hash, "byte_size": byte_size, "mime_type": mime_type, "storage_path": storage_path, "integrity_status": "سليم", "metadata": metadata or {}, "created_at": stamp, "custody_event_hash": event_hash}


def save_document_inspection(document_id: str, matter_id: str, inspection: Dict[str, Any]) -> Dict[str, Any]:
    inspection_id, stamp = _id("inspection"), now()
    with connect() as db:
        _ensure_matter(db, matter_id)
        db.execute("INSERT INTO document_inspections(id,document_id,matter_id,inspection_status,readable,full_text_available,pages,characters_scanned,words_approx,signals_json,coverage_json,errors_json,inspected_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)", (inspection_id, document_id, matter_id, inspection.get("inspection_status", "فشل الفحص"), int(bool(inspection.get("readable"))), int(bool(inspection.get("full_text_available"))), int(inspection.get("pages", 0) or 0), int(inspection.get("characters_scanned", 0) or 0), int(inspection.get("words_approx", 0) or 0), json.dumps(inspection.get("signals", {}), ensure_ascii=False), json.dumps({"keyword_occurrences": inspection.get("keyword_occurrences", {}), "manual_review_required": inspection.get("manual_review_required", True)}, ensure_ascii=False), json.dumps(inspection.get("errors", []), ensure_ascii=False), stamp))
        audit(db, "matter", matter_id, "document_inspected", {"document_id": document_id, "inspection_id": inspection_id, "status": inspection.get("inspection_status")})
    return {"id": inspection_id, "document_id": document_id, "matter_id": matter_id, "inspection_status": inspection.get("inspection_status", "فشل الفحص"), "readable": bool(inspection.get("readable")), "manual_review_required": bool(inspection.get("manual_review_required", True)), "inspected_at": stamp}


def replace_discovered_rights(matter_id: str, findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    stamp = now()
    saved = []
    with connect() as db:
        _ensure_matter(db, matter_id)
        for item in findings:
            right_id = _id("right")
            values = (right_id, matter_id, item.get("right_key", "unknown"), item.get("label", "حق محتمل"), item.get("status", "يحتاج تحقق"), int(item.get("trigger_count", 0)), item.get("reason", ""), json.dumps(item.get("elements_to_verify", []), ensure_ascii=False), json.dumps(item.get("evidence_needed", []), ensure_ascii=False), json.dumps(item.get("missing_items", []), ensure_ascii=False), json.dumps(item.get("triggers", []), ensure_ascii=False), json.dumps(item.get("source_refs", []), ensure_ascii=False), int(bool(item.get("human_review_required", True))), stamp, stamp)
            db.execute("INSERT INTO discovered_rights(id,matter_id,right_key,label,status,trigger_count,reason,elements_json,evidence_json,missing_json,triggers_json,source_refs_json,human_review_required,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(matter_id,right_key) DO UPDATE SET label=excluded.label,status=excluded.status,trigger_count=excluded.trigger_count,reason=excluded.reason,elements_json=excluded.elements_json,evidence_json=excluded.evidence_json,missing_json=excluded.missing_json,triggers_json=excluded.triggers_json,source_refs_json=excluded.source_refs_json,human_review_required=excluded.human_review_required,updated_at=excluded.updated_at", values)
            saved.append({"right_key": item.get("right_key"), "label": item.get("label"), "status": item.get("status"), "trigger_count": item.get("trigger_count", 0), "reason": item.get("reason", ""), "triggers": item.get("triggers", []), "elements_to_verify": item.get("elements_to_verify", []), "evidence_needed": item.get("evidence_needed", []), "missing_items": item.get("missing_items", []), "human_review_required": True, "updated_at": stamp})
        audit(db, "matter", matter_id, "hidden_rights_discovered", {"count": len(saved), "undisclosed_count": sum(x["status"] == "مؤشر حق غير مذكور" for x in saved)})
    return saved


def list_document_inspections(matter_id: str) -> List[Dict[str, Any]]:
    with connect() as db:
        return [dict(x) for x in db.execute("SELECT * FROM document_inspections WHERE matter_id=? ORDER BY inspected_at DESC", (matter_id,)).fetchall()]


def list_discovered_rights(matter_id: str) -> List[Dict[str, Any]]:
    with connect() as db:
        return [dict(x) for x in db.execute("SELECT * FROM discovered_rights WHERE matter_id=? ORDER BY updated_at DESC", (matter_id,)).fetchall()]


def verify_document(document_id: str, matter_id: Optional[str] = None) -> Dict[str, Any]:
    with connect() as db:
        query = "SELECT * FROM documents WHERE id=?" + (" AND matter_id=?" if matter_id else "")
        params = (document_id, matter_id) if matter_id else (document_id,)
        row = db.execute(query, params).fetchone()
        if not row:
            raise KeyError(document_id)
        doc = dict(row)
    path = doc.get("storage_path", "")
    if not path or not os.path.isfile(path):
        return {"document_id": document_id, "status": "غير قابل للتحقق", "reason": "الأصل الثنائي غير محفوظ", "expected_hash": doc["source_hash"], "verified": False}
    with open(path, "rb") as blob:
        actual = hashlib.sha256(blob.read()).hexdigest()
    verified = actual == doc["source_hash"]
    return {"document_id": document_id, "status": "سليم" if verified else "متغير", "expected_hash": doc["source_hash"], "actual_hash": actual, "verified": verified}


def build_backup_archive() -> str:
    """يبني أرشيفًا محليًا مؤقتًا؛ يجب نقله وتخزينه مشفرًا خارج الخادم."""
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    archive_path = os.path.join(tempfile.gettempdir(), f"fuhrer-backup-{stamp}.zip")
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.write(DB_PATH, "workspace.sqlite3")
        if os.path.isdir(BLOB_DIR):
            for root, _, filenames in os.walk(BLOB_DIR):
                for filename in filenames:
                    path = os.path.join(root, filename)
                    archive.write(path, os.path.join("document_blobs", filename))
        manifest = {"created_at": now(), "database": "workspace.sqlite3", "blob_directory": "document_blobs", "warning": "الأرشيف ليس مشفرًا تلقائيًا؛ خزنه داخل حاوية مشفرة ولا تشاركه."}
        archive.writestr("BACKUP_MANIFEST.json", json.dumps(manifest, ensure_ascii=False, indent=2))
    return archive_path


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
