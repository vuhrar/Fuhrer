# tests/test_phases_0_1_2.py
"""
اختبارات pytest حقيقية ودائمة لكل ما بُني في المراحل صفر و1 و2.

⚠️ ملاحظة صادقة: هذا الملف كُتب ووُثّقت صحة منطقه بتنفيذ مباشر لكل دالة
اختبار عبر python3 عاديًا (راجع تقرير التسليم)، لأن حاوية العمل هذه لا تملك
pytest مثبَّتًا ولا اتصال شبكة لتثبيته. **شغّل `pytest -q` فعليًا في بيئتك**
(المذكورة في requirements.txt أصلًا) قبل افتراض أن كل شيء هنا يعمل بصيغته
النهائية كاختبار pytest — الصياغة (fixtures، tmp_path) قياسية ومطابقة
لاتفاقيات pytest، لكنها لم تُشغَّل بمشغّل pytest الفعلي هنا.
"""
import os
import sys
import importlib
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ============================================================
# المرحلة صفر
# ============================================================

def test_severance_pay_matches_article_84():
    from legal_tools import entitlement_calculator
    r = entitlement_calculator.severance_pay(basic_salary=10000, years_of_service=7)
    assert r["amount"] == (10000 / 2) * 5 + 10000 * 2
    assert r["legal_basis"]["article"] == "84"


def test_arbitrary_dismissal_floor_matches_article_77_text_not_old_formula():
    """الإصلاح المحوري للمرحلة صفر: التحقق أن القديمة كانت تبالغ 2× بالضبط عند هذه القيم."""
    from legal_tools import entitlement_calculator
    r = entitlement_calculator.arbitrary_dismissal_floor(total_salary=10000, years_of_service=5)
    assert r["statutory_floor"] == 25000.0  # (10000/30) × 15 × 5 = نص المادة 77 حرفيًا
    old_buggy_formula_result = 10000 * min(12, max(3, int(5)))
    assert old_buggy_formula_result == 50000.0  # كانت تُعرض خطأً تحت مسمى "المادة 77"
    assert old_buggy_formula_result == r["statutory_floor"] * 2


def test_wage_delay_has_no_invented_percentage():
    """المادة 90 لا تنص على نسبة تعويض؛ يجب ألا يظهر أي رقم مالي هنا."""
    from legal_tools import entitlement_calculator
    r = entitlement_calculator.wage_delay_rights(10)
    assert "right_to_refuse_work" in r
    assert "amount" not in r and "compensation" not in r


def test_overtime_pay_is_150_percent():
    from legal_tools import entitlement_calculator
    r = entitlement_calculator.overtime_pay(hourly_rate=50, overtime_hours=10)
    assert r["amount"] == 50 * 10 * 1.5


def test_escalation_uses_real_policies_triggers():
    from legal_tools import check_escalation
    r = check_escalation("فصل تعسفي أمام المحكمة العمالية", claim_amount=100000)
    assert r["should_escalate"] is True
    assert r["matched_triggers"]


def test_is_in_scope_detects_real_text_not_only_literal_category_name():
    """الإصلاح: كانت تطابق 'الأحوال الشخصية' حرفيًا فقط ولا تكتشف نصًا فعليًا عن طلاق أو نفقة."""
    from policies import policies
    assert policies.is_in_scope("أريد نفقة لأولادي بعد الطلاق من زوجتي") is False
    assert policies.is_in_scope("فصلت تعسفيًا وأريد مستحقاتي وفق المادة 77") is True


def test_legal_review_package_wires_policies_and_escalation():
    from legal_intelligence import legal_review_package
    review = legal_review_package("تم فصلي تعسفيًا وفق المادة 77 والمادة 84", claim_amount=90000)
    assert review["escalation"]["should_escalate"] is True
    assert review["disclaimer"]
    assert len(review["sources"]) > 0


# ============================================================
# المرحلة 1
# ============================================================

def test_arabic_ordinal_parser_handles_above_100():
    """الإصلاح: الصيغة القديمة كانت تتوقف عند 100 وتفقد كل ما بعدها بصمت."""
    from law_corpus_tools import parse_arabic_ordinal
    cases = {
        "الأولى": 1, "العاشرة": 10, "الحادية عشرة": 11,
        "العشرون": 20, "الخامسة والستون": 65,
        "المائة": 100, "الخامسة والستون بعد المائة": 165,
        "الأولى بعد المائتين": 201,
    }
    for phrase, expected in cases.items():
        assert parse_arabic_ordinal(phrase) == expected, phrase


def test_search_returns_relevant_results_and_rejects_offtopic():
    from legal_tools import legal_search
    results = legal_search.search("مكافأة نهاية الخدمة", max_results=3)
    assert len(results) > 0
    assert results[0]["score"] > 0.1
    assert legal_search.search("طريقة عمل الكيك") == []  # عتبة الصلة الدنيا تمنع ضجيج النتائج الضعيفة


def test_search_results_are_deduplicated_across_sources():
    from legal_tools import legal_search
    results = legal_search.search("الفصل التعسفي", max_results=10)
    titles = [r["title"] for r in results]
    assert len(titles) == len(set(titles)), "المصدران المنسّق والمستخرج يتداخلان؛ يجب ألا تظهر نفس المادة مرتين"


# ============================================================
# المرحلة 2
# ============================================================

def test_info_extractor_no_duplicate_overlapping_matches():
    """الإصلاح: كانت تُنتج '18,500' و'18,500 ريال' كمبلغين منفصلين لنفس القيمة."""
    from legal_tools import info_extractor
    d = info_extractor.extract_all("بتاريخ 2026-02-15 ومبلغ 18,500 ريال وفق المادة 77")
    assert d["dates"] == ["2026-02-15"]
    assert d["amounts"] == ["18,500 ريال"]
    assert d["articles"] == ["المادة 77"]


def test_cross_reference_detects_info_not_captured_manually():
    """اختبار طرف-إلى-طرف بقاعدة بيانات SQLite حقيقية معزولة في مجلد مؤقت."""
    tmp_dir = tempfile.mkdtemp(prefix="fuhrer_pytest_")
    os.environ["FUHRER_DATA_DIR"] = tmp_dir
    for mod in ("workspace_store", "matter_intelligence"):
        sys.modules.pop(mod, None)
    import workspace_store as ws
    import matter_intelligence as mi

    ws.init_db()
    matter = ws.create_matter({"title": "اختبار", "matter_type": "عمالي", "status": "مفتوحة", "priority": "عالية"})
    mid = matter["id"]
    ws.add_fact(mid, {"title": "الفصل", "description": "", "event_date": "2026-02-15", "certainty": "مثبت بمستند"})
    ws.add_claim(mid, {"title": "نهاية الخدمة", "legal_basis": "المادة 84", "notes": ""})
    ws.add_document(mid, "خطاب.pdf", "pdf", "بتاريخ 2026-02-15 ومبلغ تسوية 18,500 ريال وفق المادة 77", source_hash="a" * 64)

    full = ws.get_matter(mid)
    texts = ws.get_document_texts(mid)
    result = mi.analyze_matter_deep(full, texts)
    findings = result["document_cross_reference"]["findings"]

    assert any("18,500" in v for f in findings for v in f["values"]), "يجب اكتشاف مبلغ التسوية غير المسجَّل"
    assert not any(f["type"].startswith("تاريخ") for f in findings), "التاريخ مُدخل يدويًا فعلًا؛ لا يجب تكراره كـ'جديد'"


def test_analyze_matter_deep_is_backward_compatible_without_document_texts():
    from matter_intelligence import analyze_matter, analyze_matter_deep
    matter = {"id": "x", "title": "", "description": "", "facts": [], "claims": [], "documents": [], "deadlines": [], "claim_evidence": []}
    assert "document_cross_reference" not in analyze_matter(matter)
    assert analyze_matter_deep(matter) == analyze_matter(matter)


if __name__ == "__main__":
    # تشغيل مباشر بلا pytest (للتأكد من المنطق في بيئة بلا pytest مثبَّت فقط؛
    # لا يغني عن تشغيل pytest الفعلي في بيئتك كما هو موضح أعلى الملف).
    tests = [v for k, v in list(globals().items()) if k.startswith("test_")]
    passed = 0
    for t in tests:
        try:
            t()
            print(f"✅ {t.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"❌ {t.__name__}: {e}")
    print(f"\n{passed}/{len(tests)} نجحت")
