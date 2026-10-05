import pandas as pd


input_file = "data/processed/aws_evidence_matrix.csv"

df = pd.read_csv(input_file)


# Only the future/test period where IF predictions exist
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


qc_columns = [
    "station_system_evidence",
    "core_sensor_quality_evidence",
    "continuity_evidence",
    "auxiliary_channel_evidence"
]


for column in qc_columns:
    anomalies[column] = (
        anomalies[column]
        .fillna(0)
        .astype(int)
    )


print("Test observations:", len(test))
print("IF anomalies:", len(anomalies))


print("\n========================================")
print("IF + QC CATEGORIES")
print("========================================")


for column in qc_columns:

    count = anomalies[column].sum()

    percentage = (
        count / len(anomalies) * 100
    )

    print(
        f"{column}: {count} ({percentage:.2f}%)"
    )


# Count the QC categories present on each
# IF anomaly.
anomalies["qc_category_count"] = (
    anomalies[qc_columns].sum(axis=1)
)


print("\n========================================")
print("QC CATEGORY COUNT PER IF ANOMALY")
print("========================================")

print(
    anomalies["qc_category_count"]
    .value_counts()
    .sort_index()
    .to_string()
)


print("\n========================================")
print("IF ANOMALIES WITH NO QC CATEGORY")
print("========================================")


no_qc = (
    anomalies["qc_category_count"] == 0
)

print(
    "No QC category:",
    no_qc.sum()
)


print(
    "At least one QC category:",
    (~no_qc).sum()
)


print("\n========================================")
print("STRONG STATION CASES AMONG IF ANOMALIES")
print("========================================")


station = anomalies[
    anomalies["station_system_evidence"] == 1
]


print(
    station[
        [
            "timestamp",
            "anomaly_score",
            "station_system_evidence",
            "core_sensor_quality_evidence",
            "continuity_evidence",
            "auxiliary_channel_evidence"
        ]
    ].to_string(index=False)
)


print("\n========================================")
print("QC CATEGORY COMBINATIONS")
print("========================================")


combination_counts = (
    anomalies[
        qc_columns
    ]
    .astype(int)
    .astype(str)
    .agg(
        " + ".join,
        axis=1
    )
    .value_counts()
)


print(
    combination_counts.to_string()
)