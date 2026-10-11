import numpy as np
import pandas as pd

from src.features.feature_engineering import FEATURE_COLUMNS, compute_features


def test_13_meteorological_feature_columns():
    """Verifies that the feature specification has exactly 13 meteorological features."""
    assert len(FEATURE_COLUMNS) == 13, f"Expected 13 features, got {len(FEATURE_COLUMNS)}"
    expected = [
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
    for feat in expected:
        assert feat in FEATURE_COLUMNS, f"Expected feature '{feat}' missing in FEATURE_COLUMNS"


def test_in_memory_feature_computation():
    """Verifies in-memory feature engineering without dumping disk CSVs."""
    sample_df = pd.DataFrame({
        "timestamp": pd.date_range("2026-10-10 00:00:00", periods=20, freq="30min"),
        "temperature": [28.0 + (i % 5) * 0.5 for i in range(20)],
        "humidity": [65.0 - (i % 5) * 2.0 for i in range(20)],
        "pressure": [1005.0 + (i % 3) * 0.2 for i in range(20)],
    })

    feats_df = compute_features(sample_df)

    assert len(feats_df) == 20
    for col in FEATURE_COLUMNS:
        assert col in feats_df.columns, f"Feature column '{col}' missing from computed DataFrame"
        assert not feats_df[col].isna().any(), f"Computed feature column '{col}' contains NaNs"

    # Thermodynamic sanity: Dew point must be <= Temperature
    assert (feats_df["dew_point"] <= feats_df["temperature"] + 0.1).all(), "Dew point exceeds air temperature"
