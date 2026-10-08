"""اختبارات PostgreSQL حقيقية.

التشغيل الآمن:
  FUHRER_TEST_POSTGRES_URL=postgresql://... pytest -q tests/test_repository_postgres_integration.py

لا تستخدم DATABASE_URL تلقائيًا حتى لا تتصل الاختبارات بقاعدة الإنتاج بالخطأ.
"""
from __future__ import annotations

import os
import time
import uuid
from typing import Iterator

import pytest

from repository import Repository, RepositoryConfig


@pytest.fixture(scope="module")
def postgres_repo() -> Iterator[tuple[Repository, str]]:
    dsn = os.getenv("FUHRER_TEST_POSTGRES_URL")
    if not dsn:
        pytest.skip("FUHRER_TEST_POSTGRES_URL غير مضبوط؛ تم تجاوز اختبار PostgreSQL الحقيقي")
    try:
        import psycopg2
        connection = psycopg2.connect(dsn)
        connection.close()
    except Exception as exc:
        pytest.skip(f"PostgreSQL غير متاح في DSN الاختبار: {exc}")

    repo = Repository(RepositoryConfig.from_env(dsn))
    repo.init_schema()
    marker = f"integration_{uuid.uuid4().hex[:12]}"
    try:
        yield repo, marker
    finally:
        right_id = f"{marker}_right"
        with repo.connection() as conn:
            for table, column, value in [
                ("discovered_right_triggers", "discovered_right_id", right_id),
                ("user_review_decisions", "matter_id", marker),
                ("legal_statements", "matter_id", marker),
                ("legal_entities", "matter_id", marker),
            ]:
                repo._execute(conn, f"DELETE FROM {table} WHERE {column}=?", [value])


def test_postgres_connection_schema_and_jsonb_round_trip(postgres_repo):
    repo, marker = postgres_repo
    entity = repo.save_entity(
        matter_id=marker,
        document_id=f"{marker}_doc",
        entity_type="pay_record",
        value={"agreed": 10000, "paid": 8500, "currency": "SAR", "period": "2025-05"},
        page_number=2,
        excerpt="10000 | 8500",
        confidence=0.94,
    )
    rows = repo.list_entities(marker)
    assert rows and rows[0]["id"] == entity["id"]
    assert rows[0]["value_json"]["paid"] == 8500
    assert rows[0]["value_json"]["currency"] == "SAR"


def test_postgres_statement_trigger_and_review_lifecycle(postgres_repo):
    repo, marker = postgres_repo
    statement = repo.save_statement(
        matter_id=marker,
        document_id=f"{marker}_doc",
        text="تدعي الإدارة أن العامل لم يعمل ساعات إضافية",
        speaker="الإدارة",
        polarity="منفي",
        status="negated_by_employer",
        negation_cue="لم",
        quoted=False,
        page_number=3,
        start_offset=10,
        end_offset=62,
        confidence=0.82,
    )
    trigger = repo.save_right_trigger(
        discovered_right_id=f"{marker}_right",
        statement_id=statement["id"],
        trigger_type="contextual_statement",
        excerpt=statement["text"],
        page_number=3,
        source_quality=0.95,
    )
    decision = repo.save_review_decision(
        matter_id=marker,
        discovered_right_id=f"{marker}_right",
        decision="يحتاج مستندًا إضافيًا",
        note="أرفق سجل الحضور",
    )
    assert repo.list_statements(marker)[0]["quoted"] is False
    assert repo.list_right_triggers(f"{marker}_right")[0]["id"] == trigger["id"]
    assert repo.list_review_decisions(marker)[0]["id"] == decision["id"]


def test_postgres_repository_write_read_latency_is_bounded(postgres_repo):
    repo, marker = postgres_repo
    count = int(os.getenv("FUHRER_POSTGRES_PERF_ROWS", "25"))
    started = time.perf_counter()
    for index in range(count):
        repo.save_entity(
            matter_id=marker,
            entity_type="attendance_record",
            value={"check_in": "08:00", "check_out": "22:00", "row": index},
            page_number=index + 1,
            confidence=0.88,
        )
    write_seconds = time.perf_counter() - started
    read_started = time.perf_counter()
    rows = repo.list_entities(marker)
    read_seconds = time.perf_counter() - read_started
    assert len(rows) == count
    # حد واسع يمنع جعل الاختبار هشًا على CI، لكنه يكشف انقطاع الاتصال أو الأداء الكارثي.
    max_seconds = float(os.getenv("FUHRER_POSTGRES_MAX_TEST_SECONDS", "15"))
    assert write_seconds + read_seconds < max_seconds
