import pandas as pd


input_file = "data/processed/aws_clean.csv"

df = pd.read_csv(input_file)

df["timestamp"] = pd.to_datetime(
    df["timestamp"]
)


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


# Remove known invalid temperature values
temperature = df[temp_columns].copy()

for column in temp_columns:
    temperature.loc[
        temperature[column] == -40,
        column
    ] = pd.NA


# Remove invalid humidity values
humidity = df[rh_columns].copy()

for column in rh_columns:
    humidity.loc[
        (humidity[column] < 0)
        |
        (humidity[column] > 100),
        column
    ] = pd.NA


# Calculate spreads
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


print("\n========================================")
print("TOP 20 TEMPERATURE DISAGREEMENTS")
print("========================================")

top_temperature = df[
    df["temperature_spread"].notna()
].sort_values(
    "temperature_spread",
    ascending=False
).head(20)


print(
    top_temperature[
        [
            "timestamp",
            temp_columns[0],
            temp_columns[1],
            temp_columns[2],
            "temperature_spread"
        ]
    ].to_string(index=False)
)


print("\n========================================")
print("TOP 20 HUMIDITY DISAGREEMENTS")
print("========================================")

top_humidity = df[
    df["humidity_spread"].notna()
].sort_values(
    "humidity_spread",
    ascending=False
).head(20)


print(
    top_humidity[
        [
            "timestamp",
            rh_columns[0],
            rh_columns[1],
            rh_columns[2],
            "humidity_spread"
        ]
    ].to_string(index=False)
)