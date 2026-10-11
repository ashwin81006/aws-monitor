import os
import pandas as pd
from src.preprocessing.preprocess import load_raw_dataset, preprocess_data


def test_canonical_raw_dataset_exists():
    raw_path = "data/raw/aws_dataset.csv"
    assert os.path.exists(raw_path), f"Canonical dataset missing at {raw_path}"
    df = pd.read_csv(raw_path, nrows=50)
    assert len(df) > 0, "Canonical dataset is empty"


def test_required_columns_present():
    df = load_raw_dataset()
    required_cols = ["timestamp", "temperature", "humidity", "pressure"]
    for col in required_cols:
        assert col in df.columns, f"Required column '{col}' missing from raw dataset"


def test_processed_clean_dataset():
    raw = load_raw_dataset()
    flagged, clean = preprocess_data(raw.head(100))
    assert "timestamp" in clean.columns, "timestamp missing"
    assert "is_hardware_fault" in flagged.columns, "is_hardware_fault flag missing"
    assert "time_gap_minutes" in flagged.columns, "time_gap_minutes missing"
