import os
from typing import Tuple, Optional
import numpy as np
import pandas as pd

RAW_DATA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data", "raw", "aws_dataset.csv"
)

TEMP_MIN_VALID = 5.0
TEMP_MAX_VALID = 55.0
HUMIDITY_MIN_VALID = 5.0
HUMIDITY_MAX_VALID = 100.0
PRESSURE_MIN_VALID = 900.0
PRESSURE_MAX_VALID = 1050.0

SENTINEL_TEMP_VALUES = [9999.0, -49.9, -40.0, -99.0]


def load_raw_dataset(csv_path: Optional[str] = None) -> pd.DataFrame:
    path = csv_path or RAW_DATA_PATH
    if not os.path.exists(path):
        raise FileNotFoundError(f"Raw dataset not found at: {path}")

    df = pd.read_csv(path, low_memory=False)
    
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

    if "timestamp" not in df.columns and "date_ist" in df.columns and "time_ist" in df.columns:
        df["timestamp"] = pd.to_datetime(
            df["date_ist"].astype(str) + " " + df["time_ist"].astype(str),
            format="mixed",
            dayfirst=True
        )
    else:
        df["timestamp"] = pd.to_datetime(df["timestamp"])

    df = df.sort_values("timestamp").drop_duplicates(subset=["timestamp"]).reset_index(drop=True)

    for col in ["temperature", "humidity", "pressure"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "temp_2m" not in df.columns and "temperature" in df.columns:
        df["temp_2m"] = df["temperature"]
    if "rh_2m" not in df.columns and "humidity" in df.columns:
        df["rh_2m"] = df["humidity"]

    return df


def preprocess_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    flagged = df.copy()

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

    time_diff_min = flagged["timestamp"].diff().dt.total_seconds() / 60.0
    flagged["time_gap_minutes"] = time_diff_min.fillna(30.0)
    flagged["communication_gap"] = (flagged["time_gap_minutes"] > 120.0).astype(int)

    clean_df = flagged.copy()
    
    clean_df.loc[clean_df["is_temp_sentinel"] == 1, "temperature"] = np.nan
    clean_df.loc[clean_df["is_humidity_invalid"] == 1, "humidity"] = np.nan
    clean_df.loc[clean_df["is_pressure_invalid"] == 1, "pressure"] = np.nan

    for col in ["temperature", "humidity", "pressure"]:
        clean_df[col] = clean_df[col].interpolate(method="linear", limit=10)
        clean_df[col] = clean_df[col].fillna(clean_df[col].median())

    clean_df["temp_2m"] = clean_df["temperature"]
    clean_df["rh_2m"] = clean_df["humidity"]

    return flagged, clean_df
