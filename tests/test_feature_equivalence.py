import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from src.features.feature_engineering import (
    FEATURE_COLUMNS,
    extract_features,
    StreamingFeatureExtractor,
)


def test_batch_vs_streaming_feature_equivalence():
    """
    Validates that the causal feature calculations in batch DataFrame processing
    and sequential streaming buffer yield identical numerical values across all 13 features.
    """
    np.random.seed(42)
    n_points = 15
    start_time = datetime(2024, 6, 1, 10, 0, 0)
    timestamps = [start_time + timedelta(minutes=30 * i) for i in range(n_points)]

    records = []
    base_t = 29.0
    for i, ts in enumerate(timestamps):
        records.append({
            "timestamp": ts,
            "temperature": round(base_t + np.sin(i * 0.4) * 2.0, 2),
            "humidity": round(65.0 - np.sin(i * 0.4) * 5.0, 2),
            "pressure": round(1002.5 + i * 0.1, 2),
        })

    df = pd.DataFrame(records)

    # 1. Batch computation (causal past-only window=8)
    df_batch = extract_features(df.copy(), window_size=8)

    # 2. Sequential streaming buffer computation
    extractor = StreamingFeatureExtractor(window_size=8)
    stream_records = []
    for r in records:
        feat_stream = extractor.push(
            temp=r["temperature"],
            rh=r["humidity"],
            press=r["pressure"],
            timestamp=r["timestamp"]
        )
        stream_records.append(feat_stream)

    df_stream = pd.DataFrame(stream_records)

    # 3. Assert all 13 features exist in both and compare point-by-point
    for feat in FEATURE_COLUMNS:
        assert feat in df_batch.columns, f"Feature '{feat}' missing from batch output"
        assert feat in df_stream.columns, f"Feature '{feat}' missing from streaming output"

        b_vals = df_batch[feat].values.astype(float)
        s_vals = df_stream[feat].values.astype(float)

        np.testing.assert_allclose(
            b_vals,
            s_vals,
            rtol=1e-3,
            atol=1e-3,
            err_msg=f"Feature '{feat}' diverges between batch and streaming implementations!"
        )


def test_zero_future_data_leakage():
    """
    Validates that altering a future row (e.g. index 11) does NOT alter
    any feature values computed for preceding rows (indices 0 to 10).
    """
    start_time = datetime(2024, 6, 1, 10, 0, 0)
    timestamps = [start_time + timedelta(minutes=30 * i) for i in range(12)]

    records_original = []
    for i, ts in enumerate(timestamps):
        records_original.append({
            "timestamp": ts,
            "temperature": 30.0 + i * 0.2,
            "humidity": 60.0 - (i % 3) * 1.0,
            "pressure": 1005.0 + (i % 2) * 0.5,
        })

    records_altered = [dict(r) for r in records_original]
    # Drastically alter future row 11
    records_altered[11]["temperature"] = -40.0
    records_altered[11]["pressure"] = 500.0

    df_orig = extract_features(pd.DataFrame(records_original), window_size=8)
    df_alt = extract_features(pd.DataFrame(records_altered), window_size=8)

    # For indices 0 to 10, all 13 features must be 100% IDENTICAL
    for feat in FEATURE_COLUMNS:
        orig_vals = df_orig.iloc[:11][feat].values.astype(float)
        alt_vals = df_alt.iloc[:11][feat].values.astype(float)
        np.testing.assert_array_equal(
            orig_vals,
            alt_vals,
            err_msg=f"Feature '{feat}' experienced future data leakage from row 11 into earlier rows!"
        )
