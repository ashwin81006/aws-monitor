import pandas as pd


input_file = "data/processed/aws_evidence_matrix.csv"

df = pd.read_csv(input_file)


# Only the period where Isolation Forest produced predictions
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
print("RULE PREVALENCE AND IF ASSOCIATION")
print("========================================")


rows = []


for rule in rule_columns:

    test_count = (
        test[rule]
        .fillna(0)
        .astype(int)
        .sum()
    )

    anomaly_count = (
        anomalies[rule]
        .fillna(0)
        .astype(int)
        .sum()
    )

    test_rate = (
        test_count / len(test)
    )

    anomaly_rate = (
        anomaly_count / len(anomalies)
    )


    if test_rate > 0:

        lift = (
            anomaly_rate / test_rate
        )

    else:

        lift = 0


    rows.append({
        "rule": rule,
        "test_count": test_count,
        "test_rate_percent": test_rate * 100,
        "if_anomaly_count": anomaly_count,
        "if_anomaly_rate_percent": anomaly_rate * 100,
        "lift": lift
    })


summary = pd.DataFrame(rows)


summary = summary.sort_values(
    "lift",
    ascending=False
)


print(
    summary.to_string(
        index=False
    )
)


print("\n========================================")
print("MOST COMMON RULES IN TEST DATA")
print("========================================")


common = summary.sort_values(
    "test_count",
    ascending=False
)


print(
    common[
        [
            "rule",
            "test_count",
            "test_rate_percent"
        ]
    ].to_string(index=False)
)


print("\n========================================")
print("RULES WITH HIGHEST DISCRIMINATION")
print("========================================")


print(
    summary[
        [
            "rule",
            "if_anomaly_count",
            "if_anomaly_rate_percent",
            "test_rate_percent",
            "lift"
        ]
    ].head(10).to_string(index=False)
)