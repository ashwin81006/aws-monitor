import os
import pandas as pd



def test_canonical_raw_dataset_exists():
    raw_path = "data/raw/aws_dataset.csv"
    assert os.path.exists(raw_path), f"Canonical dataset missing at {raw_path}"
    df = pd.read_csv(raw_path)
    assert len(df) == 23807, f"Expected 23,807 rows in canonical dataset, got {len(df)}"
    assert len(df.columns) == 37, f"Expected 37 raw columns, got {len(df.columns)}"


def test_required_columns_present():
    df = pd.read_csv("data/raw/aws_dataset.csv", nrows=10)
    required_cols = [
        "@STATION_ID",
        "DATE(IST)",
        "TIME(IST)",
        "AIR_TEMPERATURE1(°C at 2m height)",
        "AIR_TEMPERATURE2(°C at 4m height)",
        "AIR_TEMPERATURE3(°C at 8m height)",
        "RELATIVE_HUMIDITY1(% at 2m height)",
        "RELATIVE_HUMIDITY2(% at 4m height)",
        "RELATIVE_HUMIDITY3(% at 8m height)",
        "ATMOSPHERIC_PRESSURE(mbar) ",
        "BATTRY_VOLTAGE(V)"
    ]
    for col in required_cols:
        assert col in df.columns, f"Required column '{col}' missing from raw dataset"


def test_processed_clean_dataset():
    clean_path = "data/processed/aws_clean.csv"
    assert os.path.exists(clean_path), "Cleaned dataset data/processed/aws_clean.csv missing"
    df = pd.read_csv(clean_path, nrows=50)
    assert "timestamp" in df.columns, "timestamp column missing in cleaned dataset"
    assert "missing_any" in df.columns, "missing_any flag missing in cleaned dataset"
    assert "time_gap_minutes" in df.columns, "time_gap_minutes missing in cleaned dataset"
