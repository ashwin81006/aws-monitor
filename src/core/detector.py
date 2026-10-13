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
    def __init__(self, mode: str = "calibrated_ensemble"):
        self.mode = mode
        self.extractor = StreamingFeatureExtractor(window_size=8)
        self.model_if = None
        self.model_svm = None
        self.model_lof = None
        self.scaler = None
        self._load_models()

    def set_mode(self, mode: str):
        valid_modes = ["isolation_forest", "one_class_svm", "lof", "calibrated_ensemble", "majority_voting", "rule_cascade"]
        if mode in valid_modes:
            self.mode = mode

    def reset_history(self):
        self.extractor.reset()

    def _load_models(self):
        if_path = os.path.join(MODELS_DIR, "isolation_forest.pkl")
        svm_path = os.path.join(MODELS_DIR, "one_class_svm.pkl")
        lof_path = os.path.join(MODELS_DIR, "lof.pkl")
        sc_path = os.path.join(MODELS_DIR, "scaler.pkl")

        if os.path.exists(if_path):
            try:
                with open(if_path, "rb") as f:
                    self.model_if = pickle.load(f)
            except Exception:
                pass

        if os.path.exists(svm_path):
            try:
                with open(svm_path, "rb") as f:
                    self.model_svm = pickle.load(f)
            except Exception:
                pass

        if os.path.exists(lof_path):
            try:
                with open(lof_path, "rb") as f:
                    self.model_lof = pickle.load(f)
            except Exception:
                pass

        if os.path.exists(sc_path):
            try:
                with open(sc_path, "rb") as f:
                    self.scaler = pickle.load(f)
            except Exception:
                pass

    @property
    def model(self):
        return self.model_if

    def reset(self):
        self.extractor.reset()

    def _evaluate_ml_models(self, X_scaled: np.ndarray) -> Dict[str, Any]:
        p_if, p_svm, p_lof = 0.05, 0.05, 0.05
        is_if, is_svm, is_lof = False, False, False

        if self.model_if is not None:
            dec_if = float(self.model_if.decision_function(X_scaled)[0])
            p_if = float(np.clip(1.0 / (1.0 + np.exp(dec_if * 12.0)), 0.01, 0.99))
            is_if = dec_if < 0.0

        if self.model_svm is not None:
            dec_svm = float(self.model_svm.decision_function(X_scaled)[0])
            p_svm = float(np.clip(1.0 / (1.0 + np.exp(dec_svm * 6.0)), 0.01, 0.99))
            is_svm = dec_svm < 0.0

        if self.model_lof is not None and hasattr(self.model_lof, "decision_function"):
            dec_lof = float(self.model_lof.decision_function(X_scaled)[0])
            p_lof = float(np.clip(1.0 / (1.0 + np.exp(dec_lof * 5.0)), 0.01, 0.99))
            is_lof = dec_lof < 0.0

        if self.mode == "isolation_forest":
            final_score = p_if
            final_outlier = is_if
            method_desc = "Isolation Forest (Single Model)"
        elif self.mode == "one_class_svm":
            final_score = p_svm
            final_outlier = is_svm
            method_desc = "One-Class SVM (Margin Boundary)"
        elif self.mode == "lof":
            final_score = p_lof
            final_outlier = is_lof
            method_desc = "Local Outlier Factor (Density Estimation)"
        elif self.mode == "majority_voting":
            votes = sum([int(is_if), int(is_svm), int(is_lof)])
            final_outlier = votes >= 2
            final_score = (p_if + p_svm + p_lof) / 3.0
            method_desc = f"Majority Voting ({votes}/3 Model Votes)"
        else:
            final_score = 0.50 * p_if + 0.30 * p_svm + 0.20 * p_lof
            final_outlier = final_score > 0.50
            method_desc = "Calibrated Score Fusion Ensemble (IF 50% + SVM 30% + LOF 20%)"

        return {
            "score": round(final_score, 4),
            "is_outlier": final_outlier,
            "method": method_desc,
            "p_if": round(p_if, 4),
            "p_svm": round(p_svm, 4),
            "p_lof": round(p_lof, 4)
        }

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
                "classification": "PROBABLE_SENSOR_FAULT",
                "root_cause": "COMMUNICATION_ERROR: Missing Sensor Payload / Telemetry Dropout",
                "culprit_sensor": "All Channels (Communication Loss)",
                "is_extreme_weather": False,
                **healing
            }

        if temp >= 90.0 or temp <= -40.0:
            healing = heal_observation(temp, rh, press, fault_type="HARDWARE_SENTINEL", culprit_sensor="Temperature", history=list(self.extractor.history))
            return {
                "is_anomaly": True,
                "anomaly_flag": 1,
                "severity": 0.98,
                "confidence": 1.0,
                "fused_anomaly_score": 0.98,
                "classification": "PROBABLE_SENSOR_FAULT",
                "root_cause": f"HARDWARE_SENTINEL: Temperature Sensor Open-Circuit ({temp}°C)",
                "culprit_sensor": "Temperature",
                "is_extreme_weather": False,
                **healing
            }

        if rh < 0.0 or rh > 105.0:
            healing = heal_observation(temp, rh, press, fault_type="HARDWARE_SENTINEL", culprit_sensor="Humidity", history=list(self.extractor.history))
            return {
                "is_anomaly": True,
                "anomaly_flag": 1,
                "severity": 0.92,
                "confidence": 0.99,
                "fused_anomaly_score": 0.92,
                "classification": "PROBABLE_SENSOR_FAULT",
                "root_cause": f"HARDWARE_SENTINEL: Capacitive Humidity Range Saturation ({rh}%)",
                "culprit_sensor": "Humidity",
                "is_extreme_weather": False,
                **healing
            }

        if press < 850.0 or press > 1080.0:
            healing = heal_observation(temp, rh, press, fault_type="HARDWARE_SENTINEL", culprit_sensor="Pressure", history=list(self.extractor.history))
            return {
                "is_anomaly": True,
                "anomaly_flag": 1,
                "severity": 0.95,
                "confidence": 0.99,
                "fused_anomaly_score": 0.95,
                "classification": "PROBABLE_SENSOR_FAULT",
                "root_cause": f"HARDWARE_SENTINEL: Barometric Transducer Saturation ({press} hPa)",
                "culprit_sensor": "Pressure",
                "is_extreme_weather": False,
                **healing
            }

        feats = self.extractor.push(temp=temp, rh=rh, press=press, timestamp=timestamp)

        frozen_channel = None
        if self.extractor.t_streak >= 3:
            frozen_channel = "Temperature"
        elif self.extractor.rh_streak >= 3:
            frozen_channel = "Humidity"
        elif self.extractor.p_streak >= 3:
            frozen_channel = "Pressure"

        if frozen_channel is not None:
            healing = heal_observation(temp, rh, press, fault_type="FROZEN_SENSOR", culprit_sensor=frozen_channel, history=list(self.extractor.history))
            return {
                "is_anomaly": True,
                "anomaly_flag": 1,
                "severity": 0.82,
                "confidence": 0.94,
                "fused_anomaly_score": 0.82,
                "classification": "PROBABLE_SENSOR_FAULT",
                "root_cause": f"FROZEN_SENSOR: Mechanical / ADC Stagnation on {frozen_channel} (Zero Variance Streak)",
                "culprit_sensor": frozen_channel,
                "is_extreme_weather": False,
                **healing
            }

        is_thunderstorm = (feats["pressure_rate"] < -2.0 and feats["humidity_rate"] > 10.0 and feats["temp_rate"] < -2.0)
        is_heatwave = (temp > 42.0 and rh < 35.0 and feats["dew_point_depression"] > 18.0)

        if is_thunderstorm:
            return {
                "is_anomaly": False,
                "anomaly_flag": 0,
                "severity": 0.15,
                "confidence": 0.95,
                "fused_anomaly_score": 0.15,
                "classification": "BENIGN_EXTREME",
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
                "severity": 0.18,
                "confidence": 0.94,
                "fused_anomaly_score": 0.18,
                "classification": "BENIGN_EXTREME",
                "root_cause": "GENUINE_METEOROLOGICAL_EVENT: Severe Summer Heatwave (Thermodynamically Verified)",
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

        if abs(feats["temp_rate"]) > 6.0:
            healing = heal_observation(temp, rh, press, fault_type="SPIKE", culprit_sensor="Temperature", history=list(self.extractor.history))
            return {
                "is_anomaly": True,
                "anomaly_flag": 1,
                "severity": 0.88,
                "confidence": 0.95,
                "fused_anomaly_score": 0.88,
                "classification": "PROBABLE_SENSOR_FAULT",
                "root_cause": f"SPIKE: Kinematic Rate-of-Change Limit Exceeded ({feats['temp_rate']:+.1f}°C in 30 min)",
                "culprit_sensor": "Temperature",
                "is_extreme_weather": False,
                **healing
            }

        if abs(feats["pressure_rate"]) > 12.0:
            healing = heal_observation(temp, rh, press, fault_type="SPIKE", culprit_sensor="Pressure", history=list(self.extractor.history))
            return {
                "is_anomaly": True,
                "anomaly_flag": 1,
                "severity": 0.86,
                "confidence": 0.92,
                "fused_anomaly_score": 0.86,
                "classification": "PROBABLE_SENSOR_FAULT",
                "root_cause": f"SPIKE: Unphysical Barometric Step Jump ({feats['pressure_rate']:+.1f} hPa in 30 min)",
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
                "classification": "PROBABLE_SENSOR_FAULT",
                "root_cause": f"PHYSICAL_INCONSISTENCY: Supersaturation Violation (Dew Point {feats['dew_point']}°C > Air Temp {temp}°C)",
                "culprit_sensor": "Humidity / Temperature",
                "is_extreme_weather": False,
                **healing
            }

        ml_eval = {"score": 0.05, "is_outlier": False, "method": "Rule Cascade"}
        if self.scaler is not None and (self.model_if is not None or self.model_svm is not None):
            X_df = pd.DataFrame([feats])[FEATURE_COLUMNS]
            X_scaled = self.scaler.transform(X_df)
            ml_eval = self._evaluate_ml_models(X_scaled)

        if ml_eval["is_outlier"]:
            healing = heal_observation(temp, rh, press, fault_type="MULTIVARIATE_ANOMALY", culprit_sensor="Temperature", history=list(self.extractor.history))
            return {
                "is_anomaly": True,
                "anomaly_flag": 1,
                "severity": ml_eval["score"],
                "confidence": 0.88,
                "fused_anomaly_score": ml_eval["score"],
                "classification": "PROBABLE_SENSOR_FAULT",
                "root_cause": f"MULTIVARIATE_ANOMALY: Outlier detected in 13D Phase Space via {ml_eval['method']}",
                "culprit_sensor": "Multi-Sensor Cluster",
                "is_extreme_weather": False,
                "ensemble_breakdown": ml_eval,
                **healing
            }

        return {
            "is_anomaly": False,
            "anomaly_flag": 0,
            "severity": ml_eval["score"],
            "confidence": 0.98,
            "fused_anomaly_score": ml_eval["score"],
            "classification": "NORMAL_TELEMETRY",
            "root_cause": "NOMINAL: Healthy Sensor Operation & Physical Consistency",
            "culprit_sensor": "NONE",
            "is_extreme_weather": False,
            "is_healed": False,
            "ensemble_breakdown": ml_eval,
            "corrected_temperature": temp,
            "corrected_humidity": rh,
            "corrected_pressure": press,
            "original_temperature": temp,
            "original_humidity": rh,
            "original_pressure": press
        }

    def detect_point(self, timestamp: Any, temp: float, rh: float, press: float):
        ts = pd.to_datetime(timestamp) if isinstance(timestamp, str) else timestamp
        res = self.diagnose_and_detect(temp, rh, press, timestamp=ts)

        class DetectionResult:
            def __init__(self, d):
                self.__dict__.update(d)
                self._d = d

            def __getitem__(self, k):
                return self._d[k]

            @property
            def affected_sensors(self):
                culprit = str(self._d.get("culprit_sensor", "")).lower()
                return [culprit] if culprit and culprit != "none" else []

        return DetectionResult(res)
