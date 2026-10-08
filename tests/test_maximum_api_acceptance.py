import hashlib
import io
import zipfile


def test_maximum_api_acceptance(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_ACCESS_TOKEN", "acceptance-token")
    monkeypatch.setenv("FUHRER_DATA_DIR", str(tmp_path))
    import importlib
    import workspace_store
    workspace_store.DATA_DIR = str(tmp_path)
    workspace_store.BLOB_DIR = str(tmp_path / "document_blobs")
    workspace_store.DB_PATH = str(tmp_path / "workspace.sqlite3")
    workspace_store.init_db()
    import server
    importlib.reload(server)
    from fastapi.testclient import TestClient
    client = TestClient(server.app)
    headers = {"X-App-Token": "acceptance-token"}
    created = client.post("/api/matters", json={"title": "نزاع أجر وإنهاء", "matter_type": "نزاع عمالي"}, headers=headers)
    assert created.status_code == 200
    matter_id = created.json()["matter"]["id"]
    roles = client.get("/api/roles", headers=headers)
    assert roles.status_code == 200
    assert [x["key"] for x in roles.json()["roles"]] == ["محامي", "مستشار قانوني", "مستشار عمالي"]
    advanced = client.get(f"/api/matters/{matter_id}/advanced-review", headers=headers, params={"role": "مستشار عمالي"})
    theory = client.get(f"/api/matters/{matter_id}/case-theory", headers=headers, params={"role": "محامي"})
    assert theory.status_code == 200
    assert theory.json()["theory"]["engine_version"] == "1.0"
    assert theory.json()["theory"]["administration_challenge_plan"]
    assert advanced.status_code == 200
    assert advanced.json()["review"]["engine_version"] == "2.0"
    assert advanced.json()["review"]["role"]["label"] == "المستشار العمالي"
    raw = "راتب متأخر وخصم من الراتب والعمل ساعات إضافية بعد الدوام 2025-05-31 12000 SAR".encode()
    uploaded = client.post("/api/upload", headers=headers, data={"matter_id": matter_id}, files={"files": ("salary.txt", io.BytesIO(raw), "text/plain")})
    assert uploaded.status_code == 200
    doc = uploaded.json()["saved_documents"][0]
    assert doc["source_hash"] == hashlib.sha256(raw).hexdigest()
    assert uploaded.json()["saved_inspections"][0]["inspection_status"] == "مقروء"
    assert uploaded.json()["rights_discovery"]["undisclosed_count"] >= 2
    inspections = client.get(f"/api/matters/{matter_id}/document-inspections", headers=headers)
    assert inspections.status_code == 200
    assert inspections.json()["coverage"]["documents_read"] == 1
    rights = client.get(f"/api/matters/{matter_id}/discovered-rights", headers=headers)
    assert rights.status_code == 200
    assert any(x["right_key"] == "overtime" for x in rights.json()["rights"])
    integrity = client.get(f"/api/documents/{doc['id']}/integrity", headers=headers, params={"matter_id": matter_id})
    assert integrity.status_code == 200 and integrity.json()["integrity"]["verified"] is True
    intelligence = client.get(f"/api/matters/{matter_id}/intelligence", headers=headers)
    assert intelligence.status_code == 200
    assert intelligence.json()["analysis"]["readiness"]["not_a_legal_opinion"] is True
    requirements = client.get("/api/procedure/amicable_settlement/requirements", headers=headers)
    assert requirements.status_code == 200
    assert "21 يوم عمل" in requirements.json()["requirements"]["time_limit"]
    backup = client.get("/api/backup", headers=headers)
    assert backup.status_code == 200
    with zipfile.ZipFile(io.BytesIO(backup.content)) as archive:
        assert "workspace.sqlite3" in archive.namelist()
        assert "BACKUP_MANIFEST.json" in archive.namelist()
