import workspace_store


def test_matter_has_ordered_procedure_steps_and_updates(monkeypatch, tmp_path):
    monkeypatch.setattr(workspace_store, "DB_PATH", str(tmp_path / "workspace.sqlite3"))
    workspace_store.init_db()
    matter = workspace_store.create_matter(
        {
            "title": "اختبار مسار عمالي",
            "matter_type": "نزاع عمالي",
            "client_name": "العامل",
            "opposing_party": "المنشأة",
            "jurisdiction": "التسوية الودية",
            "description": "نزاع حول أجر وإنهاء",
        }
    )
    assert [step["step_key"] for step in matter["procedure_steps"]] == [
        "intake", "evidence", "legal_review", "amicable_settlement", "referral",
        "lawsuit", "hearings", "judgment", "enforcement", "closed",
    ]
    updated = workspace_store.update_procedure_step(
        matter["id"], "amicable_settlement", {"status": "جارية", "notes": "تم فتح طلب التسوية"}
    )
    assert updated["status"] == "جارية"
    assert updated["notes"] == "تم فتح طلب التسوية"
    stored = workspace_store.get_matter(matter["id"])
    assert stored["procedure_steps"][3]["step_key"] == "amicable_settlement"
