import pandas as pd


input_file = "data/processed/aws_clean.csv"
output_file = "data/processed/aws_rule_evidence.csv"


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

wind_direction_columns = [
    "WIND_DIRECTION1(deg at 3m height)",
    "WIND_DIRECTION2(deg at 6m height)",
    "WIND_DIRECTION3(deg at 10m height)"
]

radiation_columns = [
    "RAD_LONG_OUT(w/m2) ",
    "RAD_LONG_IN(w/m2) "
]

heat_flux_columns = [
    "HEAT_FLUX1(w/m2 at 0.50m height) ",
    "HEAT_FLUX2(w/m2 at 0.20m height)"
]


# -------------------------------------------------
# Missing data evidence
# -------------------------------------------------


df["rule_missing_core"] = (
    df[temp_columns + rh_columns].isna().any(axis=1)
)


# -------------------------------------------------
# Sentinel / invalid values
# -------------------------------------------------

df["rule_temperature_invalid"] = (
    (df[temp_columns] == -40).any(axis=1)
)


df["rule_rh_invalid"] = (
    (
        (df[rh_columns] < 0)
        |
        (df[rh_columns] > 100)
    ).any(axis=1)
)


df["rule_wind_direction_invalid"] = (
    (
        (df[wind_direction_columns] < 0)
        |
        (df[wind_direction_columns] > 360)
    ).any(axis=1)
)


df["rule_radiation_sentinel"] = (
    (df[radiation_columns] == -312).any(axis=1)
)


df["rule_heat_flux_sentinel"] = (
    (df[heat_flux_columns] == -100).any(axis=1)
)


# -------------------------------------------------
# Power / station-state evidence
# -------------------------------------------------

df["rule_zero_battery"] = (
    df["BATTRY_VOLTAGE(V)"] == 0
)


df["rule_zero_pressure"] = (
    df["ATMOSPHERIC_PRESSURE(mbar) "] == 0
)


df["rule_all_temperature_zero"] = (
    (df[temp_columns] == 0).all(axis=1)
)


df["rule_all_rh_zero"] = (
    (df[rh_columns] == 0).all(axis=1)
)


df["rule_all_core_zero"] = (
    df["rule_all_temperature_zero"]
    &
    df["rule_all_rh_zero"]
)


# -------------------------------------------------
# Time-gap evidence
# -------------------------------------------------

df["rule_large_time_gap"] = (
    df["time_gap_minutes"] > 60
)


# -------------------------------------------------
# Rainfall evidence
# -------------------------------------------------

df["rule_rainfall_suspicious"] = (
    df["rainfall_suspicious"] == 1
)


# -------------------------------------------------
# Total rule evidence
# -------------------------------------------------

rule_columns = [
    "rule_missing_core",
    "rule_temperature_invalid",
    "rule_rh_invalid",
    "rule_wind_direction_invalid",
    "rule_radiation_sentinel",
    "rule_heat_flux_sentinel",
    "rule_zero_battery",
    "rule_zero_pressure",
    "rule_all_temperature_zero",
    "rule_all_rh_zero",
    "rule_all_core_zero",
    "rule_large_time_gap",
    "rule_rainfall_suspicious"
]


df["rule_issue_count"] = (
    df[rule_columns].sum(axis=1)
)


df["rule_anomaly_flag"] = (
    df["rule_issue_count"] > 0
).astype(int)


# -------------------------------------------------
# Summary
# -------------------------------------------------

print("Total observations:", len(df))

print("\n--- RULE / QC EVIDENCE ---")

for column in rule_columns:

    print(
        column + ":",
        int(df[column].sum())
    )


print(
    "\nRows with at least one rule:",
    int(df["rule_anomaly_flag"].sum())
)


print(
    "Rows with no rule evidence:",
    int((df["rule_anomaly_flag"] == 0).sum())
)


print("\nRule evidence count distribution:")

print(
    df["rule_issue_count"]
    .value_counts()
    .sort_index()
    .to_string()
)


# -------------------------------------------------
# Save
# -------------------------------------------------

output_columns = [
    "timestamp"
] + rule_columns + [
    "rule_issue_count",
    "rule_anomaly_flag"
]


df[output_columns].to_csv(
    output_file,
    index=False
)


print("\nSaved:", output_file)