"""
Preprocessing module for Automatic Weather Station (AWS) data.
Canonical station: ISRO0119_15F077 (VIT Vellore TN)

Extracts and validates core meteorological parameters:
  - Temperature (°C)
  - Atmospheric Pressure (hPa)
  - Relative Humidity (%)
Identifies ISRO hardware sentinels (e.g., 9999.0°C, -49.9°C) and missing data.
Provides clean baseline data for ML model training in-memory without dumping intermediate CSVs.
"""

import os
from typing import Tuple, Optional
import numpy as np
import pandas as pd

RAW_DATA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data", "raw", "aws_dataset.csv"
)

# Physical meteorological boundaries for Tamil Nadu / Tropical India
TEMP_MIN_VALID = 5.0      # °C
TEMP_MAX_VALID = 55.0     # °C
HUMIDITY_MIN_VALID = 5.0  # %
HUMIDITY_MAX_VALID = 100.0# %
PRESSURE_MIN_VALID = 900.0# hPa
PRESSURE_MAX_VALID = 1050.0# hPa

# Known ISRO hardware sentinels
SENTINEL_TEMP_VALUES = [9999.0, -49.9, -40.0, -99.0]


def load_raw_dataset(csv_path: Optional[str] = None) -> pd.DataFrame:
    """Loads the raw AWS dataset and ensures canonical column names."""
    path = csv_path or RAW_DATA_PATH
    if not os.path.exists(path):
        raise FileNotFoundError(f"Raw dataset not found at: {path}")

    df = pd.read_csv(path, low_memory=False)
    
    # Standardize column names
    col_map = {
        "AIR_TEMP(°C)": "temperature",
        "HUMIDITY(%)": "humidity",
        "ATMO_PRESSURE(hpa)": "pressure",
        "DATE(IST)": "date_ist",
        "TIME(IST)": "time_ist",
    }
    for old_col, new_col in col_map.items():
        if old_col in df.columns and new_col not in df.columns:
            df[new_col] = df[old_col]

    # Timestamp extraction if separate
    if "timestamp" not in df.columns and "date_ist" in df.columns and "time_ist" in df.columns:
        df["timestamp"] = pd.to_datetime(
            df["date_ist"].astype(str) + " " + df["time_ist"].astype(str),
            format="mixed",
            dayfirst=True
        )
    else:
        df["timestamp"] = pd.to_datetime(df["timestamp"])

    df = df.sort_values("timestamp").drop_duplicates(subset=["timestamp"]).reset_index(drop=True)

    # Ensure numeric types
    for col in ["temperature", "humidity", "pressure"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Compatibility aliases for legacy multi-height callers
    if "temp_2m" not in df.columns and "temperature" in df.columns:
        df["temp_2m"] = df["temperature"]
    if "rh_2m" not in df.columns and "humidity" in df.columns:
        df["rh_2m"] = df["humidity"]

    return df


def preprocess_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Identifies hardware sentinels and missing values.
    
    Returns:
        flagged_df: Raw dataframe augmented with explicit quality and sentinel flags.
        clean_df: Imputed, physically consistent dataframe ready for ML model fitting.
    """
    flagged = df.copy()

    # 1. Quality & Sentinel Flagging
    flagged["is_temp_sentinel"] = (
        flagged["temperature"].isin(SENTINEL_TEMP_VALUES) |
        (flagged["temperature"] > TEMP_MAX_VALID) |
        (flagged["temperature"] < TEMP_MIN_VALID) |
        flagged["temperature"].isna()
    ).astype(int)

    flagged["is_humidity_invalid"] = (
        (flagged["humidity"] < HUMIDITY_MIN_VALID) |
        (flagged["humidity"] > HUMIDITY_MAX_VALID) |
        flagged["humidity"].isna()
    ).astype(int)

    flagged["is_pressure_invalid"] = (
        (flagged["pressure"] < PRESSURE_MIN_VALID) |
        (flagged["pressure"] > PRESSURE_MAX_VALID) |
        flagged["pressure"].isna()
    ).astype(int)

    flagged["is_hardware_fault"] = (
        flagged["is_temp_sentinel"] |
        flagged["is_humidity_invalid"] |
        flagged["is_pressure_invalid"]
    ).astype(int)

    # Temporal gaps
    time_diff_min = flagged["timestamp"].diff().dt.total_seconds() / 60.0
    flagged["time_gap_minutes"] = time_diff_min.fillna(30.0)
    flagged["communication_gap"] = (flagged["time_gap_minutes"] > 120.0).astype(int)

    # 2. Build clean training dataset in memory
    clean_df = flagged.copy()
    
    # Mask sentinels as NaN, then forward-fill and back-fill with seasonal median
    clean_df.loc[clean_df["is_temp_sentinel"] == 1, "temperature"] = np.nan
    clean_df.loc[clean_df["is_humidity_invalid"] == 1, "humidity"] = np.nan
    clean_df.loc[clean_df["is_pressure_invalid"] == 1, "pressure"] = np.nan

    # Interpolate short gaps linearly, then median fill any remaining
    for col in ["temperature", "humidity", "pressure"]:
        clean_df[col] = clean_df[col].interpolate(method="linear", limit=10)
        clean_df[col] = clean_df[col].fillna(clean_df[col].median())

    # Keep aliases synchronized
    clean_df["temp_2m"] = clean_df["temperature"]
    clean_df["rh_2m"] = clean_df["humidity"]

    return flagged, clean_df


if __name__ == "__main__":
    print("=" * 60)
    print(" AWS PREPROCESSING & CANONICAL DATASET LOADER ")
    print("=" * 60)
    raw = load_raw_dataset()
    flagged, clean = preprocess_data(raw)
    print(f"Total Observations:    {len(raw):,}")
    print(f"Timestamp Range:       {raw['timestamp'].min()} to {raw['timestamp'].max()}")
    print(f"Hardware Sentinels:    {flagged['is_hardware_fault'].sum():,} ({flagged['is_hardware_fault'].mean()*100:.2f}%)")
    print(f"Communication Gaps:    {flagged['communication_gap'].sum():,}")
    print(f"Clean Temp Range:      {clean['temperature'].min():.1f}°C to {clean['temperature'].max():.1f}°C (Mean: {clean['temperature'].mean():.1f}°C)")
    print(f"Clean Humidity Range:  {clean['humidity'].min():.1f}% to {clean['humidity'].max():.1f}% (Mean: {clean['humidity'].mean():.1f}%)")
    print(f"Clean Pressure Range:  {clean['pressure'].min():.1f} hPa to {clean['pressure'].max():.1f} hPa (Mean: {clean['pressure'].mean():.1f} hPa)")
    print("=" * 60)
    print("Preprocessing completed successfully in-memory.")
