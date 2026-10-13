# tests/test_phase_5.py
"""اختبارات صياغة طلب التسوية الودية (منصة تراضي) وفحص عروض التسوية — المرحلة 5."""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s)


def test_full_draft_contains_rights_reservation_paragraph():
    from amicable_settlement import AmicableSettlementRequestDrafter
    result = AmicableSettlementRequestDrafter().draft(
        plaintiff_name="أحمد", plaintiff_id="1", defendant_name="شركة", workplace_location="الرياض",
        job_title="محاسب", start_date="2020-01-01",
        facts=[{"date": "2026-02-15", "text": "فصل دون إشعار."}],
        claims=[{"title": "مكافأة نهاية الخدمة", "legal_basis": "المادة 84", "amount": 45000.0}],
        evidence=["عقد العمل"],
    )
    doc = _norm(result["document_text"])
    assert "ولا يُعدّ تقديم هذا الطلب أو المشاركة في جلسات التسوية الودية تنازلاً" in doc
    assert "لا ينتج أي أثر ملزم على أي من الطرفين إلا باتفاق تسوية نهائي مكتوب وموقّع" in doc
    assert result["missing_required_fields"] == []  # كل الحقول السبعة مزوَّدة هنا تحديدًا


def test_claims_carry_legal_basis_and_amount():
    from amicable_settlement import AmicableSettlementRequestDrafter
    result = AmicableSettlementRequestDrafter().draft(claims=[{"title": "تعويض الفصل التعسفي", "legal_basis": "المادة 77", "amount": 25000.0}])
    doc = _norm(result["document_text"])
    assert "تعويض الفصل التعسفي (الأساس: المادة 77) — المبلغ المُقدَّر: 25,000.00 ريال" in doc


def test_facts_sorted_chronologically_dated_before_undated():
    from amicable_settlement import AmicableSettlementRequestDrafter
    result = AmicableSettlementRequestDrafter().draft(facts=[
        {"date": None, "text": "واقعة بلا تاريخ"},
        {"date": "2026-01-01", "text": "واقعة أولى"},
        {"date": "2026-02-01", "text": "واقعة ثانية"},
    ])
    doc = result["document_text"]
    assert doc.index("واقعة أولى") < doc.index("واقعة ثانية") < doc.index("واقعة بلا تاريخ")
    assert result["undated_facts_count"] == 1


def test_missing_required_fields_detected_accurately():
    from amicable_settlement import AmicableSettlementRequestDrafter
    result = AmicableSettlementRequestDrafter().draft()  # كل شيء فارغ
    assert set(result["missing_required_fields"]) == {"بيانات المدعي", "مكتب التسوية والاختصاص المكاني", "بيانات المدعى عليه", "بيانات العمل", "المستندات"}


def test_offer_reviewer_flags_broad_release_and_vague_amount_and_vague_date():
    from amicable_settlement import SettlementOfferReviewer
    offer = "يوافق الطرفان على إبراء عام مطلق وتنازل عن كافة الحقوق الحالية والمستقبلية، ويُصرف للعامل مبلغ مناسب في أقرب وقت."
    review = SettlementOfferReviewer().review(offer)
    keys = {f["key"] for f in review["red_flags"]}
    assert keys == {"broad_general_release", "no_specific_amount", "no_payment_deadline"}
    for f in review["red_flags"]:
        assert f["quoted_text"] in offer  # اقتباس حرفي فعلي لا مُختلَق


def test_offer_reviewer_clean_on_well_drafted_offer():
    from amicable_settlement import SettlementOfferReviewer
    offer = "أولاً: يُصرف للعامل مبلغ 35,000 ريال بتاريخ 2026-03-01. ثانياً: يقتصر هذا الإبراء على مطالبات نهاية الخدمة المذكورة في هذا الاتفاق فقط."
    review = SettlementOfferReviewer().review(offer)
    assert review["red_flags"] == []
    present = {g["key"]: g["present"] for g in review["good_practices"]}
    assert all(present.values())


def test_pre_signature_checklist_has_core_items():
    from amicable_settlement import pre_signature_checklist
    checklist = pre_signature_checklist()
    assert len(checklist) >= 5
    assert any("استلام" in item for item in checklist)


def test_entitlements_worksheet_bridges_directly_into_settlement_claims():
    """تكامل كامل بين المرحلتين 3 و5: نفس الأرقام المحسوبة تنتقل حرفيًا لمسودة طلب التسوية دون تنسيق يدوي."""
    from legal_tools import full_entitlements_worksheet
    from amicable_settlement import entitlements_worksheet_to_claims, AmicableSettlementRequestDrafter

    ws = full_entitlements_worksheet(basic_salary=8000, total_salary=10000, start_date="2020-01-01", end_date="2026-01-01", termination_type="فصل تعسفي", notice_given_days=0, monthly_paid=True)
    claims = entitlements_worksheet_to_claims(ws)
    result = AmicableSettlementRequestDrafter().draft(claims=claims)
    doc = _norm(result["document_text"])

    arb_item = next(i for i in ws["items"] if i["item"] == "الحد الأدنى لتعويض الفصل التعسفي")
    assert f"{arb_item['amount']:,.2f} ريال" in doc
    assert "المادة 77" in doc

    notice_claim = next(c for c in claims if c["amount"] is None)
    assert notice_claim["amount"] is None  # لا رقم مُختلَق لبند بلا صيغة نظامية صريحة


def test_end_to_end_draft_from_real_matter_via_database():
    import tempfile
    tmp_dir = tempfile.mkdtemp(prefix="fuhrer_p5_pytest_")
    os.environ["FUHRER_DATA_DIR"] = tmp_dir
    for mod in ("workspace_store", "matter_intelligence"):
        sys.modules.pop(mod, None)
    import workspace_store as ws
    import matter_intelligence as mi

    ws.init_db()
    matter = ws.create_matter({"title": "اختبار", "matter_type": "عمالي", "status": "مفتوحة", "priority": "عالية", "client_name": "سالم", "opposing_party": "شركة س", "jurisdiction": "جدة"})
    mid = matter["id"]
    ws.add_fact(mid, {"title": "الفصل", "event_date": "2026-02-15", "certainty": "مثبت بمستند"})
    ws.add_claim(mid, {"title": "مكافأة نهاية الخدمة", "legal_basis": "المادة 84"})

    result = mi.draft_amicable_settlement_for_matter(ws.get_matter(mid))
    assert "سالم" in result["document_text"] and "شركة س" in result["document_text"] and "جدة" in result["document_text"]
    assert "مكافأة نهاية الخدمة" in result["document_text"]


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
