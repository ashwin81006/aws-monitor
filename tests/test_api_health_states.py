from fastapi.testclient import TestClient

from src.api.app import app

client = TestClient(app)


def test_health_reports_mode_accurately():
    """
    Verifies that /health accurately reflects the actual model state and mode.
    """
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert "status" in data
    assert "mode" in data
    assert "active_model" in data
    assert "features_count" in data
    assert data["features_count"] == 13
    assert data["status"] == "ONLINE"
    assert data["mode"] == "PRODUCTION"


def test_benchmark_reports_availability():
    """
    Verifies that /api/v1/models/benchmark reports whether artifacts are available.
    """
    res = client.get("/api/v1/models/benchmark")
    assert res.status_code == 200
    data = res.json()
    assert "status" in data
    assert data["status"] in ["AVAILABLE", "UNAVAILABLE"]
