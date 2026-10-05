import pandas as pd

input_file = "data/processed/aws_if_evidence.csv"

df = pd.read_csv(input_file)

df["timestamp"] = pd.to_datetime(
    df["timestamp"]
)

df = df.sort_values(
    "timestamp"
).reset_index(drop=True)


# Time difference between anomalous observations
df["gap_from_previous_anomaly"] = (
    df["timestamp"].diff().dt.total_seconds() / 60
)


# Start a new event when the gap is greater than 60 minutes
df["new_event"] = (
    df["gap_from_previous_anomaly"].isna()
    |
    (df["gap_from_previous_anomaly"] > 60)
).astype(int)


df["event_id"] = df["new_event"].cumsum()


events = df.groupby(
    "event_id"
).agg(
    start_time=("timestamp", "min"),
    end_time=("timestamp", "max"),
    observations=("timestamp", "count"),
    minimum_anomaly_score=("anomaly_score", "min"),
    missing_sensor_rows=("missing_core_sensor", "sum"),
    zero_battery_rows=("zero_battery", "sum"),
    all_temperature_zero_rows=("all_temperature_zero", "sum"),
    all_humidity_zero_rows=("all_humidity_zero", "sum"),
    temperature_disagreement_rows=("temperature_disagreement", "sum"),
    humidity_disagreement_rows=("humidity_disagreement", "sum"),
    large_gap_rows=("time_gap_minutes", lambda x: (x > 60).sum())
).reset_index()


events["duration_minutes"] = (
    events["end_time"] - events["start_time"]
).dt.total_seconds() / 60


print("Total anomalous observations:", len(df))

print(
    "Total anomaly events:",
    len(events)
)

print(
    "Average observations per event:",
    events["observations"].mean()
)


print("\n--- EVENT SIZE DISTRIBUTION ---")

print(
    events["observations"]
    .value_counts()
    .sort_index()
    .to_string()
)


print("\n--- LARGEST ANOMALY EVENTS ---")

largest = events.sort_values(
    [
        "observations",
        "minimum_anomaly_score"
    ],
    ascending=[
        False,
        True
    ]
).head(15)


print(
    largest.to_string(index=False)
)


print("\n--- EVENTS WITH ZERO BATTERY ---")

power_events = events[
    events["zero_battery_rows"] > 0
]

print(
    power_events.to_string(index=False)
)


events.to_csv(
    "data/processed/aws_anomaly_events.csv",
    index=False
)

print(
    "\nSaved:",
    "data/processed/aws_anomaly_events.csv"
)