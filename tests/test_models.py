import os
import joblib
import pandas as pd
import numpy as np


from src.api.services.inference_service import inference_service
from src.api.schemas.telemetry import TelemetryPointInput


def test_production_artifacts_exist():
    assert os.path.exists("models/scaler.pkl"), "scaler.pkl missing"
    assert os.path.exists("models/isolation_forest.pkl"), "isolation_forest.pkl missing"
    assert os.path.exists("models/train_medians.pkl"), "train_medians.pkl missing"
    assert os.path.exists("models/cross_sensor_thresholds.json"), "cross_sensor_thresholds.json missing"
    assert os.path.exists("models/temporal_thresholds.json"), "temporal_thresholds.json missing"


def test_isolation_forest_inference():
    scaler = joblib.load("models/scaler.pkl")
    model = joblib.load("models/isolation_forest.pkl")

    # Clean normal point
    sample = pd.DataFrame([[
        28.5, 28.2, 27.9, 65.0, 66.2, 67.0, 998.4, 13.2, 2.5, 0.0,
        0.3, 0.3, 0.6, -1.2, -0.8, -2.0,
        0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
        0.0, 0.0, 0.0, 0.25, 0.66, 0.5, 0.86
    ]], columns=inference_service.feature_columns)

    X_scaled = scaler.transform(sample)
    pred = model.predict(X_scaled)[0]
    score = float(model.decision_function(X_scaled)[0])

    assert pred == 1, "Expected normal sample to be predicted as inlier (+1)"
    assert isinstance(score, float)


def test_single_point_stream_inference():
    payload = TelemetryPointInput(
        timestamp="2026-10-10 14:30:00",
        temp_2m=28.5,
        temp_4m=28.2,
        temp_8m=27.9,
        rh_2m=65.0,
        rh_4m=66.2,
        rh_8m=67.0,
        pressure=998.4,
        battery_voltage=13.2,
        rainfall=0.0,
        wind_speed_10m=2.4
    )
    res = inference_service.infer_point(payload)

    assert res.classification in ["NORMAL", "BENIGN_EXTREME", "PROBABLE_SENSOR_FAULT", "UNCERTAIN_WARNING"]
    assert 0.0 <= res.fused_anomaly_score <= 1.0
    assert 0.0 <= res.confidence <= 1.0
    assert res.severity in ["NONE", "LOW", "MEDIUM", "HIGH", "CRITICAL"]
