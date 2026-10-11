"""
Inference Service for AWS Anomaly Detection.
Wraps the unified detector, physical rules, and self-healing engine.
"""

import os
from datetime import datetime
from typing import Dict, Any

from ..schemas.telemetry import TelemetryPointInput, TelemetryInferenceResponse
from ...core.detector import AWSUnifiedDetector

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
MODELS_DIR = os.path.join(PROJECT_ROOT, "models")


class InferenceService:
    def __init__(self):
        self.detector = AWSUnifiedDetector()
        self.model_version = "1.0.0-PROD"
        self.status = "ONLINE" if self.detector.model is not None else "DEGRADED"

    def get_service_status(self) -> Dict[str, Any]:
        has_prod = self.detector.model is not None
        return {
            "status": "ONLINE" if has_prod else "DEGRADED",
            "model_version": self.model_version,
            "mode": "PRODUCTION" if has_prod else "DEMO_FALLBACK",
            "loaded_model": "Isolation Forest (13 Meteorological Features)",
            "features_count": 13,
            "calibration": "Calibrated with Thermodynamic Consistency"
        }

    def infer_point(self, payload: TelemetryPointInput) -> TelemetryInferenceResponse:
        ts_str = payload.timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        temp = payload.get_temperature()
        rh = payload.get_humidity()
        press = payload.get_pressure()

        diag = self.detector.diagnose_and_detect(temp=temp, rh=rh, press=press)

        is_anom = diag["is_anomaly"]
        sev_score = diag["severity"]

        if sev_score >= 0.85:
            sev_label = "CRITICAL"
        elif sev_score >= 0.50:
            sev_label = "MODERATE"
        elif sev_score >= 0.20:
            sev_label = "WARNING"
        else:
            sev_label = "NOMINAL"

        return TelemetryInferenceResponse(
            timestamp=ts_str,
            classification="ANOMALY_ALARM" if is_anom else "NORMAL_TELEMETRY",
            anomaly_probability=round(float(diag["fused_anomaly_score"]), 4),
            fused_anomaly_score=round(float(diag["fused_anomaly_score"]), 4),
            confidence=round(float(diag["confidence"]), 4),
            severity=sev_label,
            probable_root_cause=diag["root_cause"],
            root_cause=diag["root_cause"],
            affected_sensors=[diag["culprit_sensor"]] if is_anom else [],
            is_anomaly=is_anom,
            if_score=round(float(sev_score), 4),
            if_outlier=is_anom,
            evidence_breakdown={
                "fused_score": diag["fused_anomaly_score"],
                "culprit_sensor": diag["culprit_sensor"],
                "is_extreme_weather": diag.get("is_extreme_weather", False)
            },
            explanation=diag["root_cause"],
            corrected_temperature=diag.get("corrected_temperature"),
            corrected_humidity=diag.get("corrected_humidity"),
            corrected_pressure=diag.get("corrected_pressure"),
            is_healed=diag.get("is_healed", False),
            healing_method=diag.get("healing_method")
        )


inference_service = InferenceService()
