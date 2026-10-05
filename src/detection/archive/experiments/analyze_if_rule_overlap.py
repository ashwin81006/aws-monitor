import pandas as pd


input_file = "data/processed/aws_evidence_matrix.csv"

df = pd.read_csv(input_file)


test = df[
    df["if_evidence_available"] == 1
].copy()


test["anomaly_flag"] = (
    test["anomaly_flag"]
    .fillna(0)
    .astype(int)
)


anomalies = test[
    test["anomaly_flag"] == 1
].copy()


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


print("Test observations:", len(test))
print("IF anomalies:", len(anomalies))


print("\n========================================")
print("IF + INDIVIDUAL QC RULES")
print("========================================")


for column in rule_columns:

    count = (
        anomalies[column]
        .fillna(0)
        .astype(int)
        .sum()
    )

    percentage = (
        count / len(anomalies) * 100
    )

    print(
        f"{column}: {count} ({percentage:.2f}%)"
    )


print("\n========================================")
print("IF ANOMALIES WITH NO QC RULE")
print("========================================")


rule_matrix = anomalies[
    rule_columns
].fillna(0).astype(int)


no_rule = (
    rule_matrix.sum(axis=1) == 0
)


print(
    "IF anomalies with no individual QC rule:",
    no_rule.sum()
)


print(
    "IF anomalies with at least one QC rule:",
    (~no_rule).sum()
)


print("\n========================================")
print("QC RULE COUNT PER IF ANOMALY")
print("========================================")


anomalies["qc_rule_count"] = (
    rule_matrix.sum(axis=1)
)


print(
    anomalies["qc_rule_count"]
    .value_counts()
    .sort_index()
    .to_string()
)


print("\n========================================")
print("RAINFALL + IF")
print("========================================")


rainfall_if = anomalies[
    anomalies["rule_rainfall_suspicious"] == 1
]

print(
    "IF anomalies with suspicious rainfall:",
    len(rainfall_if)
)


print("\n========================================")
print("HEAT FLUX + IF")
print("========================================")


heat_if = anomalies[
    anomalies["rule_heat_flux_sentinel"] == 1
]

print(
    "IF anomalies with heat-flux sentinel:",
    len(heat_if)
)


print("\n========================================")
print("MISSING CORE + IF")
print("========================================")


missing_if = anomalies[
    anomalies["rule_missing_core"] == 1
]

print(
    "IF anomalies with missing core sensor:",
    len(missing_if)
)