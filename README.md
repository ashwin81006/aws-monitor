# AWS Monitor: Intelligent Anomaly Detection & Self-Healing for Automatic Weather Stations

An end-to-end meteorological quality control, anomaly detection, and real-time self-healing engine developed for **SIH Problem Statement SIH26073 (Ministry of Earth Sciences)**.

Built on authentic observational data from the **ISRO AWS station at VIT Vellore, Tamil Nadu** (`ISRO0119_15F077`), focusing strictly on the core meteorological channels:
* **Air Temperature (°C)**
* **Relative Humidity (%)**
* **Atmospheric Pressure (hPa)**

---

## Key Highlights

* **Zero Disk Bloat:** Runs entirely in memory without writing intermediate CSV dumps or loose JSON files.
* **13 Physical Meteorological Features:** Dew point, rate of change, causal bounded rolling MAD deviations, and solar diurnal cycles.
* **Triple Unsupervised Benchmark:** Evaluates Isolation Forest, One-Class SVM, and Local Outlier Factor (LOF).
* **Fault Injection Validation:** Evaluated against realistic sensor faults (Spikes, Stagnation/Frozen, Sensor Drift, Communication Loss).
* **Thermodynamic Self-Healing:** Reconstructs faulty or missing observations in real time using physical Magnus inversion and causal autoregressive medians.
* **Full-Stack Architecture:** Asynchronous Python FastAPI backend paired with a native .NET 10 MAUI desktop dashboard.

---

## Clean Project Structure

```text
aws-monitor/
├── data/
│   └── raw/
│       └── aws_dataset.csv                  # Official ISRO dataset (32,774 observations)
├── models/
│   ├── isolation_forest.pkl                 # Primary production model
│   ├── one_class_svm.pkl                    # Boundary benchmark model
│   ├── lof.pkl                              # Density benchmark model
│   └── scaler.pkl                           # RobustScaler
├── src/
│   ├── preprocessing/
│   │   └── preprocess.py                    # Sentinel masking (9999.0°C, -49.9°C) & gap handling
│   ├── features/
│   │   └── feature_engineering.py           # 13 domain features & streaming extractor
│   ├── ml/
│   │   ├── train_models.py                  # Chronological 70/30 split & model training
│   │   └── test_models.py                   # In-memory comparative benchmarking
│   ├── validation/
│   │   └── validate.py                      # Fault injection validation suite
│   ├── core/
│   │   ├── detector.py                      # Unified real-time detection engine
│   │   └── self_healing.py                  # Thermodynamic self-healing data reconstruction
│   └── api/
│       ├── app.py                           # FastAPI main application
│       ├── config.py                        # Station metadata
│       ├── routes/                          # 9 REST endpoints
│       ├── schemas/                         # Pydantic data schemas
│       └── services/                        # In-memory telemetry, health & anomaly services
├── ui/
│   └── AwsMonitor.UI/                       # Native .NET 10 MAUI Desktop Client
├── AwsMonitor.sln / .slnx                   # Visual Studio solution
├── README.md                                # Project documentation
└── SUMMARY_FOR_PROFESSOR.md                 # Technical review summary for college presentation
```

---

## Execution Guide

### 1. Run Pipeline Modules (In Sequential Order)

Each module can be executed independently in memory:

```bash
# 1. Preprocessing
python src/preprocessing/preprocess.py

# 2. Feature Engineering
python src/features/feature_engineering.py

# 3. Model Training
python src/ml/train_models.py

# 4. Comparative Model Testing
python src/ml/test_models.py

# 5. Fault Injection Validation
python src/validation/validate.py
```

### 2. Live Cloud API & Interactive Documentation

The production REST API is deployed on Vercel:
* **Interactive Swagger UI:** [https://aws-monitor-api.vercel.app/docs](https://aws-monitor-api.vercel.app/docs)
* **Publication ReDoc:** [https://aws-monitor-api.vercel.app/redoc](https://aws-monitor-api.vercel.app/redoc)
* **Live Health Check:** [https://aws-monitor-api.vercel.app/health](https://aws-monitor-api.vercel.app/health)

*(Or run locally: `uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --reload`)*

### 3. Launch the .NET MAUI Desktop App

```bash
cd ui/AwsMonitor.UI
dotnet run -f net10.0-windows10.0.19041.0
```

---

## 3-Model Comparison Summary

Evaluated on 9,833 held-out chronological test observations from VIT Vellore:

| Model Architecture | Inference Speed | Artifact Size | TreeSHAP Explainability | Decision |
|---|---|---|---|---|
| **Isolation Forest** | **188,667 obs/sec** | **1,062 KB** | **Native Supported** | **Selected for Production** |
| **One-Class SVM** | 58,470 obs/sec | 411 KB | Kernel approximation | Boundary Baseline |
| **Local Outlier Factor** | 14,278 obs/sec | 6,711 KB | Incompatible | Density Baseline |
