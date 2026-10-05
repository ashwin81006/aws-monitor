import pandas as pd


input_file = "data/processed/aws_event_fusion.csv"

df = pd.read_csv(input_file)


print("Total anomaly events:", len(df))


print("\n========================================")
print("CLASSIFICATION COUNTS")
print("========================================")

print(
    df["candidate_class"]
    .value_counts()
    .to_string()
)


print("\n========================================")
print("CLASSIFICATION + EVIDENCE")
print("========================================")


evidence_columns = [
    "has_station_system_evidence",
    "has_core_sensor_quality",
    "has_continuity_evidence",
    "has_cross_sensor_evidence",
    "has_temporal_evidence"
]


for column in evidence_columns:

    print(
        column + ":",
        df.groupby("candidate_class")[column]
        .sum()
        .to_string()
    )


print("\n========================================")
print("EVENT EVIDENCE COMBINATIONS")
print("========================================")


combination = (
    df[
        [
            "candidate_class",
            "has_station_system_evidence",
            "has_core_sensor_quality",
            "has_continuity_evidence",
            "has_cross_sensor_evidence",
            "has_temporal_evidence"
        ]
    ]
    .astype(
        {
            "has_station_system_evidence": int,
            "has_core_sensor_quality": int,
            "has_continuity_evidence": int,
            "has_cross_sensor_evidence": int,
            "has_temporal_evidence": int
        }
    )
)


combination["evidence_pattern"] = (
    combination[
        [
            "has_station_system_evidence",
            "has_core_sensor_quality",
            "has_continuity_evidence",
            "has_cross_sensor_evidence",
            "has_temporal_evidence"
        ]
    ]
    .astype(str)
    .agg(
        " + ".join,
        axis=1
    )
)


print(
    combination.groupby(
        [
            "candidate_class",
            "evidence_pattern"
        ]
    )
    .size()
    .sort_values(
        ascending=False
    )
    .to_string()
)


print("\n========================================")
print("PROBABLE SENSOR FAULT EVENTS")
print("========================================")


faults = df[
    df["candidate_class"] ==
    "PROBABLE_SENSOR_FAULT"
].copy()


print(
    faults[
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
            "severity",
            "probable_root_cause"
        ]
    ]
    .sort_values(
        "minimum_anomaly_score"
    )
    .to_string(index=False)
)


print("\n========================================")
print("POSSIBLE WEATHER EVENTS")
print("========================================")


weather = df[
    df["candidate_class"] ==
    "POSSIBLE_WEATHER_EXTREME"
].copy()


print(
    weather[
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
            "severity",
            "probable_root_cause"
        ]
    ]
    .sort_values(
        "minimum_anomaly_score"
    )
    .to_string(index=False)
)


print("\n========================================")
print("UNCERTAIN EVENTS")
print("========================================")


uncertain = df[
    df["candidate_class"] ==
    "UNCERTAIN"
].copy()


print(
    "Count:",
    len(uncertain)
)


print(
    uncertain[
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
            "severity",
            "probable_root_cause"
        ]
    ]
    .head(30)
    .to_string(index=False)
)