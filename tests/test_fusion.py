from src.core.detector import AWSUnifiedDetector
from src.core.self_healing import heal_observation


def test_in_memory_fusion_and_scoring():
    """Validates unified multi-evidence fusion producing bounded anomaly scores."""
    detector = AWSUnifiedDetector()

    # Normal observation
    diag_norm = detector.diagnose_and_detect(temp=28.0, rh=65.0, press=1008.0)
    assert 0.0 <= diag_norm["fused_anomaly_score"] <= 1.0
    assert diag_norm["is_anomaly"] is False

    # Sentinel anomaly
    diag_sent = detector.diagnose_and_detect(temp=9999.0, rh=65.0, press=1008.0)
    assert 0.0 <= diag_sent["fused_anomaly_score"] <= 1.0
    assert diag_sent["is_anomaly"] is True
    assert diag_sent["fused_anomaly_score"] >= 0.90


def test_self_healing_data_reconstruction():
    """Validates thermodynamic and autoregressive self-healing reconstruction."""
    history = [(29.0, 68.0, 1004.0), (29.2, 67.5, 1004.1), (29.5, 66.8, 1004.0)]

    # 1. Reconstruct corrupted temperature spike
    healed_spike = heal_observation(
        temp=9999.0, rh=65.0, press=1004.0,
        fault_type="SPIKE",
        culprit_sensor="Temperature",
        history=history
    )
    assert healed_spike["is_healed"] is True
    assert 20.0 <= healed_spike["corrected_temperature"] <= 35.0
    assert healed_spike["corrected_humidity"] == 65.0

    # 2. Reconstruct complete communication gap (all None)
    healed_comm = heal_observation(
        temp=None, rh=None, press=None,
        fault_type="COMMUNICATION_ERROR",
        culprit_sensor="all",
        history=history
    )
    assert healed_comm["is_healed"] is True
    assert 25.0 <= healed_comm["corrected_temperature"] <= 35.0
    assert 50.0 <= healed_comm["corrected_humidity"] <= 80.0
    assert 990.0 <= healed_comm["corrected_pressure"] <= 1020.0
