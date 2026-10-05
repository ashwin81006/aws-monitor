import pandas as pd


input_file = "data/processed/aws_fusion_candidates.csv"

df = pd.read_csv(input_file)

df["timestamp"] = pd.to_datetime(
    df["timestamp"]
)


test_cases = {
    "Event 157": [
        "2017-07-16 16:30:00",
        "2017-07-16 17:30:00",
        "2017-07-16 18:00:00",
        "2017-07-16 19:00:00"
    ],

    "Event 45": [
        "2017-01-01 07:30:00",
        "2017-01-01 08:00:00",
        "2017-01-01 08:30:00",
        "2017-01-01 09:00:00",
        "2017-01-01 09:30:00"
    ],

    "Event 72": [
        "2017-02-02 08:30:00",
        "2017-02-02 09:00:00",
        "2017-02-02 10:00:00",
        "2017-02-02 10:30:00",
        "2017-02-02 11:00:00"
    ]
}


columns = [
    "timestamp",
    "anomaly_score",
    "anomaly_flag",

    "meaningful_evidence_count",

    "station_system_evidence",
    "core_sensor_quality_evidence",
    "continuity_evidence",
    "cross_sensor_evidence",
    "temporal_evidence",

    "candidate_class",
    "severity",
    "probable_root_cause"
]


for name, timestamps in test_cases.items():

    print("\n========================================")
    print(name)
    print("========================================")

    case = df[
        df["timestamp"].isin(
            pd.to_datetime(timestamps)
        )
    ].copy()

    if len(case) == 0:
        print("No rows found.")
        continue

    print(
        case[columns]
        .sort_values("timestamp")
        .to_string(index=False)
    )