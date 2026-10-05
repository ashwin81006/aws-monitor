import pandas as pd

clean_file = "data/processed/aws_clean.csv"
events_file = "data/processed/aws_anomaly_events.csv"

clean = pd.read_csv(clean_file)
events = pd.read_csv(events_file)

clean["timestamp"] = pd.to_datetime(
    clean["timestamp"]
)

event_ids = [157, 45, 72]


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
        print("\nEvent", event_id, "not found")
        continue

    start_time = event["start_time"].iloc[0]
    end_time = event["end_time"].iloc[0]

    print("\n================================")
    print("EVENT", event_id)
    print("Start:", start_time)
    print("End:", end_time)
    print("Anomalous observations:", event["observations"].iloc[0])
    print("================================")

    # Add a small neighborhood around the event
    start = pd.to_datetime(start_time) - pd.Timedelta(hours=1)
    end = pd.to_datetime(end_time) + pd.Timedelta(hours=1)

    window = clean[
        (clean["timestamp"] >= start)
        &
        (clean["timestamp"] <= end)
    ].copy()

    print(
        window[columns].to_string(index=False)
    )