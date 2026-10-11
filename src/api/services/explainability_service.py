import os
import json
import pandas as pd
from typing import Optional, List, Dict, Any

from ..config import SHAP_GLOBAL_PATH, SHAP_EVENTS_PATH
from ..schemas.explainability import (
    ShapFeatureImportance,
    ShapGlobalImportanceResponse,
    ShapLocalAttribution,
    ShapEventExplanationResponse,
)

FEATURE_DOMAIN_MAP = {
    "rainfall": "Precipitation / Gauge",
    "dev_pressure": "Barometric Surface Pressure",
    "diff_temp_2m_8m": "Vertical Tower Gradient",
    "dev_temp_8m": "Upper Tower Temperature",
    "temp_4m": "Mid-Level Temperature",
    "rate_temp_4m": "30-Min Temporal Dynamics",
    "wind_speed_10m": "Surface Anemometer",
    "temp_2m": "Surface Temperature",
    "diff_rh_2m_8m": "Tower Humidity Gradient",
    "dev_temp_4m": "Mid-Level Thermal Dispersion",
    "temp_8m": "Upper Tower Temperature",
    "rate_pressure": "Pressure Temporal Rate",
    "rate_temp_8m": "Upper Thermal Rate",
    "dev_rh_2m": "Surface Humidity Dispersion",
    "rate_battery": "Power Supply Voltage Rate",
    "battery_voltage": "Station Battery Voltage",
    "solar_diurnal_sin": "Diurnal Solar Cycle",
    "solar_diurnal_cos": "Diurnal Solar Cycle",
}


class ExplainabilityService:
    def __init__(self):
        self._global_df = None
        self._events_df = None
        self._summary_meta = None
        self._load_data()

    def _load_data(self):
        if os.path.exists(SHAP_GLOBAL_PATH):
            try:
                self._global_df = pd.read_csv(SHAP_GLOBAL_PATH)
            except Exception:
                self._global_df = None
        if os.path.exists(SHAP_EVENTS_PATH):
            try:
                self._events_df = pd.read_csv(SHAP_EVENTS_PATH)
            except Exception:
                self._events_df = None

        summary_path = "data/processed/aws_event_explanations_summary.json"
        if os.path.exists(summary_path):
            try:
                with open(summary_path, "r") as f:
                    self._summary_meta = json.load(f)
            except Exception:
                self._summary_meta = None

    def get_global_importance(self) -> ShapGlobalImportanceResponse:
        self._load_data()

        if self._global_df is not None and len(self._global_df) > 0:
            features = []
            for _, row in self._global_df.iterrows():
                f_name = str(row["feature"])
                domain = FEATURE_DOMAIN_MAP.get(f_name, "Meteorological Dynamics")
                features.append(
                    ShapFeatureImportance(
                        feature=f_name,
                        mean_abs_shap=round(float(row["mean_abs_shap"]), 5),
                        rank=int(row["rank"]),
                        physical_domain=domain
                    )
                )
            return ShapGlobalImportanceResponse(
                total_features_evaluated=len(features),
                top_features=features
            )

        # Return empty list when artifacts are not generated, avoiding fabricated data
        return ShapGlobalImportanceResponse(
            total_features_evaluated=0,
            top_features=[]
        )

    def get_event_explanation(self, event_id: int) -> Optional[ShapEventExplanationResponse]:
        self._load_data()

        if self._events_df is None or len(self._events_df) == 0:
            return None

        sub = self._events_df[self._events_df["event_id"] == event_id]
        if len(sub) == 0:
            return None

        row = sub.iloc[0]
        contributors = []

        total_shap_mass = 0.0
        for i in range(1, 4):
            f_name = row.get(f"top_feature_{i}")
            f_val = row.get(f"top_value_{i}")
            f_shap = row.get(f"top_shap_{i}")
            if pd.notna(f_name) and str(f_name).strip():
                val = float(f_val) if pd.notna(f_val) else 0.0
                shap_val = float(f_shap) if pd.notna(f_shap) else 0.0
                direction = "ANOMALOUS_OUTLIER" if shap_val > 0 else "NORMALIZING"
                contributors.append({
                    "feature": str(f_name),
                    "feature_value": round(val, 2),
                    "shap_value": round(shap_val, 4),
                    "direction": direction,
                    "abs_shap": abs(shap_val)
                })
                total_shap_mass += abs(shap_val)

        final_contributors = []
        for c in contributors:
            pct = (c["abs_shap"] / total_shap_mass * 100.0) if total_shap_mass > 0 else 33.3
            final_contributors.append(
                ShapLocalAttribution(
                    feature=c["feature"],
                    feature_value=c["feature_value"],
                    shap_value=c["shap_value"],
                    direction=c["direction"],
                    contribution_pct=round(pct, 1)
                )
            )

        summary_text = (
            str(row["plain_english_summary"])
            if "plain_english_summary" in row and pd.notna(row["plain_english_summary"])
            else f"Event #{event_id} flagged by Isolation Forest."
        )

        base_val = 0.0
        if self._summary_meta and "expected_value" in self._summary_meta:
            base_val = float(self._summary_meta["expected_value"])
        elif "expected_base_value" in row and pd.notna(row["expected_base_value"]):
            base_val = float(row["expected_base_value"])

        anomaly_score = float(row.get("peak_fused_score", row.get("mean_fused_score", 0.0)))

        return ShapEventExplanationResponse(
            event_id=int(row["event_id"]),
            timestamp=str(row.get("start_time", "N/A")),
            anomaly_score=round(anomaly_score, 4),
            expected_base_value=round(base_val, 4),
            prediction_outcome=str(row.get("candidate_class", "PROBABLE_SENSOR_FAULT")),
            top_contributors=final_contributors,
            plain_english_summary=summary_text
        )


explainability_service = ExplainabilityService()
