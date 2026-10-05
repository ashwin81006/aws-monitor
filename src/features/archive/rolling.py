import pandas as pd

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

df = df.sort_values("timestamp").reset_index(drop=True)

for column in sensor_columns:

    name = column.split("(")[0].strip()
    name = name.replace(" ", "_")

    series = df[column].copy()

    if "AIR_TEMPERATURE" in column:
        series = series.mask(series == -40)

    if "RELATIVE_HUMIDITY" in column:
        series = series.mask(
            (series < 0) | (series > 100)
        )

    rolling = (
        series
        .rolling(
            window=5,
            min_periods=2,
            closed="left"
        )
    )

    df[name + "_rolling_mean"] = rolling.mean()
    df[name + "_rolling_std"] = rolling.std()

new_columns = [
    column
    for column in df.columns
    if column.endswith("_rolling_mean")
    or column.endswith("_rolling_std")
]

print("Rows:", len(df))
print("Columns:", len(df.columns))

print("\nRolling features:")
print(len(new_columns))

print("\nSample:")

print(
    df[
        ["timestamp"] + new_columns[:6]
    ].head(10).to_string()
)

df.to_csv(output_file, index=False)

print("\nSaved:", output_file)