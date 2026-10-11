# Project Status Matrix — AWS Monitor

**Project Name:** Intelligent Anomaly Detection for Automatic Weather Stations (AWS-Monitor)  
**Authors:** G. Ashwin Siva (24PD11) & Hariharan. V (24PD14)  
**Date:** October 11, 2026  

---

## 📊 Subsystem Status Overview

| Subsystem | Components | Status | Verification Evidence |
| :--- | :--- | :---: | :--- |
| **Canonical Data Pipeline** | `data/raw/aws_dataset.csv`, `src/preprocessing/clean_aws.py`, missingness flags | **COMPLETE & TESTED** | Verified 23,807 continuous records; `tests/test_dataset_schema.py` passed (3/3). |
| **Feature Engineering Engine** | `src/features/feature_builder.py`, `src/features/build_features.py` (31 Causal Features) | **COMPLETE & TESTED** | Strictly causal 9-step sliding window (`center=False`); 0.0 error between streaming ring buffer and batch pandas; `tests/test_features.py` passed (3/3). |
| **ML Training & Preparation** | `src/ml/prepare_ml_data.py`, `src/ml/isolation_forest.py` | **COMPLETE & TESTED** | Chronological 70/30 split, no data leakage, RobustScaler fitted on training split only; measured fit times tracked in `models/training_meta.json`; `tests/test_models.py` passed (3/3). |
| **Benchmark Models & Selection** | `src/ml/local_outlier_factor.py`, `src/ml/one_class_svm.py`, `src/ml/model_comparison.py` | **COMPLETE & TESTED** | Evaluated on identical test sets; dynamic data-driven ranking selects Isolation Forest (76,967 obs/s, 0.420s fit time, 1001.4 KB, composite 8.03/10). |
| **Physics & Sentinel Rules** | `src/detection/rule_qc.py`, `src/detection/cross_sensor_evidence.py`, `src/detection/temporal_evidence.py` | **COMPLETE & TESTED** | Sentinels ($-40.0^\circ\text{C}, 0\,\text{mbar}$), vertical lapse rates ($\Delta T$), 30-min rates of change, battery brownout, and heatwave consensus verified; `tests/test_detection_rules.py` passed (4/4). |
| **Bayesian Evidence Fusion** | `src/detection/core_detector.py`, `src/detection/build_evidence_matrix.py`, `src/detection/event_fusion.py` | **COMPLETE & TESTED** | Centralized Noisy-OR probabilistic multi-layer fusion matrix and temporal clustering; identical scoring across batch and live stream; `tests/test_fusion.py` passed (3/3). |
| **Fault Injection & Validation** | `src/validation/inject_faults.py`, `src/validation/evaluate_validation.py`, `src/validation/run_validation_pipeline.py` | **COMPLETE & TESTED** | Injected SPIKE, DRIFT, FROZEN_SENSOR, COMMUNICATION_FAILURE scenarios; genuine bipartite interval overlap event matching (no artificial precision); `tests/test_validation.py` passed (2/2). |
| **Model Explainability (SHAP)** | `src/explainability/shap_explainer.py`, `src/api/routes/explainability.py` | **COMPLETE & TESTED** | TreeSHAP exact path decomposition, global importance rankings, and per-event waterfall attributions. Transparent fallback when artifacts are missing. |
| **FastAPI REST API** | `src/api/app.py`, `src/api/routes/`, `src/api/services/` | **COMPLETE & TESTED** | OpenAPI docs at `/docs`, streaming inference, downsampled history, hardened CSV upload (50 MB limit, strict schema check), transparent degradation modes (`ONLINE` vs `DEGRADED`); `tests/test_api_endpoints.py` passed (11/11). |
| **.NET 10 MAUI Desktop/Mobile UI** | `ui/AwsMonitor.UI/` (C# / XAML + LiveCharts2) | **COMPLETE & TESTED** | Compiled with 0 errors/0 warnings via `dotnet build -f net10.0-windows10.0.19041.0`; 6 tabs (Overview, Telemetry, Test Faults, Incidents, Sensor Health, AI Models). |
| **Automated Test Suite** | `tests/run_tests.py` | **COMPLETE & TESTED** | 35/35 unit and integration tests passing (`0 Failed`). |
| **Postman API Collection** | `tests/postman/AWS_Monitor_API.postman_collection.json` | **COMPLETE & TESTED** | Validated against running API. |
