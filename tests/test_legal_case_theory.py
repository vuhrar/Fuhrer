from legal_case_theory import build_case_theory


def test_case_theory_builds_wage_and_termination_challenges():
    matter = {
        "title": "نزاع راتب وإنهاء", "description": "العامل يطالب براتب متأخر ويطعن في الإنهاء",
        "facts": [{"id": "f1", "title": "عدم سداد الراتب", "description": "راتب مايو", "certainty": "مثبت بمستند", "event_date": "2025-05-31"}],
        "claims": [{"id": "c1", "title": "المطالبة بالأجر المتبقي", "legal_basis": "يحتاج تحققًا"}],
        "documents": [{"id": "d1", "filename": "خطاب الإنهاء.pdf", "kind": "مستند", "integrity_status": "سليم", "extracted_text": "إنهاء خدمة"}],
        "deadlines": [], "parties": [], "claim_evidence": [], "procedure_steps": [],
    }
    theory = build_case_theory(matter, "محامي")
    labels = {x["issue"] for x in theory["issues"]}
    assert "الأجر والاستحقاقات" in labels
    assert "الإنهاء والفصل والإشعار" in labels
    assert theory["role"] == "محامي"
    assert theory["administration_challenge_plan"]
    assert theory["interview_questions"]
    assert "الطلبات والمستندات المؤيدة" in theory["drafting_outline"]
