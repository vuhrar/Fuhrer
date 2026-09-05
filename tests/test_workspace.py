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
    doc = workspace_store.add_document(matter["id"], "contract.txt", "عقد", "نص العقد", "hash")
    assert doc["filename"] == "contract.txt"
    loaded = workspace_store.get_matter(matter["id"])
    assert len(loaded["documents"]) == 1
    assert any(event["action"] == "task_created" for event in loaded["audit"])
    assert workspace_store.dashboard()["counts"]["open_matters"] == 1
