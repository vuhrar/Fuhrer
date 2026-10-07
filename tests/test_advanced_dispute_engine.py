from advanced_dispute_engine import assess_matter, role_catalog


def test_role_catalog_contains_only_approved_roles():
    keys = [x["key"] for x in role_catalog()]
    assert keys == ["محامي", "مستشار قانوني", "مستشار عمالي"]
    assert "عامل" not in keys
    assert "قاضي" not in keys


def test_assessment_exposes_risks_gates_and_claim_evidence_matrix():
    matter = {
        "id": "m1", "title": "نزاع راتب وإنهاء", "matter_type": "نزاع عمالي",
        "description": "طلب تسوية ودية بسبب راتب متأخر وإنهاء خدمة",
        "jurisdiction": "المحكمة العمالية", "parties": [{"name": "أ"}, {"name": "ب"}],
        "facts": [{"id": "f1", "title": "عدم سداد الراتب", "description": "راتب مايو", "event_date": None}],
        "claims": [{"id": "c1", "title": "الأجر المتبقي", "legal_basis": ""}],
        "documents": [], "deadlines": [], "claim_evidence": [], "procedure_steps": [],
    }
    result = assess_matter(matter, "مستشار عمالي")
    assert result["engine_version"] == "2.0"
    assert result["role"]["label"] == "المستشار العمالي"
    assert len(result["risk_register"]) == 7
    assert result["claim_evidence_matrix"][0]["evidence_status"] == "غير مرتبط"
    assert any(x["status"] == "بوابة متوقفة" for x in result["procedure_gates"])
    assert result["readiness"]["score"] < 100
