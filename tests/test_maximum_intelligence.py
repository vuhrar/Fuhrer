import hashlib

import matter_intelligence
import workspace_store


def test_maximum_intelligence_links_evidence_and_integrity(tmp_path, monkeypatch):
    monkeypatch.setenv("FUHRER_DATA_DIR", str(tmp_path))
    workspace_store.DATA_DIR = str(tmp_path)
    workspace_store.BLOB_DIR = str(tmp_path / "document_blobs")
    workspace_store.DB_PATH = str(tmp_path / "workspace.sqlite3")
    workspace_store.init_db()
    matter = workspace_store.create_matter({"title": "نزاع أجر وإنهاء خدمة", "matter_type": "نزاع عمالي", "description": "طلب التسوية الودية بسبب راتب متأخر وإنهاء وإشعار"})
    workspace_store.add_fact(matter["id"], {"title": "عدم سداد الراتب", "description": "راتب مايو لم يدفع", "certainty": "غير متحقق"})
    workspace_store.add_claim(matter["id"], {"title": "المطالبة بالأجر المتبقي"})
    raw = b"bank statement"
    workspace_store.add_document(matter["id"], "bank.txt", "مرفوع", "راتب مايو", hashlib.sha256(raw).hexdigest(), raw_bytes=raw, metadata={"dates": ["2025-05-31"], "amounts_or_pay_terms": ["12,000 ريال"]})
    loaded = workspace_store.get_matter(matter["id"])
    workspace_store.link_claim_evidence(matter["id"], {"claim_id": loaded["claims"][0]["id"], "document_id": loaded["documents"][0]["id"], "note": "يثبت التحويل"})
    analysis = matter_intelligence.analyze_matter(workspace_store.get_matter(matter["id"]))
    assert analysis["context"] == "نزاع عمالي"
    assert analysis["coverage"]["evidence_links"] == 1
    assert analysis["evidence_integrity"][0]["status"] == "سليم"
    assert analysis["readiness"]["score"] < 100
