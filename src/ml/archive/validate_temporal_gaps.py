import pandas as pd
import numpy as np

features_file = "data/processed/aws_features.csv"
results_file = "data/processed/aws_if_results.csv"

features = pd.read_csv(features_file)
results = pd.read_csv(results_file)

features["timestamp"] = pd.to_datetime(
    features["timestamp"]
)

results["timestamp"] = pd.to_datetime(
    results["timestamp"]
)


train_size = len(features) - len(results)

test_features = features.iloc[
    train_size:
].copy().reset_index(drop=True)

test_features["anomaly_score"] = results[
    "anomaly_score"
].values

test_features["anomaly_flag"] = results[
    "anomaly_flag"
].values


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


test_features["temperature_mean"] = (
    test_features[temp_columns].mean(axis=1)
)

test_features["humidity_mean"] = (
    test_features[rh_columns].mean(axis=1)
)


# Actual timestamp gaps
test_features["previous_gap_minutes"] = (
    test_features["timestamp"].diff()
    .dt.total_seconds()
    / 60
)

test_features["next_gap_minutes"] = (
    test_features["timestamp"].shift(-1)
    .sub(test_features["timestamp"])
    .dt.total_seconds()
    / 60
)


# Previous and next values
test_features["temperature_previous"] = (
    test_features["temperature_mean"].shift(1)
)

test_features["temperature_next"] = (
    test_features["temperature_mean"].shift(-1)
)

test_features["humidity_previous"] = (
    test_features["humidity_mean"].shift(1)
)

test_features["humidity_next"] = (
    test_features["humidity_mean"].shift(-1)
)


# Only compare when the timestamps are close enough
valid_previous = (
    test_features["previous_gap_minutes"] <= 60
)

valid_next = (
    test_features["next_gap_minutes"] <= 60
)


test_features.loc[
    ~valid_previous,
    "temperature_previous"
] = np.nan

test_features.loc[
    ~valid_next,
    "temperature_next"
] = np.nan

test_features.loc[
    ~valid_previous,
    "humidity_previous"
] = np.nan

test_features.loc[
    ~valid_next,
    "humidity_next"
] = np.nan


# Changes only when temporal comparison is valid
test_features["temperature_change_before"] = (
    test_features["temperature_mean"]
    - test_features["temperature_previous"]
)

test_features["temperature_change_after"] = (
    test_features["temperature_next"]
    - test_features["temperature_mean"]
)

test_features["humidity_change_before"] = (
    test_features["humidity_mean"]
    - test_features["humidity_previous"]
)

test_features["humidity_change_after"] = (
    test_features["humidity_next"]
    - test_features["humidity_mean"]
)


anomalies = test_features[
    test_features["anomaly_flag"] == 1
].copy()


print("Total IF anomalies:", len(anomalies))

print("\n--- TEMPORAL VALIDITY ---")

print(
    "Valid previous neighbor:",
    anomalies["temperature_previous"].notna().sum()
)

print(
    "Valid next neighbor:",
    anomalies["temperature_next"].notna().sum()
)

print(
    "Previous gap > 60 min:",
    (anomalies["previous_gap_minutes"] > 60).sum()
)

print(
    "Next gap > 60 min:",
    (anomalies["next_gap_minutes"] > 60).sum()
)


print("\n--- VALID TEMPORAL EVENTS ---")

valid_temporal = anomalies[
    anomalies["temperature_previous"].notna()
    &
    anomalies["temperature_next"].notna()
].copy()


print(
    "Anomalies with valid temporal context:",
    len(valid_temporal)
)


temp_jump_before = (
    valid_temporal["temperature_change_before"].abs() > 5
)

temp_jump_after = (
    valid_temporal["temperature_change_after"].abs() > 5
)

rh_jump_before = (
    valid_temporal["humidity_change_before"].abs() > 20
)

rh_jump_after = (
    valid_temporal["humidity_change_after"].abs() > 20
)


print(
    "Temperature jump > 5°C before:",
    temp_jump_before.sum()
)

print(
    "Temperature change > 5°C after:",
    temp_jump_after.sum()
)

print(
    "Humidity jump > 20% before:",
    rh_jump_before.sum()
)

print(
    "Humidity change > 20% after:",
    rh_jump_after.sum()
)


print("\n--- TOP 15 WITH VALID TEMPORAL CONTEXT ---")

top = valid_temporal.sort_values(
    "anomaly_score"
).head(15)


columns = [
    "timestamp",
    "anomaly_score",
    "previous_gap_minutes",
    "next_gap_minutes",
    "temperature_previous",
    "temperature_mean",
    "temperature_next",
    "temperature_change_before",
    "temperature_change_after",
    "humidity_previous",
    "humidity_mean",
    "humidity_next",
    "humidity_change_before",
    "humidity_change_after"
]

print(
    top[columns].to_string(index=False)
)