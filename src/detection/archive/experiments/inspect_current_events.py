import pandas as pd


clean_file = "data/processed/aws_clean.csv"
events_file = "data/processed/aws_current_anomaly_events.csv"
matrix_file = "data/processed/aws_evidence_matrix.csv"


clean = pd.read_csv(clean_file)
events = pd.read_csv(events_file)
matrix = pd.read_csv(matrix_file)


clean["timestamp"] = pd.to_datetime(
    clean["timestamp"]
)

matrix["timestamp"] = pd.to_datetime(
    matrix["timestamp"]
)


event_ids = [149, 43, 62]


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


columns = [
    "timestamp",

    "AIR_TEMPERATURE1(°C at 2m height)",
    "AIR_TEMPERATURE2(°C at 4m height)",
    "AIR_TEMPERATURE3(°C at 8m height)",

    "RELATIVE_HUMIDITY1(% at 2m height)",
    "RELATIVE_HUMIDITY2(% at 4m height)",
    "RELATIVE_HUMIDITY3(% at 8m height)",

    "BATTRY_VOLTAGE(V)",
    "ATMOSPHERIC_PRESSURE(mbar) ",

    "time_gap_minutes"
]


for event_id in event_ids:

    event = events[
        events["event_id"] == event_id
    ]

    if len(event) == 0:
        print(
            "\nEvent",
            event_id,
            "not found"
        )
        continue

    start_time = pd.to_datetime(
        event["start_time"].iloc[0]
    )

    end_time = pd.to_datetime(
        event["end_time"].iloc[0]
    )

    print("\n========================================")
    print("EVENT", event_id)
    print("========================================")

    print("Start:", start_time)
    print("End:", end_time)

    print(
        "Anomalous observations:",
        event["observations"].iloc[0]
    )

    print(
        "\nEvent evidence:"
    )

    print(
        "Station/system:",
        event["has_station_system_evidence"].iloc[0]
    )

    print(
        "Core sensor quality:",
        event["has_core_sensor_quality"].iloc[0]
    )

    print(
        "Continuity:",
        event["has_continuity_evidence"].iloc[0]
    )

    print(
        "Cross-sensor:",
        event["has_cross_sensor_evidence"].iloc[0]
    )

    print(
        "Temporal:",
        event["has_temporal_evidence"].iloc[0]
    )

    # One hour before and after
    start = start_time - pd.Timedelta(hours=1)
    end = end_time + pd.Timedelta(hours=1)

    window = clean[
        (clean["timestamp"] >= start)
        &
        (clean["timestamp"] <= end)
    ].copy()

    print("\nRaw observation window:")

    print(
        window[columns]
        .to_string(index=False)
    )

    print("\nEvidence rows:")

    evidence_window = matrix[
        (matrix["timestamp"] >= start)
        &
        (matrix["timestamp"] <= end)
    ].copy()

    evidence_columns = [
        "timestamp",
        "anomaly_score",
        "anomaly_flag",
        "station_system_evidence",
        "core_sensor_quality_evidence",
        "continuity_evidence",
        "cross_sensor_evidence",
        "temporal_evidence"
    ]

    print(
        evidence_window[evidence_columns]
        .to_string(index=False)
    )