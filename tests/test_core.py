from file_processing import truncate_for_ai
from legal_intelligence import evidence_checklist, extract_obligations, legal_review_package, scan_risks, search_with_sources


def test_truncate_preserves_both_ends():
    value = "A" * 100 + "B" * 100
    result = truncate_for_ai(value, 100)
    assert result.startswith("A")
    assert result.endswith("B")
    assert "تم حذف" in result


def test_extract_obligations_identifies_party_and_text():
    result = extract_obligations("يلتزم صاحب العمل بتسليم نسخة من العقد. ويجب على العامل المحافظة على السرية.")
    assert len(result) == 2
    assert result[0]["party"] == "صاحب العمل"
    assert result[1]["party"] == "العامل"
    assert all(item["needs_review"] for item in result)


def test_scan_risks_finds_missing_critical_clauses():
    risks = scan_risks("يلتزم المورد بتقديم الخدمة وتسليم المخرج.")
    areas = {item["area"] for item in risks}
    assert "المدة والإنهاء" in areas
    assert "القانون والاختصاص" in areas
    assert "الملكية الفكرية" in areas


def test_evidence_checklist_is_issue_driven():
    result = evidence_checklist("تم إنهاء العقد وتأخر صرف الراتب.")
    issues = {item["issue"] for item in result}
    assert "الإنهاء" in issues
    assert "الأجر أو المقابل" in issues


def test_review_package_contains_traceability_fields():
    result = legal_review_package("وفقًا للمادة 77 تم إنهاء العقد.")
    assert result["mentioned_articles"] == ["77"]
    assert result["sources"]
    assert result["quality"]["requires_lawyer_review"] is True


def test_search_results_include_official_source_metadata():
    result = search_with_sources("إنهاء", max_results=2)
    assert result
    assert all(item["source"]["publisher"] for item in result)
    assert all(item["verification_required"] for item in result)
