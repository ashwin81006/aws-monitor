from src.api.services.inference_service import inference_service
from src.api.schemas.telemetry import TelemetryPointInput
from src.core.detector import AWSUnifiedDetector


def test_sentinel_hardware_fault():
    """Validates that ISRO ADC open-circuit hardware sentinels (9999.0°C or -49.9°C) are flagged as critical."""
    payload = TelemetryPointInput(
        timestamp="2026-10-10 12:00:00",
        temperature=9999.0,
        humidity=65.0,
        pressure=998.4
    )
    res = inference_service.infer_point(payload)

    assert res.is_anomaly is True
    assert res.severity == "CRITICAL"
    assert "Temperature" in res.affected_sensors or "Temperature" in res.root_cause
    assert res.fused_anomaly_score >= 0.90
    assert res.is_healed is True
    assert res.corrected_temperature is not None and res.corrected_temperature < 100.0


def test_communication_loss_detection():
    """Validates that missing or disconnected telemetry payloads trigger a communication loss alarm and self-healing."""
    detector = AWSUnifiedDetector()
    diag = detector.diagnose_and_detect(temp=None, rh=None, press=None)

    assert diag["is_anomaly"] is True
    assert "COMMUNICATION_ERROR" in diag["root_cause"]
    assert diag["severity"] >= 0.90
    assert diag["is_healed"] is True


def test_spike_divergence_detection():
    """Validates that an unphysical rate-of-change jump is flagged as an unphysical spike."""
    detector = AWSUnifiedDetector()
    # Establish stable history
    for _ in range(4):
        detector.diagnose_and_detect(temp=30.0, rh=65.0, press=1000.0)

    # Inject sharp 10°C jump in single step
    diag = detector.diagnose_and_detect(temp=42.0, rh=65.0, press=1000.0)

    assert diag["is_anomaly"] is True
    assert "SPIKE" in diag["root_cause"]
    assert diag["culprit_sensor"] == "Temperature"
    assert diag["fused_anomaly_score"] >= 0.80


def test_heatwave_consensus_no_false_alarm():
    """Validates that genuine high-temperature summer heatwaves with low humidity are recognized without false alarms."""
    detector = AWSUnifiedDetector()
    # Establish pre-conditions
    detector.diagnose_and_detect(temp=41.0, rh=28.0, press=998.0)
    diag = detector.diagnose_and_detect(temp=43.5, rh=22.0, press=996.0)

    assert diag["is_anomaly"] is False
    assert diag["is_extreme_weather"] is True
    assert diag["severity"] < 0.50
    assert "HEATWAVE" in diag["root_cause"] or "GENUINE_METEOROLOGICAL_EVENT" in diag["root_cause"]
