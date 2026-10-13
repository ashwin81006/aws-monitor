# AWS Monitor: Intelligent Anomaly Detection & Self-Healing for Automatic Weather Stations

An end-to-end meteorological quality control, anomaly detection, explainability, and real-time self-healing engine developed for **Automatic Weather Stations (ISRO AWS Station `ISRO0119_15F077`, VIT Vellore, Tamil Nadu)**.

Focuses strictly on the core meteorological channels:
* **Air Temperature (°C)**
* **Relative Humidity (%)**
* **Atmospheric Pressure (hPa)**

---

## Key System Capabilities

* **13 Physical Meteorological Features:** Exact Magnus dew point, vapor deficit ($T - T_d$), kinematic rates ($\frac{dT}{dt}, \frac{dRH}{dt}, \frac{dP}{dt}$), causal bounded rolling MAD deviations, and solar diurnal cycles ($\sin\theta, \cos\theta$).
* **Modular Multi-Model Detection:** Configurable detection across Isolation Forest (Baseline), One-Class SVM, Local Outlier Factor (LOF), Majority Voting, and Calibrated Score Fusion Ensemble ($0.50 \cdot P_{IF} + 0.30 \cdot P_{SVM} + 0.20 \cdot P_{LOF}$).
* **Meteorological Discrimination:** Separates physical extreme weather (monsoon thunderstorm cold-pool downdrafts, severe summer heatwaves) from confirmed hardware faults (ADC spikes, frozen sensors, calibration drift).
* **Auditable Thermodynamic Self-Healing:** Reconstructs faulty observations via physical Magnus psychrometric inversion with explicit confidence intervals ($\pm 0.8^\circ\text{C}$ for physical inversion, $\pm 1.8^\circ\text{C}$ for autoregressive median) and cross-channel corruption checks.
* **Explainability (TreeSHAP):** Global polynomial-time feature rankings and local per-observation directional attribution waterfalls.
* **Controlled Fault-Injection Benchmark:** Evaluates precision, recall, row F1, and event F1 across realistic synthetic sensor failures.
* **Full-Stack Desktop Platform:** FastAPI asynchronous backend paired with a native .NET 10 MAUI cross-platform client with LiveCharts2 data visualizations.

---

## Architecture & Directory Layout

```text
aws-monitor/
├── data/
│   └── raw/
│       └── aws_dataset.csv                  # Confidential ISRO dataset (32,774 observations)
├── models/
│   ├── isolation_forest.pkl                 # Primary production model
│   ├── one_class_svm.pkl                    # Margin boundary model
│   ├── lof.pkl                              # Density outlier model
│   └── scaler.pkl                           # RobustScaler
├── src/
│   ├── preprocessing/
│   │   └── preprocess.py                    # Physical bounds (-10°C to 60°C) & sentinel masking
│   ├── features/
│   │   └── feature_engineering.py           # 13 physical features & streaming extractor with streaks
│   ├── ml/
│   │   ├── train_models.py                  # Chronological 70/30 split & model training
│   │   ├── test_models.py                   # In-memory comparative benchmarking
│   │   └── explain_shap.py                  # Global and local TreeSHAP explainability
│   ├── validation/
│   │   └── validate.py                      # Synthetic fault-injection evaluation suite
│   ├── core/
│   │   ├── detector.py                      # Unified ensemble detector with meteorological filters
│   │   └── self_healing.py                  # Physical Magnus inversion & auditable self-healing
│   └── api/
│       ├── app.py                           # FastAPI application entrypoint
│       ├── routes/                          # REST endpoints (health, telemetry, anomalies, models)
│       ├── schemas/                         # Pydantic contract schemas
│       └── services/                        # In-memory telemetry, health & anomaly services
├── tests/
│   └── test_backend.py                      # 18 automated unit and integration tests (100% passing)
├── ui/
│   └── AwsMonitor.UI/                       # Native .NET 10 MAUI Desktop Client
│       ├── Models/                          # DTOs with bidirectional schema compatibility
│       ├── Services/                        # ApiService with live/demo mode tracking
│       ├── ViewModels/                      # MainViewModel with dynamic bindings and zero mock arrays
│       └── MainPage.xaml                    # Comprehensive multi-tab responsive dashboard
├── API_FRONTEND_MAPPING.md                  # 10/10 verified endpoint-to-screen matrix
├── PROJECT_AUDIT.md                         # Complete initial architecture & defect audit
├── IMPLEMENTATION_REPORT.md                 # Detailed report of all changes implemented
├── EVALUATION_REPORT.md                     # Empirical baseline vs. ensemble comparison
├── TEST_REPORT.md                           # Verification logs and test execution report
└── requirements.txt                         # Python dependencies
```

---

## Execution Guide

### 1. Python Environment Setup
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Run Automated Test Suite
```powershell
python -m unittest tests/test_backend.py
```
*Result: 18/18 tests pass in ~12 seconds.*

### 3. Run Benchmark & Evaluation
```powershell
python src/validation/validate.py
```
*Evaluates row-level and event-level precision, recall, and F1 across all models on injected faults.*

### 4. Start the FastAPI Backend
```powershell
uvicorn src.api.app:app --host 127.0.0.1 --port 8000 --reload
```
Interactive API documentation available at `http://127.0.0.1:8000/docs`.

### 5. Build and Launch the .NET 10 MAUI Client
```powershell
dotnet build ui\AwsMonitor.UI\AwsMonitor.UI.csproj -f net10.0-windows10.0.19041.0 -c Debug
```
To launch:
```powershell
dotnet run --project ui\AwsMonitor.UI\AwsMonitor.UI.csproj -f net10.0-windows10.0.19041.0
```

---

## REST API Specification

| Endpoint | Method | Description |
|---|---|---|
| `/health` | `GET` | Service operational health, active model, and feature count. |
| `/api/v1/station/summary` | `GET` | ISRO VIT station metadata, location, and observation statistics. |
| `/api/v1/telemetry/history` | `GET` | Decimated historical observation timeseries. |
| `/api/v1/anomalies/events` | `GET` | Logged station anomalies with `counts_by_category`. |
| `/api/v1/anomalies/events/{event_id}` | `GET` | Detailed incident evidence breakdown and rule flags. |
| `/api/v1/sensors/health` | `GET` | Individual channel quality scores, status, and fault tallies. |
| `/api/v1/models/benchmark` | `GET` | Throughput, model footprint, and role comparisons. |
| `/api/v1/models/shap` | `GET` | Global TreeSHAP feature importance rankings. |
| `/api/v1/models/shap/explain` | `POST` | Local directional feature attribution for specific telemetry points. |
| `/api/v1/telemetry/stream-point` | `POST` | Real-time streaming point classification, self-healing, and diagnostic scoring. |

---

## Hardware Fault vs. Weather Extreme Decision Logic

1. **Sentinels & Missing Data**: Payload values $\ge 999.0$ or $\le -40.0^\circ\text{C}$ or null immediately flagged as `COMMUNICATION_ERROR` / `POWER_FAULT`.
2. **Frozen Sensor Flatlines**: Consecutive identical float readings $\ge 3$ steps (90 min) flagged as `FROZEN_SENSOR` on the specific channel.
3. **Corroborated Extreme Weather**:
   - *Severe Thunderstorm*: $\frac{dP}{dt} < -2.0\text{ hPa} \land \frac{dRH}{dt} > +10\% \land \frac{dT}{dt} < -2.0^\circ\text{C}$ classified as `BENIGN_EXTREME`.
   - *Severe Heatwave*: $T > 42^\circ\text{C} \land RH < 35\% \land (T - T_d) > 18^\circ\text{C}$ classified as `BENIGN_EXTREME`.
4. **Kinematic Rate Spikes**: Isolated single-channel jump exceeding $|\frac{dT}{dt}| > 6^\circ\text{C}/30\text{min}$ or $|\frac{dP}{dt}| > 12\text{ hPa}/30\text{min}$ classified as `PROBABLE_SENSOR_FAULT`.
5. **Thermodynamic Consistency**: Dew point supersaturation $T_d > T + 0.5^\circ\text{C}$ flagged as physical sensor fault.
6. **Multi-Model ML Ensemble**: Calibrated score fusion evaluating 13-dimensional phase space deviation.
