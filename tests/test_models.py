import os
import pickle
import pandas as pd
import numpy as np

from src.features.feature_engineering import FEATURE_COLUMNS
from src.api.services.inference_service import inference_service
from src.api.schemas.telemetry import TelemetryPointInput


def test_production_artifacts_exist():
    """Validates that all trained model artifacts exist on disk without loose JSON files."""
    assert os.path.exists("models/scaler.pkl"), "scaler.pkl missing"
    assert os.path.exists("models/isolation_forest.pkl"), "isolation_forest.pkl missing"
    assert os.path.exists("models/one_class_svm.pkl"), "one_class_svm.pkl missing"
    assert os.path.exists("models/lof.pkl"), "lof.pkl missing"


def test_isolation_forest_inference():
    """Tests model scoring and prediction on 13 meteorological domain features."""
    with open("models/scaler.pkl", "rb") as f:
        scaler = pickle.load(f)
    with open("models/isolation_forest.pkl", "rb") as f:
        model = pickle.load(f)

    # Clean normal meteorological observation
    sample = pd.DataFrame([{
        "temperature": 28.5,
        "humidity": 65.0,
        "pressure": 998.4,
        "dew_point": 21.3,
        "dew_point_depression": 7.2,
        "temp_rate": 0.2,
        "humidity_rate": -1.0,
        "pressure_rate": 0.1,
        "temp_dev": 0.3,
        "humidity_dev": 0.5,
        "pressure_dev": 0.2,
        "sin_hour": 0.5,
        "cos_hour": 0.86
    }])[FEATURE_COLUMNS]

    X_scaled = scaler.transform(sample)
    pred = model.predict(X_scaled)[0]
    score = float(model.decision_function(X_scaled)[0])

    assert pred == 1, f"Expected normal sample to be predicted as inlier (+1), got {pred}"
    assert isinstance(score, float)


def test_single_point_stream_inference():
    """Tests real-time single-point streaming inference."""
    payload = TelemetryPointInput(
        timestamp="2026-10-10 14:30:00",
        temperature=28.5,
        humidity=65.0,
        pressure=998.4
    )
    res = inference_service.infer_point(payload)

    assert res.classification in ["NORMAL_TELEMETRY", "ANOMALY_ALARM"]
    assert 0.0 <= res.fused_anomaly_score <= 1.0
    assert 0.0 <= res.confidence <= 1.0
    assert res.severity in ["NOMINAL", "WARNING", "MODERATE", "CRITICAL"]
