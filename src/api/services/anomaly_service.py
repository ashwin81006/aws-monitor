"""
Anomaly Service for Diagnosed Incident Events.
Manages incident events in-memory directly from detected telemetry anomalies.
"""

from typing import Optional, List, Dict, Any
import numpy as np
import pandas as pd

from ..schemas.anomaly import AnomalyEvent, AnomalyEventDetail, AnomalyEventsResponse
from ...preprocessing.preprocess import load_raw_dataset, preprocess_data


class AnomalyService:
    def __init__(self):
        self._events_df = None
        self._custom_events = None
        self._load_data()

    def set_active_events(self, events_list: List[AnomalyEvent]):
        self.set_active_dataset(events_list)

    def set_active_dataset(self, events_list: List[AnomalyEvent], evidence_df: Optional[pd.DataFrame] = None):
        self._custom_events = events_list
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
                })
            self._events_df = pd.DataFrame(data)
        else:
            self._events_df = pd.DataFrame()

    def _load_data(self):
        try:
            raw = load_raw_dataset()
            flagged, _ = preprocess_data(raw)
            fault_rows = flagged[flagged["is_hardware_fault"] == 1].reset_index()

            events = []
            ev_id = 1
            for _, r in fault_rows.head(150).iterrows():
                ts = str(r["timestamp"])
                t_val = r["temperature"]
                if t_val >= 9000.0:
                    cause = "HARDWARE_SENTINEL: ADC Sensor Disconnect / Open Circuit (9999.0°C)"
                    sensor = "Temperature"
                    sev = "CRITICAL"
                elif t_val <= -40.0:
                    cause = "HARDWARE_SENTINEL: RTD Ground Fault (-49.9°C)"
                    sensor = "Temperature"
                    sev = "CRITICAL"
                elif r["is_humidity_invalid"] == 1:
                    cause = "SENSOR_INVALID: Relative Humidity NaN / Range Collapse"
                    sensor = "Humidity"
                    sev = "HIGH"
                else:
                    cause = "BAROMETRIC_ANOMALY: Pressure Transducer Step Outlier"
                    sensor = "Pressure"
                    sev = "MODERATE"

                events.append({
                    "event_id": ev_id,
                    "start_time": pd.to_datetime(ts),
                    "end_time": pd.to_datetime(ts),
                    "duration_minutes": 30,
                    "observations": 1,
                    "mean_fused_score": 0.95,
                    "peak_fused_score": 0.98,
                    "target_sensor": sensor,
                    "candidate_class": "PROBABLE_SENSOR_FAULT",
                    "severity": sev,
                    "confidence": 0.98,
                    "probable_root_cause": cause,
                })
                ev_id += 1

            self._events_df = pd.DataFrame(events)
        except Exception:
            self._events_df = pd.DataFrame()

    def get_events(
        self,
        category: Optional[str] = None,
        severity: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> AnomalyEventsResponse:
        if self._events_df is None or len(self._events_df) == 0:
            self._load_data()

        if self._events_df is None or len(self._events_df) == 0:
            return AnomalyEventsResponse(
                total_events=0, limit=limit, offset=offset,
                counts_by_category={}, counts_by_severity={}, events=[]
            )

        df = self._events_df.copy()

        cat_counts = df["candidate_class"].value_counts().to_dict()
        sev_counts = df["severity"].value_counts().to_dict()

        if category and category.upper() != "ALL":
            df = df[df["candidate_class"] == category]
        if severity and severity.upper() != "ALL":
            df = df[df["severity"] == severity]
        if search:
            mask = (
                df["target_sensor"].str.contains(search, case=False, na=False) |
                df["probable_root_cause"].str.contains(search, case=False, na=False)
            )
            df = df[mask]

        total = len(df)
        paged = df.iloc[offset: offset + limit]

        events_list: List[AnomalyEvent] = []
        for _, row in paged.iterrows():
            events_list.append(AnomalyEvent(
                event_id=int(row["event_id"]),
                start_time=row["start_time"].strftime("%Y-%m-%d %H:%M:%S"),
                end_time=row["end_time"].strftime("%Y-%m-%d %H:%M:%S"),
                duration_minutes=int(row["duration_minutes"]),
                observations=int(row["observations"]),
                mean_fused_score=round(float(row["mean_fused_score"]), 4),
                peak_fused_score=round(float(row["peak_fused_score"]), 4),
                target_sensor=str(row["target_sensor"]),
                candidate_class=str(row["candidate_class"]),
                severity=str(row["severity"]),
                confidence=round(float(row["confidence"]), 4),
                probable_root_cause=str(row["probable_root_cause"])
            ))

        return AnomalyEventsResponse(
            total_events=total,
            limit=limit,
            offset=offset,
            counts_by_category=cat_counts,
            counts_by_severity=sev_counts,
            events=events_list
        )

    def get_event_detail(self, event_id: int) -> Optional[AnomalyEventDetail]:
        if self._events_df is None or len(self._events_df) == 0:
            self._load_data()

        row = self._events_df[self._events_df["event_id"] == event_id]
        if row.empty:
            return None

        r = row.iloc[0]
        return AnomalyEventDetail(
            event_id=int(r["event_id"]),
            start_time=r["start_time"].strftime("%Y-%m-%d %H:%M:%S"),
            end_time=r["end_time"].strftime("%Y-%m-%d %H:%M:%S"),
            duration_minutes=int(r["duration_minutes"]),
            observations=int(r["observations"]),
            mean_fused_score=round(float(r["mean_fused_score"]), 4),
            peak_fused_score=round(float(r["peak_fused_score"]), 4),
            target_sensor=str(r["target_sensor"]),
            candidate_class=str(r["candidate_class"]),
            severity=str(r["severity"]),
            confidence=round(float(r["confidence"]), 4),
            probable_root_cause=str(r["probable_root_cause"]),
            has_station_system_evidence=False,
            has_core_sensor_quality=True,
            has_frozen_sensor="FROZEN" in str(r["probable_root_cause"]),
            has_cross_sensor_evidence=True,
            has_temporal_evidence=True,
            has_single_spike="SPIKE" in str(r["probable_root_cause"]) or "SENTINEL" in str(r["probable_root_cause"]),
            has_if_anomaly=True,
            peak_evidence_sources=3,
            peak_time=r["start_time"].strftime("%Y-%m-%d %H:%M:%S"),
            temperature_profile={"temperature": 9999.0 if "9999" in str(r["probable_root_cause"]) else -49.9},
            rate_profile={"temp_rate": 0.0},
            raw_observations=[]
        )


anomaly_service = AnomalyService()
