from evidence_fusion import fuse_semantic_table_evidence


def test_fusion_marks_hidden_right_and_explains_conflict():
    results = fuse_semantic_table_evidence(
        semantic_matches=[{"right_key": "overtime", "semantic_score": 0.78, "text": "عمل بعد الدوام", "document_id": "doc_1", "page": 2}],
        table_entities=[{"right_key": "overtime", "entity_type": "attendance_record", "confidence": 0.88, "reason": "وقت الانصراف 22:00 مقابل نهاية الدوام 16:00", "document_id": "doc_1", "page": 4, "source_excerpt": "22:00 | 16:00"}],
        contextual_statements=[{"right_key": "overtime", "status": "positive_signal", "speaker": "العامل", "text": "عملت بعد الدوام"}, {"right_key": "overtime", "status": "negated_by_employer", "speaker": "الإدارة", "text": "تدعي الإدارة عدم وجود ساعات إضافية"}],
        right_catalog={"overtime": {"label": "عمل إضافي محتمل", "elements": ["الساعات الفعلية", "السداد"], "evidence": ["سجل الحضور"]}},
    )
    result = results[0]
    assert result["right_key"] == "overtime"
    assert result["status"] == "محل نزاع ويحتاج تحققًا"
    assert result["contradiction"] is True
    assert result["table_score"] == 0.88
    assert result["source_trace"][0]["document_id"] == "doc_1"
    assert result["final_confidence"] > 0.5
    assert result["human_review_required"] is True


def test_fusion_marks_unmentioned_claim_when_supported_by_semantics_only():
    results = fuse_semantic_table_evidence(
        semantic_matches=[{"right_key": "deductions", "semantic_score": 0.72, "excerpt": "خصم من الراتب", "document_id": "doc_2", "page": 1}],
        claim_keys=[],
    )
    assert results[0]["status"] == "مؤشر حق غير مذكور"
    assert results[0]["final_confidence"] >= 0.2
