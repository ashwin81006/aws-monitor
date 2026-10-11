# Automatic Weather Station (AWS) Quality Control & Self-Healing Engine
**Project Overview & Technical Summary for Review & Evaluation**

* **Course & Semester:** Semester 5 Capstone / Mini-Project
* **SIH Problem Statement:** SIH26073 — Ministry of Earth Sciences (MoES)
* **Team Members:** Ashwin (Ashy) & Hariharan. V

---

## 1. Executive Summary & Problem Statement

Automatic Weather Stations (AWS) deployed across remote regions transmit continuous telemetry under severe environmental stresses. Hardware failures, sensor degradation, power fluctuations, and communication dropouts frequently corrupt meteorological records. 

This project implements an end-to-end, production-grade quality control and self-healing system tailored specifically to the core parameters specified by the Ministry of Earth Sciences:
1. **Air Temperature (°C)**
2. **Relative Humidity (%)**
3. **Atmospheric Pressure (hPa)**

### Key Highlights
* **Zero Disk Bloat:** Runs entirely in memory without creating temporary intermediate CSV dumps or loose JSON files.
* **Authentic Ground Truth:** Built using real ISRO AWS observational data from VIT Vellore, Tamil Nadu.
* **Physics + Machine Learning:** Combines thermodynamic atmospheric equations with an Isolation Forest model to avoid false alarms during natural weather extremes (such as heatwaves or convective thunderstorms).
* **Automated Self-Healing:** Instantly reconstructs missing or corrupted readings using thermodynamic inversion and autoregressive medians.
* **Multi-Platform:** High-performance Python FastAPI backend paired with a native cross-platform .NET 10 MAUI desktop dashboard.

---

## 2. Dataset Specifications

* **Station ID:** `ISRO0119_15F077` (VIT Vellore, Tamil Nadu, India)
* **Coordinates:** Latitude 12.9692° N, Longitude 79.1559° E
* **Observation Span:** 2006 to 2015 (32,774 authentic continuous observations)
* **Sampling Interval:** 30 minutes
* **Hardware Sentinels Handled:**
  * `9999.0°C` — ADC disconnect / open-circuit probe
  * `-49.9°C` — Platinum RTD ground failure
  * Extended communication dropouts & missing packet records

---

## 3. Strict Sequential ML Pipeline

The system is organized into a clean, modular architecture:

```
Raw ISRO Data (data/raw/aws_dataset.csv)
       │
       ▼
1. Preprocessing (`src/preprocessing/preprocess.py`)
   ├── Hardware sentinel masking (9999.0°C, -49.9°C)
   ├── Communication gap detection
   └── Chronological 70% Train / 30% Test split (Zero temporal leakage)
       │
       ▼
2. Domain Feature Engineering (`src/features/feature_engineering.py`)
   ├── 13 physically-sound meteorological features
   └── StreamingFeatureExtractor (0.0 delta between batch and streaming)
       │
       ▼
3. Model Training (`src/ml/train_models.py`)
   ├── RobustScaler fitting
   └── Fits 3 unsupervised models: Isolation Forest, One-Class SVM, LOF
       │
       ▼
4. Comparative Benchmarking (`src/ml/test_models.py`)
   ├── Evaluates speed, footprint, memory, and TreeSHAP explainability
   └── Production selection: Isolation Forest
       │
       ▼
5. Validation with Fault Injection (`src/validation/validate.py`)
   ├── Injects Spikes, Frozen Stagnation, Drifts, and Communication Loss
   └── Event-level precision & recall evaluation (89.5% event recall)
       │
       ▼
6. Dynamic Self-Healing Engine (`src/core/self_healing.py`)
   ├── Thermodynamic Magnus Inversion (T reconstruction from RH & Dew Point)
   └── Autoregressive causal median imputation
       │
       ▼
7. FastAPI Service & .NET 10 MAUI Desktop Client
```

---

## 4. The 13 Domain Meteorological Features

Rather than arbitrary black-box polynomials, the 13 features are derived directly from thermodynamic atmospheric physics:

| # | Feature Name | Description | Physical Formula / Derivation |
|---|---|---|---|
| 1 | `temperature` | Instantaneous air temperature | Base sensor (°C) |
| 2 | `humidity` | Relative humidity | Base sensor (%) |
| 3 | `pressure` | Barometric atmospheric pressure | Base sensor (hPa) |
| 4 | `dew_point` | Temperature at which air saturates | Magnus-Tetens Equation ($\alpha(T, RH)$) |
| 5 | `dew_point_depression` | Spread between dry bulb & dew point | $T - T_d$ (Must be $\ge 0$ in unsaturated air) |
| 6 | `temp_rate` | Rate of change over 30 minutes | $\Delta T / \Delta t$ (°C / step) |
| 7 | `humidity_rate` | Moisture change over 30 minutes | $\Delta RH / \Delta t$ (% / step) |
| 8 | `pressure_rate` | Barometric tendency | $\Delta P / \Delta t$ (hPa / step) |
| 9 | `temp_dev` | Rolling median absolute deviation | $\|T - \text{median}\| / \max(\text{MAD}, 0.5)$ |
| 10 | `humidity_dev` | Rolling median absolute deviation | $\|RH - \text{median}\| / \max(\text{MAD}, 1.0)$ |
| 11 | `pressure_dev` | Rolling median absolute deviation | $\|P - \text{median}\| / \max(\text{MAD}, 0.5)$ |
| 12 | `sin_hour` | Diurnal solar cycle harmonic | $\sin(2\pi \cdot \text{hour} / 24)$ |
| 13 | `cos_hour` | Diurnal solar cycle harmonic | $\cos(2\pi \cdot \text{hour} / 24)$ |

*Note: The MAD calculations utilize physical scale floors ($0.5$, $1.0$, $0.5$) to prevent division by near-zero during stagnant, integer-rounded measurements.*

---

## 5. 3-Model Empirical Comparison

Evaluated on 9,833 held-out chronological test observations:

| Model Architecture | Inference Speed | Artifact Size | TreeSHAP Explainability | Production Decision |
|---|---|---|---|---|
| **Isolation Forest** | **188,667 obs/sec** | **1,062 KB** | **Full Native Support** | **SELECTED FOR PRODUCTION** |
| **One-Class SVM** | 58,470 obs/sec | 411 KB | Kernel approximation only | Boundary baseline |
| **Local Outlier Factor** | 14,278 obs/sec | 6,711 KB | Incompatible | Density benchmark |

**Selection Rationale:** Isolation Forest provides the fastest inference throughput (>188k points/sec), low memory overhead, robust isolation of multidimensional anomalies, and direct support for TreeSHAP feature attributions.

---

## 6. Fault Injection Validation Results

Evaluated against realistic physical failure scenarios injected into the ISRO test stream:

* **Spike Injections:** $\pm 10^\circ\text{C}$ to $\pm 15^\circ\text{C}$ sudden jumps.
* **Frozen / Stagnant Sensors:** Mechanical potentiometer lockup (zero variance for $>4$ steps).
* **Calibration Drift:** Gradual sensor degradation ($+0.15^\circ\text{C}$ per observation).
* **Communication Loss:** Complete packet dropouts (`NaN` values).

**Performance Metrics:**
* **Event-Level Recall:** **89.5%** (Identifies real multi-step sensor faults reliably)
* **False Alarms on Heatwaves:** **0.0%** (Thermodynamic consistency distinguishes 44°C summer heat from probe failures)
* **False Alarms on Thunderstorms:** **0.0%** (Monsoon convective pressure drops matched with humidity surges are recognized as valid meteorological events)
* **Mean Detection Latency:** $\le 1.1$ observation steps ($\le 33$ minutes)

---

## 7. Thermodynamic Self-Healing

When an anomaly or hardware sentinel is isolated, the self-healing engine reconstructs the missing or corrupted values in real time:

1. **Thermodynamic Magnus Inversion:** When temperature fails but humidity and pressure are valid, the dry-bulb temperature is reconstructed from recent saturation equilibrium:
   $$T_{\text{reconstructed}} = \frac{b \cdot \gamma}{a - \gamma}, \quad \text{where } \gamma = \frac{a \cdot T_d}{b + T_d} - \ln\left(\frac{RH}{100}\right)$$
2. **Autoregressive Running Medians:** When telemetry is lost across all channels (communication dropout), readings are imputed using causal running medians conditioned on the time-of-day solar cycle.
3. **Transparency Flag:** Downstream applications receive both the original reading, the reconstructed value (`corrected_temperature`), and an explicit status flag (`is_healed: true`).

---

## 8. Verification & Test Suite

All components are covered by an automated test suite executed via:
```bash
python tests/run_tests.py
```
**Test Results:** **35 Passed \| 0 Failed (100% Pass Rate)** across 11 test suites:
* Dataset schema and raw sentinel verification
* 13 meteorological feature specification
* Causal batch vs. streaming equivalence (0.0 delta)
* Zero future-data leakage
* Model inference and artifact validation
* Physics rules, sentinels, and extreme weather consensus
* In-memory Bayesian evidence fusion
* Thermodynamic self-healing reconstruction
* Analytical Noisy-OR mathematics
* Event-level precision & recall calculations
* FastAPI REST endpoints & schema validation

---

## 9. System Execution Instructions

### Running the FastAPI Backend
```bash
uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --reload
```
Interactive OpenAPI documentation is accessible at: `http://localhost:8000/docs`

### Building the .NET MAUI Desktop Client
```bash
dotnet build ui/AwsMonitor.UI/AwsMonitor.UI.csproj -f net10.0-windows10.0.19041.0
```
