import pandas as pd
import numpy as np

results_file = "data/processed/aws_if_results.csv"

df = pd.read_csv(results_file)

anomalies = df[df["anomaly_flag"] == 1].copy()

print("Total observations:", len(df))
print("Isolation Forest anomalies:", len(anomalies))

print("\n--- ANOMALY EVIDENCE ---")


# Missing sensor readings
sensor_columns = [
    "AIR_TEMPERATURE1(°C at 2m height)",
    "AIR_TEMPERATURE2(°C at 4m height)",
    "AIR_TEMPERATURE3(°C at 8m height)",
    "RELATIVE_HUMIDITY1(% at 2m height)",
    "RELATIVE_HUMIDITY2(% at 4m height)",
    "RELATIVE_HUMIDITY3(% at 8m height)"
]

anomalies["missing_sensor"] = (
    anomalies[sensor_columns].isna().any(axis=1)
)


# Zero battery
anomalies["zero_battery"] = (
    anomalies["BATTRY_VOLTAGE(V)"] == 0
)


# All temperature sensors are zero
temp_columns = [
    "AIR_TEMPERATURE1(°C at 2m height)",
    "AIR_TEMPERATURE2(°C at 4m height)",
    "AIR_TEMPERATURE3(°C at 8m height)"
]

anomalies["all_temperature_zero"] = (
    anomalies[temp_columns] == 0
).all(axis=1)


# All RH sensors are zero
rh_columns = [
    "RELATIVE_HUMIDITY1(% at 2m height)",
    "RELATIVE_HUMIDITY2(% at 4m height)",
    "RELATIVE_HUMIDITY3(% at 8m height)"
]

anomalies["all_humidity_zero"] = (
    anomalies[rh_columns] == 0
).all(axis=1)


# Temperature spread
anomalies["temperature_spread"] = (
    anomalies[temp_columns].max(axis=1)
    -
    anomalies[temp_columns].min(axis=1)
)


# RH spread
anomalies["humidity_spread"] = (
    anomalies[rh_columns].max(axis=1)
    -
    anomalies[rh_columns].min(axis=1)
)


# Large time gap
anomalies["large_time_gap"] = (
    anomalies["time_gap_minutes"] > 60
)


print(
    "\nMissing sensor:",
    anomalies["missing_sensor"].sum()
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
    "Temperature spread > 5°C:",
    (anomalies["temperature_spread"] > 5).sum()
)

print(
    "Humidity spread > 20%:",
    (anomalies["humidity_spread"] > 20).sum()
)

print(
    "Time gap > 60 minutes:",
    anomalies["large_time_gap"].sum()
)


print("\n--- MOST SUSPICIOUS OBSERVATIONS ---")

suspicious = anomalies.sort_values(
    "anomaly_score"
).head(20)

print(
    suspicious[
        [
            "timestamp",
            "anomaly_score",
            "missing_sensor",
            "zero_battery",
            "all_temperature_zero",
            "all_humidity_zero",
            "temperature_spread",
            "humidity_spread",
            "time_gap_minutes"
        ]
    ].to_string(index=False)
)