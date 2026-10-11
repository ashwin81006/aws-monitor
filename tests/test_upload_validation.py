import io
import pandas as pd
from fastapi.testclient import TestClient

from src.api.app import app

client = TestClient(app)


def test_upload_rejects_missing_timestamps():
    """
    Verifies that uploading a CSV with no timestamp columns is explicitly rejected with 400.
    """
    csv_data = "temp_2m,rh_2m,pressure,battery_voltage\n28.5,65.0,1005.0,13.2\n"
    files = {"file": ("no_time.csv", io.BytesIO(csv_data.encode("utf-8")), "text/csv")}
    response = client.post("/api/v1/telemetry/upload", files=files)
    assert response.status_code == 400
    assert "timestamp" in response.json()["detail"].lower()


def test_upload_rejects_missing_mandatory_channels():
    """
    Verifies that uploading a CSV missing mandatory channels (e.g. pressure or battery) is rejected.
    """
    csv_data = "timestamp,temp_2m\n2024-06-01 10:00:00,28.5\n2024-06-01 10:30:00,29.0\n"
    files = {"file": ("missing_channels.csv", io.BytesIO(csv_data.encode("utf-8")), "text/csv")}
    response = client.post("/api/v1/telemetry/upload", files=files)
    assert response.status_code == 400
    assert "missing mandatory meteorological channels" in response.json()["detail"].lower()


def test_upload_rejects_non_csv():
    """
    Verifies that uploading non-CSV files is rejected with 400.
    """
    files = {"file": ("malicious.exe", io.BytesIO(b"binary"), "application/octet-stream")}
    response = client.post("/api/v1/telemetry/upload", files=files)
    assert response.status_code == 400
    assert "only csv files are supported" in response.json()["detail"].lower()
