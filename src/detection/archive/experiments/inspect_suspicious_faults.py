import pandas as pd
import numpy as np


raw_file = "data/processed/aws_clean.csv"
fusion_file = "data/processed/aws_event_fusion.csv"


raw = pd.read_csv(
    raw_file,
    parse_dates=["timestamp"]
)

fusion = pd.read_csv(
    fusion_file,
    parse_dates=["start_time", "end_time"]
)


temp_cols = [
    "AIR_TEMPERATURE1(°C at 2m height)",
    "AIR_TEMPERATURE2(°C at 4m height)",
    "AIR_TEMPERATURE3(°C at 8m height)"
]

rh_cols = [
    "RELATIVE_HUMIDITY1(% at 2m height)",
    "RELATIVE_HUMIDITY2(% at 4m height)",
    "RELATIVE_HUMIDITY3(% at 8m height)"
]

events_to_check = [43, 55]


pd.set_option("display.max_columns", 30)
pd.set_option("display.width", 240)


for event_id in events_to_check:

    event = fusion[
        fusion["event_id"] == event_id
    ].iloc[0]

    start = event["start_time"]
    end = event["end_time"]

    window_start = start - pd.Timedelta(hours=1)
    window_end = end + pd.Timedelta(hours=1)

    df = raw[
        (raw["timestamp"] >= window_start)
        &
        (raw["timestamp"] <= window_end)
    ].copy()

    df["temperature_median"] = (
        df[temp_cols]
        .replace(-40, np.nan)
        .median(axis=1)
    )

    df["humidity_median"] = (
        df[rh_cols]
        .where(
            (df[rh_cols] >= 0) &
            (df[rh_cols] <= 100)
        )
        .median(axis=1)
    )

    df["temperature_spread"] = (
        df[temp_cols]
        .replace(-40, np.nan)
        .max(axis=1)
        -
        df[temp_cols]
        .replace(-40, np.nan)
        .min(axis=1)
    )

    df["humidity_spread"] = (
        df[rh_cols]
        .where(
            (df[rh_cols] >= 0) &
            (df[rh_cols] <= 100)
        )
        .max(axis=1)
        -
        df[rh_cols]
        .where(
            (df[rh_cols] >= 0) &
            (df[rh_cols] <= 100)
        )
        .min(axis=1)
    )

    df["time_gap_minutes"] = (
        df["timestamp"]
        .diff()
        .dt.total_seconds()
        / 60
    )

    df["temperature_change"] = (
        df["temperature_median"].diff()
    )

    df["humidity_change"] = (
        df["humidity_median"].diff()
    )

    df["temperature_rate_per_hour"] = (
        df["temperature_change"]
        /
        (df["time_gap_minutes"] / 60)
    )

    df["humidity_rate_per_hour"] = (
        df["humidity_change"]
        /
        (df["time_gap_minutes"] / 60)
    )

    print("\n")
    print("=" * 110)
    print("EVENT", event_id)
    print("=" * 110)

    print(
        "Fusion class:",
        event["candidate_class"]
    )

    print(
        "Root cause:",
        event["probable_root_cause"]
    )

    print(
        "IF score:",
        round(event["minimum_anomaly_score"], 6)
    )

    print("\nEvidence:")
    print(
        "Core:",
        int(event["has_core_sensor_quality"])
    )
    print(
        "Cross:",
        int(event["has_cross_sensor_evidence"])
    )
    print(
        "Temporal:",
        int(event["has_temporal_evidence"])
    )

    print("\nDetailed measurements:")

    print(
        df[
            [
                "timestamp",

                temp_cols[0],
                temp_cols[1],
                temp_cols[2],

                "temperature_median",
                "temperature_spread",
                "temperature_change",
                "temperature_rate_per_hour",

                rh_cols[0],
                rh_cols[1],
                rh_cols[2],

                "humidity_median",
                "humidity_spread",
                "humidity_change",
                "humidity_rate_per_hour"
            ]
        ].to_string(index=False)
    )