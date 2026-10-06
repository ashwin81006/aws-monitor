import json
import joblib
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, Any, Tuple, List

from ..config import (
    SCALER_PATH,
    MEDIANS_PATH,
    FEATURE_COLS_PATH,
    IF_MODEL_PATH,
    CROSS_THRESHOLDS_PATH,
    TEMPORAL_THRESHOLDS_PATH,
)
from ..schemas.telemetry import TelemetryPointInput, TelemetryInferenceResponse


class InferenceService:
    def __init__(self):
        self.scaler = joblib.load(SCALER_PATH)
        self.medians = joblib.load(MEDIANS_PATH)
        with open(FEATURE_COLS_PATH, "r") as f:
            self.feature_columns = json.load(f)
        self.model = joblib.load(IF_MODEL_PATH)

        with open(CROSS_THRESHOLDS_PATH, "r") as f:
            self.cross_thresh = json.load(f)
        with open(TEMPORAL_THRESHOLDS_PATH, "r") as f:
            self.temporal_thresh = json.load(f)

    def infer_point(self, payload: TelemetryPointInput) -> TelemetryInferenceResponse:
        ts_str = payload.timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            dt = pd.to_datetime(ts_str)
        except Exception:
            dt = datetime.now()

        hour = dt.hour + dt.minute / 60.0
        sin_hour = np.sin(2 * np.pi * hour / 24.0)
        cos_hour = np.cos(2 * np.pi * hour / 24.0)

        # ----------------------------------------------------------------------
        # 1. Build the 31 Clean Domain Features
        # ----------------------------------------------------------------------
        t2 = payload.temp_2m
        t4 = payload.temp_4m
        t8 = payload.temp_8m
        rh2 = payload.rh_2m
        rh4 = payload.rh_4m
        rh8 = payload.rh_8m
        press = payload.pressure
        batt = payload.battery_voltage
        wind = payload.wind_speed_10m or 0.0
        rain = payload.rainfall or 0.0

        # Vertical gradients
        diff_t2_t4 = t2 - t4
        diff_t4_t8 = t4 - t8
        diff_t2_t8 = t2 - t8
        diff_rh2_rh4 = rh2 - rh4
        diff_rh4_rh8 = rh4 - rh8
        diff_rh2_rh8 = rh2 - rh8

        # 30-min rates of change
        rate_t2 = (t2 - payload.prev_temp_2m) if payload.prev_temp_2m is not None else 0.0
        rate_t4 = (t4 - payload.prev_temp_4m) if payload.prev_temp_4m is not None else 0.0
        rate_t8 = (t8 - payload.prev_temp_8m) if payload.prev_temp_8m is not None else 0.0
        rate_rh2 = (rh2 - payload.prev_rh_2m) if payload.prev_rh_2m is not None else 0.0
        rate_rh4 = (rh4 - payload.prev_rh_4m) if payload.prev_rh_4m is not None else 0.0
        rate_rh8 = (rh8 - payload.prev_rh_8m) if payload.prev_rh_8m is not None else 0.0
        rate_press = (press - payload.prev_pressure) if payload.prev_pressure is not None else 0.0
        rate_batt = (batt - payload.prev_battery_voltage) if payload.prev_battery_voltage is not None else 0.0

        # Local robust deviations (z-scores relative to regional baselines)
        dev_t2 = abs(t2 - 28.5) / 5.0
        dev_t4 = abs(t4 - 28.5) / 5.0
        dev_t8 = abs(t8 - 28.5) / 5.0
        dev_rh2 = abs(rh2 - 60.0) / 20.0
        dev_press = abs(press - 1005.0) / 10.0

        feature_dict = {
            "temp_2m": t2, "temp_4m": t4, "temp_8m": t8,
            "rh_2m": rh2, "rh_4m": rh4, "rh_8m": rh8,
            "pressure": press, "battery_voltage": batt,
            "wind_speed_10m": wind, "rainfall": rain,
            "diff_temp_2m_4m": diff_t2_t4,
            "diff_temp_4m_8m": diff_t4_t8,
            "diff_temp_2m_8m": diff_t2_t8,
            "diff_rh_2m_4m": diff_rh2_rh4,
            "diff_rh_4m_8m": diff_rh4_rh8,
            "diff_rh_2m_8m": diff_rh2_rh8,
            "rate_temp_2m": rate_t2,
            "rate_temp_4m": rate_t4,
            "rate_temp_8m": rate_t8,
            "rate_rh_2m": rate_rh2,
            "rate_rh_4m": rate_rh4,
            "rate_rh_8m": rate_rh8,
            "rate_pressure": rate_press,
            "rate_battery": rate_batt,
            "dev_temp_2m": dev_t2,
            "dev_temp_4m": dev_t4,
            "dev_temp_8m": dev_t8,
            "dev_rh_2m": dev_rh2,
            "dev_pressure": dev_press,
            "solar_diurnal_sin": sin_hour,
            "solar_diurnal_cos": cos_hour,
        }

        # Vector aligned with feature_columns
        row_values = [feature_dict.get(c, self.medians.get(c, 0.0)) for c in self.feature_columns]
        X_df = pd.DataFrame([row_values], columns=self.feature_columns)
        X_scaled = pd.DataFrame(self.scaler.transform(X_df), columns=self.feature_columns)

        # ----------------------------------------------------------------------
        # 2. ML Isolation Forest Scoring
        # ----------------------------------------------------------------------
        raw_if_score = float(self.model.decision_function(X_scaled)[0])
        is_if_outlier = bool(self.model.predict(X_scaled)[0] == -1)

        # ----------------------------------------------------------------------
        # 3. Rule QC & Sentinel Detection
        # ----------------------------------------------------------------------
        rule_flags = []
        fault_reasons = []
        affected_sensors = []

        is_sentinel = False
        if press <= 0.0:
            is_sentinel = True
            rule_flags.append("SENTINEL_PRESSURE_ZERO")
            fault_reasons.append("Atmospheric pressure reported 0.0 mbar sentinel")
            affected_sensors.append("pressure")
        elif press < 850.0 or press > 1080.0:
            rule_flags.append("PHYSICAL_PRESSURE_LIMIT")
            fault_reasons.append(f"Pressure {press:.1f} mbar violates tropospheric limits")
            affected_sensors.append("pressure")

        if batt <= 0.5:
            is_sentinel = True
            rule_flags.append("POWER_BLACKOUT")
            fault_reasons.append(f"Battery voltage collapsed to {batt:.1f}V (total power loss)")
            affected_sensors.append("battery_voltage")
        elif batt < 10.5:
            rule_flags.append("POWER_BROWNOUT")
            fault_reasons.append(f"Battery undervoltage ({batt:.1f}V < 10.5V)")
            affected_sensors.append("battery_voltage")

        for s_name, val in [("temp_2m", t2), ("temp_4m", t4), ("temp_8m", t8)]:
            if val == -40.0:
                is_sentinel = True
                rule_flags.append(f"SENTINEL_{s_name.upper()}")
                fault_reasons.append(f"Sensor '{s_name}' reads -40.0°C open-circuit sentinel")
                affected_sensors.append(s_name)
            elif val < -5.0 or val > 55.0:
                rule_flags.append(f"PHYSICAL_BOUND_{s_name.upper()}")
                fault_reasons.append(f"Sensor '{s_name}' reads {val:.1f}°C outside regional physical limits")
                affected_sensors.append(s_name)

        if rain > 3000.0:
            is_sentinel = True
            rule_flags.append("RAINFALL_REGISTER_OVERFLOW")
            fault_reasons.append(f"Rainfall {rain:.1f} mm exceeds physical gauge register")
            affected_sensors.append("rainfall")

        # ----------------------------------------------------------------------
        # 4. Multi-Height Colocated Tower Consensus
        # ----------------------------------------------------------------------
        # Temperature 3-sensor consensus
        pairs = [
            (abs(t2 - t4), "temp_8m", t8, (t2 + t4) / 2.0, "temp_2m", "temp_4m"),
            (abs(t4 - t8), "temp_2m", t2, (t4 + t8) / 2.0, "temp_4m", "temp_8m"),
            (abs(t2 - t8), "temp_4m", t4, (t2 + t8) / 2.0, "temp_2m", "temp_8m"),
        ]
        pairs.sort(key=lambda x: x[0])
        min_spread, outlier_s, outlier_v, consensus_v, s_ag1, s_ag2 = pairs[0]

        severe_cross_temp = False
        divergence_delta = 0.0
        if min_spread <= 4.0:
            divergence_delta = abs(outlier_v - consensus_v)
            if divergence_delta >= 10.0:
                severe_cross_temp = True
                rule_flags.append("CROSS_SENSOR_SEVERE_DISAGREEMENT")
                fault_reasons.append(
                    f"Sensor '{outlier_s}' reads {outlier_v:.1f}°C, diverging by {divergence_delta:.1f}°C from colocated consensus"
                )
                affected_sensors.append(outlier_s)

        # ----------------------------------------------------------------------
        # 5. Temporal Rate & Isolated Jump
        # ----------------------------------------------------------------------
        temporal_spike = False
        max_rate = max(abs(rate_t2), abs(rate_t4), abs(rate_t8))
        if max_rate >= 15.0:
            temporal_spike = True
            rule_flags.append("TEMPORAL_SPIKE")
            fault_reasons.append(f"Temporal step jump of {max_rate:.1f}°C in 30 minutes")

        # ----------------------------------------------------------------------
        # 6. Bayesian Evidence Fusion & Dynamic Classification
        # ----------------------------------------------------------------------
        score_rule = 1.0 if is_sentinel else (0.85 if rule_flags else 0.0)
        score_cross = min(1.0, divergence_delta / 12.0) if severe_cross_temp else 0.0
        score_temporal = 0.90 if temporal_spike else (0.50 if max_rate >= 8.0 else 0.0)
        score_battery = 1.0 if batt <= 0.5 else (0.75 if batt < 10.5 else 0.0)
        score_ml = max(0.0, -raw_if_score * 4.0) if raw_if_score < 0 else 0.0

        # Noisy-OR combination
        p_normal = (
            (1.0 - score_rule * 0.95) *
            (1.0 - score_cross * 0.90) *
            (1.0 - score_temporal * 0.85) *
            (1.0 - score_battery * 0.95) *
            (1.0 - score_ml * 0.70)
        )
        fused_prob = round(float(1.0 - p_normal), 4)

        # Decision mapping
        if is_sentinel:
            classification = "PROBABLE_SENSOR_FAULT"
            confidence = 0.99
            severity = "CRITICAL" if batt <= 0.5 else "HIGH"
            root_cause = "INVALID_SENTINEL_READING"
            explanation = f"Impossible hardware sentinel detected: {'; '.join(fault_reasons)}."
        elif severe_cross_temp and temporal_spike:
            classification = "PROBABLE_SENSOR_FAULT"
            confidence = 0.98
            severity = "HIGH"
            root_cause = "SENSOR_SPIKE"
            explanation = f"Sensor experienced a sharp transient jump of {max_rate:.1f}°C conflicting with colocated tower consensus."
        elif batt <= 0.5 or (severe_cross_temp and batt < 10.5):
            classification = "PROBABLE_SENSOR_FAULT"
            confidence = 0.97
            severity = "CRITICAL"
            root_cause = "STATION_OR_POWER_FAILURE"
            explanation = f"Sensor corrupted during station power failure (Battery: {batt:.1f}V)."
        elif (t2 >= 44.0 or t4 >= 44.0 or t8 >= 44.0) and min_spread <= 2.5 and not severe_cross_temp and not temporal_spike:
            classification = "POSSIBLE_WEATHER_EXTREME"
            confidence = 0.90
            severity = "MEDIUM"
            root_cause = "RAPID_COHERENT_WEATHER_EVENT"
            explanation = f"High regional temperature verified as genuine heatwave: multi-height towers agree within {min_spread:.1f}°C."
        elif fused_prob >= 0.70:
            classification = "PROBABLE_SENSOR_FAULT"
            confidence = 0.92
            severity = "HIGH"
            root_cause = "SENSOR_OR_DATA_QUALITY"
            explanation = f"Multiple independent fault signals confirm probable sensor malfunction: {'; '.join(fault_reasons)}."
        elif fused_prob >= 0.40 or is_if_outlier:
            classification = "UNCERTAIN"
            confidence = 0.65
            severity = "LOW"
            root_cause = "STATISTICAL_MULTIVARIATE_OUTLIER"
            explanation = f"Observation flagged as multivariate outlier (IF score: {raw_if_score:.3f}) without deterministic hardware failure."
        else:
            classification = "NORMAL"
            confidence = 0.95
            severity = "NONE"
            root_cause = "NORMAL_OPERATION"
            explanation = "Observation reading is within normal physical limits and consistent across multi-height towers."

        return TelemetryInferenceResponse(
            timestamp=ts_str,
            classification=classification,
            anomaly_probability=fused_prob,
            confidence=round(float(confidence), 2),
            severity=severity,
            probable_root_cause=root_cause,
            affected_sensors=list(set(affected_sensors)) if affected_sensors else ["NONE"],
            is_anomaly=classification != "NORMAL",
            if_score=round(raw_if_score, 4),
            if_outlier=is_if_outlier,
            evidence_breakdown={
                "score_rule": score_rule,
                "score_cross_consensus": score_cross,
                "score_temporal": score_temporal,
                "score_battery": score_battery,
                "score_isolation_forest": round(score_ml, 4),
                "rule_flags": rule_flags,
                "multi_height_min_spread": round(min_spread, 2),
                "divergence_delta": round(divergence_delta, 2),
            },
            explanation=explanation
        )


inference_service = InferenceService()
