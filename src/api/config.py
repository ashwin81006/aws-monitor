import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

MODELS_DIR = os.path.join(BASE_DIR, "models")
RAW_DATA_PATH = os.path.join(BASE_DIR, "data", "raw", "aws_dataset.csv")

SCALER_PATH = os.path.join(MODELS_DIR, "scaler.pkl")
IF_MODEL_PATH = os.path.join(MODELS_DIR, "isolation_forest.pkl")
LOF_MODEL_PATH = os.path.join(MODELS_DIR, "lof.pkl")
OCSVM_MODEL_PATH = os.path.join(MODELS_DIR, "one_class_svm.pkl")

STATION_METADATA = {
    "station_id": "ISRO0119_15F077",
    "station_name": "ISRO AWS Station, VIT Vellore",
    "state": "Tamil Nadu",
    "country": "India",
    "latitude": 12.9692,
    "longitude": 79.1559,
    "elevation_m": 214.0,
    "nominal_interval_minutes": 30,
    "timezone": "Asia/Kolkata (IST, UTC+5:30)",
}
