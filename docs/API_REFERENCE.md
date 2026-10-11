# API Reference — AWS Monitor REST API

**Base URL:** `http://localhost:8000`  
**Swagger UI:** `http://localhost:8000/docs`  
**ReDoc:** `http://localhost:8000/redoc`  
**Postman Collection:** `tests/postman/AWS_Monitor_API.postman_collection.json`  

---

## 1. System & Station Health

### `GET /health`
Returns high-level service status, active production model, feature counts, and station identifier.

**Response `200 OK`:**
```json
{
  "status": "ONLINE",
  "service": "AWS Monitor - Anomaly Detection API",
  "station_id": "AGROMET04_15F105",
  "active_model": "Isolation Forest (31 Clean Domain Features)",
  "features_count": 31,
  "calibration": "Empirical Bayesian Multi-Source Evidence Fusion",
  "explainability": "TreeSHAP Local & Global Attributions"
}
```

---

### `GET /api/v1/station/summary`
Returns aggregate observational statistics, observation counts, date range, and overall data quality score.

**Response `200 OK`:**
```json
{
  "station_id": "AGROMET04_15F105",
  "station_name": "Junagadh Agricultural University, Junagadh",
  "location": "Gujarat, India",
  "coordinates": {
    "latitude": 21.499166,
    "longitude": 70.443340
  },
  "total_observations": 23807,
  "start_time": "2015-09-04 13:30:00",
  "end_time": "2017-08-01 23:30:00",
  "data_gaps_count": 48,
  "verified_normal_count": 22473,
  "probable_faults_count": 625,
  "possible_extremes_count": 91,
  "uncertain_warnings_count": 217,
  "overall_reliability_pct": 98.8,
  "station_status": "HEALTHY_ONLINE"
}
```

---

## 2. Telemetry & Real-Time Inference

### `POST /api/v1/telemetry/stream-point`
Performs real-time anomaly detection and Bayesian evidence fusion on an individual 30-minute observation.

**Request Body:**
```json
{
  "timestamp": "2026-10-10 12:00:00",
  "temp_2m": 31.4,
  "temp_4m": 31.1,
  "temp_8m": 30.8,
  "rh_2m": 65.0,
  "rh_4m": 66.2,
  "rh_8m": 67.0,
  "pressure": 998.4,
  "battery_voltage": 13.2,
  "wind_speed_10m": 2.4,
  "rainfall": 0.0,
  "prev_temp_4m": 31.1
}
```

**Response `200 OK` (Normal Weather):**
```json
{
  "timestamp": "2026-10-10 12:00:00",
  "classification": "NORMAL",
  "anomaly_probability": 0.05,
  "fused_anomaly_score": 0.05,
  "confidence": 0.95,
  "severity": "NONE",
  "probable_root_cause": "NORMAL_OPERATION",
  "affected_sensors": ["NONE"],
  "is_anomaly": false,
  "if_score": 0.1245,
  "if_outlier": false,
  "evidence_breakdown": {
    "score_rule": 0.0,
    "score_cross_consensus": 0.0,
    "score_temporal": 0.0,
    "score_battery": 0.0,
    "score_isolation_forest": 0.05,
    "multi_height_min_spread": 0.3
  },
  "explanation": "Observation reading is within normal physical limits and consistent across multi-height towers."
}
```

---

### `POST /api/v1/telemetry/upload`
Uploads and dynamically activates a CSV dataset across all services and live dashboard charts.

**Request:** `multipart/form-data` with `file: <dataset.csv>`

**Response `200 OK`:**
```json
{
  "status": "VALIDATED_AND_ACTIVATED",
  "filename": "aws_dataset.csv",
  "rows_received": 23807,
  "columns_received": 37,
  "date_range": "2015-09-04 to 2017-08-01",
  "sensors_detected": ["temp_2m", "temp_4m", "temp_8m", "rh_2m", "rh_4m", "rh_8m", "pressure", "battery_voltage"],
  "flagged_faults_count": 625,
  "quality_score_pct": 98.8,
  "message": "Successfully parsed and activated 23,807 records across 10 sensors. Station reliability rated at 98.8%."
}
```

---

## 3. Sensors, Anomalies & Models

### `GET /api/v1/sensors/health`
Returns individual channel reliability breakdowns, clean readings counts, and operational health grades.

### `GET /api/v1/anomalies/events?limit=50`
Returns clustered anomaly event episodes with start/end timestamps, durations, peak anomaly scores, and root-cause diagnoses.

### `GET /api/v1/models/benchmark`
Returns quantitative evaluation comparisons across Isolation Forest, One-Class SVM, and Local Outlier Factor.

### `GET /api/v1/explainability/global-importance` (or `/api/v1/explainability/shap`)
Returns TreeSHAP global feature importance rankings.
