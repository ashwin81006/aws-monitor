import json
import pandas as pd
import numpy as np


CLEAN_FILE = "data/processed/aws_clean.csv"
FEATURES_FILE = "data/processed/aws_features.csv"

CROSS_OUTPUT = "models/cross_sensor_thresholds.json"
TEMPORAL_OUTPUT = "models/temporal_thresholds.json"


TEMP_COLS = [
    "AIR_TEMPERATURE1(°C at 2m height)",
    "AIR_TEMPERATURE2(°C at 4m height)",
    "AIR_TEMPERATURE3(°C at 8m height)"
]

RH_COLS = [
    "RELATIVE_HUMIDITY1(% at 2m height)",
    "RELATIVE_HUMIDITY2(% at 4m height)",
    "RELATIVE_HUMIDITY3(% at 8m height)"
]


def calibrate_cross_sensor():
    df = pd.read_csv(FEATURES_FILE)
    train = df.iloc[:int(len(df) * 0.70)].copy()

    temperature = train[TEMP_COLS].copy()
    temperature = temperature.replace(-40, np.nan)

    humidity = train[RH_COLS].copy()
    humidity = humidity.where(
        (humidity >= 0) & (humidity <= 100),
        np.nan
    )

    temperature_spread = temperature.max(axis=1) - temperature.min(axis=1)
    humidity_spread = humidity.max(axis=1) - humidity.min(axis=1)

    temperature_spread = temperature_spread[
        temperature.notna().sum(axis=1) >= 2
    ].dropna()

    humidity_spread = humidity_spread[
        humidity.notna().sum(axis=1) >= 2
    ].dropna()

    thresholds = {
        "temperature_spread_99th_percentile": float(
            temperature_spread.quantile(0.99)
        ),
        "humidity_spread_99th_percentile": float(
            humidity_spread.quantile(0.99)
        )
    }

    with open(CROSS_OUTPUT, "w") as file:
        json.dump(thresholds, file, indent=4)

    print("--- CROSS-SENSOR CALIBRATION ---")
    print("Training rows:", len(train))
    print(
        "Temperature spread 99th percentile:",
        thresholds["temperature_spread_99th_percentile"],
        "°C"
    )
    print(
        "Humidity spread 99th percentile:",
        thresholds["humidity_spread_99th_percentile"],
        "%"
    )
    print("Saved:", CROSS_OUTPUT)


def calibrate_temporal():
    df = pd.read_csv(CLEAN_FILE)
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    train = df.iloc[:int(len(df) * 0.70)].copy()

    temperature = train[TEMP_COLS].replace(-40, np.nan)

    humidity = train[RH_COLS].where(
        (train[RH_COLS] >= 0) & (train[RH_COLS] <= 100),
        np.nan
    )

    train["temperature_median"] = temperature.median(axis=1)
    train["humidity_median"] = humidity.median(axis=1)

    train["time_gap_minutes"] = (
        train["timestamp"].diff().dt.total_seconds() / 60
    )

    valid_gap = (
        (train["time_gap_minutes"] > 0)
        & (train["time_gap_minutes"] <= 60)
    )

    train["temperature_rate"] = (
        train["temperature_median"].diff().abs()
        / (train["time_gap_minutes"] / 60)
    )

    train["humidity_rate"] = (
        train["humidity_median"].diff().abs()
        / (train["time_gap_minutes"] / 60)
    )

    train.loc[
        ~valid_gap,
        ["temperature_rate", "humidity_rate"]
    ] = np.nan

    train.loc[
        train["temperature_median"].isna()
        | train["temperature_median"].shift(1).isna(),
        "temperature_rate"
    ] = np.nan

    train.loc[
        train["humidity_median"].isna()
        | train["humidity_median"].shift(1).isna(),
        "humidity_rate"
    ] = np.nan

    thresholds = {
        "temperature_rate_99th_percentile": float(
            train["temperature_rate"].dropna().quantile(0.99)
        ),
        "humidity_rate_99th_percentile": float(
            train["humidity_rate"].dropna().quantile(0.99)
        )
    }

    with open(TEMPORAL_OUTPUT, "w") as file:
        json.dump(thresholds, file, indent=4)

    print("\n--- TEMPORAL CALIBRATION ---")
    print("Training rows:", len(train))
    print(
        "Temperature rate 99th percentile:",
        thresholds["temperature_rate_99th_percentile"],
        "°C/hour"
    )
    print(
        "Humidity rate 99th percentile:",
        thresholds["humidity_rate_99th_percentile"],
        "%/hour"
    )
    print("Saved:", TEMPORAL_OUTPUT)


def main():
    calibrate_cross_sensor()
    calibrate_temporal()
    print("\nThreshold calibration complete.")


if __name__ == "__main__":
    main()
