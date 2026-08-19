from fastapi.testclient import TestClient

from backend.app import app

client = TestClient(app)


def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"
    assert res.json()["version"] == "2.0.0"


def test_index_status_idle():
    res = client.get("/api/index/status")
    assert res.status_code == 200
    assert res.json()["status"] in ("idle", "ready")
