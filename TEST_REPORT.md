# AWS Monitor — Test & Verification Report

**Project Title:** Intelligent Anomaly Detection for Automatic Weather Stations  
**Target Station:** ISRO Automatic Weather Station `ISRO0119_15F077`, VIT Vellore, Tamil Nadu  
**Audit & Test Timestamp:** October 2026  
**Operating Environment:** Windows 11, Python 3.10, .NET 10.0 SDK  

---

## 1. Summary of Test Execution

| Test Suite / Target | Command Executed | Tests / Steps | Result | Warnings | Errors |
|---|---|---|---|---|---|
| **Backend Unit & Integration Suite** | `python -m unittest tests/test_backend.py` | 18 Test Cases | **18 PASSED** | 0 | 0 |
| **.NET 10 MAUI Windows Target** | `dotnet build ui\AwsMonitor.UI\AwsMonitor.UI.csproj -f net10.0-windows10.0.19041.0 -c Debug` | Compilation & XAML SourceGen | **Build Succeeded** | 0 | 0 |
| **Fault-Injection Benchmark Suite** | `python src/validation/validate.py` | 1,000 Obs Injected Benchmark | **Benchmark Complete** | 0 | 0 |

---

## 2. Backend Automated Test Suite Execution Details

### Command:
```powershell
python -m unittest tests/test_backend.py
```

### Raw Test Execution Output:
```text
Ran 18 tests in 12.779s

OK
```

### Detailed Breakdown of Verified Cases:
1. `test_health_endpoint` — **PASSED**: Verifies `/health` returns status `ONLINE`, station `ISRO0119_15F077`, and 13 evaluated features.
2. `test_station_summary_endpoint` — **PASSED**: Verifies `/api/v1/station/summary` returns observation counts, coordinates, and location.
3. `test_sensors_health_endpoint` — **PASSED**: Verifies `/api/v1/sensors/health` returns list of 3 operational sensor channels (temperature, humidity, pressure).
4. `test_anomaly_events_endpoint` — **PASSED**: Verifies `/api/v1/anomalies/events` returns total event count and category distribution breakdown.
5. `test_anomaly_event_detail_endpoint` — **PASSED**: Verifies `/api/v1/anomalies/events/{id}` retrieves granular evidence breakdown, rule flags, and affected sensor channels.
6. `test_models_benchmark_endpoint` — **PASSED**: Verifies `/api/v1/models/benchmark` returns candidate model comparisons and throughput figures.
7. `test_shap_global_endpoint` — **PASSED**: Verifies `/api/v1/models/shap` computes global TreeSHAP feature importance rankings.
8. `test_shap_explain_observation_endpoint` — **PASSED**: Verifies `POST /api/v1/models/shap/explain` computes directional local SHAP attributions for arbitrary observation payloads.
9. `test_stream_point_inference` — **PASSED**: Verifies live streaming inference on impossible sensor spikes triggers anomaly detection and immediate self-healing reconstruction.
10. `test_psychrometric_dew_point` — **PASSED**: Verifies physical Magnus calculations ensure $T_d < T$ and physically valid temperatures.
11. `test_streaming_feature_extractor_parity` — **PASSED**: Verifies 13-feature extractor maintains non-null, finite mathematical parity between batch and streaming modes.
12. `test_flatline_frozen_sensor_detection` — **PASSED**: Verifies identical repeated float values trigger multi-channel frozen sensor alerts within 10 timesteps.
13. `test_drift_detection` — **PASSED**: Verifies EWMA accumulator captures persistent gradual offset shifts.
14. `test_heatwave_meteorological_discrimination` — **PASSED**: Verifies $46.5^\circ\text{C}$ extreme heat corroborated by moisture depression is classified as `BENIGN_EXTREME`.
15. `test_convective_thunderstorm_discrimination` — **PASSED**: Verifies temperature plunge with moisture surge and pressure drop is classified as genuine `BENIGN_EXTREME`.
16. `test_self_healing_magnus_inversion` — **PASSED**: Verifies temperature reconstruction from valid humidity and conserved dew point with high confidence ($\pm 0.8^\circ\text{C}$).
17. `test_self_healing_cross_channel_corruption_rejection` — **PASSED**: Verifies that when humidity is also corrupted, Magnus inversion is rejected in favor of autoregressive median.
18. `test_detector_modes` — **PASSED**: Verifies all 5 detector modes (`isolation_forest`, `one_class_svm`, `lof`, `calibrated_ensemble`, `majority_voting`) execute cleanly without exceptions.

---

## 3. .NET 10 MAUI Windows Target Build Details

### Command:
```powershell
dotnet build ui\AwsMonitor.UI\AwsMonitor.UI.csproj -f net10.0-windows10.0.19041.0 -c Debug
```

### Raw Compiler Output:
```text
  Determining projects to restore...
  All projects are up-to-date for restore.
  XAML source generation is enabled (MauiXamlInflator=SourceGen). This generates C# code from XAML at compile time for better performance.
  AwsMonitor.UI -> E:\Sem-5-packages\aws-monitor\ui\AwsMonitor.UI\bin\Debug\net10.0-windows10.0.19041.0\win-x64\AwsMonitor.UI.dll

Build succeeded.
    0 Warning(s)
    0 Error(s)

Time Elapsed 00:00:37.85
```

---

## 4. Environment Limitations & Reproduction Commands

- **Local FastAPI Execution**:
  ```powershell
  uvicorn src.api.app:app --host 127.0.0.1 --port 8000 --reload
  ```
- **Run Backend Tests**:
  ```powershell
  python -m unittest tests/test_backend.py
  ```
- **Build & Run Desktop Client**:
  ```powershell
  dotnet build ui\AwsMonitor.UI\AwsMonitor.UI.csproj -f net10.0-windows10.0.19041.0 -c Debug
  ```
