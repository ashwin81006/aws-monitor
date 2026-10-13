# AWS Monitor — Comprehensive Repository & Architecture Audit

**Project:** Intelligent Anomaly Detection for Automatic Weather Stations  
**Target Station:** ISRO AWS Station `ISRO0119_15F077`, VIT Vellore, Tamil Nadu  
**Audit Date:** October 2026  
**Auditor Role:** Senior ML & Full-Stack Systems Auditor  

---

## 1. Executive Summary

This audit assesses the alignment between the **Functional Specification (Project Abstract)**, the **Python Machine Learning & FastAPI Backend**, and the **.NET 10 MAUI Cross-Platform Client Application**.

### Overall Assessment
The project possesses a well-founded core scientific architecture: physical thermodynamic plausibility checks (Magnus-Tetens vapor calculations, diurnal solar hour cyclic projections, rolling median absolute deviation scaling) paired with an Isolation Forest unsupervised model. However, significant architectural gaps and disconnects between the backend and frontend currently exist:

1. **Schema Mismatches**: `/api/v1/sensors/health` returns `List[SensorHealthItem]` while the .NET MAUI client deserializes into `Dictionary<string, SensorChannelHealth>`, leading to silent fallback or empty sensor grids.
2. **Hardcoded UI Metric Bindings**: The failure category incident distribution chart (`IncidentChartSeries`) in `MainViewModel.cs` uses a static hardcoded array (`{ 9, 12, 15, 18, 42 }`), despite the backend returning genuine `counts_by_category` in `AnomalyEventsResponse`.
3. **Under-Integrated Endpoints**:
   - `GET /api/v1/anomalies/events/{event_id}` is implemented in FastAPI and `ApiService.cs`, but never triggered in `MainViewModel.cs` upon selecting an incident event.
   - `POST /api/v1/models/shap/explain` exists in FastAPI for local point attribution, but is completely absent from `IApiService`, `ApiService.cs`, and the UI Sensor Simulator.
4. **Ensemble Absence in Live Pipeline**: `train_models.py` trains One-Class SVM and LOF, and `test_models.py` benchmarks them, but `detector.py` exclusively loads Isolation Forest without ensemble voting or calibrated score fusion.
5. **Temporal Detection Limitations**: Frozen sensor checks only examine Temperature, ignoring Humidity and Pressure channels, and gradual calibration drift (EWMA/CUSUM) is not actively tracked in `StreamingFeatureExtractor`.
6. **Audibility & Uncertainty in Self-Healing**: `self_healing.py` applies Magnus inversion without calculating reconstruction uncertainty or checking whether the reference channel is also corrupted.

---

## 2. Component-by-Component Audit

### 2.1 Preprocessing (`src/preprocessing/preprocess.py`)
- **Strengths**: Strict WMO-aligned physical limits ($5^\circ\text{C} \le T \le 55^\circ\text{C}$, $5\% \le RH \le 100\%$, $900 \le P \le 1050\text{ hPa}$). Explicit sentinel recognition (`9999.0`, `-49.9`, `-40.0`, `-99.0`). Communication gap detection (`time_gap_minutes > 120`).
- **Issues Found**:
  - `clean_df` applies linear interpolation up to limit 10 and then fills with dataset median, which can mask genuine multi-hour station communication failures if flags are discarded downstream.
  - Preprocessing in `preprocess.py` uses $T_{min} = 5.0^\circ\text{C}$, whereas `detector.py` used $-40.0^\circ\text{C}$ for open-circuit sentinels and $5.0^\circ\text{C}$ in self-healing. These thresholds must be harmonized into shared configuration constants.

### 2.2 Feature Engineering (`src/features/feature_engineering.py`)
- **Strengths**: Exact Magnus formula constants ($a = 17.27, b = 237.7^\circ\text{C}$). Robust scaling with rolling Median and MAD. Diurnal cyclic features ($\sin(2\pi t/24), \cos(2\pi t/24)$).
- **Parity Analysis**: Batch `extract_features()` and `StreamingFeatureExtractor` match in feature names, column order, and mathematical formulas.
- **Issues Found**:
  - `StreamingFeatureExtractor` does not compute rolling flatline count or cumulative drift tracking (EWMA) needed for subtle calibration drift detection.

### 2.3 Model Training & Benchmarking (`src/ml/train_models.py`, `src/ml/test_models.py`)
- **Strengths**: Chronological 70/30 train-test split avoiding data leakage. Robust scaling (`RobustScaler`).
- **Issues Found**:
  - SVM and LOF are trained on only the first 5,000 observations of `X_train_scaled` to prevent $O(N^2)$ quadratic slowdown, but their decision thresholds are uncalibrated for score fusion.
  - Evaluation in `test_models.py` only reports inference throughput and disk size, rather than precision, recall, and F1 on injected ground-truth faults.

### 2.4 Unified Detector (`src/core/detector.py`)
- **Strengths**: Multi-tiered decision hierarchy: Sentinels $\rightarrow$ Frozen Sensor $\rightarrow$ Rate Limits $\rightarrow$ Dew Point Supersaturation $\rightarrow$ Weather Extreme Discrimination $\rightarrow$ ML Decision.
- **Issues Found**:
  - Only evaluates Isolation Forest. The abstract explicitly calls for multi-model ensemble detection.
  - The frozen sensor check only inspects temperature (`pt[0]`). Humidity and pressure flatlines are ignored.
  - Heatwave and thunderstorm checks lack continuous probability calibration.

### 2.5 Self-Healing & Reconstruction (`src/core/self_healing.py`)
- **Strengths**: Thermodynamic Magnus inversion ($T$ from $RH$ and $RH$ from $T$ via conserved dew point). Recent median fallback.
- **Issues Found**:
  - If both Temperature and Humidity are corrupted simultaneously, Magnus inversion can produce an erroneous result using an invalid reference.
  - Lacks uncertainty estimation ($\pm \sigma$ or confidence bound) and reconstruction quality grading.

### 2.6 FastAPI Backend Services (`src/api/`)
- **Endpoints Available**:
  - `GET /health` & `GET /api/v1/health`
  - `GET /api/v1/station/summary`
  - `GET /api/v1/telemetry/history`
  - `POST /api/v1/telemetry/stream-point`
  - `GET /api/v1/anomalies/events`
  - `GET /api/v1/anomalies/events/{event_id}`
  - `GET /api/v1/sensors/health`
  - `GET /api/v1/models/benchmark`
  - `GET /api/v1/models/shap`
  - `POST /api/v1/models/shap/explain`
- **Issues Found**:
  - Missing integration tests for error codes, missing inputs, and boundary validations.
  - Schema mismatch on `/api/v1/sensors/health` (returns list, frontend expected dictionary).

### 2.7 .NET MAUI Frontend (`ui/AwsMonitor.UI/`)
- **Strengths**: Modern dark glassmorphic design, CommunityToolkit.MVVM architecture, responsive cross-platform layouts, LiveCharts2 integration.
- **Issues Found**:
  - `ApiService.cs` provides offline mock fallbacks for all methods, but the UI does not distinguish when it is displaying live backend data versus offline fallback data.
  - `CountsByCategory` from `AnomalyEventsResponse` is discarded in favor of hardcoded chart values.
  - Local SHAP explanations are not wired into the Sensor Simulator.
  - Incident event selection does not query `GetAnomalyDetailAsync(id)` to show detailed sensor logs or SHAP breakdown.

---

## 3. High-Priority Action Items

1. **Contract Repair**: Synchronize C# models with FastAPI response schemas for Sensor Health and Anomaly Events.
2. **Dynamic Chart Binding**: Bind failure category distribution chart to live `CountsByCategory` from API.
3. **Local SHAP Integration**: Add `POST /api/v1/models/shap/explain` client method and display local feature attribution bars in the Sensor Simulator.
4. **Event Detail Modal / Inspector**: Wire `GET /api/v1/anomalies/events/{event_id}` into event selection.
5. **Modular Ensemble Detector**: Implement an ensemble engine in `detector.py` supporting Isolation Forest alone, One-Class SVM alone, LOF alone, and calibrated fusion.
6. **Temporal Fault Expansion**: Enhance `StreamingFeatureExtractor` and `detector.py` with multi-channel frozen checks and EWMA drift detection.
7. **Auditable Self-Healing**: Add uncertainty bounds, cross-channel corruption safeguards, and clear methodology reporting.
8. **Fault-Injection Evaluation**: Expand `validate.py` to compare all models and output rigorous Precision, Recall, F1, and Latency metrics.
