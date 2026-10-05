# Intelligent Anomaly Detection for Automatic Weather Stations

An anomaly detection system for identifying unusual patterns and possible sensor faults in Automatic Weather Station (AWS) data.

## Pipeline

```text
Raw AWS Dataset
      ↓
Dataset Inspection
      ↓
Value Analysis
      ↓
EDA
      ↓
Data Cleaning
      ↓
Feature Engineering
      ↓
Processed Feature Dataset
```

## Project Structure

```text
intelligent-anomaly-detection-for-automatic-weather-stations/
│
├── data/
│   ├── raw/
│   │   └── aws_dataset.csv
│   │
│   └── processed/
│       ├── aws_clean.csv
│       └── aws_features.csv
│
├── src/
│   ├── exploration/
│   │   ├── inspect_dataset.py
│   │   ├── analyze_values.py
│   │   └── eda_summary.py
│   │
│   ├── preprocessing/
│   │   └── clean_aws.py
│   │
│   └── features/
│       ├── build_features.py
│       └── archive/
│
└── README.md
```

## 1. Setup

Make sure Python is installed and run all commands from the project root.

Install the required libraries:

```powershell
pip install pandas numpy
```

## 2. Add the Dataset

Place the AWS dataset here:

```text
data/raw/aws_dataset.csv
```

The raw dataset should not be modified manually. The pipeline generates the processed datasets automatically.

## 3. Inspect the Dataset

```powershell
python -u "src/exploration/inspect_dataset.py"
```

Checks:

- Number of rows and columns
- Column names
- Data types
- Missing values
- Basic dataset structure

No processed dataset is created.

## 4. Analyze Sensor Values

```powershell
python -u "src/exploration/analyze_values.py"
```

Checks:

- Minimum and maximum values
- Missing values
- Suspicious values
- Possible sentinel/encoded values

No processed dataset is created.

## 5. Run EDA

```powershell
python -u "src/exploration/eda_summary.py"
```

Provides:

- Sensor statistics
- Missing-value information
- Quality flag counts
- Temporal information
- Dataset summary

No processed dataset is created.

## 6. Clean the Dataset

```powershell
python -u "src/preprocessing/clean_aws.py"
```

**Input:**

```text
data/raw/aws_dataset.csv
```

**Output:**

```text
data/processed/aws_clean.csv
```

The cleaning stage:

- Creates a combined timestamp
- Sorts observations chronologically
- Calculates time gaps
- Flags large time gaps
- Tracks missing values
- Flags known suspicious/sentinel values
- Preserves the original measurements

Suspicious values are flagged rather than automatically deleted.

## 7. Build Features

```powershell
python -u "src/features/build_features.py"
```

**Input:**

```text
data/processed/aws_clean.csv
```

**Output:**

```text
data/processed/aws_features.csv
```

The feature engineering stage creates:

### Temporal Features

```text
previous value
change
rate of change
```

Time gaps are considered when calculating these features.

### Cross-Sensor Features

```text
temperature_valid_count
temperature_mean
temperature_spread

humidity_valid_count
humidity_mean
humidity_spread
```

Sensor deviations are also calculated.

### Rolling Features

```text
rolling_mean
rolling_std
```

using previous observations.

### Repetition Features

Used to identify potentially frozen/stuck sensors:

```text
same_as_previous
repeat_count
repeat_duration_minutes
```

These calculations are designed to respect temporal gaps.

## 8. Final Processed Dataset

After running `build_features.py`, the main processed feature dataset is:

```text
data/processed/aws_features.csv
```

Current result:

```text
Rows:    23,807
Columns: 156
```

## Complete Execution

From a fresh raw dataset, run:

```powershell
python -u "src/exploration/inspect_dataset.py"
python -u "src/exploration/analyze_values.py"
python -u "src/preprocessing/clean_aws.py"
python -u "src/exploration/eda_summary.py"
python -u "src/features/build_features.py"
```

The generated files are:

```text
data/raw/aws_dataset.csv
          │
          ▼
   Exploration Scripts
          │
          ▼
   clean_aws.py
          │
          ├──► data/processed/aws_clean.csv
          │
          ▼
   build_features.py
          │
          └──► data/processed/aws_features.csv
```

### Execution Summary

| Stage | Script | Output |
|---|---|---|
| Inspect | `inspect_dataset.py` | Terminal output |
| Analyze | `analyze_values.py` | Terminal output |
| EDA | `eda_summary.py` | Terminal output |
| Clean | `clean_aws.py` | `aws_clean.csv` |
| Feature Engineering | `build_features.py` | `aws_features.csv` |

## Current Status

```text
M0  Problem + Architecture       DONE
M1  Dataset Inspection           DONE
M2  Data Cleaning                DONE
M3  EDA                          DONE
M4  Feature Engineering         DONE

M5  Isolation Forest             NEXT
```

The current pipeline ends at:

```text
aws_features.csv
```

The anomaly-detection/ML stage will be added separately.
