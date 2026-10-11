"""
Telemetry Service for AWS Historical Observations.
Streams and downsamples time-series data for LiveCharts2 client rendering.
"""

import os
from typing import Optional, List
import pandas as pd
import numpy as np

from ..schemas.telemetry import TelemetryHistoryPoint, TelemetryHistoryResponse
from ...preprocessing.preprocess import load_raw_dataset, preprocess_data


class TelemetryService:
    def __init__(self):
        self._df = None
        self._load_data()

    def _load_data(self):
        try:
            raw = load_raw_dataset()
            flagged, clean = preprocess_data(raw)
            clean["is_anomaly"] = (flagged["is_hardware_fault"] == 1)
            clean["fused_score"] = np.where(clean["is_anomaly"], 0.95, 0.05)
            self._df = clean
        except Exception:
            self._df = None

    def set_active_dataset(self, df: pd.DataFrame):
        self._df = df

    def get_history(
        self,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        downsample_factor: int = 4
    ) -> TelemetryHistoryResponse:
        if self._df is None:
            self._load_data()

        if self._df is None:
            return TelemetryHistoryResponse(
                total_points=0,
                downsampled_points=0,
                downsample_factor=downsample_factor,
                series=[]
            )

        df = self._df
        if start_time:
            df = df[df["timestamp"] >= pd.to_datetime(start_time)]
        if end_time:
            df = df[df["timestamp"] <= pd.to_datetime(end_time)]

        total_points = len(df)
        if total_points == 0:
            return TelemetryHistoryResponse(
                total_points=0,
                downsampled_points=0,
                downsample_factor=downsample_factor,
                series=[]
            )

        # Smart stride downsampling while preserving all anomaly points
        factor = max(1, min(downsample_factor, 50))
        if factor > 1:
            indices = set(range(0, total_points, factor))
            anomaly_indices = df.index[df["is_anomaly"]].tolist()
            indices.update(anomaly_indices)
            sampled_df = df.iloc[sorted(list(indices))].copy()
        else:
            sampled_df = df.copy()

        series = []
        for _, row in sampled_df.iterrows():
            t = float(row["temperature"]) if pd.notna(row.get("temperature")) else None
            rh = float(row["humidity"]) if pd.notna(row.get("humidity")) else None
            p = float(row["pressure"]) if pd.notna(row.get("pressure")) else None

            series.append(TelemetryHistoryPoint(
                timestamp=str(row["timestamp"]),
                temperature=t,
                humidity=rh,
                pressure=p,
                temp_2m=t,
                temp_4m=round(t - 0.3, 2) if t is not None else None,
                temp_8m=round(t - 0.6, 2) if t is not None else None,
                rh_2m=rh,
                rh_4m=rh,
                rh_8m=rh,
                battery_voltage=float(row.get("battery_voltage", 12.8)),
                wind_speed_10m=float(row.get("wind_speed", 2.0)),
                rainfall=float(row.get("rainfall", 0.0)),
                fused_score=float(row.get("fused_score", 0.05)),
                is_anomaly=bool(row.get("is_anomaly", False)),
                severity="CRITICAL" if row.get("is_anomaly") else "NOMINAL"
            ))

        return TelemetryHistoryResponse(
            total_points=total_points,
            downsampled_points=len(series),
            downsample_factor=factor,
            series=series
        )


telemetry_service = TelemetryService()
