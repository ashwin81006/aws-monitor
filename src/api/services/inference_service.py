import os
import json
import logging
import joblib
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, Any, Tuple, List, Optional

from ..config import (
    SCALER_PATH,
    MEDIANS_PATH,
    FEATURE_COLS_PATH,
    IF_MODEL_PATH,
    CROSS_THRESHOLDS_PATH,
    TEMPORAL_THRESHOLDS_PATH,
)
from ..schemas.telemetry import TelemetryPointInput, TelemetryInferenceResponse
from ...features.feature_builder import StreamingFeatureBuffer, ML_31_FEATURES
from ...detection.core_detector import (
    diagnose_point,
    DEFAULT_CROSS_THRESHOLDS,
    DEFAULT_TEMPORAL_THRESHOLDS,
)

logger = logging.getLogger("aws_monitor.inference")


class InferenceService:
    def __init__(self):
        self.feature_columns: List[str] = list(ML_31_FEATURES)
        self.model_version: str = "1.0.0-PROD"
        self.artifact_source: str = IF_MODEL_PATH
        self.is_demo_mode: bool = False
        self.status: str = "INITIALIZING"
        self.buffer = StreamingFeatureBuffer(window_size=9)
        self.cross_thresh = dict(DEFAULT_CROSS_THRESHOLDS)
        self.temporal_thresh = dict(DEFAULT_TEMPORAL_THRESHOLDS)
        self._init_models_and_thresholds()

    def _init_models_and_thresholds(self):
        # 1. Load Thresholds
        if os.path.exists(CROSS_THRESHOLDS_PATH):
            try:
                with open(CROSS_THRESHOLDS_PATH, "r") as f:
                    self.cross_thresh = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load cross thresholds: {e}")

        if os.path.exists(TEMPORAL_THRESHOLDS_PATH):
            try:
                with open(TEMPORAL_THRESHOLDS_PATH, "r") as f:
                    self.temporal_thresh = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load temporal thresholds: {e}")

        # 2. Load Production Artifacts
        if (
            os.path.exists(SCALER_PATH)
            and os.path.exists(IF_MODEL_PATH)
            and os.path.exists(FEATURE_COLS_PATH)
        ):
            try:
                self.scaler = joblib.load(SCALER_PATH)
                self.model = joblib.load(IF_MODEL_PATH)
                with open(FEATURE_COLS_PATH, "r") as f:
                    self.feature_columns = json.load(f)
                self.medians = (
                    joblib.load(MEDIANS_PATH)
                    if os.path.exists(MEDIANS_PATH)
                    else pd.Series(0.0, index=self.feature_columns)
                )
                self.is_demo_mode = False
                self.status = "ONLINE"
                self.model_version = "1.0.0-PROD (ISRO Junagadh AWS Trained)"
                self.artifact_source = IF_MODEL_PATH
                logger.info(
                    f"Loaded verified production model artifacts from {IF_MODEL_PATH} "
                    f"({len(self.feature_columns)} features)"
                )
                return
            except Exception as ex:
                logger.warning(f"Error loading production artifacts: {ex}. Initializing in-memory demo fallback.")

        # Fallback to in-memory demo model
        logger.info("Production model artifacts unavailable on disk. Initializing in-memory fallback mode.")
        self._fit_ephemeral_demo_models()

    def _fit_ephemeral_demo_models(self):
        """
        Creates an in-memory demo fallback model for quick testing/demo mode
        WITHOUT modifying or overwriting production artifacts on disk.
        Explicitly marked as DEMO mode.
        """
        from sklearn.ensemble import IsolationForest
        from sklearn.preprocessing import RobustScaler

        self.is_demo_mode = True
        self.status = "DEGRADED"
        self.model_version = "1.0.0-DEMO (In-Memory Ephemeral)"
        self.artifact_source = "MEMORY_EPHEMERAL"

        np.random.seed(42)
        n_samples = 1500
        t2 = np.random.normal(28.5, 4.0, n_samples)
        t4 = t2 + np.random.normal(-0.3, 0.4, n_samples)
        t8 = t4 + np.random.normal(-0.3, 0.4, n_samples)
        rh2 = np.random.normal(65.0, 15.0, n_samples).clip(10, 100)
        rh4 = rh2 + np.random.normal(1.2, 1.0, n_samples).clip(10, 100)
        rh8 = rh4 + np.random.normal(1.0, 1.0, n_samples).clip(10, 100)
        press = np.random.normal(998.4, 6.0, n_samples)
        batt = np.random.normal(13.2, 0.4, n_samples).clip(11, 14.5)
        wind = np.random.exponential(2.5, n_samples)
        rain = np.zeros(n_samples)

        data = {
            "temp_2m": t2, "temp_4m": t4, "temp_8m": t8,
            "rh_2m": rh2, "rh_4m": rh4, "rh_8m": rh8,
            "pressure": press, "battery_voltage": batt,
            "wind_speed_10m": wind, "rainfall": rain,
            "diff_temp_2m_4m": t2 - t4, "diff_temp_4m_8m": t4 - t8, "diff_temp_2m_8m": t2 - t8,
            "diff_rh_2m_4m": rh2 - rh4, "diff_rh_4m_8m": rh4 - rh8, "diff_rh_2m_8m": rh2 - rh8,
            "rate_temp_2m": np.random.normal(0, 0.8, n_samples),
            "rate_temp_4m": np.random.normal(0, 0.8, n_samples),
            "rate_temp_8m": np.random.normal(0, 0.8, n_samples),
            "rate_rh_2m": np.random.normal(0, 2.0, n_samples),
            "rate_rh_4m": np.random.normal(0, 2.0, n_samples),
            "rate_rh_8m": np.random.normal(0, 2.0, n_samples),
            "rate_pressure": np.random.normal(0, 0.5, n_samples),
            "rate_battery": np.random.normal(0, 0.05, n_samples),
            "dev_temp_2m": np.abs(t2 - 28.5) / 5.0,
            "dev_temp_4m": np.abs(t4 - 28.5) / 5.0,
            "dev_temp_8m": np.abs(t8 - 28.5) / 5.0,
            "dev_rh_2m": np.abs(rh2 - 60.0) / 20.0,
            "dev_pressure": np.abs(press - 1005.0) / 10.0,
            "solar_diurnal_sin": np.sin(np.linspace(0, 2 * np.pi, n_samples)),
            "solar_diurnal_cos": np.cos(np.linspace(0, 2 * np.pi, n_samples)),
        }
        df_fit = pd.DataFrame(data)[self.feature_columns]

        self.scaler = RobustScaler()
        X_scaled = self.scaler.fit_transform(df_fit)
        self.model = IsolationForest(n_estimators=100, contamination=0.05, random_state=42)
        self.model.fit(X_scaled)
        self.medians = df_fit.median()

    def get_service_status(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "is_demo_mode": self.is_demo_mode,
            "model_version": self.model_version,
            "artifact_source": self.artifact_source,
            "features_count": len(self.feature_columns),
            "features": self.feature_columns
        }

    def infer_point(self, payload: TelemetryPointInput) -> TelemetryInferenceResponse:
        ts_str = payload.timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            dt = pd.to_datetime(ts_str)
        except Exception:
            dt = datetime.now()

        raw_dict = {
            "temp_2m": payload.temp_2m,
            "temp_4m": payload.temp_4m,
            "temp_8m": payload.temp_8m,
            "rh_2m": payload.rh_2m,
            "rh_4m": payload.rh_4m,
            "rh_8m": payload.rh_8m,
            "pressure": payload.pressure,
            "battery_voltage": payload.battery_voltage,
            "wind_speed_10m": payload.wind_speed_10m or 0.0,
            "rainfall": payload.rainfall or 0.0
        }

        prev_dict = None
        if payload.prev_temp_2m is not None:
            prev_dict = {
                "temp_2m": payload.prev_temp_2m,
                "temp_4m": payload.prev_temp_4m if payload.prev_temp_4m is not None else payload.temp_4m,
                "temp_8m": payload.prev_temp_8m if payload.prev_temp_8m is not None else payload.temp_8m,
                "rh_2m": payload.prev_rh_2m if payload.prev_rh_2m is not None else payload.rh_2m,
                "rh_4m": payload.prev_rh_4m if payload.prev_rh_4m is not None else payload.rh_4m,
                "rh_8m": payload.prev_rh_8m if payload.prev_rh_8m is not None else payload.rh_8m,
                "pressure": payload.prev_pressure if payload.prev_pressure is not None else payload.pressure,
                "battery_voltage": payload.prev_battery_voltage if payload.prev_battery_voltage is not None else payload.battery_voltage
            }

        # 1. Compute 31 Causal Domain Features via shared StreamingFeatureBuffer
        feat_dict = self.buffer.compute_point_features(raw_dict, ts=dt, prev_point=prev_dict)

        # 2. Vectorize and Scale with RobustScaler
        row_values = [feat_dict.get(c, self.medians.get(c, 0.0)) for c in self.feature_columns]
        X_df = pd.DataFrame([row_values], columns=self.feature_columns)
        X_scaled = pd.DataFrame(self.scaler.transform(X_df), columns=self.feature_columns)

        # 3. Isolation Forest Inference
        raw_if_score = float(self.model.decision_function(X_scaled)[0])
        is_if_outlier = bool(self.model.predict(X_scaled)[0] == -1)

        # 4. Centralized Diagnosis & Bayesian Fusion Engine
        diag = diagnose_point(
            features=feat_dict,
            raw_point=raw_dict,
            ml_decision_score=raw_if_score,
            is_ml_outlier=is_if_outlier,
            cross_thresholds=self.cross_thresh,
            temporal_thresholds=self.temporal_thresh
        )

        fused_score = diag["fused_anomaly_score"]
        classification = diag["candidate_class"]
        severity = diag["severity"]
        root_cause = diag["probable_root_cause"]
        target_sensor = diag["target_sensor"]
        confidence = diag["confidence"]
        rule_flags = diag["rule_flags"]

        # Explanation string
        if classification == "NORMAL":
            explanation = "Observation reading is within normal physical limits and consistent across multi-height towers."
        elif classification == "POSSIBLE_WEATHER_EXTREME":
            explanation = "Coherent multi-height temperature shift without tower lapse disagreement; verified benign extreme."
        else:
            explanation = f"Flagged as {classification} ({root_cause}) with fused score {fused_score:.3f}. Primary target: {target_sensor}."

        affected = [target_sensor] if target_sensor not in ["NONE", "CORE_SENSORS", "CONSENSUS_ALL_HEIGHTS"] else ["NONE"]

        return TelemetryInferenceResponse(
            timestamp=ts_str,
            classification=classification,
            anomaly_probability=fused_score,
            fused_anomaly_score=fused_score,
            confidence=confidence,
            severity=severity,
            probable_root_cause=root_cause,
            root_cause=root_cause,
            affected_sensors=affected,
            is_anomaly=classification != "NORMAL",
            if_score=round(raw_if_score, 4),
            if_outlier=is_if_outlier,
            evidence_breakdown={
                "score_rule": diag["score_rule"],
                "score_cross_consensus": diag["score_cross"],
                "score_temporal": diag["score_temporal"],
                "score_isolation_forest": diag["score_ml"],
                "rule_flags": rule_flags,
                "target_sensor": target_sensor,
            },
            explanation=explanation
        )


inference_service = InferenceService()
