import pandas as pd
import numpy as np

clean_file = "data/processed/aws_clean.csv"
if_file = "data/processed/aws_if_results.csv"

output_file = "data/processed/aws_if_evidence.csv"


clean = pd.read_csv(clean_file)
results = pd.read_csv(if_file)

clean["timestamp"] = pd.to_datetime(
    clean["timestamp"]
)

results["timestamp"] = pd.to_datetime(
    results["timestamp"]
)


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


# Work only with the test-period observations
test_start = results["timestamp"].min()
test_data = clean[
    clean["timestamp"] >= test_start
].copy()


# Attach IF results
df = test_data.merge(
    results[
        [
            "timestamp",
            "anomaly_score",
            "anomaly_flag"
        ]
    ],
    on="timestamp",
    how="left"
)


# Core missing-data evidence
df["missing_core_sensor"] = (
    df[temp_columns + rh_columns]
    .isna()
    .any(axis=1)
)


# Battery evidence
df["zero_battery"] = (
    df["BATTRY_VOLTAGE(V)"] == 0
)


# All temperature sensors zero
df["all_temperature_zero"] = (
    df[temp_columns] == 0
).all(axis=1)


# All humidity sensors zero
df["all_humidity_zero"] = (
    df[rh_columns] == 0
).all(axis=1)


# Cross-sensor spread
df["temperature_spread"] = (
    df[temp_columns].max(axis=1)
    -
    df[temp_columns].min(axis=1)
)

df["humidity_spread"] = (
    df[rh_columns].max(axis=1)
    -
    df[rh_columns].min(axis=1)
)


# Exploratory disagreement indicators
df["temperature_disagreement"] = (
    df["temperature_spread"] > 5
)

df["humidity_disagreement"] = (
    df["humidity_spread"] > 20
)


# Time-gap evidence
df["time_gap_large"] = (
    df["time_gap_minutes"] > 60
)


# Station-level means for temporal evidence
df["temperature_mean"] = (
    df[temp_columns].mean(axis=1)
)

df["humidity_mean"] = (
    df[rh_columns].mean(axis=1)
)


# Previous / next timestamps
df["previous_timestamp"] = (
    df["timestamp"].shift(1)
)

df["next_timestamp"] = (
    df["timestamp"].shift(-1)
)


df["previous_gap_minutes"] = (
    df["timestamp"]
    .diff()
    .dt.total_seconds()
    / 60
)

df["next_gap_minutes"] = (
    df["timestamp"]
    .shift(-1)
    .sub(df["timestamp"])
    .dt.total_seconds()
    / 60
)


# Previous / next station means
df["temperature_previous"] = (
    df["temperature_mean"].shift(1)
)

df["temperature_next"] = (
    df["temperature_mean"].shift(-1)
)

df["humidity_previous"] = (
    df["humidity_mean"].shift(1)
)

df["humidity_next"] = (
    df["humidity_mean"].shift(-1)
)


# Remove temporal neighbors when gaps are too large
valid_previous = (
    df["previous_gap_minutes"] <= 60
)

valid_next = (
    df["next_gap_minutes"] <= 60
)


df.loc[
    ~valid_previous,
    [
        "temperature_previous",
        "humidity_previous"
    ]
] = np.nan


df.loc[
    ~valid_next,
    [
        "temperature_next",
        "humidity_next"
    ]
] = np.nan


# Temporal changes
df["temperature_change_before"] = (
    df["temperature_mean"]
    -
    df["temperature_previous"]
)

df["temperature_change_after"] = (
    df["temperature_next"]
    -
    df["temperature_mean"]
)

df["humidity_change_before"] = (
    df["humidity_mean"]
    -
    df["humidity_previous"]
)

df["humidity_change_after"] = (
    df["humidity_next"]
    -
    df["humidity_mean"]
)


# Keep anomalies only
anomalies = df[
    df["anomaly_flag"] == 1
].copy()


# Sort by Isolation Forest abnormality
anomalies = anomalies.sort_values(
    "anomaly_score"
)


columns = [
    "timestamp",
    "anomaly_score",

    "missing_core_sensor",
    "zero_battery",
    "all_temperature_zero",
    "all_humidity_zero",

    "temperature_spread",
    "humidity_spread",
    "temperature_disagreement",
    "humidity_disagreement",

    "time_gap_minutes",
    "previous_gap_minutes",
    "next_gap_minutes",

    "temperature_change_before",
    "temperature_change_after",

    "humidity_change_before",
    "humidity_change_after"
]


print("Total IF anomalies:", len(anomalies))

print("\nEvidence counts:")

print(
    "Missing core sensor:",
    anomalies["missing_core_sensor"].sum()
)

print(
    "Zero battery:",
    anomalies["zero_battery"].sum()
)

print(
    "All temperature zero:",
    anomalies["all_temperature_zero"].sum()
)

print(
    "All humidity zero:",
    anomalies["all_humidity_zero"].sum()
)

print(
    "Temperature disagreement:",
    anomalies["temperature_disagreement"].sum()
)

print(
    "Humidity disagreement:",
    anomalies["humidity_disagreement"].sum()
)

print(
    "Large time gap:",
    anomalies["time_gap_large"].sum()
)


print("\nTop 20 evidence rows:")

print(
    anomalies[columns]
    .head(20)
    .to_string(index=False)
)


anomalies[columns].to_csv(
    output_file,
    index=False
)

print("\nSaved:", output_file)