import json
import pandas as pd


input_file = "data/processed/aws_clean.csv"
threshold_file = "models/cross_sensor_thresholds.json"
output_file = "data/processed/aws_cross_sensor_evidence.csv"


df = pd.read_csv(input_file)


with open(threshold_file, "r") as file:
    thresholds = json.load(file)


temperature_threshold = thresholds[
    "temperature_spread_99th_percentile"
]

humidity_threshold = thresholds[
    "humidity_spread_99th_percentile"
]


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


# Remove known invalid values
temperature = df[temp_columns].copy()

for column in temp_columns:
    temperature.loc[
        temperature[column] == -40,
        column
    ] = pd.NA


humidity = df[rh_columns].copy()

for column in rh_columns:
    humidity.loc[
        (humidity[column] < 0)
        |
        (humidity[column] > 100),
        column
    ] = pd.NA


# Valid sensor counts
df["temperature_valid_count"] = (
    temperature.notna().sum(axis=1)
)

df["humidity_valid_count"] = (
    humidity.notna().sum(axis=1)
)


# Sensor means
df["temperature_mean"] = (
    temperature.mean(axis=1)
)

df["humidity_mean"] = (
    humidity.mean(axis=1)
)


# Sensor spreads
df["temperature_spread"] = (
    temperature.max(axis=1)
    -
    temperature.min(axis=1)
)

df["humidity_spread"] = (
    humidity.max(axis=1)
    -
    humidity.min(axis=1)
)


# Spread is meaningful only when at least two sensors exist
df.loc[
    df["temperature_valid_count"] < 2,
    "temperature_spread"
] = pd.NA

df.loc[
    df["humidity_valid_count"] < 2,
    "humidity_spread"
] = pd.NA


# Actual evidence signals
df["temperature_disagreement"] = (
    df["temperature_spread"]
    > temperature_threshold
).fillna(False)


df["humidity_disagreement"] = (
    df["humidity_spread"]
    > humidity_threshold
).fillna(False)


df["cross_sensor_evidence"] = (
    df["temperature_disagreement"]
    |
    df["humidity_disagreement"]
).astype(int)


# Tri-sensor majority voting: identify specifically which sensor is divergent
df["temp_divergent_sensor"] = ""
df["rh_divergent_sensor"] = ""
df["temp_isolated_fault"] = 0
df["rh_isolated_fault"] = 0

temp_med = temperature.median(axis=1)
rh_med = humidity.median(axis=1)

for idx in df[df["temperature_disagreement"]].index:
    valid_sensors = [col for col in temp_columns if pd.notna(temperature.loc[idx, col])]
    if len(valid_sensors) >= 2:
        devs = {col: abs(temperature.loc[idx, col] - temp_med.loc[idx]) for col in valid_sensors}
        sorted_sensors = sorted(devs.items(), key=lambda x: x[1], reverse=True)
        if sorted_sensors[0][1] >= (temperature_threshold * 0.5):
            df.loc[idx, "temp_divergent_sensor"] = sorted_sensors[0][0].split("(")[0].strip()
            df.loc[idx, "temp_isolated_fault"] = 1

for idx in df[df["humidity_disagreement"]].index:
    valid_sensors = [col for col in rh_columns if pd.notna(humidity.loc[idx, col])]
    if len(valid_sensors) >= 2:
        devs = {col: abs(humidity.loc[idx, col] - rh_med.loc[idx]) for col in valid_sensors}
        sorted_sensors = sorted(devs.items(), key=lambda x: x[1], reverse=True)
        if sorted_sensors[0][1] >= (humidity_threshold * 0.5):
            df.loc[idx, "rh_divergent_sensor"] = sorted_sensors[0][0].split("(")[0].strip()
            df.loc[idx, "rh_isolated_fault"] = 1


print("Total observations:", len(df))

print("\n--- CROSS-SENSOR EVIDENCE ---")

print(
    "Temperature threshold:",
    temperature_threshold,
    "°C"
)

print(
    "Humidity threshold:",
    humidity_threshold,
    "%"
)

print(
    "\nTemperature disagreement:",
    df["temperature_disagreement"].sum()
)

print(
    "Humidity disagreement:",
    df["humidity_disagreement"].sum()
)

print(
    "Rows with cross-sensor evidence:",
    df["cross_sensor_evidence"].sum()
)


print("\n--- STRONGEST DISAGREEMENTS ---")

strong = df[
    df["cross_sensor_evidence"] == 1
].copy()

strong = strong.sort_values(
    [
        "temperature_spread",
        "humidity_spread"
    ],
    ascending=False
)


print(
    strong[
        [
            "timestamp",
            temp_columns[0],
            temp_columns[1],
            temp_columns[2],
            "temperature_spread",
            rh_columns[0],
            rh_columns[1],
            rh_columns[2],
            "humidity_spread"
        ]
    ].head(20).to_string(index=False)
)


output_columns = [
    "timestamp",

    "temperature_valid_count",
    "temperature_mean",
    "temperature_spread",
    "temperature_disagreement",
    "temp_divergent_sensor",
    "temp_isolated_fault",

    "humidity_valid_count",
    "humidity_mean",
    "humidity_spread",
    "humidity_disagreement",
    "rh_divergent_sensor",
    "rh_isolated_fault",

    "cross_sensor_evidence"
]


df[output_columns].to_csv(
    output_file,
    index=False
)


print(
    "\nSaved:",
    output_file
)