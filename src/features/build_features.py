import pandas as pd
import numpy as np

input_file = "data/processed/aws_clean.csv"
output_file = "data/processed/aws_features.csv"

df = pd.read_csv(input_file)

df["timestamp"] = pd.to_datetime(df["timestamp"])
df = df.sort_values("timestamp").reset_index(drop=True)

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

temperature_columns = [
    "AIR_TEMPERATURE1(°C at 2m height)",
    "AIR_TEMPERATURE2(°C at 4m height)",
    "AIR_TEMPERATURE3(°C at 8m height)"
]

humidity_columns = [
    "RELATIVE_HUMIDITY1(% at 2m height)",
    "RELATIVE_HUMIDITY2(% at 4m height)",
    "RELATIVE_HUMIDITY3(% at 8m height)"
]


# ==================================================
# TEMPORAL FEATURES
# ==================================================

for column in sensor_columns:

    name = column.split("(")[0].strip()
    name = name.replace(" ", "_").replace("%", "pct")

    previous = df[column].shift(1)

    previous_valid = previous.notna()
    current_valid = df[column].notna()

    if column in temperature_columns:
        previous_valid &= previous != -40
        current_valid &= df[column] != -40

    if column in humidity_columns:
        previous_valid &= (previous >= 0) & (previous <= 100)
        current_valid &= (df[column] >= 0) & (df[column] <= 100)

    continuous = (
        df["time_gap_minutes"] <= 60
    )

    valid_pair = (
        previous_valid &
        current_valid &
        continuous
    )

    df[name + "_previous"] = previous

    df[name + "_change"] = np.where(
        valid_pair,
        df[column] - previous,
        np.nan
    )

    df[name + "_rate"] = np.where(
        valid_pair,
        df[name + "_change"] /
        (df["time_gap_minutes"] / 60),
        np.nan
    )


# ==================================================
# CROSS-SENSOR FEATURES
# ==================================================

temperature_valid = df[temperature_columns].replace(
    -40,
    np.nan
)

humidity_valid = df[humidity_columns].where(
    (df[humidity_columns] >= 0) &
    (df[humidity_columns] <= 100)
)

df["temperature_valid_count"] = (
    temperature_valid.notna().sum(axis=1)
)

df["humidity_valid_count"] = (
    humidity_valid.notna().sum(axis=1)
)

df["temperature_mean"] = (
    temperature_valid.mean(axis=1)
)

df["temperature_spread"] = np.where(
    df["temperature_valid_count"] >= 2,
    temperature_valid.max(axis=1) -
    temperature_valid.min(axis=1),
    np.nan
)

for column in temperature_columns:

    name = column.split("(")[0].strip()
    name = name.replace(" ", "_")

    df[name + "_deviation"] = (
        df[column] -
        df["temperature_mean"]
    )

    invalid = (
        (df[column] == -40) |
        (df["temperature_valid_count"] < 2)
    )

    df.loc[
        invalid,
        name + "_deviation"
    ] = np.nan


df["humidity_mean"] = (
    humidity_valid.mean(axis=1)
)

df["humidity_spread"] = np.where(
    df["humidity_valid_count"] >= 2,
    humidity_valid.max(axis=1) -
    humidity_valid.min(axis=1),
    np.nan
)

for column in humidity_columns:

    name = column.split("(")[0].strip()
    name = name.replace(" ", "_")

    df[name + "_deviation"] = (
        df[column] -
        df["humidity_mean"]
    )

    invalid = (
        (df[column] < 0) |
        (df[column] > 100) |
        (df["humidity_valid_count"] < 2)
    )

    df.loc[
        invalid,
        name + "_deviation"
    ] = np.nan


# ==================================================
# ROLLING FEATURES
# ==================================================

for column in sensor_columns:

    name = column.split("(")[0].strip()
    name = name.replace(" ", "_")

    series = df[column].copy()

    if column in temperature_columns:
        series = series.mask(series == -40)

    if column in humidity_columns:
        series = series.mask(
            (series < 0) |
            (series > 100)
        )

    rolling = series.rolling(
        window=5,
        min_periods=2,
        closed="left"
    )

    df[name + "_rolling_mean"] = rolling.mean()
    df[name + "_rolling_std"] = rolling.std()


# ==================================================
# REPETITION FEATURES
# ==================================================

for column in sensor_columns:

    name = column.split("(")[0].strip()
    name = name.replace(" ", "_")

    current = df[column]
    previous = current.shift(1)

    valid_current = current.notna()
    valid_previous = previous.notna()

    if column in temperature_columns:
        valid_current &= current != -40
        valid_previous &= previous != -40

    if column in humidity_columns:
        valid_current &= (
            (current >= 0) &
            (current <= 100)
        )
        valid_previous &= (
            (previous >= 0) &
            (previous <= 100)
        )

    continuous = (
        df["time_gap_minutes"] <= 60
    )

    same = (
        valid_current &
        valid_previous &
        continuous &
        (current == previous)
    )

    df[name + "_same_as_previous"] = (
        same.astype(int)
    )

    group = (~same).cumsum()

    df[name + "_repeat_count"] = (
        same.groupby(group).cumsum()
    )

    df.loc[
        ~valid_current,
        name + "_repeat_count"
    ] = 0


# ==================================================
# REPEAT DURATION FEATURES
# ==================================================

for column in sensor_columns:

    name = column.split("(")[0].strip()
    name = name.replace(" ", "_")

    current = df[column]
    previous = current.shift(1)

    valid_current = current.notna()
    valid_previous = previous.notna()

    if column in temperature_columns:
        valid_current &= current != -40
        valid_previous &= previous != -40

    if column in humidity_columns:
        valid_current &= (
            (current >= 0) &
            (current <= 100)
        )
        valid_previous &= (
            (previous >= 0) &
            (previous <= 100)
        )

    continuous = (
        df["time_gap_minutes"] <= 60
    )

    same = (
        valid_current &
        valid_previous &
        continuous &
        (current == previous)
    )

    start_time = df["timestamp"].where(
        ~same
    ).ffill()

    duration = (
        df["timestamp"] -
        start_time
    ).dt.total_seconds() / 60

    df[name + "_repeat_duration_minutes"] = np.where(
        same,
        duration,
        0
    )


# ==================================================
# SUMMARY
# ==================================================
temporal_features = [
    column
    for column in df.columns
    if column.endswith("_change")
    or column.endswith("_rate")
]

temporal_helper_features = [
    column
    for column in df.columns
    if column.endswith("_previous")
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

generated_features = (
    temporal_features +
    temporal_helper_features +
    cross_sensor_features +
    rolling_features +
    repetition_features
)

generated_features = list(dict.fromkeys(generated_features))

print("Rows:", len(df))
print("Columns:", len(df.columns))

print("\nFeature groups:")
print("Temporal:", len(temporal_features))
print("Temporal helpers:", len(temporal_helper_features))
print("Cross-sensor:", len(cross_sensor_features))
print("Rolling:", len(rolling_features))
print("Repetition:", len(repetition_features))

print("\nUnique generated features:")
print(len(generated_features))

print("\nSaved:", output_file)

df = df.copy()
df.to_csv(output_file, index=False)