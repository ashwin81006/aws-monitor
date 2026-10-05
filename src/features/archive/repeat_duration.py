import pandas as pd
import numpy as np

input_file = "data/processed/aws_features.csv"
output_file = "data/processed/aws_features.csv"

df = pd.read_csv(input_file)

df["timestamp"] = pd.to_datetime(df["timestamp"])

sensor_columns = [
    "AIR_TEMPERATURE1(°C at 2m height)",
    "AIR_TEMPERATURE2(°C at 4m height)",
    "AIR_TEMPERATURE3(°C at 8m height)",
    "RELATIVE_HUMIDITY1(% at 2m height)",
    "RELATIVE_HUMIDITY2(% at 4m height)",
    "RELATIVE_HUMIDITY3(% at 8m height)",
    "WIND_SPEED1(m/s at 3m height) ",
    "WIND_SPEED2(m/s at 6m height)",
    "WIND_SPEED3(m/s at 10m height)",
    "ATMOSPHERIC_PRESSURE(mbar) ",
    "BATTRY_VOLTAGE(V)"
]

for column in sensor_columns:

    name = column.split("(")[0].strip()
    name = name.replace(" ", "_")

    current = df[column]
    previous = current.shift(1)

    same = (
        current.notna() &
        previous.notna() &
        (current == previous)
    )

    start_time = df["timestamp"].where(
        ~same
    ).ffill()

    duration = (
        df["timestamp"] - start_time
    ).dt.total_seconds() / 60

    df[name + "_repeat_duration_minutes"] = np.where(
        same,
        duration,
        0
    )

new_columns = [
    column
    for column in df.columns
    if column.endswith("_repeat_duration_minutes")
]

print("Rows:", len(df))
print("Columns:", len(df.columns))

print("\nRepeat duration features:")
print(len(new_columns))

print("\nMaximum repeat durations:")

print(
    df[new_columns]
    .max()
    .sort_values(ascending=False)
    .to_string()
)

df.to_csv(output_file, index=False)

print("\nSaved:", output_file)