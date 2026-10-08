import importlib


def test_repository_rights_api_persists_analysis_and_review(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_ACCESS_TOKEN", "repo-api-token")
    monkeypatch.setenv("FUHRER_DATA_DIR", str(tmp_path))
    monkeypatch.delenv("DATABASE_URL", raising=False)
    import workspace_store
    workspace_store.DATA_DIR = str(tmp_path)
    workspace_store.BLOB_DIR = str(tmp_path / "document_blobs")
    workspace_store.DB_PATH = str(tmp_path / "workspace.sqlite3")
    workspace_store.init_db()
    import server
    importlib.reload(server)
    from fastapi.testclient import TestClient
    client = TestClient(server.app)
    headers = {"X-App-Token": "repo-api-token"}
    matter = client.post("/api/matters", headers=headers, json={"title": "اختبار Repository"})
    assert matter.status_code == 200
    matter_id = matter.json()["matter"]["id"]

    response = client.post(
        f"/api/matters/{matter_id}/rights/analyze",
        headers=headers,
        json={
            "text": "تدعي الإدارة أن العامل لم يعمل ساعات إضافية. ويذكر العامل أنه عمل بعد الدوام.",
            "right_concepts": {"overtime": ["ساعات إضافية", "بعد الدوام"]},
            "semantic_matches": [{"right_key": "overtime", "semantic_score": 0.76, "text": "عمل خارج الوقت", "document_id": "doc_1", "page": 2}],
            "table_entities": [{"right_key": "overtime", "confidence": 0.88, "reason": "وقت الانصراف 22:00", "document_id": "doc_1", "page": 4}],
            "right_catalog": {"overtime": {"label": "عمل إضافي محتمل", "elements": ["الساعات الفعلية"], "evidence": ["سجل الحضور"]}},
            "document_id": "doc_1",
            "page": 2,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["persisted"]["statements"]
    assert body["persisted"]["findings"][0]["right_key"] == "overtime"

    rights = client.get(f"/api/matters/{matter_id}/repository-rights", headers=headers)
    assert rights.status_code == 200
    assert rights.json()["rights"][0]["right_key"] == "overtime"

    review = client.post(f"/api/matters/{matter_id}/right-review", headers=headers, json={"discovered_right_id": body["persisted"]["findings"][0]["id"], "decision": "يحتاج مستندًا إضافيًا", "note": "أرفق سجل الحضور"})
    assert review.status_code == 200
    statements = client.get(f"/api/matters/{matter_id}/legal-statements", headers=headers)
    assert statements.status_code == 200
    assert statements.json()["statements"][0]["status"] in {"negated_by_employer", "positive_signal"}
