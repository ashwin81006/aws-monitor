import pandas as pd


RULE_FILE = "data/processed/aws_rule_evidence.csv"
CROSS_FILE = "data/processed/aws_cross_sensor_evidence.csv"
TEMPORAL_FILE = "data/processed/aws_temporal_evidence.csv"
IF_FILE = "data/processed/aws_if_results.csv"

OUTPUT_FILE = "data/processed/aws_evidence_matrix.csv"


rule = pd.read_csv(RULE_FILE)
cross = pd.read_csv(CROSS_FILE)
temporal = pd.read_csv(TEMPORAL_FILE)
if_results = pd.read_csv(IF_FILE)


for data in [rule, cross, temporal, if_results]:
    data["timestamp"] = pd.to_datetime(data["timestamp"])


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


rule_data = rule[
    ["timestamp"] + rule_columns + [
        "rule_issue_count"
    ]
].copy()


# Station/system evidence derived directly from rule evidence.
rule_data["station_zero_battery"] = (
    rule_data["rule_zero_battery"] == 1
).astype(int)

rule_data["station_zero_pressure"] = (
    rule_data["rule_zero_pressure"] == 1
).astype(int)

rule_data["station_all_core_zero"] = (
    rule_data["rule_all_core_zero"] == 1
).astype(int)

rule_data["station_coordinated_zero"] = (
    (rule_data["station_zero_battery"] == 1)
    & (rule_data["station_all_core_zero"] == 1)
).astype(int)

station_columns = [
    "station_zero_battery",
    "station_zero_pressure",
    "station_all_core_zero"
]

rule_data["station_evidence_count"] = (
    rule_data[station_columns].sum(axis=1)
)

rule_data["station_evidence_flag"] = (
    rule_data["station_evidence_count"] > 0
).astype(int)

rule_data["strong_station_evidence"] = (
    rule_data["station_evidence_count"] >= 2
).astype(int)


# Evidence categories used by event-level fusion.
rule_data["station_system_evidence"] = (
    rule_data["station_evidence_flag"]
).astype(int)

rule_data["strong_station_system_evidence"] = (
    rule_data["strong_station_evidence"]
).astype(int)

rule_data["core_sensor_quality_evidence"] = (
    (rule_data["rule_missing_core"] == 1)
    | (rule_data["rule_temperature_invalid"] == 1)
    | (rule_data["rule_rh_invalid"] == 1)
).astype(int)

rule_data["continuity_evidence"] = (
    rule_data["rule_large_time_gap"] == 1
).astype(int)

rule_data["auxiliary_channel_evidence"] = (
    (rule_data["rule_wind_direction_invalid"] == 1)
    | (rule_data["rule_radiation_sentinel"] == 1)
    | (rule_data["rule_heat_flux_sentinel"] == 1)
    | (rule_data["rule_rainfall_suspicious"] == 1)
).astype(int)


station_output = [
    "timestamp",
    "station_zero_battery",
    "station_zero_pressure",
    "station_all_core_zero",
    "station_coordinated_zero",
    "station_evidence_count",
    "station_evidence_flag",
    "strong_station_evidence"
]

category_output = [
    "timestamp",
    "station_system_evidence",
    "strong_station_system_evidence",
    "core_sensor_quality_evidence",
    "continuity_evidence",
    "auxiliary_channel_evidence"
]


cross_columns = [
    "timestamp",
    "temperature_valid_count",
    "temperature_mean",
    "temperature_spread",
    "temperature_disagreement",
    "humidity_valid_count",
    "humidity_mean",
    "humidity_spread",
    "humidity_disagreement",
    "cross_sensor_evidence"
]

temporal_columns = [
    "timestamp",
    "previous_gap_minutes",
    "temperature_median",
    "temperature_change",
    "temperature_rate",
    "temperature_rate_anomaly",
    "humidity_median",
    "humidity_change",
    "humidity_rate",
    "humidity_rate_anomaly",
    "temporal_evidence_count",
    "temporal_evidence"
]

if_columns = [
    "timestamp",
    "anomaly_score",
    "anomaly_flag"
]


matrix = rule_data.merge(
    cross[cross_columns],
    on="timestamp",
    how="left"
)

matrix = matrix.merge(
    temporal[temporal_columns],
    on="timestamp",
    how="left"
)

matrix = matrix.merge(
    if_results[if_columns],
    on="timestamp",
    how="left"
)

matrix["if_evidence_available"] = (
    matrix["anomaly_flag"].notna()
).astype(int)


boolean_columns = [
    "station_system_evidence",
    "strong_station_system_evidence",
    "core_sensor_quality_evidence",
    "continuity_evidence",
    "auxiliary_channel_evidence",
    "station_evidence_flag",
    "strong_station_evidence",
    "temperature_disagreement",
    "humidity_disagreement",
    "cross_sensor_evidence",
    "temperature_rate_anomaly",
    "humidity_rate_anomaly",
    "temporal_evidence"
]

for column in boolean_columns:
    matrix[column] = (
        matrix[column]
        .fillna(False)
        .astype(int)
    )


print("Total observations:", len(matrix))
print("Unique timestamps:", matrix["timestamp"].nunique())
print("Duplicate timestamps:", matrix["timestamp"].duplicated().sum())
print("IF evidence available:", matrix["if_evidence_available"].sum())
print("IF anomalies:", matrix["anomaly_flag"].fillna(0).sum())

print("\n--- EVIDENCE COUNTS ---")
print(
    "Generic rule evidence:",
    matrix[rule_columns].sum(axis=1).gt(0).sum()
)
print("Station/system evidence:", matrix["station_system_evidence"].sum())
print("Strong station/system evidence:", matrix["strong_station_system_evidence"].sum())
print("Core sensor quality evidence:", matrix["core_sensor_quality_evidence"].sum())
print("Continuity evidence:", matrix["continuity_evidence"].sum())
print("Auxiliary channel evidence:", matrix["auxiliary_channel_evidence"].sum())
print("Cross-sensor evidence:", matrix["cross_sensor_evidence"].sum())
print("Temporal evidence:", matrix["temporal_evidence"].sum())


matrix.to_csv(
    OUTPUT_FILE,
    index=False
)

print("\nSaved:", OUTPUT_FILE)
