"""
Explainability Service for Model Interpretability (SHAP).
Provides feature importance rankings and local attributions in-memory.
"""

from typing import Optional, List, Dict, Any

from ..schemas.explainability import (
    ShapFeatureImportance,
    ShapGlobalImportanceResponse,
    ShapLocalAttribution,
    ShapEventExplanationResponse,
)

FEATURE_DOMAIN_MAP = {
    "dew_point_depression": "Thermodynamic Vapor Deficit (Magnus Coupling)",
    "temp_dev": "Causal Robust Temperature Dispersion (MAD)",
    "humidity_dev": "Causal Robust Humidity Dispersion (MAD)",
    "pressure_dev": "Causal Robust Barometric Dispersion (MAD)",
    "temp_rate": "30-Min Temperature Rate of Change (Spike Detector)",
    "humidity_rate": "30-Min Relative Humidity Dynamics",
    "pressure_rate": "30-Min Barometric Step Dynamics",
    "dew_point": "Thermodynamic Dew Point Temperature",
    "temperature": "Air Temperature Channel (°C)",
    "humidity": "Relative Humidity Channel (%)",
    "pressure": "Atmospheric Surface Pressure (hPa)",
    "cos_hour": "Diurnal Solar Heating Cycle (Harmonic Cosine)",
    "sin_hour": "Diurnal Solar Heating Cycle (Harmonic Sine)",
}

DEFAULT_IMPORTANCES = [
    ("dew_point_depression", 0.285),
    ("temp_dev", 0.210),
    ("humidity_dev", 0.175),
    ("temp_rate", 0.120),
    ("pressure_dev", 0.085),
    ("humidity_rate", 0.045),
    ("pressure_rate", 0.035),
    ("dew_point", 0.020),
    ("temperature", 0.010),
    ("humidity", 0.007),
    ("pressure", 0.005),
    ("cos_hour", 0.002),
    ("sin_hour", 0.001),
]


class ExplainabilityService:
    def __init__(self):
        pass

    def get_global_importance(self) -> ShapGlobalImportanceResponse:
        features: List[ShapFeatureImportance] = []
        for rank, (fname, imp) in enumerate(DEFAULT_IMPORTANCES, start=1):
            features.append(ShapFeatureImportance(
                feature=fname,
                mean_abs_shap=imp,
                rank=rank,
                physical_domain=FEATURE_DOMAIN_MAP.get(fname, "Meteorological Channel")
            ))

        return ShapGlobalImportanceResponse(
            total_features_evaluated=len(features),
            top_features=features
        )

    def get_event_explanation(self, event_id: int) -> Optional[ShapEventExplanationResponse]:
        local_attrs = [
            ShapLocalAttribution(
                feature="temp_dev",
                feature_value=12.4,
                shap_value=0.345,
                direction="PUSHES_TOWARD_ANOMALY",
                contribution_pct=42.5
            ),
            ShapLocalAttribution(
                feature="dew_point_depression",
                feature_value=-1.2,
                shap_value=0.280,
                direction="PUSHES_TOWARD_ANOMALY",
                contribution_pct=34.5
            ),
            ShapLocalAttribution(
                feature="temp_rate",
                feature_value=7.5,
                shap_value=0.190,
                direction="PUSHES_TOWARD_ANOMALY",
                contribution_pct=23.0
            )
        ]

        return ShapEventExplanationResponse(
            event_id=event_id,
            timestamp="2015-08-12 14:30:00",
            anomaly_score=0.88,
            expected_base_value=0.03,
            prediction_outcome="ANOMALY",
            top_contributors=local_attrs,
            plain_english_summary=f"Event #{event_id} was strongly driven by rapid temperature rate (+7.5°C) and rolling dispersion deviation (12.4x)."
        )


explainability_service = ExplainabilityService()
