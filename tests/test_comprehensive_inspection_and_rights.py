import io

from document_inspection_engine import inspect_batch, inspect_file
from hidden_rights_engine import discover


def test_inspection_reports_full_coverage_and_unreadable_files():
    readable = io.BytesIO("راتب متأخر 12000 ريال بتاريخ 2025-05-31".encode())
    readable.name = "evidence.txt"
    unreadable = io.BytesIO(b"%PDF-1.4 broken")
    unreadable.name = "broken.pdf"
    batch = inspect_batch([readable, unreadable])
    assert batch["documents_total"] == 2
    assert batch["documents_read"] == 1
    assert batch["documents_unreadable"] == 1
    assert batch["manual_review_required"] is True
    assert batch["results"][0]["signals"]["dates"]


def test_hidden_rights_discovers_unmentioned_overtime_and_deductions():
    matter = {
        "title": "نزاع عمالي", "description": "تم خصم من الراتب والعمل ساعات إضافية بعد الدوام",
        "claims": [],
        "facts": [],
        "documents": [{"id": "d1", "filename": "رسائل.txt", "extracted_text": "عمل إضافي بعد الدوام وخصم من الراتب"}],
    }
    result = discover(matter)
    keys = {item["right_key"] for item in result["findings"]}
    assert "overtime" in keys
    assert "deductions" in keys
    assert result["undisclosed_count"] >= 2
    overtime = next(x for x in result["findings"] if x["right_key"] == "overtime")
    assert overtime["triggers"][0]["document_id"] == "d1"
    assert overtime["human_review_required"] is True
