from legal_intelligence import scan_risks


def test_labor_context_uses_labor_risk_rules():
    risks = scan_risks("نزاع عمالي حول راتب وإنهاء خدمة والتسوية الودية")
    areas = [item["area"] for item in risks]
    assert "الأجر والاستحقاقات" in areas
    assert "الإنهاء والإشعار" in areas
    assert "نطاق العمل" not in areas
    assert "الملكية الفكرية" not in areas
