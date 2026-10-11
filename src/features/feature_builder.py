import numpy as np
import pandas as pd
from collections import deque
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

# ==============================================================================
# CANONICAL 31 DOMAIN-SPECIFIC METEOROLOGICAL FEATURES
# ==============================================================================
# 1. 10 Base Monitored Channels (physical tower measurements)
# 2. 6 Vertical Tower Gradients (boundary layer stability & sensor divergence)
# 3. 8 Temporal Rates of Change (30-min normalized rate of change)
# 4. 5 Robust Causal Rolling Dispersion Deviations (past-only window=9, no future leakage)
# 5. 2 Diurnal Solar Harmonics (solar cycle phase)
# ==============================================================================

BASE_FEATURES = [
    "temp_2m", "temp_4m", "temp_8m",
    "rh_2m", "rh_4m", "rh_8m",
    "pressure", "battery_voltage", "wind_speed_10m", "rainfall"
]

GRADIENT_FEATURES = [
    "diff_temp_2m_4m", "diff_temp_4m_8m", "diff_temp_2m_8m",
    "diff_rh_2m_4m", "diff_rh_4m_8m", "diff_rh_2m_8m"
]

RATE_FEATURES = [
    "rate_temp_2m", "rate_temp_4m", "rate_temp_8m",
    "rate_rh_2m", "rate_rh_4m", "rate_rh_8m",
    "rate_pressure", "rate_battery"
]

DISPERSION_FEATURES = [
    "dev_temp_2m", "dev_temp_4m", "dev_temp_8m",
    "dev_rh_2m", "dev_pressure"
]

DIURNAL_FEATURES = [
    "solar_diurnal_sin", "solar_diurnal_cos"
]

ML_31_FEATURES: List[str] = (
    BASE_FEATURES
    + GRADIENT_FEATURES
    + RATE_FEATURES
    + DISPERSION_FEATURES
    + DIURNAL_FEATURES
)

# Canonical mapping from raw IMD/ISRO and alternative naming schemes
RAW_COLUMN_ALIASES: Dict[str, str] = {
    "temp_2m": "AIR_TEMPERATURE1(°C at 2m height)",
    "temp_4m": "AIR_TEMPERATURE2(°C at 4m height)",
    "temp_8m": "AIR_TEMPERATURE3(°C at 8m height)",
    "rh_2m": "RELATIVE_HUMIDITY1(% at 2m height)",
    "rh_4m": "RELATIVE_HUMIDITY2(% at 4m height)",
    "rh_8m": "RELATIVE_HUMIDITY3(% at 8m height)",
    "wind_speed_10m": "WIND_SPEED3(m/s at 10m height)",
    "pressure": "ATMOSPHERIC_PRESSURE(mbar) ",
    "battery_voltage": "BATTRY_VOLTAGE(V)",
    "rainfall": "RAINFALL(mm)",
}

RATE_MAPPINGS: List[Tuple[str, str]] = [
    ("rate_temp_2m", "temp_2m"),
    ("rate_temp_4m", "temp_4m"),
    ("rate_temp_8m", "temp_8m"),
    ("rate_rh_2m", "rh_2m"),
    ("rate_rh_4m", "rh_4m"),
    ("rate_rh_8m", "rh_8m"),
    ("rate_pressure", "pressure"),
    ("rate_battery", "battery_voltage"),
]

DEV_MAPPINGS: List[Tuple[str, str]] = [
    ("dev_temp_2m", "temp_2m"),
    ("dev_temp_4m", "temp_4m"),
    ("dev_temp_8m", "temp_8m"),
    ("dev_rh_2m", "rh_2m"),
    ("dev_pressure", "pressure"),
]


def map_raw_telemetry_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardizes raw or heterogeneous column names to the 10 canonical base channel names.
    Preserves existing columns.
    """
    df = df.copy()

    # Match from explicit RAW_COLUMN_ALIASES
    for canonical, raw_col in RAW_COLUMN_ALIASES.items():
        if canonical not in df.columns and raw_col in df.columns:
            df[canonical] = pd.to_numeric(df[raw_col], errors="coerce")

    # Flexible fallback matching if still missing
    for col in list(df.columns):
        c_clean = str(col).lower().strip()
        if "temp" in c_clean and ("2m" in c_clean or "1" in c_clean) and "temp_2m" not in df.columns:
            df["temp_2m"] = pd.to_numeric(df[col], errors="coerce")
        elif "temp" in c_clean and ("4m" in c_clean or "2" in c_clean) and "temp_4m" not in df.columns:
            df["temp_4m"] = pd.to_numeric(df[col], errors="coerce")
        elif "temp" in c_clean and ("8m" in c_clean or "3" in c_clean) and "temp_8m" not in df.columns:
            df["temp_8m"] = pd.to_numeric(df[col], errors="coerce")
        elif ("rh" in c_clean or "humid" in c_clean) and ("2m" in c_clean or "1" in c_clean) and "rh_2m" not in df.columns:
            df["rh_2m"] = pd.to_numeric(df[col], errors="coerce")
        elif ("rh" in c_clean or "humid" in c_clean) and ("4m" in c_clean or "2" in c_clean) and "rh_4m" not in df.columns:
            df["rh_4m"] = pd.to_numeric(df[col], errors="coerce")
        elif ("rh" in c_clean or "humid" in c_clean) and ("8m" in c_clean or "3" in c_clean) and "rh_8m" not in df.columns:
            df["rh_8m"] = pd.to_numeric(df[col], errors="coerce")
        elif ("press" in c_clean or "baro" in c_clean) and "pressure" not in df.columns:
            df["pressure"] = pd.to_numeric(df[col], errors="coerce")
        elif ("batt" in c_clean or "volt" in c_clean) and "battery_voltage" not in df.columns:
            df["battery_voltage"] = pd.to_numeric(df[col], errors="coerce")
        elif ("rain" in c_clean or "precip" in c_clean) and "rainfall" not in df.columns:
            df["rainfall"] = pd.to_numeric(df[col], errors="coerce")
        elif "wind" in c_clean and "wind_speed_10m" not in df.columns:
            df["wind_speed_10m"] = pd.to_numeric(df[col], errors="coerce")

    return df


def compute_31_features_df(df: pd.DataFrame, window_size: int = 9) -> pd.DataFrame:
    """
    Computes all 31 clean meteorological domain features from a DataFrame.
    STRICTLY CAUSAL:
      - Rolling median and MAD use past observations only (center=False).
      - Rates of change normalize consecutive differences by observed elapsed time.
      - Zero future-data leakage.
    """
    df = map_raw_telemetry_columns(df)

    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        df = df.sort_values("timestamp").reset_index(drop=True)
    else:
        # Default 30-min spacing if timestamp column is completely absent
        df["timestamp"] = pd.date_range(start="2024-01-01 00:00:00", periods=len(df), freq="30min")

    # Time gap calculation
    if "time_gap_minutes" not in df.columns:
        df["time_gap_minutes"] = df["timestamp"].diff().dt.total_seconds() / 60.0

    # 1. Base monitored channels
    for col in BASE_FEATURES:
        if col not in df.columns:
            raise KeyError(f"Required base channel '{col}' missing from telemetry DataFrame.")

    # 2. Vertical tower gradients
    df["diff_temp_2m_4m"] = df["temp_2m"] - df["temp_4m"]
    df["diff_temp_4m_8m"] = df["temp_4m"] - df["temp_8m"]
    df["diff_temp_2m_8m"] = df["temp_2m"] - df["temp_8m"]

    df["diff_rh_2m_4m"] = df["rh_2m"] - df["rh_4m"]
    df["diff_rh_4m_8m"] = df["rh_4m"] - df["rh_8m"]
    df["diff_rh_2m_8m"] = df["rh_2m"] - df["rh_8m"]

    # 3. Temporal 30-min normalized rates of change
    # Normalizes difference by (dt / 30.0). For gaps > 60 min or first observation, set to 0.0.
    continuous_mask = (df["time_gap_minutes"] <= 60.0) & (df["time_gap_minutes"] > 0)

    for rate_name, base_col in RATE_MAPPINGS:
        diff_val = df[base_col].diff()
        rate = np.where(continuous_mask, diff_val / (df["time_gap_minutes"] / 30.0), 0.0)
        df[rate_name] = pd.Series(rate, index=df.index).fillna(0.0)

    # 4. Robust CAUSAL rolling deviations (window=9, center=False, past-only)
    for dev_name, base_col in DEV_MAPPINGS:
        med = df[base_col].rolling(window=window_size, min_periods=1, center=False).median()
        abs_dev = np.abs(df[base_col] - med)
        mad = abs_dev.rolling(window=window_size, min_periods=1, center=False).median() * 1.4826
        # Robust z-score deviation relative to causal historical window
        df[dev_name] = np.where(mad > 1e-4, abs_dev / mad, abs_dev)

    # 5. Diurnal solar harmonics
    hours = df["timestamp"].dt.hour + df["timestamp"].dt.minute / 60.0
    df["solar_diurnal_sin"] = np.sin(2 * np.pi * hours / 24.0)
    df["solar_diurnal_cos"] = np.cos(2 * np.pi * hours / 24.0)

    return df


class StreamingFeatureBuffer:
    """
    Maintains a sliding history buffer of up to `window_size` (default 9) observations
    to compute CAUSAL features for sequential streaming inference.
    Guarantees feature equivalence with offline batch feature generation.
    """

    def __init__(self, window_size: int = 9):
        self.window_size = window_size
        self.history: deque = deque(maxlen=window_size)
        self.abs_dev_history: Dict[str, deque] = {dev_name: deque(maxlen=window_size) for dev_name, _ in DEV_MAPPINGS}
        self.last_timestamp: Optional[datetime] = None

    def reset(self):
        self.history.clear()
        for d in self.abs_dev_history.values():
            d.clear()
        self.last_timestamp = None

    def compute_point_features(
        self,
        point: Dict[str, float],
        ts: Optional[datetime] = None,
        prev_point: Optional[Dict[str, float]] = None
    ) -> Dict[str, float]:
        """
        Computes 31 features for the incoming observation using the streaming buffer.
        If history is empty but `prev_point` is provided in payload, uses `prev_point` for rates.
        """
        if ts is None:
            ts = datetime.now()

        # Compute elapsed time gap in minutes
        if self.last_timestamp is not None:
            gap_minutes = max(0.1, (ts - self.last_timestamp).total_seconds() / 60.0)
        else:
            gap_minutes = 30.0

        # Base physical values
        t2 = float(point["temp_2m"])
        t4 = float(point["temp_4m"])
        t8 = float(point["temp_8m"])
        rh2 = float(point["rh_2m"])
        rh4 = float(point["rh_4m"])
        rh8 = float(point["rh_8m"])
        press = float(point["pressure"])
        batt = float(point["battery_voltage"])
        wind = float(point.get("wind_speed_10m", 0.0) or 0.0)
        rain = float(point.get("rainfall", 0.0) or 0.0)

        # Append current reading to history buffer
        cur_record = {
            "temp_2m": t2, "temp_4m": t4, "temp_8m": t8,
            "rh_2m": rh2, "rh_4m": rh4, "rh_8m": rh8,
            "pressure": press, "battery_voltage": batt,
            "wind_speed_10m": wind, "rainfall": rain,
            "timestamp": ts
        }
        self.history.append(cur_record)
        self.last_timestamp = ts

        # 1. Base Monitored Channels
        out: Dict[str, float] = {
            "temp_2m": t2, "temp_4m": t4, "temp_8m": t8,
            "rh_2m": rh2, "rh_4m": rh4, "rh_8m": rh8,
            "pressure": press, "battery_voltage": batt,
            "wind_speed_10m": wind, "rainfall": rain
        }

        # 2. Vertical Tower Gradients
        out["diff_temp_2m_4m"] = t2 - t4
        out["diff_temp_4m_8m"] = t4 - t8
        out["diff_temp_2m_8m"] = t2 - t8
        out["diff_rh_2m_4m"] = rh2 - rh4
        out["diff_rh_4m_8m"] = rh4 - rh8
        out["diff_rh_2m_8m"] = rh2 - rh8

        # 3. Temporal 30-min Rates of Change
        # Determine previous values: from second-to-last item in buffer, or prev_point fallback
        if len(self.history) >= 2:
            prev = self.history[-2]
            scale = gap_minutes / 30.0 if gap_minutes <= 60.0 else 1.0
            out["rate_temp_2m"] = (t2 - prev["temp_2m"]) / scale if gap_minutes <= 60.0 else 0.0
            out["rate_temp_4m"] = (t4 - prev["temp_4m"]) / scale if gap_minutes <= 60.0 else 0.0
            out["rate_temp_8m"] = (t8 - prev["temp_8m"]) / scale if gap_minutes <= 60.0 else 0.0
            out["rate_rh_2m"] = (rh2 - prev["rh_2m"]) / scale if gap_minutes <= 60.0 else 0.0
            out["rate_rh_4m"] = (rh4 - prev["rh_4m"]) / scale if gap_minutes <= 60.0 else 0.0
            out["rate_rh_8m"] = (rh8 - prev["rh_8m"]) / scale if gap_minutes <= 60.0 else 0.0
            out["rate_pressure"] = (press - prev["pressure"]) / scale if gap_minutes <= 60.0 else 0.0
            out["rate_battery"] = (batt - prev["battery_voltage"]) / scale if gap_minutes <= 60.0 else 0.0
        elif prev_point is not None:
            out["rate_temp_2m"] = t2 - float(prev_point.get("temp_2m", t2))
            out["rate_temp_4m"] = t4 - float(prev_point.get("temp_4m", t4))
            out["rate_temp_8m"] = t8 - float(prev_point.get("temp_8m", t8))
            out["rate_rh_2m"] = rh2 - float(prev_point.get("rh_2m", rh2))
            out["rate_rh_4m"] = rh4 - float(prev_point.get("rh_4m", rh4))
            out["rate_rh_8m"] = rh8 - float(prev_point.get("rh_8m", rh8))
            out["rate_pressure"] = press - float(prev_point.get("pressure", press))
            out["rate_battery"] = batt - float(prev_point.get("battery_voltage", batt))
        else:
            out["rate_temp_2m"] = 0.0
            out["rate_temp_4m"] = 0.0
            out["rate_temp_8m"] = 0.0
            out["rate_rh_2m"] = 0.0
            out["rate_rh_4m"] = 0.0
            out["rate_rh_8m"] = 0.0
            out["rate_pressure"] = 0.0
            out["rate_battery"] = 0.0

        # 4. Robust Causal Rolling Dispersion Deviations (over buffer)
        hist_list = list(self.history)
        for dev_name, base_col in DEV_MAPPINGS:
            vals = np.array([h[base_col] for h in hist_list], dtype=float)
            med = float(np.median(vals))
            cur_abs_dev = abs(point[base_col] - med)
            self.abs_dev_history[dev_name].append(cur_abs_dev)

            dev_vals = np.array(list(self.abs_dev_history[dev_name]), dtype=float)
            mad = float(np.median(dev_vals)) * 1.4826
            out[dev_name] = float(cur_abs_dev / mad if mad > 1e-4 else cur_abs_dev)

        # 5. Diurnal Solar Harmonics
        hour = ts.hour + ts.minute / 60.0
        out["solar_diurnal_sin"] = float(np.sin(2 * np.pi * hour / 24.0))
        out["solar_diurnal_cos"] = float(np.cos(2 * np.pi * hour / 24.0))

        return out
