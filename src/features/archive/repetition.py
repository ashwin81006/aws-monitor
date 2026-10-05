import pandas as pd
import numpy as np

input_file = "data/processed/aws_features.csv"
output_file = "data/processed/aws_features.csv"

df = pd.read_csv(input_file)

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

    df[name + "_same_as_previous"] = same.astype(int)

    group = (
        (~same)
        .cumsum()
    )

    df[name + "_repeat_count"] = (
        same.groupby(group)
        .cumsum()
    )

    df.loc[
        ~current.notna(),
        name + "_repeat_count"
    ] = 0

new_columns = [
    column
    for column in df.columns
    if column.endswith("_same_as_previous")
    or column.endswith("_repeat_count")
]

print("Rows:", len(df))
print("Columns:", len(df.columns))

print("\nRepetition features:")
print(len(new_columns))

print("\nSample:")

print(
    df[
        ["timestamp"] + new_columns[:6]
    ].head(15).to_string()
)

print("\nMaximum repeat counts:")

repeat_columns = [
    column
    for column in df.columns
    if column.endswith("_repeat_count")
]

print(
    df[repeat_columns]
    .max()
    .sort_values(ascending=False)
    .to_string()
)

df.to_csv(output_file, index=False)

print("\nSaved:", output_file)