import os
import json
import pandas as pd



def test_31_ml_feature_columns():
    feature_meta_path = "models/ml_feature_columns.json"
    assert os.path.exists(feature_meta_path), "ml_feature_columns.json missing"
    with open(feature_meta_path, "r") as f:
        features = json.load(f)

    assert len(features) == 31, f"Expected exactly 31 features, got {len(features)}"
    expected_core = [
        "temp_2m", "temp_4m", "temp_8m",
        "rh_2m", "rh_4m", "rh_8m",
        "pressure", "battery_voltage", "wind_speed_10m", "rainfall",
        "diff_temp_2m_4m", "diff_temp_4m_8m", "diff_temp_2m_8m",
        "diff_rh_2m_4m", "diff_rh_4m_8m", "diff_rh_2m_8m",
        "rate_temp_2m", "rate_temp_4m", "rate_temp_8m",
        "rate_rh_2m", "rate_rh_4m", "rate_rh_8m",
        "rate_pressure", "rate_battery",
        "dev_temp_2m", "dev_temp_4m", "dev_temp_8m",
        "dev_rh_2m", "dev_pressure",
        "solar_diurnal_sin", "solar_diurnal_cos"
    ]
    for feat in expected_core:
        assert feat in features, f"Expected feature '{feat}' missing in feature specification"


def test_processed_features_file():
    feat_path = "data/processed/aws_features.csv"
    assert os.path.exists(feat_path), "aws_features.csv missing"
    df = pd.read_csv(feat_path, nrows=20)
    assert len(df) == 20
    assert "diff_temp_2m_8m" in df.columns
    assert "rate_temp_4m" in df.columns
    assert "solar_diurnal_sin" in df.columns
