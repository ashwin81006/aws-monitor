import os
import json
import joblib
import pandas as pd
import numpy as np
from sklearn.preprocessing import RobustScaler

# ==============================================================================
# ML DATA PREPARATION PIPELINE (31 CLEAN DOMAIN FEATURES)
# ==============================================================================
# 1. Selects the 31 clean domain-specific meteorological features.
# 2. Performs strict chronological 70/30 train/test split.
# 3. Imputes missing/infinite values using ONLY training medians (leakage prevention).
# 4. Fits RobustScaler on training features and transforms train & test sets.
# 5. Serializes scaler, medians, feature list, and scaled train/test datasets.
# ==============================================================================

INPUT_FEATURES_FILE = "data/processed/aws_features.csv"
TRAIN_SCALED_OUT = "data/processed/aws_train_scaled.csv"
TEST_SCALED_OUT = "data/processed/aws_test_scaled.csv"
SCALER_OUT = "models/scaler.pkl"
MEDIANS_OUT = "models/train_medians.pkl"
FEATURE_COLS_OUT = "models/ml_feature_columns.json"

ML_31_FEATURES = [
    # 1. Base monitored channels (10)
    "temp_2m", "temp_4m", "temp_8m",
    "rh_2m", "rh_4m", "rh_8m",
    "pressure", "battery_voltage", "wind_speed_10m", "rainfall",

    # 2. Multi-height vertical gradients (6)
    "diff_temp_2m_4m", "diff_temp_4m_8m", "diff_temp_2m_8m",
    "diff_rh_2m_4m", "diff_rh_4m_8m", "diff_rh_2m_8m",

    # 3. Temporal 30-min rates of change (8)
    "rate_temp_2m", "rate_temp_4m", "rate_temp_8m",
    "rate_rh_2m", "rate_rh_4m", "rate_rh_8m",
    "rate_pressure", "rate_battery",

    # 4. Robust rolling dispersion deviations (5)
    "dev_temp_2m", "dev_temp_4m", "dev_temp_8m",
    "dev_rh_2m", "dev_pressure",

    # 5. Diurnal solar harmonics (2)
    "solar_diurnal_sin", "solar_diurnal_cos",
]


def prepare_ml_data():
    print("=" * 60)
    print("      PREPARING MACHINE LEARNING DATA (31 CLEAN FEATURES)")
    print("=" * 60)

    print("\n[1/4] Loading engineered features...")
    df = pd.read_csv(INPUT_FEATURES_FILE)
    print(f"Loaded: {INPUT_FEATURES_FILE} ({len(df)} rows, {df.shape[1]} columns)")

    # Select the 31 clean features
    print("\n[2/4] Validating 31 domain feature set...")
    missing_features = [f for f in ML_31_FEATURES if f not in df.columns]
    if missing_features:
        raise ValueError(f"Missing required features in {INPUT_FEATURES_FILE}: {missing_features}")

    ml_df = df[ML_31_FEATURES].copy()
    print(f"  Selected features: {len(ML_31_FEATURES)}")

    # --------------------------------------------------
    # Chronological 70/30 Train/Test Split
    # --------------------------------------------------
    print("\n[3/4] Performing chronological 70/30 train/test split...")
    split_idx = int(len(ml_df) * 0.70)
    train_df = ml_df.iloc[:split_idx].copy()
    test_df = ml_df.iloc[split_idx:].copy()

    print(f"  Train set: {len(train_df)} rows ({len(train_df)/len(ml_df):.1%})")
    print(f"  Test set : {len(test_df)} rows ({len(test_df)/len(ml_df):.1%})")

    # Replace inf with nan
    train_df = train_df.replace([np.inf, -np.inf], np.nan)
    test_df = test_df.replace([np.inf, -np.inf], np.nan)

    # Compute training medians
    train_medians = train_df.median().fillna(0.0)
    train_df = train_df.fillna(train_medians)
    test_df = test_df.fillna(train_medians)

    # --------------------------------------------------
    # RobustScaler Fit & Transform
    # --------------------------------------------------
    print("\n[4/4] Fitting RobustScaler and transforming...")
    scaler = RobustScaler()
    train_scaled = pd.DataFrame(
        scaler.fit_transform(train_df),
        columns=ML_31_FEATURES,
        index=train_df.index
    )
    test_scaled = pd.DataFrame(
        scaler.transform(test_df),
        columns=ML_31_FEATURES,
        index=test_df.index
    )

    # Serialize artifacts
    os.makedirs("models", exist_ok=True)
    os.makedirs("data/processed", exist_ok=True)

    joblib.dump(scaler, SCALER_OUT)
    joblib.dump(train_medians, MEDIANS_OUT)
    with open(FEATURE_COLS_OUT, "w") as f:
        json.dump(ML_31_FEATURES, f, indent=2)

    train_scaled.to_csv(TRAIN_SCALED_OUT, index=False)
    test_scaled.to_csv(TEST_SCALED_OUT, index=False)

    print(f"  Saved Scaler:        {SCALER_OUT}")
    print(f"  Saved Medians:       {MEDIANS_OUT}")
    print(f"  Saved Feature List:  {FEATURE_COLS_OUT}")
    print(f"  Saved Train Scaled:  {TRAIN_SCALED_OUT} ({train_scaled.shape})")
    print(f"  Saved Test Scaled:   {TEST_SCALED_OUT} ({test_scaled.shape})")
    print("\nML Data Preparation Complete!")


if __name__ == "__main__":
    prepare_ml_data()