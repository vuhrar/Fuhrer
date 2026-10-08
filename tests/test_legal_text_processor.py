from legal_text_processor import analyze_legal_text, classify_polarity
from evidence_fusion import fuse_text_with_evidence

CONCEPTS = {"overtime": ["ساعات إضافية", "بعد الدوام"], "unpaid_wages": ["راتب متأخر", "عدم سداد الراتب"]}


def test_complex_arabic_negation_identifies_employer_position():
    text = "تدعي الإدارة أن العامل لم يعمل ساعات إضافية. ويذكر العامل أنه عمل بعد الدوام حتى الساعة 22:00."
    statements = analyze_legal_text(text, CONCEPTS, document_id="doc_1", page=3)
    employer = next(x for x in statements if x["speaker"] == "الإدارة")
    worker = next(x for x in statements if x["speaker"] == "العامل")
    assert employer["status"] == "negated_by_employer"
    assert employer["polarity"] == "منفي"
    assert employer["negation_cue"] in {"لم", "لم يثبت"}
    assert worker["status"] == "positive_signal"
    assert worker["page"] == 3


def test_payment_and_unproven_are_not_positive_right_evidence():
    assert classify_polarity("تم دفع الراتب المتأخر بالكامل", ["راتب متأخر"])["status"] == "paid_claimed"
    assert classify_polarity("لم يثبت عدم سداد الراتب", ["عدم سداد الراتب"])["status"] == "unproven"


def test_fuse_text_with_evidence_preserves_statements_and_conflict():
    result = fuse_text_with_evidence(
        "تدعي الإدارة أن العامل لم يعمل ساعات إضافية. ويذكر العامل أنه عمل بعد الدوام.",
        CONCEPTS,
        semantic_matches=[{"right_key": "overtime", "semantic_score": 0.74, "text": "عمل خارج الوقت"}],
        table_entities=[{"right_key": "overtime", "confidence": 0.86, "reason": "وقت الانصراف 22:00", "document_id": "doc_1", "page": 4}],
        document_id="doc_1",
        page=2,
    )
    finding = next(x for x in result["findings"] if x["right_key"] == "overtime")
    assert len(result["statements"]) == 2
    assert finding["contradiction"] is True
    assert finding["status"] == "محل نزاع ويحتاج تحققًا"
    assert finding["human_review_required"] is True
