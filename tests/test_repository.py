from pathlib import Path

import pytest

from repository import Repository, RepositoryConfig


def test_sqlite_repository_persists_normalized_legal_records(tmp_path: Path):
    repo = Repository(RepositoryConfig.from_env(f"sqlite:///{tmp_path / 'repo.sqlite3'}"))
    repo.init_schema()
    entity = repo.save_entity(matter_id="matter_1", document_id="doc_1", entity_type="pay_record", value={"agreed": 10000, "paid": 8500}, page_number=2, excerpt="10000 | 8500", confidence=0.94)
    statement = repo.save_statement(matter_id="matter_1", document_id="doc_1", text="تدعي الإدارة أن العامل لم يعمل ساعات إضافية", speaker="الإدارة", polarity="منفي", status="negated_by_employer", negation_cue="لم", page_number=3, confidence=0.82)
    trigger = repo.save_right_trigger(discovered_right_id="right_1", entity_id=entity["id"], statement_id=statement["id"], trigger_type="contradiction", excerpt="10000 | 8500", page_number=2, source_quality=0.95)
    decision = repo.save_review_decision(matter_id="matter_1", discovered_right_id="right_1", decision="يحتاج مستندًا إضافيًا", note="أرفق كشف الحساب")
    assert repo.list_entities("matter_1")[0]["value_json"] == {"agreed": 10000, "paid": 8500}
    assert repo.list_statements("matter_1")[0]["status"] == "negated_by_employer"
    assert repo.list_right_triggers("right_1")[0]["id"] == trigger["id"]
    assert repo.list_review_decisions("matter_1")[0]["decision"] == decision["decision"]


def test_database_url_selects_postgresql_backend_without_connecting():
    config = RepositoryConfig.from_env("postgresql://user:pass@example.test:5432/fuhrer")
    assert config.backend == "postgresql"
    assert config.sqlite_path is None


def test_invalid_database_scheme_is_rejected():
    with pytest.raises(ValueError):
        RepositoryConfig.from_env("mysql://user:pass@localhost/fuhrer")
