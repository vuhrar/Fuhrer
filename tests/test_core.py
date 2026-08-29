import io

from file_processing import extract_text_from_file, truncate_for_ai
from legal_tools_advanced import entitlements_calculator, legal_classifier


class NamedBytes(io.BytesIO):
    def __init__(self, content: bytes, name: str):
        super().__init__(content)
        self.name = name


def test_truncate_preserves_both_ends():
    value = "A" * 100 + "B" * 100
    result = truncate_for_ai(value, 100)
    assert result.startswith("A")
    assert result.endswith("B")
    assert "تم حذف" in result


def test_text_extraction_utf8():
    result = extract_text_from_file(NamedBytes("نص قانوني".encode(), "note.txt"))
    assert result["success"] is True
    assert result["text"] == "نص قانوني"
    assert result["pages"] == 1


def test_classifier_returns_general_for_empty_text():
    category, confidence, keywords = legal_classifier.classify("")
    assert category == "عام"
    assert confidence == 0.0
    assert keywords == []


def test_eosb_result_has_explainable_components():
    result = entitlements_calculator.calculate_eosb(
        basic_salary=10000,
        total_salary=15000,
        years_of_service=5,
        is_arbitrary=False,
    )
    assert result["totals"]["eosb_total"] == 25000
    assert result["totals"]["grand_total"] == 25000
    assert set(result["details"]) == {"eosb", "arbitrary", "delay"}
