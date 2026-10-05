import pandas as pd


input_file = "data/processed/aws_clean.csv"
output_file = "data/processed/aws_cross_sensor_evidence.csv"


df = pd.read_csv(input_file)


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


# Ignore known invalid values when calculating
# cross-sensor relationships.

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


# Number of valid sensors available at each row
df["temperature_valid_count"] = (
    temperature.notna().sum(axis=1)
)

df["humidity_valid_count"] = (
    humidity.notna().sum(axis=1)
)


# Mean across valid sensors
df["temperature_mean"] = (
    temperature.mean(axis=1)
)

df["humidity_mean"] = (
    humidity.mean(axis=1)
)


# Difference between highest and lowest valid sensor
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


# Only consider spread when at least two sensors exist
df.loc[
    df["temperature_valid_count"] < 2,
    "temperature_spread"
] = pd.NA

df.loc[
    df["humidity_valid_count"] < 2,
    "humidity_spread"
] = pd.NA


print("Total observations:", len(df))


print("\n--- VALID SENSOR COUNTS ---")

print(
    "Temperature:"
)

print(
    df["temperature_valid_count"]
    .value_counts()
    .sort_index()
    .to_string()
)

print(
    "\nHumidity:"
)

print(
    df["humidity_valid_count"]
    .value_counts()
    .sort_index()
    .to_string()
)


print("\n--- TEMPERATURE SPREAD ---")

print(
    df["temperature_spread"].describe(
        percentiles=[
            0.50,
            0.75,
            0.90,
            0.95,
            0.99
        ]
    )
)


print("\n--- HUMIDITY SPREAD ---")

print(
    df["humidity_spread"].describe(
        percentiles=[
            0.50,
            0.75,
            0.90,
            0.95,
            0.99
        ]
    )
)


print("\n--- LARGE TEMPERATURE SPREADS ---")

print(
    "Temperature spread > 2°C:",
    (
        df["temperature_spread"] > 2
    ).sum()
)

print(
    "Temperature spread > 5°C:",
    (
        df["temperature_spread"] > 5
    ).sum()
)


print("\n--- LARGE HUMIDITY SPREADS ---")

print(
    "Humidity spread > 10%:",
    (
        df["humidity_spread"] > 10
    ).sum()
)

print(
    "Humidity spread > 20%:",
    (
        df["humidity_spread"] > 20
    ).sum()
)

print(
    "Humidity spread > 50%:",
    (
        df["humidity_spread"] > 50
    ).sum()
)


output_columns = [
    "timestamp",

    "temperature_valid_count",
    "temperature_mean",
    "temperature_spread",

    "humidity_valid_count",
    "humidity_mean",
    "humidity_spread"
]


df[output_columns].to_csv(
    output_file,
    index=False
)


print("\nSaved:", output_file)