import pandas as pd


input_file = "data/processed/aws_evidence_matrix.csv"


df = pd.read_csv(input_file)


# Only rows where Isolation Forest produced
# a prediction: the chronological test period.
test = df[
    df["if_evidence_available"] == 1
].copy()


# Make sure all evidence fields are integers.
evidence_columns = [
    "rule_anomaly_flag",
    "strong_station_evidence",
    "cross_sensor_evidence",
    "temporal_evidence",
    "anomaly_flag"
]

for column in evidence_columns:
    test[column] = (
        test[column]
        .fillna(0)
        .astype(int)
    )


if_anomalies = test[
    test["anomaly_flag"] == 1
].copy()


print("Total test observations:", len(test))

print(
    "Isolation Forest anomalies:",
    len(if_anomalies)
)


print("\n========================================")
print("EVIDENCE AMONG IF ANOMALIES")
print("========================================")


print(
    "IF + Rule evidence:",
    if_anomalies["rule_anomaly_flag"].sum()
)

print(
    "IF + Strong station evidence:",
    if_anomalies["strong_station_evidence"].sum()
)

print(
    "IF + Cross-sensor evidence:",
    if_anomalies["cross_sensor_evidence"].sum()
)

print(
    "IF + Temporal evidence:",
    if_anomalies["temporal_evidence"].sum()
)


# Number of different evidence sources
if_anomalies["evidence_source_count"] = (
    if_anomalies[
        [
            "rule_anomaly_flag",
            "strong_station_evidence",
            "cross_sensor_evidence",
            "temporal_evidence"
        ]
    ].sum(axis=1)
)


print("\nEvidence source count among IF anomalies:")

print(
    if_anomalies["evidence_source_count"]
    .value_counts()
    .sort_index()
    .to_string()
)


print("\n========================================")
print("IF ANOMALY CATEGORIES")
print("========================================")


only_if = if_anomalies[
    if_anomalies["evidence_source_count"] == 0
]

print(
    "IF only:",
    len(only_if)
)


strong_multi = if_anomalies[
    if_anomalies["evidence_source_count"] >= 2
]

print(
    "IF + at least 2 other evidence sources:",
    len(strong_multi)
)


all_four = if_anomalies[
    if_anomalies["evidence_source_count"] == 4
]

print(
    "IF + all 4 evidence sources:",
    len(all_four)
)


print("\n========================================")
print("PAIRWISE OVERLAP")
print("========================================")


pairs = [
    (
        "Rule",
        "Cross-sensor",
        "rule_anomaly_flag",
        "cross_sensor_evidence"
    ),
    (
        "Rule",
        "Temporal",
        "rule_anomaly_flag",
        "temporal_evidence"
    ),
    (
        "Rule",
        "Station",
        "rule_anomaly_flag",
        "strong_station_evidence"
    ),
    (
        "Cross-sensor",
        "Temporal",
        "cross_sensor_evidence",
        "temporal_evidence"
    ),
    (
        "Cross-sensor",
        "Station",
        "cross_sensor_evidence",
        "strong_station_evidence"
    ),
    (
        "Temporal",
        "Station",
        "temporal_evidence",
        "strong_station_evidence"
    )
]


for name1, name2, col1, col2 in pairs:

    overlap = (
        if_anomalies[col1].astype(bool)
        &
        if_anomalies[col2].astype(bool)
    ).sum()

    print(
        f"{name1} + {name2}:",
        overlap
    )


print("\n========================================")
print("MOST MULTI-EVIDENCE IF ANOMALIES")
print("========================================")


columns = [
    "timestamp",
    "anomaly_score",
    "rule_anomaly_flag",
    "strong_station_evidence",
    "cross_sensor_evidence",
    "temporal_evidence",
    "evidence_source_count"
]


print(
    if_anomalies
    .sort_values(
        [
            "evidence_source_count",
            "anomaly_score"
        ],
        ascending=[
            False,
            True
        ]
    )
    [columns]
    .head(20)
    .to_string(index=False)
)