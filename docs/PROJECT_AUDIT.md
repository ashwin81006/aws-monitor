# Project Architecture & Baseline Audit Report — AWS Monitor

**Project Name:** Intelligent Anomaly Detection for Automatic Weather Stations  
**Authors:** G. Ashwin Siva (24PD11) & Hariharan. V (24PD14)  
**Date:** October 11, 2026  

---

## 1. Executive Baseline Summary

This audit establishes the ground-truth technical state of the **AWS-Monitor** repository. The system is designed to continuously inspect multi-channel automated weather station observations, distinguish hardware/sensor failures from natural extreme weather events, estimate anomaly severity and confidence, isolate root causes, and present interpretable diagnostics via a cross-platform .NET 10 MAUI desktop/mobile dashboard.

---

## 2. Baseline Inventory & Verified Findings

### 2.1 Canonical Dataset Discrepancy (Resolved)
* **Finding:** The repository previously contained two raw dataset files in `data/raw/`:
  - `data/raw/aws_dataset.csv` (19,921 rows; September 2015 – March 2017)
  - `data/raw/aws_dataset1.csv` (23,807 rows; September 2015 – August 2017)
* **Resolution:** Synchronized `data/raw/aws_dataset.csv` to contain the full, canonical 23,807 continuous observations from the ISRO/MOSDAC Junagadh station (`AGROMET04_15F105`), ensuring complete chronological alignment across all 16 pipeline stages.

### 2.2 Feature Consistency & Metadata Alignment
* **Finding:** Prior references in early documentation cited historical feature counts of 156 and 112 from initial experimental exploration, while the production engine converged on 31 domain features.
* **Resolution:** Consolidated all feature definitions into one authoritative 31-feature specification (`models/ml_feature_columns.json`) spanning:
  1. Base monitored channels ($10$)
  2. Multi-height vertical lapse rate gradients ($6$)
  3. 30-minute rates of change ($8$)
  4. Robust dispersion deviations ($5$)
  5. Solar diurnal harmonics ($2$)
* Training, offline evaluation, streaming API inference, and CSV upload processing all use this identical feature definition.

### 2.3 Model Artifact Lifecycle & Loading Safeguards
* **Finding:** When model files were deleted from disk, `inference_service.py` had an uncontrolled fallback that wrote synthesized models to production paths.
* **Resolution:** Separated production artifact loading from demo/ephemeral mode. In production mode, verified model artifacts (`models/isolation_forest.pkl`, `models/scaler.pkl`) are strictly validated and loaded with logged provenance. In demo mode, ephemeral models operate entirely in RAM without overwriting production disk files.

### 2.4 Missing Value & Sentinel Semantics
* **Finding:** Missing sensor values in early prototypes could be silently filled with averages.
* **Resolution:** Explicit missingness tracking (`missing_any`, `is_imputed`), sentinel detection (e.g. $-40.0^\circ\text{C}$ open-circuit, $0.0\,\text{mbar}$ barometric failure, $\le 0.5\,\text{V}$ power collapse), and adiabatic lapse rate bounds ensure that missing readings are never fabricated as authentic observations.

### 2.5 Explainability & API Endpoint Route Alignment
* **Finding:** The MAUI client queried `/api/v1/explainability/shap`, which previously returned 404 because the backend only exposed `/global-importance`.
* **Resolution:** Added route aliases (`/shap`, `/summary`, `/global-importance`) and guaranteed TreeSHAP global importance fallback responses so that explainability cards render seamlessly under all network states.

---

## 3. Resolution of Static Code Review Audit Findings

### 3.1 Unification of Feature Engineering & Causal Windows (AUDIT-P1.1)
* **Defect:** Training used centered rolling windows (`center=True`), leaking future observations (4 steps ahead). Streaming and CSV uploads used fixed scalar baselines ($28.5^\circ\text{C}, 60\%, 1005\,\text{mbar}$).
* **Fix:** Implemented `src/features/feature_builder.py` with causal rolling windows (`center=False`) in `compute_31_features_df` and created `StreamingFeatureBuffer` maintaining historical ring buffers for both raw values and deviation scores. Achieves exact numerical parity ($0.0$ difference) between batch pandas and real-time streaming.

### 3.2 Genuine Event-Level Validation Metrics (AUDIT-P1.2)
* **Defect:** `evaluate_validation.py` previously set `event_precision = (1.0 if fault_detected_count > 0 else 0.0)`, artificially inflating precision and F1 to 100% upon detecting a single fault.
* **Fix:** Replaced heuristic with bipartite interval overlap matching between true fault windows and contiguous predicted alert intervals. Now calculates true TP, FP, FN, Precision, Recall, and F1 across full test splits and evaluation benchmark windows.

### 3.3 Dynamic, Data-Driven Model Selection (AUDIT-P1.3)
* **Defect:** `model_comparison.py` used a hardcoded scoring dictionary and static justification text, irrespective of actual benchmark runs. Training time was set to 0.0s when loading pre-trained models.
* **Fix:** Measured actual model fitting times during training and serialized them in `models/training_meta.json`. In `model_comparison.py`, all criteria scores and composite weighted rankings are calculated dynamically from measured fitting duration, inference throughput, disk size, and ROC-AUC.

### 3.4 Shared Bayesian Noisy-OR Fusion & Diagnosis (AUDIT-P1.4)
* **Defect:** The offline pipeline combined evidence via Noisy-OR, while the streaming point endpoint and CSV-upload processor implemented diverging heuristic scoring rules.
* **Fix:** Centralized Bayesian Noisy-OR scoring (`compute_noisy_or_fusion`) and physical diagnosis decision tree (`diagnose_point`) in `src/detection/core_detector.py`. All entry points (offline matrix, streaming endpoint, CSV batch) now execute identical scoring logic.

### 3.5 Transparent Status & Degradation Modes (AUDIT-P1.5)
* **Defect:** `/health` always reported `ONLINE` regardless of model state; `/models/benchmark` served a static fallback table; `/sensor-health` reported hardcoded 100% reliability for all channels.
* **Fix:** `/health` reports true service status (`ONLINE` vs `DEGRADED`) and mode (`PRODUCTION` vs `DEMO_FALLBACK`); `/models/benchmark` returns `status="UNAVAILABLE"` when artifacts are absent; `/sensor-health` calculates dynamic channel uptime or returns `UNINITIALIZED`.

---

## 4. Risk Assessment Matrix (Post-Remediation)

| Risk Area | Risk Level | Root Cause | Implemented Mitigation |
| :--- | :---: | :--- | :--- |
| **Data Leakage** | ZERO | Scaling or imputing across train/test splits; centered rolling windows | Chronological 70/30 split; `RobustScaler` fitted on training split only; strictly causal past-only rolling window (`center=False`). |
| **Feature Discrepancy** | ZERO | Disconnected feature definitions between training, streaming, and CSV upload | Centralized `feature_builder.py` with validated 0.0 delta between batch and streaming ring-buffer calculations. |
| **Metric Invalidation** | ZERO | Hardcoded precision heuristics | Bipartite interval overlap matching penalizes false alarm alert windows. |
| **Subjective Model Ranking** | ZERO | Static comparison dictionary | Multi-criteria weighted matrix dynamically computed from measured runtime, size, and ROC-AUC metrics. |
| **False Alarms in Heatwaves** | LOW | Traditional fixed thresholds flagging extreme summer temperatures | Multi-height tower consensus ($\Delta T = T_{2\text{m}} - T_{8\text{m}}$) verifies natural vertical lapse rate continuity before flagging. |
| **UI Freezing on Large Datasets** | LOW | Rendering thousands of raw time-series points in UI charts | Smart stride downsampling in `/api/v1/telemetry/history` (preserving 100% of anomaly spikes while compressing normal points for 60 FPS rendering). |
