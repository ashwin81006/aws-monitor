import os
import sys
import pandas as pd

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

try:
    from src.features.feature_builder import compute_31_features_df, ML_31_FEATURES
except ImportError:
    from .feature_builder import compute_31_features_df, ML_31_FEATURES

# ==============================================================================
# FEATURE ENGINEERING PIPELINE (31 CLEAN CAUSAL METEOROLOGICAL FEATURES)
# ==============================================================================
# 1. 10 Base Monitored Channels (temp 2m/4m/8m, rh 2m/4m/8m, pressure, battery, wind, rain)
# 2. 6 Vertical Tower Gradients (boundary-layer thermodynamics across 2m, 4m, 8m)
# 3. 8 Temporal 30-min Rates of Change (step dynamics & jump detection, dt-normalized)
# 4. 5 Robust Causal Rolling Deviations (past-only window=9, no future leakage)
# 5. 2 Diurnal Solar Harmonics (sin/cos of hour of day)
# ==============================================================================


def build_features(
    input_file: str = "data/processed/aws_clean.csv",
    output_file: str = "data/processed/aws_features.csv"
) -> pd.DataFrame:
    print("=" * 65)
    print("   FEATURE ENGINEERING (31 CLEAN CAUSAL DOMAIN FEATURES)")
    print("=" * 65)

    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file not found: {input_file}")

    print(f"Loading cleaned dataset: {input_file}")
    df = pd.read_csv(input_file)
    print(f"Loaded {len(df)} rows.")

    print("\nComputing 31 causal domain features...")
    df_feat = compute_31_features_df(df, window_size=9)

    print(f"\nEngineered {len(ML_31_FEATURES)} clean domain-specific ML features:")
    for i, f in enumerate(ML_31_FEATURES, 1):
        print(f"  [{i:02d}] {f}")

    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    df_feat.to_csv(output_file, index=False)
    print(f"\nSaved feature dataset: {output_file} (Rows: {len(df_feat)}, Cols: {len(df_feat.columns)})")
    return df_feat


if __name__ == "__main__":
    build_features()