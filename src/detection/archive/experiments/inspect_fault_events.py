import pandas as pd
import numpy as np


fusion_file = "data/processed/aws_event_fusion.csv"
raw_file = "data/processed/aws_clean.csv"
evidence_file = "data/processed/aws_evidence_matrix.csv"


fusion = pd.read_csv(
    fusion_file,
    parse_dates=["start_time", "end_time"]
)

raw = pd.read_csv(
    raw_file,
    parse_dates=["timestamp"]
)

evidence = pd.read_csv(
    evidence_file,
    parse_dates=["timestamp"]
)


faults = fusion[
    fusion["candidate_class"] == "PROBABLE_SENSOR_FAULT"
].copy()

faults = faults.sort_values("event_id")

def find_column(df, *names):
    for name in names:
        if name in df.columns:
            return name

    lowered = {
        col.lower(): col
        for col in df.columns
    }

    for name in names:
        if name.lower() in lowered:
            return lowered[name.lower()]

    return None


temp_cols = [
    find_column(
        raw,
        "AIR_TEMPERATURE1(°C at 2m height)",
        "air_temperature_2m",
        "temperature_2m"
    ),
    find_column(
        raw,
        "AIR_TEMPERATURE2(°C at 4m height)",
        "air_temperature_4m",
        "temperature_4m"
    ),
    find_column(
        raw,
        "AIR_TEMPERATURE3(°C at 8m height)",
        "air_temperature_8m",
        "temperature_8m"
    )
]

rh_cols = [
    find_column(
        raw,
        "RELATIVE_HUMIDITY1(% at 2m height)",
        "relative_humidity_2m",
        "humidity_2m"
    ),
    find_column(
        raw,
        "RELATIVE_HUMIDITY2(% at 4m height)",
        "relative_humidity_4m",
        "humidity_4m"
    ),
    find_column(
        raw,
        "RELATIVE_HUMIDITY3(% at 8m height)",
        "relative_humidity_8m",
        "humidity_8m"
    )
]

pressure_col = find_column(
    raw,
    "ATMOSPHERIC_PRESSURE(mbar)",
    "atmospheric_pressure",
    "pressure"
)

battery_col = find_column(
    raw,
    "BATTRY_VOLTAGE(V)",
    "battery_voltage",
    "battery"
)


temp_cols = [c for c in temp_cols if c is not None]
rh_cols = [c for c in rh_cols if c is not None]

print("\nResolved columns:")
print("Temperature:", temp_cols)
print("Humidity:", rh_cols)
print("Pressure:", pressure_col)
print("Battery:", battery_col)


pd.set_option("display.max_columns", 50)
pd.set_option("display.width", 240)
pd.set_option("display.max_rows", 100)


print("=" * 100)
print("FAULT EVENT INSPECTION")
print("=" * 100)

print("Total probable sensor fault events:", len(faults))


for _, event in faults.iterrows():

    event_id = int(event["event_id"])
    start = event["start_time"]
    end = event["end_time"]

    print("\n")
    print("=" * 100)
    print("EVENT", event_id)
    print("=" * 100)

    print("Start:", start)
    print("End:", end)
    print("Observations:", int(event["observations"]))
    print("Minimum IF score:", round(event["minimum_anomaly_score"], 6))

    print("\nEvidence:")
    print(
        "Station/System:",
        int(event["has_station_system_evidence"])
    )
    print(
        "Core sensor quality:",
        int(event["has_core_sensor_quality"])
    )
    print(
        "Continuity:",
        int(event["has_continuity_evidence"])
    )
    print(
        "Cross-sensor:",
        int(event["has_cross_sensor_evidence"])
    )
    print(
        "Temporal:",
        int(event["has_temporal_evidence"])
    )

    print("\nFusion decision:")
    print("Class:", event["candidate_class"])
    print("Severity:", event["severity"])
    print("Root cause:", event["probable_root_cause"])


    window_start = start - pd.Timedelta(hours=1)
    window_end = end + pd.Timedelta(hours=1)


    raw_window = raw[
        (raw["timestamp"] >= window_start)
        &
        (raw["timestamp"] <= window_end)
    ].copy()


    for col in temp_cols:
        if col not in raw_window.columns:
            raw_window[col] = np.nan

    for col in rh_cols:
        if col not in raw_window.columns:
            raw_window[col] = np.nan

    raw_window["temp_spread"] = (
    raw_window[temp_cols].max(axis=1, skipna=True)
    -
    raw_window[temp_cols].min(axis=1, skipna=True)
)

    raw_window["rh_spread"] = (
        raw_window[rh_cols].max(axis=1, skipna=True)
        -
        raw_window[rh_cols].min(axis=1, skipna=True)
    )


    display_cols = [
        "timestamp",
        *temp_cols,
        "temp_spread",
        *rh_cols,
        "rh_spread"
    ]

    if pressure_col is not None:
        display_cols.append(pressure_col)

    if battery_col is not None:
        display_cols.append(battery_col)


    print("\nRaw sensor window:")

    print(
        raw_window[
            display_cols
        ].to_string(index=False)
    )
    evidence_window = evidence[
        (evidence["timestamp"] >= window_start)
        &
        (evidence["timestamp"] <= window_end)
    ].copy()


    evidence_cols = [
        "timestamp",
        "if_anomaly",
        "if_score",
        "has_station_system_evidence",
        "has_core_sensor_quality",
        "has_continuity_evidence",
        "has_cross_sensor_evidence",
        "has_temporal_evidence"
    ]


    available_cols = [
        col for col in evidence_cols
        if col in evidence_window.columns
    ]


    print("\nEvidence window:")

    print(
        evidence_window[
            available_cols
        ].to_string(index=False)
    )


print("\n")
print("=" * 100)
print("INSPECTION COMPLETE")
print("=" * 100)