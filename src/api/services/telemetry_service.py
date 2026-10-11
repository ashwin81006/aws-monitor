import os
import numpy as np
import pandas as pd
from typing import Optional, List

from ..config import FEATURES_DATA_PATH, EVIDENCE_MATRIX_PATH
from ..schemas.telemetry import TelemetryHistoryPoint, TelemetryHistoryResponse


class TelemetryService:
    def __init__(self):
        self._df = None
        self._load_data()

    def _load_data(self):
        if not os.path.exists(FEATURES_DATA_PATH):
            return

        df = pd.read_csv(FEATURES_DATA_PATH)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.sort_values("timestamp").reset_index(drop=True)

        if os.path.exists(EVIDENCE_MATRIX_PATH):
            ev_df = pd.read_csv(EVIDENCE_MATRIX_PATH, usecols=["timestamp", "fused_anomaly_score", "fused_anomaly_flag"])
            ev_df["timestamp"] = pd.to_datetime(ev_df["timestamp"])
            df = df.merge(ev_df, on="timestamp", how="left")
            df["fused_anomaly_score"] = df["fused_anomaly_score"].fillna(0.0)
            df["fused_anomaly_flag"] = df["fused_anomaly_flag"].fillna(0).astype(int)
        else:
            df["fused_anomaly_score"] = 0.0
            df["fused_anomaly_flag"] = 0

        self._df = df

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

        total_pts = len(df)
        if total_pts == 0:
            return TelemetryHistoryResponse(
                total_points=0,
                downsampled_points=0,
                downsample_factor=downsample_factor,
                series=[]
            )

        # Smart downsampling: keep every Nth row, PLUS all anomaly rows
        factor = max(1, downsample_factor)
        if factor > 1:
            step_mask = (np.arange(len(df)) % factor == 0)
            anomaly_mask = (df["fused_anomaly_flag"] == 1).values
            keep_mask = step_mask | anomaly_mask
            filtered = df[keep_mask].copy()
        else:
            filtered = df.copy()

        points = []
        for _, row in filtered.iterrows():
            ts_str = row["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
            is_anom = bool(row["fused_anomaly_flag"] == 1)
            score = round(float(row["fused_anomaly_score"]), 4)

            points.append(
                TelemetryHistoryPoint(
                    timestamp=ts_str,
                    temp_2m=float(row["temp_2m"]) if pd.notna(row.get("temp_2m")) else None,
                    temp_4m=float(row["temp_4m"]) if pd.notna(row.get("temp_4m")) else None,
                    temp_8m=float(row["temp_8m"]) if pd.notna(row.get("temp_8m")) else None,
                    rh_2m=float(row["rh_2m"]) if pd.notna(row.get("rh_2m")) else None,
                    rh_4m=float(row["rh_4m"]) if pd.notna(row.get("rh_4m")) else None,
                    rh_8m=float(row["rh_8m"]) if pd.notna(row.get("rh_8m")) else None,
                    pressure=float(row["pressure"]) if pd.notna(row.get("pressure")) else None,
                    battery_voltage=float(row["battery_voltage"]) if pd.notna(row.get("battery_voltage")) else None,
                    wind_speed_10m=float(row["wind_speed_10m"]) if pd.notna(row.get("wind_speed_10m")) else None,
                    rainfall=float(row["rainfall"]) if pd.notna(row.get("rainfall")) else None,
                    is_anomaly=is_anom,
                    fused_score=score,
                    classification="ANOMALY" if is_anom else "NORMAL"
                )
            )

        return TelemetryHistoryResponse(
            total_points=total_pts,
            downsampled_points=len(points),
            downsample_factor=factor,
            series=points
        )


telemetry_service = TelemetryService()
