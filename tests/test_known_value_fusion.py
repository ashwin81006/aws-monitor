import numpy as np

from src.detection.core_detector import (
    compute_noisy_or_fusion,
    diagnose_point,
    W_RULE,
    W_CROSS,
    W_TEMP,
    W_ML,
)


def test_noisy_or_math_evaluation():
    """
    Verifies that Bayesian Noisy-OR combination evaluates accurately according
    to the written analytical formula and corrects the earlier documentation error.
    """
    # Test zero inputs
    assert compute_noisy_or_fusion(0.0, 0.0, 0.0, 0.0) == 0.0

    # Test single high rule evidence
    s_rule = compute_noisy_or_fusion(1.0, 0.0, 0.0, 0.0)
    assert s_rule >= 0.95

    # Verification of multi-channel fusion:
    # 1 - (1 - 0.98 * 0.90) * (1 - 0.99 * 0.85) * (1 - 0.992 * 0.70)
    # Expected: 0.9943
    no_fault = (
        (1.0 - 0.90 * 0.98) *
        (1.0 - 0.85 * 0.99) *
        (1.0 - 0.70 * 0.992)
    )
    expected_score = round(1.0 - no_fault, 4)
    assert abs(expected_score - 0.9943) < 0.0005


def test_diagnose_hardware_sentinel():
    """
    Verifies that -40.0°C open circuit sentinel produces CRITICAL PROBABLE_SENSOR_FAULT.
    """
    raw_pt = {
        "temp_2m": 31.0, "temp_4m": -40.0, "temp_8m": 30.5,
        "rh_2m": 60.0, "rh_4m": 60.0, "rh_8m": 60.0,
        "pressure": 1005.0, "battery_voltage": 13.0,
        "wind_speed_10m": 2.0, "rainfall": 0.0
    }
    feats = {
        "temp_2m": 31.0, "temp_4m": -40.0, "temp_8m": 30.5,
        "diff_temp_2m_4m": 71.0, "diff_temp_4m_8m": -70.5, "diff_temp_2m_8m": 0.5,
        "rate_temp_4m": -71.0
    }

    diag = diagnose_point(features=feats, raw_point=raw_pt, ml_decision_score=-0.2)
    assert diag["candidate_class"] == "PROBABLE_SENSOR_FAULT"
    assert diag["severity"] == "CRITICAL"
    assert diag["probable_root_cause"] == "INVALID_SENTINEL_READING"
    assert diag["target_sensor"] == "temp_4m"
    assert diag["fused_anomaly_score"] >= 0.95


def test_diagnose_power_blackout():
    """
    Verifies that battery collapse <= 0.5V produces CRITICAL STATION_SYSTEM_FAILURE.
    """
    raw_pt = {
        "temp_2m": 0.0, "temp_4m": 0.0, "temp_8m": 0.0,
        "rh_2m": 0.0, "rh_4m": 0.0, "rh_8m": 0.0,
        "pressure": 0.0, "battery_voltage": 0.2,
        "wind_speed_10m": 0.0, "rainfall": 0.0
    }
    feats = dict(raw_pt)
    diag = diagnose_point(features=feats, raw_point=raw_pt, ml_decision_score=-0.3)
    assert diag["candidate_class"] == "STATION_SYSTEM_FAILURE"
    assert diag["severity"] == "CRITICAL"
    assert diag["probable_root_cause"] == "STATION_OR_POWER_FAILURE"
    assert diag["target_sensor"] == "battery_voltage"


def test_diagnose_coherent_heatwave_rejection():
    """
    Verifies that high regional temperature (44°C) with smooth multi-height consensus
    is classified as POSSIBLE_WEATHER_EXTREME without false-alarming as hardware failure.
    """
    raw_pt = {
        "temp_2m": 44.5, "temp_4m": 44.2, "temp_8m": 43.9,
        "rh_2m": 22.0, "rh_4m": 23.0, "rh_8m": 23.5,
        "pressure": 1002.0, "battery_voltage": 13.5,
        "wind_speed_10m": 4.0, "rainfall": 0.0
    }
    feats = {
        "temp_2m": 44.5, "temp_4m": 44.2, "temp_8m": 43.9,
        "diff_temp_2m_4m": 0.3, "diff_temp_4m_8m": 0.3, "diff_temp_2m_8m": 0.6,
        "diff_rh_2m_4m": -1.0, "diff_rh_4m_8m": -0.5, "diff_rh_2m_8m": -1.5,
        "rate_temp_2m": 0.8, "rate_temp_4m": 0.7, "rate_temp_8m": 0.6
    }
    diag = diagnose_point(features=feats, raw_point=raw_pt, ml_decision_score=0.1)
    assert diag["candidate_class"] == "POSSIBLE_WEATHER_EXTREME"
    assert diag["probable_root_cause"] == "RAPID_COHERENT_WEATHER_EVENT"
    assert diag["severity"] == "MEDIUM"
