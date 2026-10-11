"""
Feature Engineering Pipeline Wrapper.
Extracts 13 clean causal meteorological domain features.
"""

import os
import sys
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from src.features.feature_engineering import extract_features, FEATURE_COLUMNS


def build_features(df_or_path=None, output_file=None) -> pd.DataFrame:
    if isinstance(df_or_path, pd.DataFrame):
        df = df_or_path
    elif isinstance(df_or_path, str) and os.path.exists(df_or_path):
        df = pd.read_csv(df_or_path)
    else:
        from src.preprocessing.preprocess import load_raw_dataset, preprocess_data
        raw = load_raw_dataset()
        _, df = preprocess_data(raw)

    feat_df = extract_features(df)
    if output_file:
        feat_df.to_csv(output_file, index=False)
    return feat_df


if __name__ == "__main__":
    res = build_features()
    print(f"Features ready: {res.shape[1]} columns, {len(res):,} rows.")