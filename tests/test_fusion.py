import os
import pandas as pd



def test_evidence_matrix_structure():
    ev_path = "data/processed/aws_evidence_matrix.csv"
    assert os.path.exists(ev_path), "aws_evidence_matrix.csv missing"
    df = pd.read_csv(ev_path, nrows=50)

    required_cols = [
        "timestamp",
        "score_rule",
        "score_cross",
        "score_temporal",
        "score_ml",
        "fused_anomaly_score",
        "fused_anomaly_flag"
    ]
    for col in required_cols:
        assert col in df.columns, f"Required column '{col}' missing from evidence matrix"


    assert (df["fused_anomaly_score"] >= 0.0).all() and (df["fused_anomaly_score"] <= 1.0).all()
    assert set(df["fused_anomaly_flag"].unique()).issubset({0, 1})


def test_event_fusion_clustering():
    events_path = "data/processed/aws_event_fusion.csv"
    assert os.path.exists(events_path), "aws_event_fusion.csv missing"
    df = pd.read_csv(events_path, nrows=30)

    assert "event_id" in df.columns
    assert "duration_minutes" in df.columns
    assert "probable_root_cause" in df.columns
    assert "severity" in df.columns
