import pandas as pd


input_file = "data/processed/aws_evidence_matrix.csv"
output_file = "data/processed/aws_fusion_candidates.csv"


df = pd.read_csv(input_file)


# We evaluate the period where Isolation Forest
# produced independent future/test predictions.
df = df[
    df["if_evidence_available"] == 1
].copy()


df["anomaly_flag"] = (
    df["anomaly_flag"]
    .fillna(0)
    .astype(int)
)


evidence_columns = [
    "station_system_evidence",
    "core_sensor_quality_evidence",
    "continuity_evidence",
    "cross_sensor_evidence",
    "temporal_evidence"
]


for column in evidence_columns:
    df[column] = (
        df[column]
        .fillna(0)
        .astype(int)
    )


# Count meaningful evidence sources.
df["meaningful_evidence_count"] = (
    df[evidence_columns]
    .sum(axis=1)
)


# -------------------------------------------------
# Candidate classification
# -------------------------------------------------

df["candidate_class"] = "NORMAL"
df["severity"] = "NONE"
df["probable_root_cause"] = "NONE"


# Strong station/system event
strong_station = (
    df["strong_station_system_evidence"] == 1
)


df.loc[
    strong_station,
    "candidate_class"
] = "PROBABLE_SENSOR_FAULT"


df.loc[
    strong_station,
    "severity"
] = "HIGH"


df.loc[
    strong_station,
    "probable_root_cause"
] = "STATION_OR_POWER_FAILURE"


# Station/system evidence corroborated by another
# meaningful evidence source
station_corrob = (
    (df["station_system_evidence"] == 1)
    &
    (
        df["core_sensor_quality_evidence"]
        |
        df["cross_sensor_evidence"]
        |
        df["temporal_evidence"]
        |
        (df["anomaly_flag"] == 1)
    )
)


df.loc[
    station_corrob
    &
    ~strong_station,
    "candidate_class"
] = "PROBABLE_SENSOR_FAULT"


df.loc[
    station_corrob
    &
    ~strong_station,
    "severity"
] = "HIGH"


df.loc[
    station_corrob
    &
    ~strong_station,
    "probable_root_cause"
] = "STATION_OR_POWER_FAILURE"


# Cross-sensor disagreement + core sensor
# quality evidence
cross_core = (
    (df["cross_sensor_evidence"] == 1)
    &
    (df["core_sensor_quality_evidence"] == 1)
)


df.loc[
    cross_core,
    "candidate_class"
] = "PROBABLE_SENSOR_FAULT"


df.loc[
    cross_core,
    "severity"
] = "HIGH"


df.loc[
    cross_core,
    "probable_root_cause"
] = "SENSOR_OR_DATA_QUALITY"


# Cross-sensor disagreement + rapid temporal change
cross_temporal = (
    (df["cross_sensor_evidence"] == 1)
    &
    (df["temporal_evidence"] == 1)
)


df.loc[
    cross_temporal
    &
    ~strong_station
    &
    ~station_corrob,
    "candidate_class"
] = "PROBABLE_SENSOR_FAULT"


df.loc[
    cross_temporal
    &
    ~strong_station
    &
    ~station_corrob,
    "severity"
] = "HIGH"


df.loc[
    cross_temporal
    &
    ~strong_station
    &
    ~station_corrob,
    "probable_root_cause"
] = "SENSOR_DISAGREEMENT_WITH_RAPID_CHANGE"


# Possible weather extreme:
# rapid change, no direct fault evidence,
# and Isolation Forest also considers it unusual.
possible_weather = (
    (df["anomaly_flag"] == 1)
    &
    (df["temporal_evidence"] == 1)
    &
    (df["station_system_evidence"] == 0)
    &
    (df["core_sensor_quality_evidence"] == 0)
    &
    (df["cross_sensor_evidence"] == 0)
)


df.loc[
    possible_weather,
    "candidate_class"
] = "POSSIBLE_WEATHER_EXTREME"


df.loc[
    possible_weather,
    "severity"
] = "MEDIUM"


df.loc[
    possible_weather,
    "probable_root_cause"
] = "RAPID_BUT_COHERENT_WEATHER_CHANGE"


# Any remaining IF anomaly becomes uncertain
remaining_if = (
    (df["anomaly_flag"] == 1)
    &
    (df["candidate_class"] == "NORMAL")
)


df.loc[
    remaining_if,
    "candidate_class"
] = "UNCERTAIN"


df.loc[
    remaining_if,
    "severity"
] = "LOW"


df.loc[
    remaining_if,
    "probable_root_cause"
] = "UNRESOLVED_ANOMALY"


# Other meaningful evidence without an IF anomaly
other_evidence = (
    (df["meaningful_evidence_count"] > 0)
    &
    (df["candidate_class"] == "NORMAL")
)


df.loc[
    other_evidence,
    "candidate_class"
] = "UNCERTAIN"


df.loc[
    other_evidence,
    "severity"
] = "LOW"


df.loc[
    other_evidence,
    "probable_root_cause"
] = "NON_ML_EVIDENCE"


# -------------------------------------------------
# Summary
# -------------------------------------------------

print(
    "Test observations:",
    len(df)
)

print(
    "IF anomalies:",
    df["anomaly_flag"].sum()
)


print("\n========================================")
print("FUSION CANDIDATE CLASSIFICATION")
print("========================================")


print(
    df["candidate_class"]
    .value_counts()
    .to_string()
)


print("\n========================================")
print("SEVERITY")
print("========================================")


print(
    df["severity"]
    .value_counts()
    .to_string()
)


print("\n========================================")
print("ROOT CAUSE")
print("========================================")


print(
    df["probable_root_cause"]
    .value_counts()
    .to_string()
)


print("\n========================================")
print("HIGH-SEVERITY EVENTS")
print("========================================")


high = df[
    df["severity"] == "HIGH"
].sort_values(
    "anomaly_score",
    ascending=True
)


print(
    high[
        [
            "timestamp",
            "anomaly_score",
            "candidate_class",
            "severity",
            "probable_root_cause",
            "meaningful_evidence_count",
            "station_system_evidence",
            "core_sensor_quality_evidence",
            "cross_sensor_evidence",
            "temporal_evidence"
        ]
    ].head(20).to_string(index=False)
)


print("\n========================================")
print("UNCERTAIN IF ANOMALIES")
print("========================================")


uncertain = df[
    (df["candidate_class"] == "UNCERTAIN")
    &
    (df["anomaly_flag"] == 1)
]


print(
    "Count:",
    len(uncertain)
)


print(
    uncertain[
        [
            "timestamp",
            "anomaly_score",
            "meaningful_evidence_count",
            "core_sensor_quality_evidence",
            "cross_sensor_evidence",
            "temporal_evidence"
        ]
    ]
    .head(20)
    .to_string(index=False)
)


df.to_csv(
    output_file,
    index=False
)


print(
    "\nSaved:",
    output_file
)