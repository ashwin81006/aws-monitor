import pandas as pd


INPUT_FILE = "data/processed/aws_evidence_matrix.csv"
OUTPUT_FILE = "data/processed/aws_event_fusion.csv"


matrix = pd.read_csv(INPUT_FILE)
matrix["timestamp"] = pd.to_datetime(matrix["timestamp"])


matrix["anomaly_flag"] = (
    matrix["anomaly_flag"]
    .fillna(0)
    .astype(int)
)

anomalies = matrix[
    matrix["if_evidence_available"] == 1
].copy()

anomalies = anomalies[
    anomalies["anomaly_flag"] == 1
].sort_values(
    "timestamp"
).reset_index(drop=True)


anomalies["gap_from_previous_anomaly"] = (
    anomalies["timestamp"].diff().dt.total_seconds() / 60
)

anomalies["new_event"] = (
    anomalies["gap_from_previous_anomaly"].isna()
    | (anomalies["gap_from_previous_anomaly"] > 60)
).astype(int)

anomalies["event_id"] = anomalies["new_event"].cumsum()


evidence_columns = [
    "station_system_evidence",
    "core_sensor_quality_evidence",
    "continuity_evidence",
    "cross_sensor_evidence",
    "temporal_evidence"
]

for column in evidence_columns:
    anomalies[column] = (
        anomalies[column].fillna(0).astype(int)
    )


events = anomalies.groupby("event_id").agg(
    start_time=("timestamp", "min"),
    end_time=("timestamp", "max"),
    observations=("timestamp", "count"),
    minimum_anomaly_score=("anomaly_score", "min"),
    station_system_rows=("station_system_evidence", "sum"),
    core_sensor_quality_rows=("core_sensor_quality_evidence", "sum"),
    continuity_rows=("continuity_evidence", "sum"),
    cross_sensor_rows=("cross_sensor_evidence", "sum"),
    temporal_rows=("temporal_evidence", "sum")
).reset_index()


events["duration_minutes"] = (
    events["end_time"] - events["start_time"]
).dt.total_seconds() / 60

events["has_station_system_evidence"] = (
    events["station_system_rows"] > 0
).astype(int)

events["has_core_sensor_quality"] = (
    events["core_sensor_quality_rows"] > 0
).astype(int)
events["has_continuity_evidence"] = (
    events["continuity_rows"] > 0
).astype(int)
events["has_cross_sensor_evidence"] = (
    events["cross_sensor_rows"] > 0
).astype(int)
events["has_temporal_evidence"] = (
    events["temporal_rows"] > 0
).astype(int)

events["meaningful_evidence_count"] = events[
    [
        "has_station_system_evidence",
        "has_core_sensor_quality",
        "has_continuity_evidence",
        "has_cross_sensor_evidence",
        "has_temporal_evidence"
    ]
].sum(axis=1)


events["candidate_class"] = "UNCERTAIN"
events["severity"] = "LOW"
events["probable_root_cause"] = "UNRESOLVED_ANOMALY"


for index, event in events.iterrows():
    station = event["has_station_system_evidence"]
    core = event["has_core_sensor_quality"]
    continuity = event["has_continuity_evidence"]
    cross_sensor = event["has_cross_sensor_evidence"]
    temporal = event["has_temporal_evidence"]

    if station == 1:
        events.loc[index, "candidate_class"] = "PROBABLE_SENSOR_FAULT"
        events.loc[index, "severity"] = "HIGH"
        events.loc[index, "probable_root_cause"] = "STATION_OR_POWER_FAILURE"
        continue

    if core == 1 and cross_sensor == 1:
        events.loc[index, "candidate_class"] = "PROBABLE_SENSOR_FAULT"
        events.loc[index, "severity"] = "HIGH"
        events.loc[index, "probable_root_cause"] = "SENSOR_OR_DATA_QUALITY"
        continue

    if core == 1 and continuity == 1:
        events.loc[index, "severity"] = "MEDIUM"
        events.loc[index, "probable_root_cause"] = "DATA_AVAILABILITY_OR_SENSOR_QUALITY"
        continue

    if (
        temporal == 1
        and station == 0
        and core == 0
        and cross_sensor == 0
    ):
        events.loc[index, "candidate_class"] = "POSSIBLE_WEATHER_EXTREME"
        events.loc[index, "severity"] = "MEDIUM"
        events.loc[index, "probable_root_cause"] = "RAPID_BUT_COHERENT_WEATHER_CHANGE"
        continue

    if (
        cross_sensor == 1
        and temporal == 1
        and core == 0
        and station == 0
    ):
        events.loc[index, "severity"] = "MEDIUM"
        events.loc[index, "probable_root_cause"] = "UNUSUAL_WEATHER_OR_SENSOR_BEHAVIOR"
        continue

    if (
        cross_sensor == 1
        and core == 0
        and station == 0
    ):
        events.loc[index, "probable_root_cause"] = "CROSS_SENSOR_DISAGREEMENT"
        continue


print("Total IF anomalous observations:", len(anomalies))
print("Total anomaly events:", len(events))

print("\n========================================")
print("EVENT-LEVEL CLASSIFICATION")
print("========================================")
print(events["candidate_class"].value_counts().to_string())

print("\n========================================")
print("EVENT SEVERITY")
print("========================================")
print(events["severity"].value_counts().to_string())

print("\n========================================")
print("EVENT ROOT CAUSES")
print("========================================")
print(events["probable_root_cause"].value_counts().to_string())

print("\n========================================")
print("EVENT CLASSIFICATION TABLE")
print("========================================")
print(
    events[
        [
            "event_id",
            "start_time",
            "end_time",
            "observations",
            "minimum_anomaly_score",
            "has_station_system_evidence",
            "has_core_sensor_quality",
            "has_continuity_evidence",
            "has_cross_sensor_evidence",
            "has_temporal_evidence",
            "candidate_class",
            "severity",
            "probable_root_cause"
        ]
    ].head(30).to_string(index=False)
)


events.to_csv(OUTPUT_FILE, index=False)

print("\nSaved:", OUTPUT_FILE)
