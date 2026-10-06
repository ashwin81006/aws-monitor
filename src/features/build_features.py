import os
import numpy as np
import pandas as pd

# ==============================================================================
# FEATURE ENGINEERING: CLEAN 31 DOMAIN-SPECIFIC METEOROLOGICAL FEATURES
# ==============================================================================
# 1. 10 Base Physical Channels (temp 2m/4m/8m, rh 2m/4m/8m, pressure, battery, wind, rain)
# 2. 6 Vertical Tower Gradients (boundary-layer thermodynamics across 2m, 4m, 8m)
# 3. 8 Temporal 30-min Rates of Change (step dynamics & jump detection)
# 4. 5 Robust Rolling Dispersion Deviations (normalized by MAD over 4.5h window)
# 5. 2 Diurnal Solar Harmonics (sin/cos of hour of day)
# ==============================================================================

input_file = "data/processed/aws_clean.csv"
output_file = "data/processed/aws_features.csv"

df = pd.read_csv(input_file)
df["timestamp"] = pd.to_datetime(df["timestamp"])
df = df.sort_values("timestamp").reset_index(drop=True)

# Ensure canonical column names are present
COLUMN_MAP = {
    "temp_2m": "AIR_TEMPERATURE1(°C at 2m height)",
    "temp_4m": "AIR_TEMPERATURE2(°C at 4m height)",
    "temp_8m": "AIR_TEMPERATURE3(°C at 8m height)",
    "rh_2m": "RELATIVE_HUMIDITY1(% at 2m height)",
    "rh_4m": "RELATIVE_HUMIDITY2(% at 4m height)",
    "rh_8m": "RELATIVE_HUMIDITY3(% at 8m height)",
    "wind_speed_3m": "WIND_SPEED1(m/s at 3m height) ",
    "wind_speed_6m": "WIND_SPEED2(m/s at 6m height)",
    "wind_speed_10m": "WIND_SPEED3(m/s at 10m height)",
    "wind_dir_3m": "WIND_DIRECTION1(deg at 3m height)",
    "wind_dir_6m": "WIND_DIRECTION2(deg at 6m height)",
    "wind_dir_10m": "WIND_DIRECTION3(deg at 10m height)",
    "pressure": "ATMOSPHERIC_PRESSURE(mbar) ",
    "battery_voltage": "BATTRY_VOLTAGE(V)",
    "rainfall": "RAINFALL(mm)",
}

for alias, raw_col in COLUMN_MAP.items():
    if alias not in df.columns and raw_col in df.columns:
        df[alias] = pd.to_numeric(df[raw_col], errors="coerce")

# Ensure time_gap_minutes exists
if "time_gap_minutes" not in df.columns:
    df["time_gap_minutes"] = df["timestamp"].diff().dt.total_seconds() / 60.0

# ------------------------------------------------------------------------------
# 1. BASE MONITORED CHANNELS (10 features)
# ------------------------------------------------------------------------------
base_features = [
    "temp_2m", "temp_4m", "temp_8m",
    "rh_2m", "rh_4m", "rh_8m",
    "pressure", "battery_voltage", "wind_speed_10m", "rainfall"
]

# ------------------------------------------------------------------------------
# 2. VERTICAL TOWER GRADIENTS (6 features)
# ------------------------------------------------------------------------------
df["diff_temp_2m_4m"] = df["temp_2m"] - df["temp_4m"]
df["diff_temp_4m_8m"] = df["temp_4m"] - df["temp_8m"]
df["diff_temp_2m_8m"] = df["temp_2m"] - df["temp_8m"]

df["diff_rh_2m_4m"] = df["rh_2m"] - df["rh_4m"]
df["diff_rh_4m_8m"] = df["rh_4m"] - df["rh_8m"]
df["diff_rh_2m_8m"] = df["rh_2m"] - df["rh_8m"]

gradient_features = [
    "diff_temp_2m_4m", "diff_temp_4m_8m", "diff_temp_2m_8m",
    "diff_rh_2m_4m", "diff_rh_4m_8m", "diff_rh_2m_8m"
]

# ------------------------------------------------------------------------------
# 3. TEMPORAL 30-MIN RATES OF CHANGE (8 features)
# ------------------------------------------------------------------------------
continuous_mask = (df["time_gap_minutes"] <= 60.0) & (df["time_gap_minutes"] > 0)
rate_cols = [
    ("rate_temp_2m", "temp_2m"),
    ("rate_temp_4m", "temp_4m"),
    ("rate_temp_8m", "temp_8m"),
    ("rate_rh_2m", "rh_2m"),
    ("rate_rh_4m", "rh_4m"),
    ("rate_rh_8m", "rh_8m"),
    ("rate_pressure", "pressure"),
    ("rate_battery", "battery_voltage"),
]

rate_features = []
for rate_name, base_col in rate_cols:
    diff_val = df[base_col].diff()
    # Normalize rate to per-30-minute interval
    rate = np.where(continuous_mask, diff_val / (df["time_gap_minutes"] / 30.0), np.nan)
    df[rate_name] = rate
    rate_features.append(rate_name)

# ------------------------------------------------------------------------------
# 4. ROBUST ROLLING DEVIATIONS (5 features)
# Window = 9 steps (4.5 hours centered)
# ------------------------------------------------------------------------------
dev_cols = [
    ("dev_temp_2m", "temp_2m"),
    ("dev_temp_4m", "temp_4m"),
    ("dev_temp_8m", "temp_8m"),
    ("dev_rh_2m", "rh_2m"),
    ("dev_pressure", "pressure"),
]

dispersion_features = []
window_size = 9
for dev_name, base_col in dev_cols:
    med = df[base_col].rolling(window=window_size, min_periods=3, center=True).median()
    abs_dev = np.abs(df[base_col] - med)
    mad = abs_dev.rolling(window=window_size, min_periods=3, center=True).median() * 1.4826
    # Robust z-score deviation
    df[dev_name] = np.where(mad > 1e-4, abs_dev / mad, abs_dev)
    dispersion_features.append(dev_name)

# ------------------------------------------------------------------------------
# 5. DIURNAL SOLAR HARMONICS (2 features)
# ------------------------------------------------------------------------------
hours = df["timestamp"].dt.hour + df["timestamp"].dt.minute / 60.0
df["solar_diurnal_sin"] = np.sin(2 * np.pi * hours / 24.0)
df["solar_diurnal_cos"] = np.cos(2 * np.pi * hours / 24.0)
diurnal_features = ["solar_diurnal_sin", "solar_diurnal_cos"]

# Total clean ML feature set: 10 + 6 + 8 + 5 + 2 = 31 features
ML_31_FEATURES = (
    base_features
    + gradient_features
    + rate_features
    + dispersion_features
    + diurnal_features
)

print(f"Engineered {len(ML_31_FEATURES)} clean domain-specific ML features:")
for i, f in enumerate(ML_31_FEATURES, 1):
    print(f"  [{i:02d}] {f}")

# Save features dataset
df.to_csv(output_file, index=False)
print(f"\nSaved feature dataset: {output_file} (Rows: {len(df)}, Cols: {len(df.columns)})")