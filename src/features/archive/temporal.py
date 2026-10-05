import pandas as pd
import numpy as np

input_file = "data/processed/aws_clean.csv"
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
    name = name.replace(" ", "_").replace("%", "pct")

    previous = df[column].shift(1)

    previous_valid = previous.notna()
    current_valid = df[column].notna()

    if "AIR_TEMPERATURE" in column:
        previous_valid &= previous != -40
        current_valid &= df[column] != -40

    if "RELATIVE_HUMIDITY" in column:
        previous_valid &= (previous >= 0) & (previous <= 100)
        current_valid &= (df[column] >= 0) & (df[column] <= 100)

    if "WIND_DIRECTION" in column:
        previous_valid &= (previous >= 0) & (previous <= 360)
        current_valid &= (df[column] >= 0) & (df[column] <= 360)

    valid_pair = previous_valid & current_valid

    df[name + "_previous"] = previous

    df[name + "_change"] = np.where(
        valid_pair,
        df[column] - previous,
        np.nan
    )

    df[name + "_rate"] = np.where(
        valid_pair & (df["time_gap_minutes"] <= 60),
        df[name + "_change"] /
        (df["time_gap_minutes"] / 60),
        np.nan
    )

print("Rows:", len(df))
print("Columns:", len(df.columns))

print("\nNew temporal features:")

new_columns = [
    column
    for column in df.columns
    if column.endswith("_previous")
    or column.endswith("_change")
    or column.endswith("_rate")
]

print(len(new_columns))

print("\nSample:")
print(
    df[
        ["timestamp"] +
        new_columns[:6]
    ].head(10).to_string()
)

df.to_csv(output_file, index=False)

print("\nSaved:", output_file)