import pandas as pd

input_file = "data/processed/aws_clean.csv"

df = pd.read_csv(input_file)

columns = [
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
    "BATTRY_VOLTAGE(V)",
    "RAINFALL(mm)"
]

print("=== SENSOR SUMMARY ===")

print(
    df[columns]
    .describe()
    .T
    .to_string()
)

print("\n=== QUALITY FLAG COUNTS ===")

flag_columns = [
    column
    for column in df.columns
    if column.endswith("_invalid")
]

flag_columns += [
    "rainfall_suspicious",
    "large_time_gap",
    "missing_any",
    "quality_issue"
]

print(
    df[flag_columns]
    .sum()
    .sort_values(ascending=False)
    .to_string()
)