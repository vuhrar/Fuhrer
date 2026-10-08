"""طبقة Repository موحدة لـ SQLite وPostgreSQL.

تستخدم DB-API مباشرة حتى تبقى محركات التحليل مستقلة عن نوع قاعدة البيانات.
الاختيار:
    DATABASE_URL=sqlite:////absolute/path/workspace.sqlite3
    DATABASE_URL=postgresql://user:password@host:5432/fuhrer

في حال عدم ضبط DATABASE_URL يستخدم FUHRER_DATA_DIR/workspace.sqlite3.
"""
from __future__ import annotations

import json
import os
import re
import sqlite3
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Mapping, Optional
from urllib.parse import urlparse


class RepositoryError(RuntimeError):
    """خطأ موحد في طبقة التخزين."""


@dataclass(frozen=True)
class RepositoryConfig:
    url: str
    backend: str
    sqlite_path: Optional[str] = None

    @classmethod
    def from_env(cls, url: Optional[str] = None) -> "RepositoryConfig":
        value = url or os.getenv("DATABASE_URL")
        if not value:
            data_dir = Path(os.getenv("FUHRER_DATA_DIR", Path.home() / "fuhrer_data"))
            data_dir.mkdir(parents=True, exist_ok=True)
            value = f"sqlite:///{data_dir / 'workspace.sqlite3'}"
        parsed = urlparse(value)
        scheme = parsed.scheme.lower()
        if scheme == "sqlite":
            path = parsed.path
            if parsed.netloc and parsed.netloc not in ("", "localhost"):
                path = f"//{parsed.netloc}{path}"
            if not path:
                raise ValueError("مسار SQLite غير موجود في DATABASE_URL")
            return cls(url=value, backend="sqlite", sqlite_path=path)
        if scheme in {"postgres", "postgresql", "postgresql+psycopg2"}:
            return cls(url=value, backend="postgresql")
        raise ValueError(f"قاعدة بيانات غير مدعومة: {scheme}")


class Repository:
    """مستودع البيانات المنظم الذي تستخدمه محركات التحليل وواجهة API."""

    def __init__(self, config: Optional[RepositoryConfig] = None):
        self.config = config or RepositoryConfig.from_env()

    @staticmethod
    def _id(prefix: str) -> str:
        return f"{prefix}_{uuid.uuid4().hex[:16]}"

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @property
    def is_sqlite(self) -> bool:
        return self.config.backend == "sqlite"

    @contextmanager
    def connection(self) -> Iterator[Any]:
        conn = None
        try:
            if self.is_sqlite:
                Path(self.config.sqlite_path).parent.mkdir(parents=True, exist_ok=True)
                conn = sqlite3.connect(self.config.sqlite_path, timeout=20)
                conn.row_factory = sqlite3.Row
                conn.execute("PRAGMA foreign_keys=ON")
                conn.execute("PRAGMA busy_timeout=20000")
            else:
                try:
                    import psycopg2
                    conn = psycopg2.connect(self.config.url.replace("postgresql+psycopg2://", "postgresql://", 1))
                except ImportError as exc:
                    raise RepositoryError("ثبت psycopg2-binary مطلوب لتشغيل PostgreSQL") from exc
            yield conn
            conn.commit()
        except Exception:
            if conn is not None:
                conn.rollback()
            raise
        finally:
            if conn is not None:
                conn.close()

    def _sql(self, statement: str) -> str:
        return statement if self.is_sqlite else statement.replace("?", "%s")

    @staticmethod
    def _postgres_json(value: Any) -> Any:
        try:
            from psycopg2.extras import Json
            return Json(value, dumps=lambda item: json.dumps(item, ensure_ascii=False))
        except ImportError as exc:
            raise RepositoryError("ثبت psycopg2-binary مطلوب لتخزين JSON في PostgreSQL") from exc

    def _rows(self, cursor: Any) -> List[Dict[str, Any]]:
        if self.is_sqlite:
            return [dict(row) for row in cursor.fetchall()]
        columns = [column[0] for column in cursor.description] if cursor.description else []
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def _execute(self, conn: Any, statement: str, params: Iterable[Any] = ()) -> Any:
        cursor = conn.cursor()
        cursor.execute(self._sql(statement), tuple(params))
        return cursor

    def init_schema(self) -> None:
        """ينشئ جداول الطبقة المنظمة دون حذف أو تعديل جداول التطبيق الحالية."""
        auto_id = "TEXT PRIMARY KEY" if self.is_sqlite else "VARCHAR(80) PRIMARY KEY"
        bool_type = "INTEGER" if self.is_sqlite else "BOOLEAN"
        bool_default = "0" if self.is_sqlite else "FALSE"
        json_type = "TEXT" if self.is_sqlite else "JSONB"
        timestamp = "TEXT" if self.is_sqlite else "TIMESTAMPTZ"
        statements = [
            f"""CREATE TABLE IF NOT EXISTS legal_entities (
                id {auto_id}, matter_id VARCHAR(120) NOT NULL, document_id VARCHAR(120),
                entity_type VARCHAR(100) NOT NULL, value_json {json_type} NOT NULL,
                page_number INTEGER, excerpt TEXT NOT NULL DEFAULT '', confidence DOUBLE PRECISION,
                polarity VARCHAR(60), speaker VARCHAR(120), created_at {timestamp} NOT NULL
            )""",
            f"""CREATE TABLE IF NOT EXISTS legal_statements (
                id {auto_id}, matter_id VARCHAR(120) NOT NULL, document_id VARCHAR(120),
                text TEXT NOT NULL, speaker VARCHAR(120), polarity VARCHAR(80), status VARCHAR(100),
                negation_cue VARCHAR(120), quoted {bool_type} NOT NULL DEFAULT {bool_default},
                page_number INTEGER, start_offset INTEGER, end_offset INTEGER, confidence DOUBLE PRECISION,
                created_at {timestamp} NOT NULL
            )""",
            f"""CREATE TABLE IF NOT EXISTS discovered_right_triggers (
                id {auto_id}, discovered_right_id VARCHAR(120) NOT NULL,
                entity_id VARCHAR(120), statement_id VARCHAR(120), trigger_type VARCHAR(80) NOT NULL,
                excerpt TEXT NOT NULL DEFAULT '', page_number INTEGER, source_quality DOUBLE PRECISION,
                created_at {timestamp} NOT NULL
            )""",
            f"""CREATE TABLE IF NOT EXISTS user_review_decisions (
                id {auto_id}, matter_id VARCHAR(120) NOT NULL, discovered_right_id VARCHAR(120) NOT NULL,
                decision VARCHAR(80) NOT NULL, note TEXT NOT NULL DEFAULT '', created_at {timestamp} NOT NULL
            )""",
            "CREATE INDEX IF NOT EXISTS idx_legal_entities_matter ON legal_entities(matter_id)",
            "CREATE INDEX IF NOT EXISTS idx_legal_statements_matter ON legal_statements(matter_id)",
            "CREATE INDEX IF NOT EXISTS idx_right_triggers_right ON discovered_right_triggers(discovered_right_id)",
        ]
        with self.connection() as conn:
            for statement in statements:
                self._execute(conn, statement)

    def save_entity(self, *, matter_id: str, entity_type: str, value: Mapping[str, Any], document_id: Optional[str] = None, page_number: Optional[int] = None, excerpt: str = "", confidence: Optional[float] = None, polarity: Optional[str] = None, speaker: Optional[str] = None, entity_id: Optional[str] = None) -> Dict[str, Any]:
        item = {"id": entity_id or self._id("entity"), "matter_id": matter_id, "document_id": document_id, "entity_type": entity_type, "value_json": value, "page_number": page_number, "excerpt": excerpt, "confidence": confidence, "polarity": polarity, "speaker": speaker, "created_at": self._now()}
        with self.connection() as conn:
            value = json.dumps(item["value_json"], ensure_ascii=False) if self.is_sqlite else self._postgres_json(item["value_json"])
            self._execute(conn, "INSERT INTO legal_entities(id,matter_id,document_id,entity_type,value_json,page_number,excerpt,confidence,polarity,speaker,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)", [item["id"], item["matter_id"], item["document_id"], item["entity_type"], value, item["page_number"], item["excerpt"], item["confidence"], item["polarity"], item["speaker"], item["created_at"]])
        return item

    def save_statement(self, *, matter_id: str, text: str, speaker: Optional[str] = None, polarity: Optional[str] = None, status: Optional[str] = None, negation_cue: Optional[str] = None, quoted: bool = False, document_id: Optional[str] = None, page_number: Optional[int] = None, start_offset: Optional[int] = None, end_offset: Optional[int] = None, confidence: Optional[float] = None, statement_id: Optional[str] = None) -> Dict[str, Any]:
        item = {"id": statement_id or self._id("statement"), "matter_id": matter_id, "document_id": document_id, "text": text, "speaker": speaker, "polarity": polarity, "status": status, "negation_cue": negation_cue, "quoted": quoted, "page_number": page_number, "start_offset": start_offset, "end_offset": end_offset, "confidence": confidence, "created_at": self._now()}
        with self.connection() as conn:
            self._execute(conn, "INSERT INTO legal_statements(id,matter_id,document_id,text,speaker,polarity,status,negation_cue,quoted,page_number,start_offset,end_offset,confidence,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)", [item["id"], item["matter_id"], item["document_id"], item["text"], item["speaker"], item["polarity"], item["status"], item["negation_cue"], int(item["quoted"]) if self.is_sqlite else item["quoted"], item["page_number"], item["start_offset"], item["end_offset"], item["confidence"], item["created_at"]])
        return item

    def save_right_trigger(self, *, discovered_right_id: str, trigger_type: str, excerpt: str = "", entity_id: Optional[str] = None, statement_id: Optional[str] = None, page_number: Optional[int] = None, source_quality: Optional[float] = None, trigger_id: Optional[str] = None) -> Dict[str, Any]:
        item = {"id": trigger_id or self._id("trigger"), "discovered_right_id": discovered_right_id, "entity_id": entity_id, "statement_id": statement_id, "trigger_type": trigger_type, "excerpt": excerpt, "page_number": page_number, "source_quality": source_quality, "created_at": self._now()}
        with self.connection() as conn:
            self._execute(conn, "INSERT INTO discovered_right_triggers(id,discovered_right_id,entity_id,statement_id,trigger_type,excerpt,page_number,source_quality,created_at) VALUES(?,?,?,?,?,?,?,?,?)", list(item.values()))
        return item

    def save_review_decision(self, *, matter_id: str, discovered_right_id: str, decision: str, note: str = "", decision_id: Optional[str] = None) -> Dict[str, Any]:
        item = {"id": decision_id or self._id("review"), "matter_id": matter_id, "discovered_right_id": discovered_right_id, "decision": decision, "note": note, "created_at": self._now()}
        with self.connection() as conn:
            self._execute(conn, "INSERT INTO user_review_decisions(id,matter_id,discovered_right_id,decision,note,created_at) VALUES(?,?,?,?,?,?)", list(item.values()))
        return item

    def list_entities(self, matter_id: str) -> List[Dict[str, Any]]:
        with self.connection() as conn:
            rows = self._rows(self._execute(conn, "SELECT * FROM legal_entities WHERE matter_id=? ORDER BY created_at", [matter_id]))
        for row in rows:
            if isinstance(row.get("value_json"), str):
                row["value_json"] = json.loads(row["value_json"] or "{}")
        return rows

    def list_statements(self, matter_id: str) -> List[Dict[str, Any]]:
        with self.connection() as conn:
            return self._rows(self._execute(conn, "SELECT * FROM legal_statements WHERE matter_id=? ORDER BY created_at", [matter_id]))

    def list_right_triggers(self, discovered_right_id: str) -> List[Dict[str, Any]]:
        with self.connection() as conn:
            return self._rows(self._execute(conn, "SELECT * FROM discovered_right_triggers WHERE discovered_right_id=? ORDER BY created_at", [discovered_right_id]))

    def list_review_decisions(self, matter_id: str) -> List[Dict[str, Any]]:
        with self.connection() as conn:
            return self._rows(self._execute(conn, "SELECT * FROM user_review_decisions WHERE matter_id=? ORDER BY created_at", [matter_id]))


def repository_from_env() -> Repository:
    """مصنع واحد تستخدمه FastAPI أو مهام الخلفية."""
    repository = Repository(RepositoryConfig.from_env())
    repository.init_schema()
    return repository
