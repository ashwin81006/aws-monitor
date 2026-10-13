# AWS Monitor — Complete Engineering Implementation Report

**Project Title:** Intelligent Anomaly Detection for Automatic Weather Stations  
**Target Station:** ISRO Automatic Weather Station `ISRO0119_15F077`, VIT Vellore, Tamil Nadu  
**Auditor & Implementation Engineer:** Senior ML, Backend & .NET MAUI Engineer  
**Status:** Complete, Verified, Zero Errors  

---

## 1. Overview of Delivered Work

This implementation delivers complete end-to-end alignment between the project specification, the machine learning detection engine, the FastAPI backend services, and the .NET 10 MAUI cross-platform UI. Every identified schema discrepancy, hardcoded mock metric, missing endpoint, and detection limitation has been resolved with verified code.

---

## 2. File-by-File Changes & Implemented Architecture

### 2.1 Backend Core Machine Learning & Feature Engineering

#### [`src/features/feature_engineering.py`](file:///e:/Sem-5-packages/aws-monitor/src/features/feature_engineering.py)
- **Multi-Channel Flatline Tracking**: Added consecutive identical value counters (`t_streak`, `rh_streak`, `p_streak`) to `StreamingFeatureExtractor` to detect frozen sensor outputs across temperature, relative humidity, and barometric pressure.
- **EWMA Drift Accumulator**: Implemented Exponentially Weighted Moving Average (`ewma_t` with $\alpha = 0.25$) to capture persistent gradual sensor calibration shifts.
- **State Management**: Added explicit `reset()` method to clear historical deques, streak counters, and drift states between sessions.
- **Psychrometric Parity**: Verified identical Magnus-Tetens formulas ($a = 17.27, b = 237.7^\circ\text{C}$) and rolling MAD deviations between batch and streaming modes.

#### [`src/core/detector.py`](file:///e:/Sem-5-packages/aws-monitor/src/core/detector.py)
- **Modular Multi-Model Detection Engine**: Enhanced `AWSUnifiedDetector` with configurable operating modes:
  1. `isolation_forest`: Baseline unsupervised partition isolation.
  2. `one_class_svm`: Margin boundary support vector classification.
  3. `lof`: Local density outlier detection.
  4. `majority_voting`: Discrete binary vote consensus across all 3 models.
  5. `calibrated_ensemble`: Sigmoid-calibrated score fusion ($0.50 \cdot P_{IF} + 0.30 \cdot P_{SVM} + 0.20 \cdot P_{LOF}$).
  6. `rule_cascade`: Meteorological physics prioritized ahead of statistical models.
- **Weather Extreme Discrimination**: Prioritized multi-channel physical corroboration before single-channel rate limits:
  - *Convective Thunderstorms*: Correlated temperature drops ($\frac{dT}{dt} < -2.0^\circ\text{C}$), rapid moisture surges ($\frac{dRH}{dt} > +10\%$), and barometric depressions ($\frac{dP}{dt} < -2.0\text{ hPa}$) classified as `BENIGN_EXTREME` rather than isolated hardware spikes.
  - *Severe Summer Heatwaves*: High temperatures ($T > 42^\circ\text{C}$) corroborated by low moisture ($RH < 35\%$) and elevated vapor deficit ($T - T_d > 18^\circ\text{C}$) classified as genuine meteorological events.
- **Physical Rate & Consistency Checks**:
  - Unphysical temperature jump ($|\frac{dT}{dt}| > 6.0^\circ\text{C}/\text{step}$).
  - Barometric pressure transient jump ($|\frac{dP}{dt}| > 12.0\text{ hPa}/\text{step}$).
  - Supersaturation violation ($T_d > T + 0.5^\circ\text{C}$).
- **Convenience Wrapper**: Added `detect_point()` and state `reset()` to ensure seamless integration with validation pipelines and testing suites.

#### [`src/core/self_healing.py`](file:///e:/Sem-5-packages/aws-monitor/src/core/self_healing.py)
- **Cross-Channel Integrity Verification**: Prevented using a corrupted sensor to reconstruct another channel (e.g. if relative humidity is invalid or missing, Magnus inversion is safely rejected).
- **Physical Magnus Inversion**: Reconstructed air temperature from valid relative humidity and recent conserved dew point:
  $$T_{healed} = \frac{b \cdot \gamma}{a - \gamma}, \quad \text{where } \gamma = \frac{a \cdot T_d}{b + T_d} - \ln\left(\frac{RH}{100}\right)$$
- **Auditable Quality & Uncertainty Metrics**:
  - `reconstruction_grade`: `HIGH_CONFIDENCE_PHYSICAL` for psychrometric inversion vs. `MODERATE_CONFIDENCE_AUTOREGRESSIVE` for rolling median fallback.
  - `uncertainty_estimate`: Documented confidence bounds ($\pm 0.8^\circ\text{C}$ for physical inversion, $\pm 1.8^\circ\text{C}$ for median fallback).
  - `supporting_evidence`: Clear human-readable justification detailing exactly which physical laws and observations were used.

#### [`src/ml/explain_shap.py`](file:///e:/Sem-5-packages/aws-monitor/src/ml/explain_shap.py)
- **Point-Level Derivation**: Updated `explain_observation()` so that when raw inputs $(T, RH, P)$ are provided, psychrometric dew point, vapor deficit, rates, and cyclic diurnal sine/cosine features are dynamically derived before scaling, preventing zero-filled inputs.
- **TreeSHAP Integration**: Generated local feature contributions sorted by absolute importance, including directional indicators (`Pushes Anomaly` vs. `Pushes Normal`) and meteorological domain labels.

#### [`src/validation/validate.py`](file:///e:/Sem-5-packages/aws-monitor/src/validation/validate.py)
- **Controlled Fault Injection**: Implemented synthetic injection of:
  - Sudden ADC spikes ($T < -20^\circ\text{C}$ or $T > 55^\circ\text{C}$).
  - Multi-step frozen sensor flatlines (10 consecutive identical readings).
  - Gradual calibration drift ($+0.05^\circ\text{C}$ to $+0.15^\circ\text{C}$ per step).
  - Barometric pressure transient steps ($\pm 15\text{ hPa}$).
  - Communication dropouts (missing sentinels).
- **Empirical Benchmarking**: Evaluated baseline Isolation Forest against One-Class SVM, LOF, and the Calibrated Ensemble on 1,000 chronological observations, measuring row-level precision, recall, F1, event-level F1, and throughput.

---

### 2.2 FastAPI Backend Schemas & Services

#### [`src/api/schemas/health.py`](file:///e:/Sem-5-packages/aws-monitor/src/api/schemas/health.py) & [`src/api/services/health_service.py`](file:///e:/Sem-5-packages/aws-monitor/src/api/services/health_service.py)
- Added bidirectional field aliases (`channel`, `quality_score_pct`, `flagged_anomaly_count`, `total_readings`, `overall_health_score`) to `SensorHealthItem` and `SensorHealthResponse`.
- Eliminated schema mismatch so both list and dictionary representations are supported without serialization failure.

#### [`src/api/services/anomaly_service.py`](file:///e:/Sem-5-packages/aws-monitor/src/api/services/anomaly_service.py)
- Updated `get_event_detail()` to populate all required fields of `AnomalyEventDetail` (`explanation`, `rule_flags`, `affected_sensors`, `evidence_breakdown`, `peak_fused_score`).

---

### 2.3 .NET 10 MAUI Client Application

#### [`ui/AwsMonitor.UI/Models/DiagnosticModels.cs`](file:///e:/Sem-5-packages/aws-monitor/ui/AwsMonitor.UI/Models/DiagnosticModels.cs)
- Refactored `StationHealthSummary` to expose `List<SensorChannelHealth> SensorList` while maintaining a computed `Dictionary<string, SensorChannelHealth> Sensors` property.
- Added `ShapLocalFeatureImpact` model with properties `Feature`, `ShapValue`, `AbsoluteImpact`, `Direction`, `Domain`, `FriendlyFeatureName`, and `DirectionColor`.

#### [`ui/AwsMonitor.UI/Models/AnomalyModels.cs`](file:///e:/Sem-5-packages/aws-monitor/ui/AwsMonitor.UI/Models/AnomalyModels.cs)
- Added `CountsByCategory` and `CountsBySeverity` dictionaries to `AnomalyEventsResponse`.
- Added property backing fields and full setters for `ObservationsCount`, `Classification`, and `RootCause` in `AnomalyDetailResponse`.

#### [`ui/AwsMonitor.UI/Services/ApiService.cs`](file:///e:/Sem-5-packages/aws-monitor/ui/AwsMonitor.UI/Services/ApiService.cs)
- Added `ExplainObservationAsync(Dictionary<string, double> payload)` to `IApiService` and implemented calling `POST /api/v1/models/shap/explain`.
- Updated `GetSensorHealthAsync()` to deserialize into `StationHealthSummary` with live connection tracking.

#### [`ui/AwsMonitor.UI/ViewModels/MainViewModel.cs`](file:///e:/Sem-5-packages/aws-monitor/ui/AwsMonitor.UI/ViewModels/MainViewModel.cs)
- **Eliminated Hardcoded Incident Metrics**: Replaced static `{ 9, 12, 15, 18, 42 }` in `LoadEventsAsync()` with live dynamic binding to `res.CountsByCategory`.
- **Dynamic Throughput Charts**: Replaced hardcoded values in `LoadModelDiagnosticsAsync()` with live values from `ModelBenchmarkResponse`.
- **Event Deep Dive Selection**: Integrated `SelectEventAsync(AnomalyEvent? ev)` to call `_api.GetAnomalyDetailAsync(ev.EventId)` and display detailed rule flags, explanation, and affected sensors.
- **Local SHAP Attribution**: Integrated `RunTestInferenceAsync()` to call `_api.ExplainObservationAsync()` and populate `LocalShapList`.
- **Connection & Mode Banner**: Added explicit status badges:
  - `● PRODUCTION LIVE (ISRO0119_15F077)` when API is connected.
  - `⚠ OFFLINE DEMO MODE (CACHED DATA)` when offline with explanatory notice.

#### [`ui/AwsMonitor.UI/MainPage.xaml`](file:///e:/Sem-5-packages/aws-monitor/ui/AwsMonitor.UI/MainPage.xaml)
- Added live Connection Status Chip and Refresh button in the top header.
- Added Selected Incident Deep Dive Inspector Card in the Incidents tab.
- Added Local SHAP Feature Impact panel in the Sensor Simulator tab.

---

## 3. Verification & Build Confirmation

1. **Backend Automated Tests**:
   - Executed `python -m unittest tests/test_backend.py`.
   - Result: **18 tests ran in 12.78s — ALL PASSED (OK)**.
2. **.NET MAUI Windows Build**:
   - Executed `dotnet build ui\AwsMonitor.UI\AwsMonitor.UI.csproj -f net10.0-windows10.0.19041.0 -c Debug`.
   - Result: **Build Succeeded (0 Warnings, 0 Errors)**.
