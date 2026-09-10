from case_package import build_package, to_html, to_json, to_markdown


def sample_matter():
    return {
        "id": "matter_test",
        "title": "نزاع عمالي اختباري",
        "matter_type": "نزاع عمالي",
        "status": "مفتوحة",
        "priority": "عالية",
        "client_name": "المستخدم",
        "opposing_party": "صاحب العمل",
        "jurisdiction": "يحدد بعد التحقق",
        "description": "وصف النزاع",
        "parties": [{"name": "المستخدم", "role": "مدعٍ", "contact": ""}],
        "facts": [{"title": "إيقاف الراتب", "event_date": "2026-01-15", "certainty": "مثبت بمستند", "description": "خطاب"}],
        "claims": [{"title": "أجور متأخرة", "position": "مقترح", "status": "قيد التحقق", "legal_basis": "يحتاج تحققًا"}],
        "documents": [{"filename": "خطاب.pdf", "kind": "دليل", "source_hash": "abc123", "created_at": "2026-01-15"}],
        "deadlines": [{"title": "موعد الرد", "due_date": "2026-09-10", "status": "مفتوح", "source": "إشعار"}],
        "tasks": [{"title": "مراجعة الإشعار", "status": "مفتوحة", "due_date": "2026-09-08"}],
        "audit": [],
    }


def test_all_case_package_formats_have_core_sections():
    package = build_package(sample_matter())
    markdown = to_markdown(package)
    html = to_html(package)
    payload = to_json(package)
    for section in ("الأطراف", "الخط الزمني", "الطلبات", "المواعيد", "فحص جودة"):
        assert section in markdown
        assert section in html
    assert '"quality_flags"' in payload
    assert "SHA-256" in markdown
    assert "abc123" in html
