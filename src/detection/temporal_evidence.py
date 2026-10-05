import json
import pandas as pd
import numpy as np


input_file = "data/processed/aws_clean.csv"
threshold_file = "models/temporal_thresholds.json"
output_file = "data/processed/aws_temporal_evidence.csv"


df = pd.read_csv(input_file)

df["timestamp"] = pd.to_datetime(
    df["timestamp"]
)


with open(threshold_file, "r") as file:
    thresholds = json.load(file)


temperature_threshold = thresholds[
    "temperature_rate_99th_percentile"
]

humidity_threshold = thresholds[
    "humidity_rate_99th_percentile"
]


temp_columns = [
    "AIR_TEMPERATURE1(°C at 2m height)",
    "AIR_TEMPERATURE2(°C at 4m height)",
    "AIR_TEMPERATURE3(°C at 8m height)"
]

rh_columns = [
    "RELATIVE_HUMIDITY1(% at 2m height)",
    "RELATIVE_HUMIDITY2(% at 4m height)",
    "RELATIVE_HUMIDITY3(% at 8m height)"
]


# Remove known invalid values
temperature = df[temp_columns].copy()

for column in temp_columns:
    temperature.loc[
        temperature[column] == -40,
        column
    ] = np.nan


humidity = df[rh_columns].copy()

for column in rh_columns:
    humidity.loc[
        (humidity[column] < 0)
        |
        (humidity[column] > 100),
        column
    ] = np.nan


# Use the median across heights so that
# one faulty sensor does not dominate the
# station-level temporal signal.
df["temperature_median"] = (
    temperature.median(axis=1)
)

df["humidity_median"] = (
    humidity.median(axis=1)
)


# Time since previous observation
df["previous_gap_minutes"] = (
    df["timestamp"]
    .diff()
    .dt.total_seconds()
    / 60
)


# Previous station-level values
df["temperature_previous"] = (
    df["temperature_median"].shift(1)
)

df["humidity_previous"] = (
    df["humidity_median"].shift(1)
)


# Only compare genuinely consecutive observations
valid_previous = (
    (df["previous_gap_minutes"] > 0)
    &
    (df["previous_gap_minutes"] <= 60)
)


# Change from previous observation
df["temperature_change"] = (
    df["temperature_median"]
    -
    df["temperature_previous"]
)

df["humidity_change"] = (
    df["humidity_median"]
    -
    df["humidity_previous"]
)


# Convert change to rate per hour
df["temperature_rate"] = (
    df["temperature_change"].abs()
    /
    (df["previous_gap_minutes"] / 60)
)

df["humidity_rate"] = (
    df["humidity_change"].abs()
    /
    (df["previous_gap_minutes"] / 60)
)


# Remove invalid temporal comparisons
df.loc[
    ~valid_previous,
    [
        "temperature_change",
        "humidity_change",
        "temperature_rate",
        "humidity_rate"
    ]
] = np.nan


# Evidence flags
df["temperature_rate_anomaly"] = (
    df["temperature_rate"]
    > temperature_threshold
).fillna(False)


df["humidity_rate_anomaly"] = (
    df["humidity_rate"]
    > humidity_threshold
).fillna(False)


df["temporal_evidence"] = (
    df["temperature_rate_anomaly"]
    |
    df["humidity_rate_anomaly"]
).astype(int)


df["temporal_evidence_count"] = (
    df["temperature_rate_anomaly"].astype(int)
    +
    df["humidity_rate_anomaly"].astype(int)
)


print("Total observations:", len(df))

print("\n--- TEMPORAL EVIDENCE ---")

print(
    "Temperature rate threshold:",
    temperature_threshold,
    "°C/hour"
)

print(
    "Humidity rate threshold:",
    humidity_threshold,
    "%/hour"
)

print(
    "\nTemperature rate anomalies:",
    df["temperature_rate_anomaly"].sum()
)

print(
    "Humidity rate anomalies:",
    df["humidity_rate_anomaly"].sum()
)

print(
    "Rows with temporal evidence:",
    df["temporal_evidence"].sum()
)


print("\n--- TEMPORAL EVIDENCE COUNT ---")

print(
    df["temporal_evidence_count"]
    .value_counts()
    .sort_index()
    .to_string()
)


print("\n--- STRONGEST TEMPORAL EVENTS ---")

strong = df[
    df["temporal_evidence"] == 1
].sort_values(
    [
        "temperature_rate",
        "humidity_rate"
    ],
    ascending=False
)


print(
    strong[
        [
            "timestamp",
            "previous_gap_minutes",
            "temperature_median",
            "temperature_change",
            "temperature_rate",
            "humidity_median",
            "humidity_change",
            "humidity_rate",
            "temperature_rate_anomaly",
            "humidity_rate_anomaly"
        ]
    ].head(20).to_string(index=False)
)


output_columns = [
    "timestamp",

    "previous_gap_minutes",

    "temperature_median",
    "temperature_change",
    "temperature_rate",
    "temperature_rate_anomaly",

    "humidity_median",
    "humidity_change",
    "humidity_rate",
    "humidity_rate_anomaly",

    "temporal_evidence_count",
    "temporal_evidence"
]


df[output_columns].to_csv(
    output_file,
    index=False
)


print(
    "\nSaved:",
    output_file
)