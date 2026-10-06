import os
import json
import joblib
import pandas as pd
import numpy as np
from sklearn.preprocessing import RobustScaler

# ==============================================================================
# ML DATA PREPARATION PIPELINE
# ==============================================================================
# 1. Selects the 112 machine learning features from engineered features.
# 2. Generates missingness indicators for raw sensor channels.
# 3. Performs strict chronological 70/30 train/test split.
# 4. Imputes continuous missing/infinite values using ONLY training medians.
# 5. Fits RobustScaler on continuous training features and transforms train & test.
# 6. Serializes scaler and outputs standardized scaled train/test datasets.
# ==============================================================================

INPUT_FEATURES_FILE = "data/processed/aws_features.csv"
TRAIN_SCALED_OUT = "data/processed/aws_train_scaled.csv"
TEST_SCALED_OUT = "data/processed/aws_test_scaled.csv"
SCALER_OUT = "models/scaler.pkl"
MEDIANS_OUT = "models/train_medians.pkl"
FEATURE_COLS_OUT = "models/ml_feature_columns.json"


def prepare_ml_data():
    print("=" * 60)
    print("           PREPARING MACHINE LEARNING DATA")
    print("=" * 60)

    print("\n[1/4] Loading engineered features...")
    df = pd.read_csv(INPUT_FEATURES_FILE)
    print(f"Loaded: {INPUT_FEATURES_FILE} ({len(df)} rows, {df.shape[1]} columns)")

    # --------------------------------------------------
    # 1. Feature Selection
    # --------------------------------------------------
    print("\n[2/4] Selecting ML feature groups...")
    base_features = ["time_gap_minutes"]

    raw_features = [
        "AIR_TEMPERATURE1(°C at 2m height)",
        "AIR_TEMPERATURE2(°C at 4m height)",
        "AIR_TEMPERATURE3(°C at 8m height)",
        "RELATIVE_HUMIDITY1(% at 2m height)",
        "RELATIVE_HUMIDITY2(% at 4m height)",
        "RELATIVE_HUMIDITY3(% at 8m height)",
        "WIND_SPEED1(m/s at 3m height) ",
        "WIND_SPEED2(m/s at 6m height)",
        "WIND_SPEED3(m/s at 10m height)",
        "ATMOSPHERIC_PRESSURE(mbar) ",
        "BATTRY_VOLTAGE(V)"
    ]

    temporal_features = [
        c for c in df.columns
        if c.endswith("_change")
        or c.endswith("_rate")
        or c.endswith("_rolling_mean")
        or c.endswith("_rolling_std")
    ]

    cross_sensor_features = [
        "temperature_valid_count",
        "temperature_mean",
        "temperature_spread",
        "humidity_valid_count",
        "humidity_mean",
        "humidity_spread"
    ] + [c for c in df.columns if c.endswith("_deviation")]

    repetition_features = [
        c for c in df.columns
        if c.endswith("_same_as_previous")
        or c.endswith("_repeat_count")
        or c.endswith("_repeat_duration_minutes")
    ]

    feature_columns = list(dict.fromkeys(
        base_features + raw_features + temporal_features + cross_sensor_features + repetition_features
    ))
    ml_df = df[feature_columns].copy()

    # Missingness indicators
    missing_columns = []
    for col in raw_features:
        name = col.split("(")[0].strip().replace(" ", "_") + "_missing"
        ml_df[name] = df[col].isna().astype(int)
        missing_columns.append(name)

    continuous_columns = [c for c in ml_df.columns if c not in missing_columns]
    print(f"  Total ML features   : {ml_df.shape[1]}")
    print(f"  Continuous features : {len(continuous_columns)}")
    print(f"  Missing indicators  : {len(missing_columns)}")

    # --------------------------------------------------
    # 2. Chronological 70/30 Split
    # --------------------------------------------------
    print("\n[3/4] Performing chronological 70/30 train/test split...")
    split_index = int(len(ml_df) * 0.70)
    train = ml_df.iloc[:split_index].copy().reset_index(drop=True)
    test = ml_df.iloc[split_index:].copy().reset_index(drop=True)
    print(f"  Training observations: {len(train)} (70%)")
    print(f"  Testing observations : {len(test)} (30%)")

    # --------------------------------------------------
    # 3. Imputation (Using ONLY Training Medians)
    # --------------------------------------------------
    # Replace inf with NaN
    train[continuous_columns] = train[continuous_columns].replace([np.inf, -np.inf], np.nan)
    test[continuous_columns] = test[continuous_columns].replace([np.inf, -np.inf], np.nan)

    # Calculate medians strictly on training split
    train_medians = train[continuous_columns].median()
    train[continuous_columns] = train[continuous_columns].fillna(train_medians)
    test[continuous_columns] = test[continuous_columns].fillna(train_medians)

    # --------------------------------------------------
    # 4. Robust Scaling (Fitted ONLY on Training Split)
    # --------------------------------------------------
    print("\n[4/4] Fitting RobustScaler and transforming features...")
    scaler = RobustScaler()
    scaler.fit(train[continuous_columns])

    train_scaled = train.copy()
    test_scaled = test.copy()
    train_scaled[continuous_columns] = scaler.transform(train[continuous_columns])
    test_scaled[continuous_columns] = scaler.transform(test[continuous_columns])

    # Save artifacts
    os.makedirs("models", exist_ok=True)
    os.makedirs("data/processed", exist_ok=True)

    joblib.dump(scaler, SCALER_OUT)
    joblib.dump(train_medians, MEDIANS_OUT)
    with open(FEATURE_COLS_OUT, "w") as f:
        json.dump(list(train.columns), f, indent=2)

    train_scaled.to_csv(TRAIN_SCALED_OUT, index=False)
    test_scaled.to_csv(TEST_SCALED_OUT, index=False)

    print("\nSaved artifacts:")
    print(f"  Scaler        : {SCALER_OUT}")
    print(f"  Train Medians : {MEDIANS_OUT}")
    print(f"  Feature Cols  : {FEATURE_COLS_OUT}")
    print(f"  Train Scaled  : {TRAIN_SCALED_OUT} ({train_scaled.shape})")
    print(f"  Test Scaled   : {TEST_SCALED_OUT} ({test_scaled.shape})")
    print("=" * 60)
    print("         ML DATA PREPARATION COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    prepare_ml_data()