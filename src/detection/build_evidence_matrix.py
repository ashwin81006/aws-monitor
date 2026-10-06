import os
import json
import numpy as np
import pandas as pd

# ==============================================================================
# MULTI-SOURCE EVIDENCE MATRIX & BAYESIAN NOISY-OR FUSION ENGINE
# ==============================================================================
# Consolidates 4 independent anomaly evidence streams:
#   1. Deterministic Rule QC (Physics bounds, electrical limits, frozen values)
#   2. Physical Cross-Sensor Consistency (Tri-sensor height spatial spread)
#   3. Temporal Dynamics (Rate of change, acceleration, single spikes)
#   4. Unsupervised ML Anomaly Detection (Multivariate isolation scores)
#
# Generates:
#   - Continuous normalized sub-scores: score_rule, score_cross, score_temporal, score_ml ∈ [0, 1]
#   - Bayesian Noisy-OR fused anomaly score: fused_anomaly_score ∈ [0, 1]
#   - Active evidence streams count & primary contributing source
#   - Calibrated binary fused anomaly trigger flag: fused_anomaly_flag
# ==============================================================================

RULE_FILE = "data/processed/aws_rule_evidence.csv"
CROSS_FILE = "data/processed/aws_cross_sensor_evidence.csv"
TEMPORAL_FILE = "data/processed/aws_temporal_evidence.csv"
IF_FILE = "data/processed/aws_if_results.csv"

CROSS_THRESHOLDS = "models/cross_sensor_thresholds.json"
TEMPORAL_THRESHOLDS = "models/temporal_thresholds.json"

OUTPUT_FILE = "data/processed/aws_evidence_matrix.csv"


def build_evidence_matrix():
    print("=" * 65)
    print("       MULTI-SOURCE EVIDENCE MATRIX & BAYESIAN FUSION")
    print("=" * 65)

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

    if "rule_sensor_frozen" in rule.columns:
        rule_columns.append("rule_sensor_frozen")

    rule_data = rule[["timestamp"] + rule_columns + ["rule_issue_count"]].copy()

    # Derived station/system evidence
    rule_data["station_zero_battery"] = (rule_data["rule_zero_battery"] == 1).astype(int)
    rule_data["station_zero_pressure"] = (rule_data["rule_zero_pressure"] == 1).astype(int)
    rule_data["station_all_core_zero"] = (rule_data["rule_all_core_zero"] == 1).astype(int)
    rule_data["station_coordinated_zero"] = (
        (rule_data["station_zero_battery"] == 1) & (rule_data["station_all_core_zero"] == 1)
    ).astype(int)

    station_columns = ["station_zero_battery", "station_zero_pressure", "station_all_core_zero"]
    rule_data["station_evidence_count"] = rule_data[station_columns].sum(axis=1)
    rule_data["station_evidence_flag"] = (rule_data["station_evidence_count"] > 0).astype(int)
    rule_data["strong_station_evidence"] = (rule_data["station_evidence_count"] >= 2).astype(int)

    rule_data["station_system_evidence"] = rule_data["station_evidence_flag"].astype(int)
    rule_data["strong_station_system_evidence"] = rule_data["strong_station_evidence"].astype(int)

    has_frozen = "rule_sensor_frozen" in rule_data.columns
    rule_data["frozen_sensor_evidence"] = (rule_data["rule_sensor_frozen"] == 1).astype(int) if has_frozen else 0

    rule_data["core_sensor_quality_evidence"] = (
        (rule_data["rule_missing_core"] == 1)
        | (rule_data["rule_temperature_invalid"] == 1)
        | (rule_data["rule_rh_invalid"] == 1)
        | (rule_data["frozen_sensor_evidence"] == 1)
    ).astype(int)

    rule_data["continuity_evidence"] = (rule_data["rule_large_time_gap"] == 1).astype(int)
    rule_data["auxiliary_channel_evidence"] = (
        (rule_data["rule_wind_direction_invalid"] == 1)
        | (rule_data["rule_radiation_sentinel"] == 1)
        | (rule_data["rule_heat_flux_sentinel"] == 1)
        | (rule_data["rule_rainfall_suspicious"] == 1)
    ).astype(int)

    # Cross sensor columns
    cross_columns = [
        "timestamp", "temperature_valid_count", "temperature_mean", "temperature_spread",
        "temperature_disagreement", "temp_divergent_sensor", "temp_isolated_fault",
        "humidity_valid_count", "humidity_mean", "humidity_spread", "humidity_disagreement",
        "rh_divergent_sensor", "rh_isolated_fault", "cross_sensor_evidence"
    ]
    cross_columns = [c for c in cross_columns if c in cross.columns]

    # Temporal columns
    temporal_columns = [
        "timestamp", "previous_gap_minutes", "temperature_median", "temperature_change",
        "temperature_rate", "temperature_rate_anomaly", "temperature_single_rate_anomaly",
        "humidity_median", "humidity_change", "humidity_rate", "humidity_rate_anomaly",
        "humidity_single_rate_anomaly", "consensus_rate_anomaly", "single_spike_anomaly",
        "temporal_evidence_count", "temporal_evidence"
    ]
    temporal_columns = [c for c in temporal_columns if c in temporal.columns]

    if_columns = ["timestamp", "anomaly_score", "anomaly_flag"]
    if_columns = [c for c in if_columns if c in if_results.columns]

    # Merge into unified matrix
    matrix = rule_data.merge(cross[cross_columns], on="timestamp", how="left")
    matrix = matrix.merge(temporal[temporal_columns], on="timestamp", how="left")
    matrix = matrix.merge(if_results[if_columns], on="timestamp", how="left")

    matrix["if_evidence_available"] = matrix["anomaly_flag"].notna().astype(int)

    boolean_columns = [
        "station_system_evidence", "strong_station_system_evidence", "core_sensor_quality_evidence",
        "continuity_evidence", "auxiliary_channel_evidence", "frozen_sensor_evidence",
        "station_evidence_flag", "strong_station_evidence", "temperature_disagreement",
        "humidity_disagreement", "temp_isolated_fault", "rh_isolated_fault", "cross_sensor_evidence",
        "temperature_rate_anomaly", "humidity_rate_anomaly", "temperature_single_rate_anomaly",
        "humidity_single_rate_anomaly", "consensus_rate_anomaly", "single_spike_anomaly",
        "temporal_evidence"
    ]
    boolean_columns = [c for c in boolean_columns if c in matrix.columns]

    for column in boolean_columns:
        matrix[column] = matrix[column].fillna(False).astype(int)

    # --------------------------------------------------------------------------
    # CONTINUOUS CALIBRATED SUB-SCORES GENERATION
    # --------------------------------------------------------------------------
    print("\n[1/3] Computing calibrated continuous sub-scores...")

    # Load calibration thresholds if available
    t_spread_thresh = 6.05
    rh_spread_thresh = 17.8
    if os.path.exists(CROSS_THRESHOLDS):
        with open(CROSS_THRESHOLDS, "r") as f:
            c_thresh = json.load(f)
            t_spread_thresh = c_thresh.get("temperature_spread_99th_percentile", 6.05)
            rh_spread_thresh = c_thresh.get("humidity_spread_99th_percentile", 17.8)

    t_rate_thresh = 7.3
    rh_rate_thresh = 28.8
    if os.path.exists(TEMPORAL_THRESHOLDS):
        with open(TEMPORAL_THRESHOLDS, "r") as f:
            t_thresh = json.load(f)
            t_rate_thresh = t_thresh.get("temperature_rate_99th_percentile", 7.3)
            rh_rate_thresh = t_thresh.get("humidity_rate_99th_percentile", 28.8)

    # 1. Rule Evidence Sub-Score (score_rule in [0, 1])
    score_rule = pd.Series(0.0, index=matrix.index)
    score_rule = np.where(matrix["rule_missing_core"] == 1, 0.80, score_rule)
    score_rule = np.where(matrix["frozen_sensor_evidence"] == 1, 0.90, score_rule)
    score_rule = np.where(
        (matrix.get("rule_temperature_invalid", 0) == 1) | (matrix.get("rule_rh_invalid", 0) == 1),
        0.95, score_rule
    )
    score_rule = np.where(matrix["station_system_evidence"] == 1, 1.00, score_rule)
    matrix["score_rule"] = np.round(score_rule, 4)

    # 2. Cross-Sensor Consistency Sub-Score (score_cross in [0, 1])
    t_ratio = (matrix["temperature_spread"] / t_spread_thresh).clip(lower=0.0).fillna(0.0)
    rh_ratio = (matrix["humidity_spread"] / rh_spread_thresh).clip(lower=0.0).fillna(0.0)
    max_cross_ratio = np.maximum(t_ratio, rh_ratio)

    score_cross = 1.0 / (1.0 + np.exp(-3.5 * (max_cross_ratio - 1.0)))
    score_cross = np.where(max_cross_ratio < 0.50, 0.0, score_cross)
    # Boost isolated sensor divergences
    has_isolated = (matrix.get("temp_isolated_fault", 0) == 1) | (matrix.get("rh_isolated_fault", 0) == 1)
    score_cross = np.clip(score_cross + np.where(has_isolated, 0.10, 0.0), 0.0, 1.0)
    matrix["score_cross"] = np.round(score_cross, 4)

    # 3. Temporal Dynamics Sub-Score (score_temporal in [0, 1])
    t_r_ratio = (matrix["temperature_rate"] / t_rate_thresh).clip(lower=0.0).fillna(0.0)
    rh_r_ratio = (matrix["humidity_rate"] / rh_rate_thresh).clip(lower=0.0).fillna(0.0)
    max_rate_ratio = np.maximum(t_r_ratio, rh_r_ratio)

    score_temp = 1.0 / (1.0 + np.exp(-3.5 * (max_rate_ratio - 1.0)))
    score_temp = np.where(max_rate_ratio < 0.50, 0.0, score_temp)
    if "single_spike_anomaly" in matrix.columns:
        score_temp = np.where(matrix["single_spike_anomaly"] == 1, np.maximum(score_temp, 0.88), score_temp)
    matrix["score_temporal"] = np.round(score_temp, 4)

    # 4. Machine Learning Sub-Score (score_ml in [0, 1])
    score_ml = pd.Series(0.0, index=matrix.index)
    if "anomaly_score" in matrix.columns and matrix["if_evidence_available"].sum() > 0:
        valid_mask = matrix["if_evidence_available"] == 1
        anom_scores = matrix.loc[valid_mask, "anomaly_score"]
        ml_anom_prob = np.where(
            anom_scores < 0,
            np.clip(0.50 + 0.50 * (-anom_scores / 0.10), 0.50, 1.0),
            0.0
        )
        score_ml.loc[valid_mask] = ml_anom_prob
    matrix["score_ml"] = np.round(score_ml, 4)

    # --------------------------------------------------------------------------
    # MULTI-SOURCE BAYESIAN NOISY-OR PROBABILISTIC FUSION
    # --------------------------------------------------------------------------
    print("\n[2/3] Executing Bayesian Noisy-OR multi-layer fusion...")
    # Channel reliability weights
    w_rule = 0.95
    w_cross = 0.90
    w_temp = 0.85
    w_ml = 0.80

    no_fault_prob = (
        (1.0 - w_rule * matrix["score_rule"]) *
        (1.0 - w_cross * matrix["score_cross"]) *
        (1.0 - w_temp * matrix["score_temporal"])
    )
    if matrix["if_evidence_available"].sum() > 0:
        ml_term = np.where(matrix["if_evidence_available"] == 1, 1.0 - w_ml * matrix["score_ml"], 1.0)
        no_fault_prob = no_fault_prob * ml_term

    matrix["fused_anomaly_score"] = np.round((1.0 - no_fault_prob).clip(lower=0.0, upper=1.0), 4)

    # Evidence streams agreement count
    has_rule_stream = (matrix["score_rule"] >= 0.50).astype(int)
    has_cross_stream = (matrix["score_cross"] >= 0.50).astype(int)
    has_temp_stream = (matrix["score_temporal"] >= 0.50).astype(int)
    has_ml_stream = (matrix["score_ml"] >= 0.50).astype(int)
    matrix["evidence_sources_count"] = has_rule_stream + has_cross_stream + has_temp_stream + has_ml_stream

    # Dominant primary contributing source
    sub_score_df = matrix[["score_rule", "score_cross", "score_temporal", "score_ml"]]
    id_map = {
        "score_rule": "RULE_ENGINE",
        "score_cross": "CROSS_SENSOR",
        "score_temporal": "TEMPORAL_DYNAMICS",
        "score_ml": "MACHINE_LEARNING"
    }
    dominant_col = sub_score_df.idxmax(axis=1)
    matrix["primary_evidence_source"] = np.where(
        matrix["fused_anomaly_score"] >= 0.30,
        dominant_col.map(id_map),
        "NORMAL_BACKGROUND"
    )

    # Fused observation-level anomaly flag
    critical_rule_flag = (
        (matrix["station_system_evidence"] == 1) |
        (matrix["core_sensor_quality_evidence"] == 1) |
        (matrix["cross_sensor_evidence"] == 1) |
        (matrix["single_spike_anomaly"] == 1) |
        (matrix["temporal_evidence"] == 1) |
        (matrix.get("anomaly_flag", 0) == 1)
    )
    matrix["fused_anomaly_flag"] = (
        (matrix["fused_anomaly_score"] >= 0.50) | critical_rule_flag
    ).astype(int)

    # --------------------------------------------------------------------------
    # SUMMARY & EXPORT
    # --------------------------------------------------------------------------
    print("\n[3/3] Saving multi-source evidence matrix...")
    print(f"Total observations        : {len(matrix)}")
    print(f"Unique timestamps         : {matrix['timestamp'].nunique()}")
    print(f"Fused anomalies flagged   : {matrix['fused_anomaly_flag'].sum()} ({matrix['fused_anomaly_flag'].mean()*100:.2f}%)")
    print(f"Mean fused anomaly score  : {matrix['fused_anomaly_score'].mean():.4f}")
    print(f"Max fused anomaly score   : {matrix['fused_anomaly_score'].max():.4f}")

    print("\nEvidence stream distributions (active >= 0.50):")
    print(f"  Rule QC Stream          : {has_rule_stream.sum()}")
    print(f"  Cross-Sensor Stream     : {has_cross_stream.sum()}")
    print(f"  Temporal Dynamic Stream : {has_temp_stream.sum()}")
    print(f"  Machine Learning Stream : {has_ml_stream.sum()}")

    matrix.to_csv(OUTPUT_FILE, index=False)
    print(f"\nSaved unified evidence matrix to: {OUTPUT_FILE}")
    print("=" * 65)


if __name__ == "__main__":
    build_evidence_matrix()
