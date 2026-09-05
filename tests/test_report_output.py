from reporting import build_matter_report


def test_report_contains_dispute_sections():
    report = build_matter_report({
        "title": "نزاع عمالي",
        "status": "مفتوحة",
        "matter_type": "نزاع عمالي",
        "priority": "عالية",
        "description": "واقعة",
        "parties": [{"name": "صاحب العمل", "role": "مدعى عليه", "contact": ""}],
        "facts": [{"event_date": "2026-01-01", "title": "إيقاف الراتب", "certainty": "مثبت بمستند", "description": "خطاب"}],
        "claims": [{"title": "أجور متأخرة", "status": "قيد التحقق", "position": "مقترح", "legal_basis": "مادة تحتاج تحقق"}],
        "deadlines": [{"due_date": "2026-09-10", "title": "موعد رد", "status": "مفتوح", "source": "إشعار"}],
        "tasks": [], "documents": []
    })
    assert "الأطراف" in report
    assert "الخط الزمني والوقائع" in report
    assert "الطلبات والمواقف القانونية" in report
    assert "المواعيد والإجراءات" in report
