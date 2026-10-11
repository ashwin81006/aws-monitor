import io
from fastapi.testclient import TestClient


from src.api.app import app

client = TestClient(app)


def test_health_check():
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in ["ONLINE", "HEALTHY", "DEGRADED"]
    assert "station_id" in data



def test_station_summary():
    res = client.get("/api/v1/station/summary")
    assert res.status_code == 200
    data = res.json()
    assert "station_name" in data
    assert data["total_observations"] > 0
    assert 0.0 <= data["overall_reliability_pct"] <= 100.0


def test_telemetry_history():
    res = client.get("/api/v1/telemetry/history?downsample_factor=10")
    assert res.status_code == 200
    data = res.json()
    assert "series" in data
    assert len(data["series"]) > 0


def test_streaming_point_inference():
    payload = {
        "timestamp": "2026-10-10 12:00:00",
        "temp_2m": 31.4,
        "temp_4m": 31.1,
        "temp_8m": 30.8,
        "rh_2m": 65.0,
        "rh_4m": 66.2,
        "rh_8m": 67.0,
        "pressure": 998.4,
        "battery_voltage": 13.2,
        "wind_speed_10m": 2.4,
        "rainfall": 0.0
    }
    res = client.post("/api/v1/telemetry/stream-point", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "classification" in data
    assert "fused_anomaly_score" in data
    assert "severity" in data


def test_sensor_health():
    res = client.get("/api/v1/sensors/health")
    assert res.status_code == 200
    data = res.json()
    assert "sensors" in data
    assert len(data["sensors"]) >= 6


def test_model_benchmark():
    res = client.get("/api/v1/models/benchmark")
    assert res.status_code == 200
    data = res.json()
    assert "comparison_table" in data
    assert len(data["comparison_table"]) >= 3


def test_explainability_endpoints():
    res1 = client.get("/api/v1/explainability/global-importance")
    assert res1.status_code == 200
    data1 = res1.json()
    assert "top_features" in data1
    assert len(data1["top_features"]) > 0

    res2 = client.get("/api/v1/explainability/shap")
    assert res2.status_code == 200


def test_csv_upload():
    csv_content = (
        "DATE(IST),TIME(IST),AIR_TEMPERATURE1(°C at 2m height),AIR_TEMPERATURE2(°C at 4m height),AIR_TEMPERATURE3(°C at 8m height),RELATIVE_HUMIDITY1(% at 2m height),ATMOSPHERIC_PRESSURE(mbar) ,BATTRY_VOLTAGE(V)\n"
        "2026-10-10,12:00:00,31.4,31.1,30.8,65.0,998.4,13.2\n"
        "2026-10-10,12:30:00,31.8,31.5,31.2,64.0,998.1,13.2\n"
        "2026-10-10,13:00:00,32.2,-40.0,31.6,63.0,997.8,13.1\n"
    )
    files = {"file": ("test_station.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
    res = client.post("/api/v1/telemetry/upload", files=files)
    data = res.json()
    assert data["status"] in ["SUCCESS", "VALIDATED_AND_ACTIVATED"]
    assert data.get("observations_count", data.get("rows_received")) == 3

