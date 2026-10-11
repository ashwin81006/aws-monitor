import os
import json
import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple, Optional, List

# ==============================================================================
# CORE ANOMALY DETECTOR & BAYESIAN EVIDENCE FUSION ENGINE
# ==============================================================================
# Shared detection and diagnosis engine used across:
#   1. Offline pipeline (build_evidence_matrix.py, event_fusion.py)
#   2. Streaming point API (inference_service.py)
#   3. Dashboard batch CSV uploads (dataset_processor.py)
#
# Eliminates detector discrepancy and guarantees identical classifications.
# ==============================================================================

W_RULE = 0.95
W_CROSS = 0.90
W_TEMP = 0.85
W_ML = 0.80

DEFAULT_CROSS_THRESHOLDS = {
    "temperature_spread_99th_percentile": 6.05,
    "humidity_spread_99th_percentile": 17.8
}

DEFAULT_TEMPORAL_THRESHOLDS = {
    "temperature_rate_99th_percentile": 7.3,
    "humidity_rate_99th_percentile": 28.8,
    "max_temp_jump_30min": 10.0,
    "max_pressure_jump_30min": 5.0
}


def compute_noisy_or_fusion(
    score_rule: float,
    score_cross: float,
    score_temp: float,
    score_ml: float
) -> float:
    """
    Computes calibrated Bayesian Noisy-OR fused anomaly score in [0.0, 1.0].
    """
    no_fault = (
        (1.0 - W_RULE * np.clip(score_rule, 0.0, 1.0)) *
        (1.0 - W_CROSS * np.clip(score_cross, 0.0, 1.0)) *
        (1.0 - W_TEMP * np.clip(score_temp, 0.0, 1.0)) *
        (1.0 - W_ML * np.clip(score_ml, 0.0, 1.0))
    )
    return float(np.round(np.clip(1.0 - no_fault, 0.0, 1.0), 4))


def diagnose_point(
    features: Dict[str, float],
    raw_point: Dict[str, float],
    ml_decision_score: Optional[float] = None,
    is_ml_outlier: bool = False,
    cross_thresholds: Optional[Dict[str, float]] = None,
    temporal_thresholds: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """
    Unified point diagnosis combining physical rule checks, vertical tower consistency,
    temporal rate thresholds, and unsupervised ML outlier scores.
    """
    c_thresh = cross_thresholds or DEFAULT_CROSS_THRESHOLDS
    t_thresh = temporal_thresholds or DEFAULT_TEMPORAL_THRESHOLDS

    t2 = float(raw_point.get("temp_2m", features.get("temp_2m", 25.0)))
    t4 = float(raw_point.get("temp_4m", features.get("temp_4m", 25.0)))
    t8 = float(raw_point.get("temp_8m", features.get("temp_8m", 25.0)))
    rh2 = float(raw_point.get("rh_2m", features.get("rh_2m", 60.0)))
    rh4 = float(raw_point.get("rh_4m", features.get("rh_4m", 60.0)))
    rh8 = float(raw_point.get("rh_8m", features.get("rh_8m", 60.0)))
    press = float(raw_point.get("pressure", features.get("pressure", 1000.0)))
    batt = float(raw_point.get("battery_voltage", features.get("battery_voltage", 12.5)))
    rain = float(raw_point.get("rainfall", features.get("rainfall", 0.0)) or 0.0)

    diff_t2_t4 = features.get("diff_temp_2m_4m", t2 - t4)
    diff_t4_t8 = features.get("diff_temp_4m_8m", t4 - t8)
    diff_t2_t8 = features.get("diff_temp_2m_8m", t2 - t8)
    t_spread = max(abs(diff_t2_t4), abs(diff_t4_t8), abs(diff_t2_t8))

    diff_rh2_rh4 = features.get("diff_rh_2m_4m", rh2 - rh4)
    diff_rh4_rh8 = features.get("diff_rh_4m_8m", rh4 - rh8)
    diff_rh2_rh8 = features.get("diff_rh_2m_8m", rh2 - rh8)
    rh_spread = max(abs(diff_rh2_rh4), abs(diff_rh4_rh8), abs(diff_rh2_rh8))

    rate_t2 = features.get("rate_temp_2m", 0.0)
    rate_t4 = features.get("rate_temp_4m", 0.0)
    rate_t8 = features.get("rate_temp_8m", 0.0)
    max_t_rate = max(abs(rate_t2), abs(rate_t4), abs(rate_t8))

    rate_rh2 = features.get("rate_rh_2m", 0.0)
    rate_rh4 = features.get("rate_rh_4m", 0.0)
    rate_rh8 = features.get("rate_rh_8m", 0.0)
    max_rh_rate = max(abs(rate_rh2), abs(rate_rh4), abs(rate_rh8))

    # 1. Rule Evidence
    rule_flags = []
    score_rule = 0.0

    # Sentinel / Power / Pressure limits
    is_power_failure = (batt <= 0.5)
    is_sentinel_temp = (t2 == -40.0) or (t4 == -40.0) or (t8 == -40.0)
    is_sentinel_press = (press <= 0.0)
    is_invalid_pressure = (press < 850.0 or press > 1080.0)
    is_brownout = (batt < 10.5) and (batt > 0.5)

    if is_power_failure:
        rule_flags.append("POWER_BLACKOUT")
        score_rule = max(score_rule, 1.0)
    elif is_sentinel_temp:
        rule_flags.append("SENTINEL_TEMP_MINUS_40")
        score_rule = max(score_rule, 0.95)
    elif is_sentinel_press:
        rule_flags.append("SENTINEL_PRESSURE_ZERO")
        score_rule = max(score_rule, 0.95)
    elif is_invalid_pressure:
        rule_flags.append("PHYSICAL_PRESSURE_LIMIT")
        score_rule = max(score_rule, 0.90)
    elif is_brownout:
        rule_flags.append("BATTERY_BROWNOUT")
        score_rule = max(score_rule, 0.85)

    # 2. Cross-Sensor Consistency Sub-Score
    t_spread_thresh = c_thresh.get("temperature_spread_99th_percentile", 6.05)
    rh_spread_thresh = c_thresh.get("humidity_spread_99th_percentile", 17.8)

    t_ratio = t_spread / t_spread_thresh if t_spread_thresh > 0 else 0.0
    rh_ratio = rh_spread / rh_spread_thresh if rh_spread_thresh > 0 else 0.0
    max_cross_ratio = max(t_ratio, rh_ratio)

    if max_cross_ratio < 0.50:
        score_cross = 0.0
    else:
        score_cross = 1.0 / (1.0 + np.exp(-3.5 * (max_cross_ratio - 1.0)))
    if max_cross_ratio > 1.2:
        rule_flags.append("CROSS_SENSOR_DISAGREEMENT")

    # 3. Temporal Dynamics Sub-Score
    t_rate_thresh = t_thresh.get("temperature_rate_99th_percentile", 7.3)
    rh_rate_thresh = t_thresh.get("humidity_rate_99th_percentile", 28.8)

    t_r_ratio = max_t_rate / t_rate_thresh if t_rate_thresh > 0 else 0.0
    rh_r_ratio = max_rh_rate / rh_rate_thresh if rh_rate_thresh > 0 else 0.0
    max_rate_ratio = max(t_r_ratio, rh_r_ratio)

    if max_rate_ratio < 0.50:
        score_temp = 0.0
    else:
        score_temp = 1.0 / (1.0 + np.exp(-3.5 * (max_rate_ratio - 1.0)))

    # Single spike flag: one level spikes sharply while others do not
    single_spike = (
        (abs(rate_t4) >= 8.0 and abs(rate_t2) < 3.0 and abs(rate_t8) < 3.0) or
        (abs(rate_t2) >= 8.0 and abs(rate_t4) < 3.0 and abs(rate_t8) < 3.0) or
        (abs(rate_t8) >= 8.0 and abs(rate_t2) < 3.0 and abs(rate_t4) < 3.0)
    )
    if single_spike:
        score_temp = max(score_temp, 0.88)
        rule_flags.append("TEMPORAL_SINGLE_SPIKE")

    # 4. Machine Learning Sub-Score
    if ml_decision_score is not None:
        if ml_decision_score < 0:
            score_ml = float(np.clip(0.50 + 0.50 * (-ml_decision_score / 0.10), 0.50, 1.0))
        else:
            score_ml = 0.0
    elif is_ml_outlier:
        score_ml = 0.75
    else:
        score_ml = 0.0

    # 5. Bayesian Noisy-OR Fusion
    fused_score = compute_noisy_or_fusion(score_rule, score_cross, score_temp, score_ml)

    # 6. Diagnosis Decision Tree & Physical Root Cause Isolation
    # Check for coherent weather extreme (all levels shift together without tower split)
    is_coherent_heatwave = (
        (t2 >= 42.0 or t4 >= 42.0 or t8 >= 42.0) and
        t_spread < 4.0 and
        not single_spike and
        score_rule == 0.0
    )
    is_severe_split = (t_spread > 8.0) or (rh_spread > 25.0)

    # Target sensor localization
    if is_sentinel_temp:
        if t4 == -40.0:
            target_sensor = "temp_4m"
        elif t2 == -40.0:
            target_sensor = "temp_2m"
        else:
            target_sensor = "temp_8m"
    elif is_power_failure or is_brownout:
        target_sensor = "battery_voltage"
    elif is_sentinel_press or is_invalid_pressure:
        target_sensor = "pressure"
    elif single_spike:
        if abs(rate_t4) == max_t_rate:
            target_sensor = "temp_4m"
        elif abs(rate_t2) == max_t_rate:
            target_sensor = "temp_2m"
        else:
            target_sensor = "temp_8m"
    elif is_severe_split:
        # Which sensor diverges from the other two?
        d24 = abs(t2 - t4)
        d48 = abs(t4 - t8)
        d28 = abs(t2 - t8)
        if d24 > 6.0 and d48 > 6.0 and d28 < 3.0:
            target_sensor = "temp_4m"  # 4m diverges from 2m and 8m
        elif d24 > 6.0 and d28 > 6.0 and d48 < 3.0:
            target_sensor = "temp_2m"
        elif d48 > 6.0 and d28 > 6.0 and d24 < 3.0:
            target_sensor = "temp_8m"
        else:
            target_sensor = "temp_4m"
    elif is_coherent_heatwave:
        target_sensor = "CONSENSUS_ALL_HEIGHTS"
    else:
        target_sensor = "NONE" if fused_score < 0.50 else "CORE_SENSORS"

    # Candidate Class & Severity
    if is_power_failure:
        candidate_class = "STATION_SYSTEM_FAILURE"
        severity = "CRITICAL"
        root_cause = "STATION_OR_POWER_FAILURE"
        confidence = 0.99
    elif is_sentinel_temp or is_sentinel_press or is_invalid_pressure:
        candidate_class = "PROBABLE_SENSOR_FAULT"
        severity = "CRITICAL"
        root_cause = "INVALID_SENTINEL_READING"
        confidence = 0.98
    elif is_brownout:
        candidate_class = "STATION_SYSTEM_FAILURE"
        severity = "HIGH"
        root_cause = "BATTERY_BROWNOUT"
        confidence = 0.92
    elif single_spike:
        candidate_class = "PROBABLE_SENSOR_FAULT"
        severity = "HIGH"
        root_cause = "SENSOR_SPIKE"
        confidence = 0.94
    elif is_severe_split:
        candidate_class = "PROBABLE_SENSOR_FAULT"
        severity = "HIGH"
        root_cause = "CALIBRATION_DRIFT_OR_BIAS"
        confidence = 0.91
    elif is_coherent_heatwave:
        candidate_class = "POSSIBLE_WEATHER_EXTREME"
        severity = "MEDIUM"
        root_cause = "RAPID_COHERENT_WEATHER_EVENT"
        confidence = 0.90
    elif fused_score >= 0.50:
        candidate_class = "UNCERTAIN"
        severity = "LOW"
        root_cause = "STATISTICAL_MULTIVARIATE_OUTLIER"
        confidence = round(float(fused_score), 2)
    else:
        candidate_class = "NORMAL"
        severity = "NONE"
        root_cause = "NORMAL_OPERATION"
        confidence = round(float(1.0 - fused_score), 2)

    return {
        "score_rule": round(float(score_rule), 4),
        "score_cross": round(float(score_cross), 4),
        "score_temporal": round(float(score_temp), 4),
        "score_ml": round(float(score_ml), 4),
        "fused_anomaly_score": fused_score,
        "fused_anomaly_flag": int(fused_score >= 0.50 and candidate_class != "NORMAL"),
        "candidate_class": candidate_class,
        "severity": severity,
        "probable_root_cause": root_cause,
        "target_sensor": target_sensor,
        "confidence": confidence,
        "rule_flags": rule_flags
    }
