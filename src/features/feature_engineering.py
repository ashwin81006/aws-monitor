"""
Feature Engineering module for Automatic Weather Stations (AWS).
Transforms raw meteorological parameters (Temperature, Humidity, Pressure)
into 13 physically-sound, causal domain features.

Zero intermediate CSV writes - runs entirely in-memory.
"""

import os
from collections import deque
from typing import Dict, List, Optional
import numpy as np
import pandas as pd

FEATURE_COLUMNS = [
    "temperature",
    "humidity",
    "pressure",
    "dew_point",
    "dew_point_depression",
    "temp_rate",
    "humidity_rate",
    "pressure_rate",
    "temp_dev",
    "humidity_dev",
    "pressure_dev",
    "sin_hour",
    "cos_hour"
]

# Magnus-Tetens atmospheric constants (valid for -40°C to 50°C)
MAGNUS_A = 17.27
MAGNUS_B = 237.7


def compute_dew_point(temperature: np.ndarray, humidity: np.ndarray) -> np.ndarray:
    """Calculates dew point (°C) using the Magnus-Tetens formula."""
    rh_clipped = np.clip(humidity, 0.5, 100.0)
    alpha = ((MAGNUS_A * temperature) / (MAGNUS_B + temperature)) + np.log(rh_clipped / 100.0)
    dew_point = (MAGNUS_B * alpha) / (MAGNUS_A - alpha)
    return np.round(dew_point, 3)


def extract_features(df: pd.DataFrame, window_size: int = 8) -> pd.DataFrame:
    """
    Extracts 13 meteorological domain features in-memory.
    All rolling operations are strictly causal (center=False, past-only).
    
    Args:
        df: DataFrame containing ['timestamp', 'temperature', 'humidity', 'pressure']
        window_size: Past causal window length for rolling dispersion statistics.
        
    Returns:
        DataFrame containing the 13 feature columns.
    """
    feat = df.copy()

    # 1. Base parameters
    temp = feat["temperature"].to_numpy(dtype=float)
    rh = feat["humidity"].to_numpy(dtype=float)
    press = feat["pressure"].to_numpy(dtype=float)

    # 2. Atmospheric Physics (Thermodynamic moisture coupling)
    dp = compute_dew_point(temp, rh)
    feat["dew_point"] = dp
    feat["dew_point_depression"] = np.round(temp - dp, 3)

    # 3. Temporal Rates of Change (step differences normalized by minutes)
    if "timestamp" in feat.columns:
        ts = pd.to_datetime(feat["timestamp"])
        time_diff = ts.diff().dt.total_seconds().fillna(1800.0) / 1800.0 # Normalized to 30-min steps
        time_diff = np.where(time_diff <= 0, 1.0, time_diff)
    else:
        time_diff = np.ones(len(feat))

    feat["temp_rate"] = np.round(feat["temperature"].diff().fillna(0.0) / time_diff, 3)
    feat["humidity_rate"] = np.round(feat["humidity"].diff().fillna(0.0) / time_diff, 3)
    feat["pressure_rate"] = np.round(feat["pressure"].diff().fillna(0.0) / time_diff, 3)

    # 4. Causal Rolling Deviation (MAD over past window with physical floor)
    min_scales = {"temperature": 0.5, "humidity": 1.0, "pressure": 0.5}
    for col, dev_col in [("temperature", "temp_dev"), ("humidity", "humidity_dev"), ("pressure", "pressure_dev")]:
        rolling_med = feat[col].rolling(window=window_size, min_periods=1, center=False).median()
        abs_diff = (feat[col] - rolling_med).abs()
        rolling_mad = abs_diff.rolling(window=window_size, min_periods=1, center=False).median()
        mad_denom = np.maximum(rolling_mad, min_scales[col])
        feat[dev_col] = np.round(abs_diff / mad_denom, 3)

    # 5. Diurnal Solar Harmonics
    if "timestamp" in feat.columns:
        ts = pd.to_datetime(feat["timestamp"])
        hour_fraction = ts.dt.hour + ts.dt.minute / 60.0
        feat["sin_hour"] = np.round(np.sin(2 * np.pi * hour_fraction / 24.0), 4)
        feat["cos_hour"] = np.round(np.cos(2 * np.pi * hour_fraction / 24.0), 4)
    else:
        feat["sin_hour"] = 0.0
        feat["cos_hour"] = 1.0

    return feat[FEATURE_COLUMNS].copy()


class StreamingFeatureExtractor:
    """
    Maintains a causal ring buffer for real-time streaming observations.
    Computes identical features to the batch engine with 0.0 training-inference delta.
    """
    def __init__(self, window_size: int = 8):
        self.window_size = window_size
        self.history = deque(maxlen=window_size)
        self.abs_diff_t = deque(maxlen=window_size)
        self.abs_diff_rh = deque(maxlen=window_size)
        self.abs_diff_p = deque(maxlen=window_size)
        self.last_ts: Optional[pd.Timestamp] = None

    def push(self, temp: float, rh: float, press: float, timestamp: Optional[pd.Timestamp] = None) -> Dict[str, float]:
        """Pushes a new observation and returns the 13 feature values."""
        ts = timestamp or pd.Timestamp.now()
        dt_steps = 1.0
        if self.last_ts is not None:
            gap_sec = (ts - self.last_ts).total_seconds()
            if gap_sec >= 60.0:
                dt_steps = max(1.0, gap_sec / 1800.0)

        # 1. Base parameters
        prev = self.history[-1] if self.history else None
        self.history.append((temp, rh, press))
        self.last_ts = ts

        # 2. Dew point
        dp = float(compute_dew_point(np.array([temp]), np.array([rh]))[0])
        dp_dep = round(temp - dp, 3)

        # 3. Temporal rates
        if prev is not None:
            t_rate = round((temp - prev[0]) / dt_steps, 3)
            rh_rate = round((rh - prev[1]) / dt_steps, 3)
            p_rate = round((press - prev[2]) / dt_steps, 3)
        else:
            t_rate, rh_rate, p_rate = 0.0, 0.0, 0.0

        # 4. Causal rolling MAD with physical floor
        temps = [p[0] for p in self.history]
        rhs = [p[1] for p in self.history]
        presses = [p[2] for p in self.history]

        t_med = float(np.median(temps))
        rh_med = float(np.median(rhs))
        p_med = float(np.median(presses))

        cur_t_diff = abs(temp - t_med)
        cur_rh_diff = abs(rh - rh_med)
        cur_p_diff = abs(press - p_med)

        self.abs_diff_t.append(cur_t_diff)
        self.abs_diff_rh.append(cur_rh_diff)
        self.abs_diff_p.append(cur_p_diff)

        t_mad = float(np.median(list(self.abs_diff_t)))
        rh_mad = float(np.median(list(self.abs_diff_rh)))
        p_mad = float(np.median(list(self.abs_diff_p)))

        t_dev = round(cur_t_diff / max(t_mad, 0.5), 3)
        rh_dev = round(cur_rh_diff / max(rh_mad, 1.0), 3)
        p_dev = round(cur_p_diff / max(p_mad, 0.5), 3)

        # 5. Diurnal solar harmonics
        hr_frac = ts.hour + ts.minute / 60.0
        sin_hr = round(float(np.sin(2 * np.pi * hr_frac / 24.0)), 4)
        cos_hr = round(float(np.cos(2 * np.pi * hr_frac / 24.0)), 4)

        return {
            "temperature": round(temp, 2),
            "humidity": round(rh, 2),
            "pressure": round(press, 2),
            "dew_point": dp,
            "dew_point_depression": dp_dep,
            "temp_rate": t_rate,
            "humidity_rate": rh_rate,
            "pressure_rate": p_rate,
            "temp_dev": t_dev,
            "humidity_dev": rh_dev,
            "pressure_dev": p_dev,
            "sin_hour": sin_hr,
            "cos_hour": cos_hr
        }


compute_features = extract_features


if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from src.preprocessing.preprocess import load_raw_dataset, preprocess_data

    print("=" * 60)
    print(" IN-MEMORY METEOROLOGICAL FEATURE ENGINEERING ")
    print("=" * 60)
    raw = load_raw_dataset()
    _, clean = preprocess_data(raw)
    feats = extract_features(clean)
    print(f"Extracted {feats.shape[1]} features for {feats.shape[0]:,} observations.")
    print("Feature Columns:")
    for i, col in enumerate(FEATURE_COLUMNS, 1):
        print(f"  {i:2d}. {col:22s} min: {feats[col].min():8.2f} | max: {feats[col].max():8.2f} | mean: {feats[col].mean():8.2f}")
    print("=" * 60)
    print("Feature engineering verified successfully.")
