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


# Combine the anomaly results with the original feature data
df = features.copy()

df["anomaly_score"] = np.nan
df["anomaly_flag"] = 0

df.loc[
    df.index[-len(results):],
    "anomaly_score"
] = results["anomaly_score"].values

df.loc[
    df.index[-len(results):],
    "anomaly_flag"
] = results["anomaly_flag"].values


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


# Use average of the three levels for a simple temporal view
df["temperature_mean"] = df[temp_columns].mean(axis=1)
df["humidity_mean"] = df[rh_columns].mean(axis=1)


# Previous and next observations
df["temperature_previous"] = df["temperature_mean"].shift(1)
df["temperature_next"] = df["temperature_mean"].shift(-1)

df["humidity_previous"] = df["humidity_mean"].shift(1)
df["humidity_next"] = df["humidity_mean"].shift(-1)


# Change before and after anomaly
df["temperature_change_before"] = (
    df["temperature_mean"]
    - df["temperature_previous"]
)

df["temperature_change_after"] = (
    df["temperature_next"]
    - df["temperature_mean"]
)

df["humidity_change_before"] = (
    df["humidity_mean"]
    - df["humidity_previous"]
)

df["humidity_change_after"] = (
    df["humidity_next"]
    - df["humidity_mean"]
)


anomalies = df[
    df["anomaly_flag"] == 1
].copy()


print("Total anomalies:", len(anomalies))


print("\n--- TEMPORAL ANOMALY SUMMARY ---")


# Large temperature jump into anomaly
temp_jump_before = (
    anomalies["temperature_change_before"].abs() > 5
)

print(
    "Temperature jump > 5°C before anomaly:",
    temp_jump_before.sum()
)


# Large temperature rebound after anomaly
temp_jump_after = (
    anomalies["temperature_change_after"].abs() > 5
)

print(
    "Temperature change > 5°C after anomaly:",
    temp_jump_after.sum()
)


# Large humidity jump
humidity_jump_before = (
    anomalies["humidity_change_before"].abs() > 20
)

print(
    "Humidity jump > 20% before anomaly:",
    humidity_jump_before.sum()
)


humidity_jump_after = (
    anomalies["humidity_change_after"].abs() > 20
)

print(
    "Humidity change > 20% after anomaly:",
    humidity_jump_after.sum()
)


print("\n--- TOP 15 ANOMALIES WITH TEMPORAL CONTEXT ---")


columns = [
    "timestamp",
    "anomaly_score",

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


top = anomalies.sort_values(
    "anomaly_score"
).head(15)


print(
    top[columns].to_string(index=False)
)