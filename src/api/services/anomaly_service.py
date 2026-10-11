import os
import pandas as pd
from typing import Optional, List, Dict, Any

from ..config import EVENT_FUSION_PATH, EVIDENCE_MATRIX_PATH, SHAP_EVENTS_PATH
from ..schemas.anomaly import AnomalyEvent, AnomalyEventDetail, AnomalyEventsResponse


class AnomalyService:
    def __init__(self):
        self._events_df = None
        self._evidence_df = None
        self._shap_df = None
        self._custom_events = None
        self._load_data()

    def set_active_events(self, events_list: List[AnomalyEvent]):
        self.set_active_dataset(events_list)

    def set_active_dataset(self, events_list: List[AnomalyEvent], evidence_df: Optional[pd.DataFrame] = None):
        self._custom_events = events_list
        self._evidence_df = evidence_df
        # Also build a dataframe representation
        if events_list:
            data = []
            for ev in events_list:
                data.append({
                    "event_id": ev.event_id,
                    "start_time": pd.to_datetime(ev.start_time),
                    "end_time": pd.to_datetime(ev.end_time),
                    "duration_minutes": ev.duration_minutes,
                    "observations": ev.observations,
                    "mean_fused_score": ev.mean_fused_score,
                    "peak_fused_score": ev.peak_fused_score,
                    "target_sensor": ev.target_sensor,
                    "candidate_class": ev.candidate_class,
                    "severity": ev.severity,
                    "confidence": ev.confidence,
                    "probable_root_cause": ev.probable_root_cause,
                    "has_station_system_evidence": False,
                    "has_core_sensor_quality": True,
                    "has_frozen_sensor": "FROZEN" in ev.probable_root_cause,
                    "has_cross_sensor_evidence": True,
                    "has_temporal_evidence": True,
                    "has_single_spike": "SPIKE" in ev.probable_root_cause,
                    "has_if_anomaly": True,
                    "peak_evidence_sources": 3,
                })
            self._events_df = pd.DataFrame(data)
        else:
            self._events_df = pd.DataFrame()

    def _load_data(self):
        if os.path.exists(EVENT_FUSION_PATH):
            df = pd.read_csv(EVENT_FUSION_PATH)
            df["start_time"] = pd.to_datetime(df["start_time"])
            df["end_time"] = pd.to_datetime(df["end_time"])
            self._events_df = df

        if os.path.exists(EVIDENCE_MATRIX_PATH):
            self._evidence_df = pd.read_csv(EVIDENCE_MATRIX_PATH)
            self._evidence_df["timestamp"] = pd.to_datetime(self._evidence_df["timestamp"])

        if os.path.exists(SHAP_EVENTS_PATH):
            self._shap_df = pd.read_csv(SHAP_EVENTS_PATH)

    def get_events(
        self,
        category: Optional[str] = None,
        severity: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> AnomalyEventsResponse:
        if self._events_df is None:
            self._load_data()

        if self._events_df is None or len(self._events_df) == 0:
            return AnomalyEventsResponse(
                total_events=0, limit=limit, offset=offset,
                counts_by_category={}, counts_by_severity={}, events=[]
            )

        df = self._events_df.copy()

        # Overall category counts
        cat_counts = df["candidate_class"].value_counts().to_dict()
        sev_counts = df["severity"].value_counts().to_dict()

        if category and category.upper() != "ALL":
            df = df[df["candidate_class"].str.upper() == category.upper()]

        if severity and severity.upper() != "ALL":
            df = df[df["severity"].str.upper() == severity.upper()]

        if search:
            s_low = search.lower()
            df = df[
                df["target_sensor"].str.lower().str.contains(s_low, na=False)
                | df["probable_root_cause"].str.lower().str.contains(s_low, na=False)
            ]

        total_filtered = len(df)
        paginated = df.iloc[offset : offset + limit]

        events_list = []
        for _, row in paginated.iterrows():
            events_list.append(
                AnomalyEvent(
                    event_id=int(row["event_id"]),
                    start_time=row["start_time"].strftime("%Y-%m-%d %H:%M:%S"),
                    end_time=row["end_time"].strftime("%Y-%m-%d %H:%M:%S"),
                    duration_minutes=float(row["duration_minutes"]),
                    observations=int(row["observations"]),
                    mean_fused_score=float(row["mean_fused_score"]),
                    peak_fused_score=float(row["peak_fused_score"]),
                    target_sensor=str(row["target_sensor"]),
                    candidate_class=str(row["candidate_class"]),
                    severity=str(row["severity"]),
                    confidence=float(row["confidence"]),
                    probable_root_cause=str(row["probable_root_cause"]),
                )
            )

        return AnomalyEventsResponse(
            total_events=total_filtered,
            limit=limit,
            offset=offset,
            counts_by_category=cat_counts,
            counts_by_severity=sev_counts,
            events=events_list
        )

    def get_event_detail(self, event_id: int) -> Optional[AnomalyEventDetail]:
        if self._events_df is None:
            self._load_data()

        if self._events_df is None:
            return None

        event_rows = self._events_df[self._events_df["event_id"] == event_id]
        if len(event_rows) == 0:
            return None

        row = event_rows.iloc[0]
        start_t = row["start_time"]
        end_t = row["end_time"]

        # Evidence breakdown
        rule_flags = []
        cross_delta = None
        temp_rate = None
        batt_lvl = None
        if_score = None

        if self._evidence_df is not None:
            sub = self._evidence_df[
                (self._evidence_df["timestamp"] >= start_t) & (self._evidence_df["timestamp"] <= end_t)
            ]
            if len(sub) > 0:
                if "temperature_spread" in sub.columns:
                    cross_delta = round(float(sub["temperature_spread"].max()), 2)
                if "temperature_rate" in sub.columns:
                    temp_rate = round(float(sub["temperature_rate"].max()), 2)
                if "battery_voltage" in sub.columns:
                    batt_lvl = round(float(sub["battery_voltage"].min()), 2)
                if "anomaly_score" in sub.columns:
                    if_score = round(float(sub["anomaly_score"].min()), 4)

                # Check triggered flags
                for col in sub.columns:
                    if col.startswith("rule_") and (sub[col] == 1).any():
                        rule_flags.append(col)

        # Top SHAP contributors if available
        top_shap = []
        explanation_text = f"Event #{event_id} ({row['candidate_class']}): Diagnosed as {row['probable_root_cause']} on {row['target_sensor']} with {row['confidence']*100:.0f}% confidence."

        if self._shap_df is not None:
            shap_sub = self._shap_df[self._shap_df["event_id"] == event_id]
            if len(shap_sub) > 0:
                s_row = shap_sub.iloc[0]
                if "plain_english_summary" in s_row and pd.notna(s_row["plain_english_summary"]):
                    explanation_text = str(s_row["plain_english_summary"])
                for i in range(1, 4):
                    f_name = s_row.get(f"top_feature_{i}")
                    f_val = s_row.get(f"top_value_{i}")
                    f_shap = s_row.get(f"top_shap_{i}")
                    if pd.notna(f_name) and str(f_name).strip():
                        top_shap.append({
                            "feature": str(f_name),
                            "value": float(f_val) if pd.notna(f_val) else 0.0,
                            "shap_attribution": float(f_shap) if pd.notna(f_shap) else 0.0
                        })

        return AnomalyEventDetail(
            event_id=int(row["event_id"]),
            start_time=row["start_time"].strftime("%Y-%m-%d %H:%M:%S"),
            end_time=row["end_time"].strftime("%Y-%m-%d %H:%M:%S"),
            duration_minutes=float(row["duration_minutes"]),
            observations=int(row["observations"]),
            mean_fused_score=float(row["mean_fused_score"]),
            peak_fused_score=float(row["peak_fused_score"]),
            target_sensor=str(row["target_sensor"]),
            candidate_class=str(row["candidate_class"]),
            severity=str(row["severity"]),
            confidence=float(row["confidence"]),
            probable_root_cause=str(row["probable_root_cause"]),
            evidence_breakdown={
                "has_station_system_evidence": bool(row["has_station_system_evidence"]),
                "has_core_sensor_quality": bool(row["has_core_sensor_quality"]),
                "has_frozen_sensor": bool(row["has_frozen_sensor"]),
                "has_cross_sensor_evidence": bool(row["has_cross_sensor_evidence"]),
                "has_temporal_evidence": bool(row["has_temporal_evidence"]),
                "has_single_spike": bool(row["has_single_spike"]),
                "has_if_anomaly": bool(row["has_if_anomaly"]),
                "peak_evidence_sources": int(row["peak_evidence_sources"]),
            },
            affected_sensors=[str(row["target_sensor"])] if row["target_sensor"] != "CORE_SENSORS" else ["temp_2m", "temp_4m", "rh_2m"],
            rule_flags=rule_flags,
            cross_sensor_delta=cross_delta,
            temporal_rate_max=temp_rate,
            battery_level=batt_lvl,
            if_score=if_score,
            explanation=explanation_text,
            top_shap_features=top_shap
        )


anomaly_service = AnomalyService()
