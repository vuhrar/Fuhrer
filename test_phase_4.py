# tests/test_phase_4.py
"""اختبارات محرك تحليل المراسلات الإلكترونية (المرحلة 4)."""
import hashlib
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_favorable_pattern_detected_with_verbatim_quote():
    from correspondence_intelligence import analyze_correspondence
    r = analyze_correspondence([{"id": "m1", "date": "2026-01-10", "text": "نعتذر عن التأخير في صرف راتب شهر ديسمبر."}])
    assert len(r["favorable_to_user"]) == 1
    finding = r["favorable_to_user"][0]
    assert finding["quoted_text"] in "نعتذر عن التأخير في صرف راتب شهر ديسمبر."  # اقتباس حرفي فعلي من النص الأصلي
    assert len(finding["possible_interpretations"]) >= 2  # لا تفسير واحد جازم


def test_cautionary_pattern_detected_for_employee_waiver():
    from correspondence_intelligence import analyze_correspondence
    r = analyze_correspondence([{"id": "m1", "date": "2026-02-20", "text": "أقر باستلام كامل مستحقاتي ولا يوجد لدي أي مطالبة."}])
    assert len(r["cautionary_for_user"]) == 1


def test_neutral_text_produces_zero_findings():
    """لا نتائج كاذبة على نص إداري محايد تمامًا — اختبار أساسي ضد الإفراط في التحسس."""
    from correspondence_intelligence import analyze_correspondence
    r = analyze_correspondence([{"id": "m1", "date": "2026-01-20", "text": "تذكير بموعد اجتماع فريق المبيعات يوم الأحد القادم."}])
    assert r["favorable_to_user"] == [] and r["cautionary_for_user"] == []


def test_undated_item_excluded_from_timeline_and_flagged():
    from correspondence_intelligence import analyze_correspondence
    r = analyze_correspondence([
        {"id": "dated", "date": "2026-01-10", "text": "نص عادي."},
        {"id": "undated", "date": None, "text": "نص آخر بلا تاريخ."},
    ])
    assert len(r["timeline"]) == 1 and r["timeline"][0]["id"] == "dated"
    assert len(r["needs_more_info"]) == 1 and r["needs_more_info"][0]["item_id"] == "undated"


def test_timeline_sorted_chronologically_not_by_input_order():
    from correspondence_intelligence import analyze_correspondence
    r = analyze_correspondence([
        {"id": "late", "date": "2026-03-01", "text": "x"},
        {"id": "early", "date": "2026-01-01", "text": "y"},
        {"id": "mid", "date": "2026-02-01", "text": "z"},
    ])
    assert [t["id"] for t in r["timeline"]] == ["early", "mid", "late"]


def test_cross_reference_links_items_sharing_real_amount():
    from correspondence_intelligence import analyze_correspondence
    r = analyze_correspondence([
        {"id": "a", "date": "2026-01-10", "text": "تم الاتفاق على مبلغ 18,500 ريال."},
        {"id": "b", "date": "2026-01-15", "text": "نؤكد أن مبلغ 18,500 ريال سيُحوَّل غدًا."},
        {"id": "c", "date": "2026-01-20", "text": "موضوع مختلف تمامًا."},
    ])
    assert len(r["cross_references"]) == 1
    assert set(r["cross_references"][0]["item_ids"]) == {"a", "b"}


def test_sender_field_not_required_or_flagged():
    """تبسيط مقصود: المراسلات عبر منصة رسمية موثّقة الهوية؛ لا يُشترط حقل مرسل ولا يُفقد بسببه."""
    from correspondence_intelligence import analyze_correspondence
    r = analyze_correspondence([{"id": "m1", "date": "2026-01-10", "text": "نعتذر عن التأخير في صرف راتبك."}])
    assert r["needs_more_info"] == []  # لا نقص مُبلَّغ عنه رغم غياب أي حقل مرسل


def test_end_to_end_via_real_database_excludes_non_correspondence_documents():
    """اختبار طرف-إلى-طرف: يستبعد تحليل المراسلات أي مستند غير مصنَّف kind='مراسلة'."""
    tmp_dir = tempfile.mkdtemp(prefix="fuhrer_p4_pytest_")
    os.environ["FUHRER_DATA_DIR"] = tmp_dir
    for mod in ("workspace_store", "matter_intelligence"):
        sys.modules.pop(mod, None)
    import workspace_store as ws
    import matter_intelligence as mi

    ws.init_db()
    matter = ws.create_matter({"title": "اختبار", "matter_type": "عمالي", "status": "مفتوحة", "priority": "عالية"})
    mid = matter["id"]

    text = "نعتذر عن التأخير في صرف راتب شهر ديسمبر."
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    ws.add_document(matter_id=mid, filename="مراسلة.txt", kind="مراسلة", extracted_text=text, source_hash=digest, metadata={"date": "2026-01-10", "channel": "بريد رسمي"})
    ws.add_document(matter_id=mid, filename="عقد.pdf", kind="pdf", extracted_text="نص عقد لا علاقة له بالمراسلات", source_hash="y" * 64)

    full = ws.get_matter(mid)
    texts = ws.get_document_texts(mid)
    result = mi.analyze_correspondence_for_matter(full, texts)
    assert result["items_analyzed"] == 1  # المستند العادي مستبعد


def test_matter_with_no_correspondence_returns_clear_note_not_error():
    matter = {"id": "x", "documents": []}
    from matter_intelligence import analyze_correspondence_for_matter
    r = analyze_correspondence_for_matter(matter, {})
    assert r["items_analyzed"] == 0 and "note" in r


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
