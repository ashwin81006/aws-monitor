# AWS Monitor: Intelligent Anomaly Detection for Automatic Weather Stations

**Project Team:** G. ASHWIN SIVA (24PD11) | HARIHARAN. V (24PD14)

An end-to-end, multi-layered anomaly detection and fault diagnosis system for Automatic Weather Stations (AWS), combining unsupervised machine learning, physical cross-sensor consistency validation, temporal dynamics, and domain rule quality control.

---

## Architecture Pipeline

```text
Raw AWS Telemetry (data/raw/aws_dataset.csv)
       │
       ▼
[1] Preprocessing & Quality Flags (src/preprocessing/clean_aws.py)
       │ ──► data/processed/aws_clean.csv
       ▼
[2] EDA & Data Profiling (src/exploration/eda_summary.py)
       │
       ▼
[3] Feature Engineering (src/features/build_features.py)
       │ ──► data/processed/aws_features.csv (156 features)
       ▼
[4] ML Data Prep & Scaling (src/ml/prepare_ml_data.py)
       │ ──► models/scaler.pkl, train_medians.pkl, ml_feature_columns.json
       │ ──► data/processed/aws_train_scaled.csv & aws_test_scaled.csv
       ▼
[5-7] Unsupervised Model Training (src/ml/)
       │ ──► models/isolation_forest.pkl (Primary)
       │ ──► models/lof_model.pkl (Benchmark)
       │ ──► models/ocsvm_model.pkl (Benchmark)
       ▼
[8-11] Multi-Source Evidence Engines (src/detection/)
       │ ──► Rule QC, Calibrated Thresholds, Cross-Sensor Evidence, Temporal Evidence
       ▼
[12] Unified Evidence Matrix (src/detection/build_evidence_matrix.py)
       │ ──► data/processed/aws_evidence_matrix.csv
       ▼
[13] Event Fusion & Root Cause Diagnosis (src/detection/event_fusion.py)
       │ ──► data/processed/aws_event_fusion.csv
       ▼
[14] Controlled Synthetic Fault Validation (src/validation/run_validation.py)
       │ ──► data/processed/aws_validation_evaluation.csv & metrics_summary.json
       ▼
[15] Model Benchmarking Suite (src/ml/model_comparison.py)
       │ ──► data/processed/aws_model_comparison.csv & metrics_summary.json
```

---

## Cleaned Project Structure

The project has been cleaned and streamlined, eliminating redundant intermediate CSVs and consolidating prototype scripts into 18 dedicated, production-ready files:

```text
intelligent-anomaly-detection-for-automatic-weather-stations/
│
├── data/
│   ├── raw/
│   │   └── aws_dataset.csv                   # Raw historical telemetry (23,807 rows)
│   └── processed/
│       ├── aws_clean.csv                     # Cleaned dataset with quality flags
│       ├── aws_features.csv                  # 156 engineered features
│       ├── aws_train_scaled.csv              # Scaled training split (16,664 rows, 112 features)
│       ├── aws_test_scaled.csv               # Scaled test split (7,143 rows, 112 features)
│       ├── aws_evidence_matrix.csv           # Multi-source fused evidence matrix
│       ├── aws_event_fusion.csv              # Clustered events with severity & root cause
│       ├── aws_fault_labels.csv              # Validation ground truth fault labels
│       ├── aws_injected_events.csv           # Validation injected event metadata
│       ├── aws_validation_evaluation.csv     # Row-level validation evaluation
│       ├── aws_validation_event_evaluation.csv# Event-level validation evaluation
│       ├── aws_validation_metrics_summary.json# Validation metrics summary
│       ├── aws_model_comparison.csv          # Architecture comparison table
│       ├── aws_fault_breakdown.csv           # Fault-wise model breakdown
│       ├── aws_model_predictions.csv         # Comparative predictions
│       └── aws_model_comparison_metrics.json # Full benchmark metrics JSON
│
├── models/
│   ├── isolation_forest.pkl                  # Primary unsupervised detector (982 KB)
│   ├── lof_model.pkl                         # Benchmark density detector (17.4 MB)
│   ├── ocsvm_model.pkl                       # Benchmark margin detector (163 KB)
│   ├── scaler.pkl                            # Fitted RobustScaler
│   ├── train_medians.pkl                     # Training reference medians for imputation
│   ├── ml_feature_columns.json               # Schema of 112 ML feature names
│   ├── cross_sensor_thresholds.json          # Empirical 99th percentile spread thresholds
│   └── temporal_thresholds.json              # Empirical 99th percentile rate thresholds
│
├── src/
│   ├── exploration/
│   │   └── eda_summary.py                    # Sensor descriptive statistics & quality profiling
│   ├── preprocessing/
│   │   └── clean_aws.py                      # Sentinel handling, timestamp parsing, quality flags
│   ├── features/
│   │   └── build_features.py                 # Temporal, cross-sensor, rolling & repetition features
│   ├── ml/
│   │   ├── prepare_ml_data.py                # Consolidated selection, split, imputation, scaling
│   │   ├── isolation_forest.py               # Standalone training & inference (Primary Model)
│   │   ├── local_outlier_factor.py           # Standalone training & inference (Benchmark Model)
│   │   ├── one_class_svm.py                  # Standalone training & inference (Benchmark Model)
│   │   └── model_comparison.py               # Evaluation, throughput & benchmarking suite
│   ├── detection/
│   │   ├── rule_qc.py                        # Deterministic domain QC checks
│   │   ├── calibrate_thresholds.py           # Statistical percentile threshold calibration
│   │   ├── cross_sensor_evidence.py          # Tri-sensor spatial consistency & divergent sensor isolation
│   │   ├── temporal_evidence.py              # Dynamic rate-of-change & single-spike detection
│   │   ├── build_evidence_matrix.py          # Unified multi-evidence matrix
│   │   └── event_fusion.py                   # Event clustering, root cause diagnosis & severity scoring
│   └── validation/
│       ├── inject_faults.py                  # Controlled synthetic fault injection engine
│       ├── run_validation_pipeline.py        # Streamlined validation pipeline runner
│       ├── evaluate_validation.py            # Observation & event-level precision/recall/latency
│       └── run_validation.py                 # CLI validation runner
│
├── run_pipeline.py                           # 15-step consolidated end-to-end pipeline runner
└── README.md
```

---

## Quickstart & Execution

### 1. Requirements

Install standard dependencies:

```powershell
pip install pandas numpy scikit-learn joblib
```

### 2. Complete End-to-End Pipeline

Run all 15 stages with a single command:

```powershell
python -u run_pipeline.py
```

The pipeline executes sequentially:
1. `[1/16]` Data Cleaning & Quality Flags (`src/preprocessing/clean_aws.py`)
2. `[2/16]` EDA Summary & Quality Profiling (`src/exploration/eda_summary.py`)
3. `[3/16]` Feature Engineering (`src/features/build_features.py`)
4. `[4/16]` ML Preparation, Train/Test Split & Robust Scaling (`src/ml/prepare_ml_data.py`)
5. `[5/16]` Primary Model Training — Isolation Forest (`src/ml/isolation_forest.py`)
6. `[6/16]` Benchmark Model Training — Local Outlier Factor (`src/ml/local_outlier_factor.py`)
7. `[7/16]` Benchmark Model Training — One-Class SVM (`src/ml/one_class_svm.py`)
8. `[8/16]` Rule-based Quality Control (`src/detection/rule_qc.py`)
9. `[9/16]` Empirical Threshold Calibration (`src/detection/calibrate_thresholds.py`)
10. `[10/16]` Cross-Sensor Consistency Evidence (`src/detection/cross_sensor_evidence.py`)
11. `[11/16]` Temporal Dynamic Evidence (`src/detection/temporal_evidence.py`)
12. `[12/16]` Multi-Source Evidence Matrix Construction (`src/detection/build_evidence_matrix.py`)
13. `[13/16]` Event-Level Clustering & Root Cause Fusion (`src/detection/event_fusion.py`)
14. `[14/16]` Controlled Synthetic Fault Validation (`src/validation/run_validation.py`)
15. `[15/16]` ML Model Comparison & Benchmarking (`src/ml/model_comparison.py`)
16. `[16/16]` Telemetry Model Explainability — SHAP (`src/explainability/shap_explainer.py`)

---

## Development Roadmap & Status

| Stage / Component | Focus | Key Deliverables | Status |
|---|---|---|:---:|
| **Dataset Inspection** | Data Structure & Gaps | Structure, timestamps, sensors, gap profiling | ✅ Complete |
| **Data Cleaning** | Quality Preprocessing | Sentinels (-40, -312, -100), timestamps, quality flags | ✅ Complete |
| **Exploratory Analysis** | Statistical Profiling | Sensor distributions, physical range checks, correlations | ✅ Complete |
| **Feature Engineering** | Dynamic Telemetry Signals | 156 features: temporal, cross-sensor spread, rolling, repetition | ✅ Complete |
| **ML Data Preparation** | Leakage-Free Normalization | 112 features, 70/30 split, training imputation, RobustScaler | ✅ Complete |
| **Initial Detection Engine** | Heuristic & Unsupervised ML | Isolation Forest, rule engine, empirical percentile thresholds | ✅ Complete |
| **Evidence Fusion** | Multi-Stream Integration | Multi-evidence matrix, temporal clustering, root cause, severity | ✅ Complete |
| **Controlled Validation** | Precision & Latency Verification| Synthetic faults (spikes, drifts, frozen, outages), precision/recall | ✅ Complete |
| **Model Comparison** | Architecture Benchmarking | Rigorous comparison: IF vs LOF vs OC-SVM across throughput & accuracy | ✅ Complete |
| **Fusion Improvements** | Multi-Layer Evidence Tuning | Bayesian Noisy-OR, continuous sub-scores, dynamic confidence | ✅ Complete |
| **Explainability** | Diagnostic Explanations | SHAP TreeExplainer, feature importance, event waterfall plots | ✅ Complete |
| **Inference API** | Real-Time Serving | FastAPI real-time scoring and batch anomaly endpoints | ⏳ Next |
| **Telemetry Dashboard** | Visual Operations Console | Interactive telemetry, fault events, station health & charts | ⏳ |
| **Production Validation** | System Hardening | End-to-end integration testing, system benchmarks, demo readiness | ⏳ |

---

## Benchmark Highlights

### Controlled Fault Validation Benchmark Results
- **Fault Event Detection Rate:** 5/5 (100.0%)
- **Diagnostic Root Cause Match:** 6/6 (100.0%)
- **Candidate Class Match:** 6/6 (100.0%)
- **Weather Extreme False Alarm Rejection:** 100% Passed (Cleanly distinguished from sensor faults)
- **Artifacts:** `aws_validation_event_evaluation.csv`, `aws_validation_metrics_summary.json`

### Unsupervised Model Comparison Benchmark Results

| Model Architecture | Throughput | Model Disk Size | Uncorrupted Anomaly % | Standalone ROC-AUC | Injected Power Failure | Injected Event Detection (Fused) | SHAP Method | Production Decision Role |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Isolation Forest** | **58,367 obs/s** | **982.4 KB** | **2.30%** | 0.5579 | **100% (6/6)** | **100% (5/5)** | **TreeExplainer (Exact, Fast)** | **PRIMARY PRODUCTION DETECTOR** |
| **Local Outlier Factor (LOF)** | 10,784 obs/s | 17,446.0 KB | 2.69% | **0.8693** | **100% (6/6)** | **100% (5/5)** | KernelExplainer (Slow Sampling) | SECONDARY BENCHMARK |
| **One-Class SVM (OC-SVM)** | 18,512 obs/s | **163.3 KB** | 3.68% | 0.7609 | **100% (6/6)** | **100% (5/5)** | KernelExplainer (Slow Sampling) | SECONDARY BENCHMARK |

**Primary Selection: Isolation Forest**
- Exceptional throughput (17.1 µs latency per sample).
- Compact serialization footprint (982 KB).
- Exact, real-time SHAP TreeExplainer compatibility.
- Seamless synergy with cross-sensor and temporal rules via multi-evidence matrix fusion.
