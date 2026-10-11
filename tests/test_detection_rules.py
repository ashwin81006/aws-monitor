from src.api.services.inference_service import inference_service
from src.api.schemas.telemetry import TelemetryPointInput



def test_sentinel_hardware_fault():
    # 4m sensor open-circuit sentinel (-40°C)
    payload = TelemetryPointInput(
        timestamp="2026-10-10 12:00:00",
        temp_2m=31.2,
        temp_4m=-40.0,
        temp_8m=30.8,
        rh_2m=65.0,
        rh_4m=66.2,
        rh_8m=67.0,
        pressure=998.4,
        battery_voltage=13.1
    )
    res = inference_service.infer_point(payload)

    assert res.classification == "PROBABLE_SENSOR_FAULT"
    assert res.severity == "CRITICAL"
    assert "temp_4m" in res.affected_sensors
    assert res.fused_anomaly_score >= 0.90


def test_battery_brownout_detection():
    # Battery drops below 10.5V safety limit
    payload = TelemetryPointInput(
        timestamp="2026-10-10 03:00:00",
        temp_2m=24.5,
        temp_4m=24.2,
        temp_8m=24.0,
        rh_2m=75.0,
        rh_4m=76.0,
        rh_8m=77.0,
        pressure=1001.2,
        battery_voltage=9.4
    )
    res = inference_service.infer_point(payload)

    assert res.classification in ["PROBABLE_SENSOR_FAULT", "STATION_SYSTEM_FAILURE"]
    assert "battery_voltage" in res.affected_sensors
    assert res.fused_anomaly_score >= 0.85


def test_spike_divergence_detection():
    # 4m spikes suddenly while 2m and 8m stay normal
    payload = TelemetryPointInput(
        timestamp="2026-10-10 15:00:00",
        temp_2m=32.0,
        temp_4m=-15.0,
        temp_8m=31.5,
        rh_2m=60.0,
        rh_4m=61.0,
        rh_8m=62.0,
        pressure=998.0,
        battery_voltage=13.0,
        prev_temp_4m=31.8
    )
    res = inference_service.infer_point(payload)

    assert res.classification == "PROBABLE_SENSOR_FAULT"
    assert "temp_4m" in res.affected_sensors
    assert res.fused_anomaly_score >= 0.90


def test_heatwave_consensus_no_false_alarm():
    # All 3 sensors rise smoothly to 46°C with natural vertical lapse rate
    payload = TelemetryPointInput(
        timestamp="2026-10-10 14:00:00",
        temp_2m=46.2,
        temp_4m=45.9,
        temp_8m=45.6,
        rh_2m=25.0,
        rh_4m=25.5,
        rh_8m=26.0,
        pressure=996.0,
        battery_voltage=13.5
    )
    res = inference_service.infer_point(payload)

    assert res.classification in ["POSSIBLE_WEATHER_EXTREME", "BENIGN_EXTREME", "NORMAL"]
    assert res.severity != "CRITICAL"
    assert "temp_4m" not in res.affected_sensors

