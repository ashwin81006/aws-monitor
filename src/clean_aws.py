import pandas as pd

input_file = "data/raw/aws_dataset.csv"
output_file = "data/processed/aws_clean.csv"

df = pd.read_csv(input_file)

df["timestamp"] = pd.to_datetime(
    df["DATE(IST)"] + " " + df["TIME(IST)"],
    format="mixed"
)

df = df.sort_values("timestamp").reset_index(drop=True)

# --------------------------------------------------
# Quality flags
# --------------------------------------------------

missing_check_columns = [
    column
    for column in df.columns
    if df[column].notna().any()
]

df["missing_any"] = (
    df[missing_check_columns].isna().any(axis=1)
).astype(int)


df["time_gap_minutes"] = (
    df["timestamp"].diff().dt.total_seconds() / 60
)

df["large_time_gap"] = (
    df["time_gap_minutes"] > 30
).astype(int)

# --------------------------------------------------
# Temperature
# --------------------------------------------------

temp_columns = [
    "AIR_TEMPERATURE1(°C at 2m height)",
    "AIR_TEMPERATURE2(°C at 4m height)",
    "AIR_TEMPERATURE3(°C at 8m height)"
]

for column in temp_columns:
    df[column + "_invalid"] = (
        df[column] == -40
    ).astype(int)

# --------------------------------------------------
# Relative humidity
# --------------------------------------------------

rh_columns = [
    "RELATIVE_HUMIDITY1(% at 2m height)",
    "RELATIVE_HUMIDITY2(% at 4m height)",
    "RELATIVE_HUMIDITY3(% at 8m height)"
]

for column in rh_columns:
    df[column + "_invalid"] = (
        (df[column] < 0) |
        (df[column] > 100)
    ).astype(int)

# --------------------------------------------------
# Wind direction
# --------------------------------------------------

wind_direction_columns = [
    "WIND_DIRECTION1(deg at 3m height)",
    "WIND_DIRECTION2(deg at 6m height)",
    "WIND_DIRECTION3(deg at 10m height)"
]

for column in wind_direction_columns:
    df[column + "_invalid"] = (
        (df[column] < 0) |
        (df[column] > 360)
    ).astype(int)

# --------------------------------------------------
# Radiation sentinel
# --------------------------------------------------

radiation_columns = [
    "RAD_LONG_OUT(w/m2) ",
    "RAD_LONG_IN(w/m2) "
]

for column in radiation_columns:
    df[column + "_invalid"] = (
        df[column] == -312
    ).astype(int)

# --------------------------------------------------
# Heat flux sentinel
# --------------------------------------------------

heat_flux_columns = [
    "HEAT_FLUX1(w/m2 at 0.50m height) ",
    "HEAT_FLUX2(w/m2 at 0.20m height)"
]

for column in heat_flux_columns:
    df[column + "_invalid"] = (
        df[column] == -100
    ).astype(int)

# --------------------------------------------------
# Rainfall suspicious values
# --------------------------------------------------

rainfall = "RAINFALL(mm)"

df["rainfall_suspicious"] = (
    df[rainfall] > 100
).astype(int)

# --------------------------------------------------
# Combined quality flag
# --------------------------------------------------

flag_columns = [
    column
    for column in df.columns
    if column.endswith("_invalid")
]

flag_columns.append("rainfall_suspicious")

df["quality_issue"] = (
    df[flag_columns].any(axis=1)
).astype(int)

# --------------------------------------------------
# Save
# --------------------------------------------------

df.to_csv(output_file, index=False)

print("Rows:", len(df))
print("Columns:", len(df.columns))
print("Quality issue rows:", df["quality_issue"].sum())
print("Large time gaps:", df["large_time_gap"].sum())
print("Saved:", output_file)