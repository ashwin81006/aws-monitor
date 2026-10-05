import pandas as pd
import numpy as np

input_file = "data/processed/aws_features.csv"
output_file = "data/processed/aws_ml_features.csv"

df = pd.read_csv(input_file)

base_features = [
    "time_gap_minutes"
]

raw_features = [
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

temporal_features = [
    column
    for column in df.columns
    if column.endswith("_change")
    or column.endswith("_rate")
]

cross_sensor_features = [
    "temperature_valid_count",
    "temperature_mean",
    "temperature_spread",
    "humidity_valid_count",
    "humidity_mean",
    "humidity_spread"
]

cross_sensor_features += [
    column
    for column in df.columns
    if column.endswith("_deviation")
]

rolling_features = [
    column
    for column in df.columns
    if column.endswith("_rolling_mean")
    or column.endswith("_rolling_std")
]

repetition_features = [
    column
    for column in df.columns
    if column.endswith("_same_as_previous")
    or column.endswith("_repeat_count")
    or column.endswith("_repeat_duration_minutes")
]

feature_columns = (
    base_features +
    raw_features +
    temporal_features +
    cross_sensor_features +
    rolling_features +
    repetition_features
)

feature_columns = list(dict.fromkeys(feature_columns))

ml_df = df[feature_columns].copy()

missing_indicator_columns = []

for column in raw_features:

    name = column.split("(")[0].strip()
    name = name.replace(" ", "_")

    indicator = name + "_missing"

    ml_df[indicator] = (
        ml_df[column].isna().astype(int)
    )

    missing_indicator_columns.append(indicator)


# --------------------------------------------------
# Replace known invalid values
# --------------------------------------------------

temperature_columns = [
    "AIR_TEMPERATURE1(°C at 2m height)",
    "AIR_TEMPERATURE2(°C at 4m height)",
    "AIR_TEMPERATURE3(°C at 8m height)"
]

for column in temperature_columns:
    ml_df.loc[
        ml_df[column] == -40,
        column
    ] = np.nan


humidity_columns = [
    "RELATIVE_HUMIDITY1(% at 2m height)",
    "RELATIVE_HUMIDITY2(% at 4m height)",
    "RELATIVE_HUMIDITY3(% at 8m height)"
]

for column in humidity_columns:
    ml_df.loc[
        (ml_df[column] < 0) |
        (ml_df[column] > 100),
        column
    ] = np.nan


# --------------------------------------------------
# Final feature list
# --------------------------------------------------

all_features = (
    feature_columns +
    missing_indicator_columns
)

all_features = list(dict.fromkeys(all_features))

ml_df = ml_df[all_features]


# --------------------------------------------------
# Summary
# --------------------------------------------------

print("Total ML features:", len(all_features))

print("\nFeature groups:")
print("Base:", len(base_features))
print("Raw:", len(raw_features))
print("Temporal:", len(temporal_features))
print("Cross-sensor:", len(cross_sensor_features))
print("Rolling:", len(rolling_features))
print("Repetition:", len(repetition_features))
print("Missing indicators:", len(missing_indicator_columns))

print("\nRows:", len(ml_df))
print("Columns:", len(ml_df.columns))

print("\nMissing values:")

missing = (
    ml_df.isna()
    .sum()
    .sort_values(ascending=False)
)

missing = missing[missing > 0]

if len(missing) == 0:
    print("None")
else:
    print(missing.to_string())

print("\nFeature list:")

for i, column in enumerate(all_features, start=1):
    print(f"{i:3}. {column}")

ml_df.to_csv(output_file, index=False)

print("\nSaved:", output_file)