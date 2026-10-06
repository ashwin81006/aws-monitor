import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

MODELS_DIR = os.path.join(BASE_DIR, "models")
DATA_DIR = os.path.join(BASE_DIR, "data", "processed")
REPORTS_DIR = os.path.join(BASE_DIR, "reports", "figures")

# Models & calibration
SCALER_PATH = os.path.join(MODELS_DIR, "scaler.pkl")
MEDIANS_PATH = os.path.join(MODELS_DIR, "train_medians.pkl")
FEATURE_COLS_PATH = os.path.join(MODELS_DIR, "ml_feature_columns.json")
IF_MODEL_PATH = os.path.join(MODELS_DIR, "isolation_forest.pkl")
LOF_MODEL_PATH = os.path.join(MODELS_DIR, "lof_model.pkl")
OCSVM_MODEL_PATH = os.path.join(MODELS_DIR, "ocsvm_model.pkl")
CROSS_THRESHOLDS_PATH = os.path.join(MODELS_DIR, "cross_sensor_thresholds.json")
TEMPORAL_THRESHOLDS_PATH = os.path.join(MODELS_DIR, "temporal_thresholds.json")

# Processed datasets
CLEAN_DATA_PATH = os.path.join(DATA_DIR, "aws_clean.csv")
FEATURES_DATA_PATH = os.path.join(DATA_DIR, "aws_features.csv")
EVIDENCE_MATRIX_PATH = os.path.join(DATA_DIR, "aws_evidence_matrix.csv")
EVENT_FUSION_PATH = os.path.join(DATA_DIR, "aws_event_fusion.csv")
MODEL_COMPARISON_PATH = os.path.join(DATA_DIR, "aws_model_comparison.csv")
MODEL_METRICS_PATH = os.path.join(DATA_DIR, "aws_model_comparison_metrics.json")
SHAP_GLOBAL_PATH = os.path.join(DATA_DIR, "aws_shap_global_importance.csv")
SHAP_EVENTS_PATH = os.path.join(DATA_DIR, "aws_event_explanations.csv")

# Station details
STATION_METADATA = {
    "station_id": "AGROMET04_15F105",
    "station_name": "Junagadh Agricultural University, Junagadh",
    "state": "Gujarat",
    "country": "India",
    "latitude": 21.499166,
    "longitude": 70.443340,
    "nominal_interval_minutes": 30,
    "timezone": "Asia/Kolkata (IST, UTC+5:30)",
}
