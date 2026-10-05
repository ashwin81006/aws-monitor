import pandas as pd


input_file = "data/processed/aws_evidence_matrix.csv"

df = pd.read_csv(input_file)


test = df[
    df["if_evidence_available"] == 1
].copy()


test["anomaly_flag"] = (
    test["anomaly_flag"]
    .fillna(0)
    .astype(int)
)


anomalies = test[
    test["anomaly_flag"] == 1
].copy()


evidence_columns = [
    "station_system_evidence",
    "core_sensor_quality_evidence",
    "continuity_evidence",
    "cross_sensor_evidence",
    "temporal_evidence"
]


for column in evidence_columns:
    anomalies[column] = (
        anomalies[column]
        .fillna(0)
        .astype(int)
    )


anomalies["meaningful_evidence_count"] = (
    anomalies[evidence_columns]
    .sum(axis=1)
)


print("IF anomalies:", len(anomalies))


print("\n========================================")
print("MEANINGFUL EVIDENCE CONVERGENCE")
print("========================================")


for column in evidence_columns:

    count = anomalies[column].sum()

    print(
        f"{column}: {count}"
    )


print(
    "\nMeaningful evidence count distribution:"
)

print(
    anomalies["meaningful_evidence_count"]
    .value_counts()
    .sort_index()
    .to_string()
)


print("\n========================================")
print("IF ANOMALIES BY EVIDENCE LEVEL")
print("========================================")


for count in range(6):

    rows = anomalies[
        anomalies["meaningful_evidence_count"] == count
    ]

    print(
        f"{count} supporting evidence sources:",
        len(rows)
    )


print("\n========================================")
print("IF ONLY")
print("========================================")


if_only = anomalies[
    anomalies["meaningful_evidence_count"] == 0
]

print(
    "IF anomalies with no meaningful secondary evidence:",
    len(if_only)
)


print("\n========================================")
print("MULTI-EVIDENCE CASES")
print("========================================")


multi = anomalies[
    anomalies["meaningful_evidence_count"] >= 2
]


print(
    "IF anomalies with at least 2 meaningful evidence sources:",
    len(multi)
)


print(
    "\nExamples:"
)


columns = [
    "timestamp",
    "anomaly_score",
    "station_system_evidence",
    "core_sensor_quality_evidence",
    "continuity_evidence",
    "cross_sensor_evidence",
    "temporal_evidence",
    "meaningful_evidence_count"
]


print(
    multi.sort_values(
        [
            "meaningful_evidence_count",
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