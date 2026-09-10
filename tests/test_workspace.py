import os


def test_workspace_lifecycle(tmp_path, monkeypatch):
    monkeypatch.setenv("FUHRER_DATA_DIR", str(tmp_path))
    import importlib
    import workspace_store
    workspace_store.DATA_DIR = str(tmp_path)
    workspace_store.DB_PATH = os.path.join(str(tmp_path), "workspace.sqlite3")
    workspace_store.init_db()
    matter = workspace_store.create_matter({"title": "مراجعة عقد خدمات", "matter_type": "عقد", "client_name": "عميل اختباري"})
    assert matter["title"] == "مراجعة عقد خدمات"
    matter = workspace_store.create_task(matter["id"], {"title": "التحقق من بند الإنهاء", "due_date": "2026-09-10"})
    assert len(matter["tasks"]) == 1
    matter = workspace_store.add_party(matter["id"], {"name": "صاحب العمل", "role": "مدعى عليه"})
    matter = workspace_store.add_fact(matter["id"], {"title": "إيقاف الراتب", "event_date": "2026-01-15", "certainty": "مثبت بمستند"})
    matter = workspace_store.add_claim(matter["id"], {"title": "المطالبة بالأجور المتأخرة", "legal_basis": "يحتاج تحققًا من النص النافذ"})
    matter = workspace_store.add_deadline(matter["id"], {"title": "مراجعة موعد الإجراء", "due_date": "2026-09-10", "source": "إشعار"})
    doc = workspace_store.add_document(matter["id"], "contract.txt", "عقد", "نص العقد", "hash")
    assert doc["filename"] == "contract.txt"
    loaded = workspace_store.get_matter(matter["id"])
    assert len(loaded["documents"]) == 1
    assert len(loaded["parties"]) == 1
    assert len(loaded["facts"]) == 1
    assert len(loaded["claims"]) == 1
    assert len(loaded["deadlines"]) == 1
    claim_id = loaded["claims"][0]["id"]
    document_id = loaded["documents"][0]["id"]
    loaded = workspace_store.link_claim_evidence(matter["id"], {"claim_id": claim_id, "document_id": document_id, "note": "الخطاب يؤيد الطلب"})
    assert len(loaded["claim_evidence"]) == 1
    assert loaded["claim_evidence"][0]["claim_id"] == claim_id
    assert any(event["action"] == "claim_evidence_linked" for event in loaded["audit"])
    assert any(event["action"] == "task_created" for event in loaded["audit"])
    assert workspace_store.dashboard()["counts"]["open_matters"] == 1
