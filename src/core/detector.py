import os
import sys
import pickle
from typing import Dict, Any, Optional
import numpy as np
import pandas as pd

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from src.features.feature_engineering import StreamingFeatureExtractor, FEATURE_COLUMNS
from src.core.self_healing import heal_observation

MODELS_DIR = os.path.join(PROJECT_ROOT, "models")


class AWSUnifiedDetector:
    def __init__(self):
        self.extractor = StreamingFeatureExtractor(window_size=8)
        self.model = None
        self.scaler = None
        self._load_models()

    def _load_models(self):
        if_path = os.path.join(MODELS_DIR, "isolation_forest.pkl")
        sc_path = os.path.join(MODELS_DIR, "scaler.pkl")

        if os.path.exists(if_path) and os.path.exists(sc_path):
            with open(if_path, "rb") as f:
                self.model = pickle.load(f)
            with open(sc_path, "rb") as f:
                self.scaler = pickle.load(f)

    def diagnose_and_detect(
        self,
        temp: Optional[float],
        rh: Optional[float],
        press: Optional[float],
        timestamp: Optional[pd.Timestamp] = None
    ) -> Dict[str, Any]:
        if temp is None or rh is None or press is None or np.isnan(temp) or np.isnan(rh) or np.isnan(press):
            healing = heal_observation(temp, rh, press, fault_type="COMMUNICATION_ERROR", culprit_sensor="all", history=list(self.extractor.history))
            return {
                "is_anomaly": True,
                "anomaly_flag": 1,
                "severity": 0.95,
                "confidence": 0.99,
                "fused_anomaly_score": 0.95,
                "root_cause": "COMMUNICATION_ERROR: Missing / Disconnected Sensor Payload",
                "culprit_sensor": "All Sensors (Telemetry Loss)",
                "is_extreme_weather": False,
                **healing
            }

        if temp >= 90.0 or temp <= -40.0:
            healing = heal_observation(temp, rh, press, fault_type="SPIKE", culprit_sensor="Temperature", history=list(self.extractor.history))
            return {
                "is_anomaly": True,
                "anomaly_flag": 1,
                "severity": 0.98,
                "confidence": 1.0,
                "fused_anomaly_score": 0.98,
                "root_cause": f"HARDWARE_SENTINEL: Temperature Sensor Open-Circuit ({temp}°C)",
                "culprit_sensor": "Temperature",
                "is_extreme_weather": False,
                **healing
            }

        is_frozen = False
        frozen_channel = "NONE"
        if len(self.extractor.history) >= 4:
            recent_t = [pt[0] for pt in self.extractor.history]
            if np.std(recent_t) < 1e-4 and abs(temp - recent_t[-1]) < 1e-4:
                is_frozen = True
                frozen_channel = "Temperature"

        if is_frozen:
            healing = heal_observation(temp, rh, press, fault_type="FROZEN_SENSOR", culprit_sensor=frozen_channel, history=list(self.extractor.history))
            return {
                "is_anomaly": True,
                "anomaly_flag": 1,
                "severity": 0.75,
                "confidence": 0.90,
                "fused_anomaly_score": 0.75,
                "root_cause": f"FROZEN_SENSOR: Mechanical Stagnation on {frozen_channel} (Zero Variance)",
                "culprit_sensor": frozen_channel,
                "is_extreme_weather": False,
                **healing
            }

        feats = self.extractor.push(temp=temp, rh=rh, press=press, timestamp=timestamp)

        if abs(feats["temp_rate"]) > 6.0:
            healing = heal_observation(temp, rh, press, fault_type="SPIKE", culprit_sensor="Temperature", history=list(self.extractor.history))
            return {
                "is_anomaly": True,
                "anomaly_flag": 1,
                "severity": 0.88,
                "confidence": 0.92,
                "fused_anomaly_score": 0.88,
                "root_cause": f"SPIKE: Unphysical Temperature Jump ({feats['temp_rate']:+.1f}°C in 30 min)",
                "culprit_sensor": "Temperature",
                "is_extreme_weather": False,
                **healing
            }

        if abs(feats["pressure_rate"]) > 15.0:
            healing = heal_observation(temp, rh, press, fault_type="SPIKE", culprit_sensor="Pressure", history=list(self.extractor.history))
            return {
                "is_anomaly": True,
                "anomaly_flag": 1,
                "severity": 0.85,
                "confidence": 0.90,
                "fused_anomaly_score": 0.85,
                "root_cause": f"SPIKE: Unphysical Barometric Step ({feats['pressure_rate']:+.1f} hPa in 30 min)",
                "culprit_sensor": "Pressure",
                "is_extreme_weather": False,
                **healing
            }

        if feats["dew_point_depression"] < -0.5:
            healing = heal_observation(temp, rh, press, fault_type="PHYSICAL_INCONSISTENCY", culprit_sensor="Humidity", history=list(self.extractor.history))
            return {
                "is_anomaly": True,
                "anomaly_flag": 1,
                "severity": 0.80,
                "confidence": 0.88,
                "fused_anomaly_score": 0.80,
                "root_cause": "PHYSICAL_INCONSISTENCY: Supersaturation Violation (Dew Point > Air Temperature)",
                "culprit_sensor": "Humidity / Temperature",
                "is_extreme_weather": False,
                **healing
            }

        is_thunderstorm = (feats["pressure_rate"] < -3.0 and feats["humidity_rate"] > 15.0 and feats["temp_rate"] < -2.0)
        is_heatwave = (temp > 42.0 and rh < 35.0 and feats["dew_point_depression"] > 20.0)

        if is_thunderstorm:
            return {
                "is_anomaly": False,
                "anomaly_flag": 0,
                "severity": 0.15,
                "confidence": 0.95,
                "fused_anomaly_score": 0.15,
                "root_cause": "GENUINE_METEOROLOGICAL_EVENT: Severe Monsoon Thunderstorm Convection",
                "culprit_sensor": "NONE (Physical Weather Event)",
                "is_extreme_weather": True,
                "is_healed": False,
                "corrected_temperature": temp,
                "corrected_humidity": rh,
                "corrected_pressure": press,
                "original_temperature": temp,
                "original_humidity": rh,
                "original_pressure": press
            }

        if is_heatwave:
            return {
                "is_anomaly": False,
                "anomaly_flag": 0,
                "severity": 0.20,
                "confidence": 0.92,
                "fused_anomaly_score": 0.20,
                "root_cause": "GENUINE_METEOROLOGICAL_EVENT: Severe Summer Heatwave (Thermodynamically Consistent)",
                "culprit_sensor": "NONE (Physical Weather Event)",
                "is_extreme_weather": True,
                "is_healed": False,
                "corrected_temperature": temp,
                "corrected_humidity": rh,
                "corrected_pressure": press,
                "original_temperature": temp,
                "original_humidity": rh,
                "original_pressure": press
            }

        ml_score = 0.0
        ml_is_outlier = False
        if self.model and self.scaler:
            X_df = pd.DataFrame([feats])[FEATURE_COLUMNS]
            X_scaled = self.scaler.transform(X_df)
            decision = float(self.model.decision_function(X_scaled)[0])
            ml_is_outlier = bool(decision < -0.05)
            ml_score = float(np.clip(1.0 / (1.0 + np.exp(decision * 10.0)), 0.02, 0.98))

        if ml_is_outlier:
            healing = heal_observation(temp, rh, press, fault_type="MULTIVARIATE_ANOMALY", culprit_sensor="Temperature", history=list(self.extractor.history))
            return {
                "is_anomaly": True,
                "anomaly_flag": 1,
                "severity": round(ml_score, 2),
                "confidence": 0.85,
                "fused_anomaly_score": round(ml_score, 2),
                "root_cause": "MULTIVARIATE_ANOMALY: Observation Outlier in 13-Dimensional Phase Space",
                "culprit_sensor": "Temperature / Humidity Matrix",
                "is_extreme_weather": False,
                **healing
            }

        return {
            "is_anomaly": False,
            "anomaly_flag": 0,
            "severity": round(ml_score, 2),
            "confidence": 0.98,
            "fused_anomaly_score": round(ml_score, 2),
            "root_cause": "NOMINAL: Healthy Sensor Operation & Physical Consistency",
            "culprit_sensor": "NONE",
            "is_extreme_weather": False,
            "is_healed": False,
            "corrected_temperature": temp,
            "corrected_humidity": rh,
            "corrected_pressure": press,
            "original_temperature": temp,
            "original_humidity": rh,
            "original_pressure": press
        }
