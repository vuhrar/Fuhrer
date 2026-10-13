# tests/test_phase_3.py
"""اختبارات محركات المرحلة 3: المواعيد والتقادم، مشروعية الإنهاء، وورقة العمل الشاملة."""
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_prescription_one_year_for_contract_claims():
    from legal_tools import deadline_engine
    ref = (datetime.now() - timedelta(days=335)).strftime("%Y-%m-%d")
    r = deadline_engine.prescription_deadline(ref, "عقد")
    assert 25 <= r["days_remaining"] <= 35
    assert r["legal_basis"]["article"] == "222"


def test_prescription_expired_is_flagged_not_hidden():
    from legal_tools import deadline_engine
    ref = (datetime.now() - timedelta(days=800)).strftime("%Y-%m-%d")
    r = deadline_engine.prescription_deadline(ref, "عقد")
    assert r["days_remaining"] < 0
    assert "منقضٍ" in r["status"]


def test_prescription_three_years_for_injury_claims():
    """الفرق الجوهري في المادة 222: دعاوى الإصابة تتقادم بثلاث سنوات لا سنة واحدة."""
    from legal_tools import deadline_engine
    ref = (datetime.now() - timedelta(days=800)).strftime("%Y-%m-%d")
    contract = deadline_engine.prescription_deadline(ref, "عقد")
    injury = deadline_engine.prescription_deadline(ref, "إصابة عمل")
    assert contract["days_remaining"] < 0
    assert injury["days_remaining"] > 0


def test_prescription_handles_leap_year_edge_case():
    from legal_tools import deadline_engine
    r = deadline_engine.prescription_deadline("2024-02-29", "عقد")
    assert r["deadline"] == "2025-02-28"


def test_termination_no_notice_no_valid_ground_flags_arbitrary_dismissal():
    from legal_tools import termination_assessment
    r = termination_assessment.assess(initiated_by="صاحب العمل", notice_given_days=0)
    assert any(f["legal_basis"]["article"] == "77" for f in r["findings"])


def test_termination_with_valid_article_81_ground():
    from legal_tools import termination_assessment
    r = termination_assessment.assess(initiated_by="صاحب العمل", notice_given_days=0, employer_claimed_ground="unauthorized_absence")
    assert r["findings"][0]["legal_basis"]["article"] == "81"
    assert "evidence_needed" in r["findings"][0]


def test_termination_invalid_claimed_ground_still_flags_arbitrary():
    """السبب الحصري غير المدرج في المادة 81 لا يُعفي من مؤشر الفصل التعسفي."""
    from legal_tools import termination_assessment
    r = termination_assessment.assess(initiated_by="صاحب العمل", notice_given_days=0, employer_claimed_ground="سبب_مختلق")
    assert "77" in str(r)


def test_worker_leaving_for_employer_breach_cites_article_80():
    from legal_tools import termination_assessment
    r = termination_assessment.assess(initiated_by="العامل", notice_given_days=0, worker_claimed_ground="employer_breach")
    assert r["findings"][0]["legal_basis"]["article"] == "80"


def test_entitlements_worksheet_arbitrary_dismissal_floor_counted_in_total():
    """
    إصلاح محوري اكتُشف بالاختبار الفعلي أثناء بناء هذه المرحلة: كانت
    arbitrary_dismissal_floor تُعيد 'statutory_floor' فقط لا 'amount'،
    فكان منطق التجميع العام (الذي يبحث عن 'amount' كبقية الدوال) يستبعد
    هذا الرقم صامتًا من الإجمالي الموثوق ويضعه خطأً في "يحتاج معلومة إضافية".
    """
    from legal_tools import full_entitlements_worksheet
    ws = full_entitlements_worksheet(
        basic_salary=8000, total_salary=10000,
        start_date="2020-01-01", end_date="2026-01-01",
        termination_type="فصل تعسفي", notice_given_days=0, monthly_paid=True,
    )
    items_by_name = {i["item"]: i for i in ws["items"]}
    arb_item = items_by_name["الحد الأدنى لتعويض الفصل التعسفي"]
    assert arb_item["amount"] is not None and arb_item["amount"] > 0
    assert "الحد الأدنى لتعويض الفصل التعسفي" not in ws["items_needing_further_info"]
    assert arb_item["amount"] <= ws["confident_total_sar"]  # لا بد أن يكون محتسبًا ضمن المجموع فعليًا


def test_entitlements_worksheet_total_equals_sum_of_confident_items():
    from legal_tools import full_entitlements_worksheet
    ws = full_entitlements_worksheet(
        basic_salary=8000, total_salary=10000,
        start_date="2020-01-01", end_date="2026-01-01",
        termination_type="فصل تعسفي", notice_given_days=0, monthly_paid=True,
        unused_leave_days=15, overtime_hours=20, overtime_hourly_rate=40,
    )
    expected = sum(i["amount"] for i in ws["items"] if isinstance(i.get("amount"), (int, float)))
    assert ws["confident_total_sar"] == round(expected, 2)


def test_entitlements_worksheet_does_not_invent_notice_shortfall_amount():
    """لا نص صريح لصيغة تعويض نقص الإشعار؛ يجب أن يبقى amount=None لا رقمًا مُخترعًا."""
    from legal_tools import full_entitlements_worksheet
    ws = full_entitlements_worksheet(
        basic_salary=8000, total_salary=10000,
        start_date="2020-01-01", end_date="2026-01-01",
        termination_type="فصل بسبب (م81)", notice_given_days=5, monthly_paid=True,
    )
    notice_items = [i for i in ws["items"] if "الإشعار" in i["item"]]
    assert notice_items and notice_items[0]["amount"] is None


def test_search_corpus_curated_tier_is_exactly_25_articles_no_duplication():
    """
    إصلاح محوري آخر من هذه الجلسة: get_all_articles() القديمة كانت تُستخدم
    في بناء فهرس البحث وتُصنَّف بالكامل 'curated'، رغم أنها تضم فعليًا
    المواد المستخرجة آليًا المدموجة من legal_database.__init__ أيضًا —
    فكانت كل مادة مستخرجة تظهر مرتين (مرة 'curated' خطأً، ومرة 'extracted').
    """
    from semantic_search import build_corpus
    from legal_database import get_legal_database
    corpus = build_corpus()
    curated = [d for d in corpus if d["trust_tier"] == "curated"]
    if getattr(get_legal_database(), "_source_mode", "") == "official_snapshot":
        assert len(corpus) == 245
        assert all(d["trust_tier"] == "official_snapshot" for d in corpus)
    else:
        assert len(curated) == 25


if __name__ == "__main__":
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
