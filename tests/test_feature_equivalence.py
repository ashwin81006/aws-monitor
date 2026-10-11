import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from src.features.feature_builder import (
    compute_31_features_df,
    StreamingFeatureBuffer,
    ML_31_FEATURES,
)


def test_batch_vs_streaming_feature_equivalence():
    """
    Validates that the causal feature calculations in batch DataFrame processing
    and sequential streaming buffer yield identical numerical values across all 31 features.
    """
    np.random.seed(42)
    n_points = 15
    start_time = datetime(2024, 6, 1, 10, 0, 0)
    timestamps = [start_time + timedelta(minutes=30 * i) for i in range(n_points)]

    # Generate synthetic sequence
    records = []
    base_t = 29.0
    for i, ts in enumerate(timestamps):
        records.append({
            "timestamp": ts,
            "temp_2m": round(base_t + np.sin(i * 0.4) * 2.0, 2),
            "temp_4m": round(base_t + np.sin(i * 0.4) * 2.0 - 0.3, 2),
            "temp_8m": round(base_t + np.sin(i * 0.4) * 2.0 - 0.6, 2),
            "rh_2m": round(65.0 - np.sin(i * 0.4) * 5.0, 2),
            "rh_4m": round(66.0 - np.sin(i * 0.4) * 5.0, 2),
            "rh_8m": round(67.0 - np.sin(i * 0.4) * 5.0, 2),
            "pressure": round(1002.5 + i * 0.1, 2),
            "battery_voltage": round(13.4 - (i % 3) * 0.1, 2),
            "wind_speed_10m": round(2.5 + (i % 2) * 0.5, 2),
            "rainfall": 0.0 if i < 10 else 1.2
        })

    df = pd.DataFrame(records)

    # 1. Batch computation (causal past-only window=9)
    df_batch = compute_31_features_df(df.copy(), window_size=9)

    # 2. Sequential streaming buffer computation
    buffer = StreamingFeatureBuffer(window_size=9)
    stream_records = []
    for r in records:
        point_data = dict(r)
        ts_val = point_data.pop("timestamp")
        feat_stream = buffer.compute_point_features(point_data, ts=ts_val)
        stream_records.append(feat_stream)

    df_stream = pd.DataFrame(stream_records)

    # 3. Assert all 31 features exist in both
    for feat in ML_31_FEATURES:
        assert feat in df_batch.columns, f"Feature '{feat}' missing from batch output"
        assert feat in df_stream.columns, f"Feature '{feat}' missing from streaming output"

        # Compare values point-by-point
        b_vals = df_batch[feat].values.astype(float)
        s_vals = df_stream[feat].values.astype(float)

        np.testing.assert_allclose(
            b_vals,
            s_vals,
            rtol=1e-4,
            atol=1e-4,
            err_msg=f"Feature '{feat}' diverges between batch and streaming implementations!"
        )


def test_zero_future_data_leakage():
    """
    Validates that changing a future row (e.g. index 10) does NOT alter
    any feature values computed for preceding rows (indices 0 to 9).
    """
    start_time = datetime(2024, 6, 1, 10, 0, 0)
    timestamps = [start_time + timedelta(minutes=30 * i) for i in range(12)]

    records_original = []
    for i, ts in enumerate(timestamps):
        records_original.append({
            "timestamp": ts,
            "temp_2m": 30.0 + i * 0.2,
            "temp_4m": 29.8 + i * 0.2,
            "temp_8m": 29.5 + i * 0.2,
            "rh_2m": 60.0, "rh_4m": 61.0, "rh_8m": 62.0,
            "pressure": 1005.0, "battery_voltage": 13.0,
            "wind_speed_10m": 3.0, "rainfall": 0.0
        })

    records_altered = [dict(r) for r in records_original]
    # Alter future row 11 drastically
    records_altered[11]["temp_2m"] = -40.0
    records_altered[11]["pressure"] = 500.0

    df_orig = compute_31_features_df(pd.DataFrame(records_original), window_size=9)
    df_alt = compute_31_features_df(pd.DataFrame(records_altered), window_size=9)

    # For indices 0 to 10, all 31 features must be 100% IDENTICAL
    for feat in ML_31_FEATURES:
        orig_vals = df_orig.iloc[:11][feat].values.astype(float)
        alt_vals = df_alt.iloc[:11][feat].values.astype(float)
        np.testing.assert_array_equal(
            orig_vals,
            alt_vals,
            err_msg=f"Feature '{feat}' experienced future data leakage from row 11 into earlier rows!"
        )
