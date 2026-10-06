import os
import pandas as pd
import numpy as np

# ==============================================================================
# EVENT-LEVEL FUSION, ROOT CAUSE DIAGNOSIS & DYNAMIC CONFIDENCE SCORING
# ==============================================================================
# Clusters temporally proximate anomalous observations into unified events,
# evaluates physical multi-channel corroboration, and performs root cause
# diagnosis with dynamic confidence and explicit sensor localization.
# ==============================================================================

INPUT_FILE = "data/processed/aws_evidence_matrix.csv"
OUTPUT_FILE = "data/processed/aws_event_fusion.csv"


def run_event_fusion():
    print("=" * 65)
    print("   EVENT-LEVEL FUSION, ROOT CAUSE & DYNAMIC CONFIDENCE")
    print("=" * 65)

    matrix = pd.read_csv(INPUT_FILE)
    matrix["timestamp"] = pd.to_datetime(matrix["timestamp"])

    # Ensure continuous fused score exists (from build_evidence_matrix)
    if "fused_anomaly_score" not in matrix.columns:
        if_flag = matrix["anomaly_flag"].fillna(0).astype(int) if "anomaly_flag" in matrix.columns else pd.Series(0, index=matrix.index)
        station_flag = matrix["station_system_evidence"].fillna(0).astype(int)
        core_flag = matrix["core_sensor_quality_evidence"].fillna(0).astype(int)
        frozen_flag = matrix["frozen_sensor_evidence"].fillna(0).astype(int)
        cross_flag = matrix["cross_sensor_evidence"].fillna(0).astype(int)
        spike_flag = matrix["single_spike_anomaly"].fillna(0).astype(int)
        temporal_flag = matrix["temporal_evidence"].fillna(0).astype(int)
        matrix["fused_anomaly_flag"] = (
            (if_flag == 1) | (station_flag == 1) | (core_flag == 1) |
            (frozen_flag == 1) | (cross_flag == 1) | (spike_flag == 1) | (temporal_flag == 1)
        ).astype(int)
        matrix["fused_anomaly_score"] = matrix["fused_anomaly_flag"].astype(float)

    # Scope evaluation: evaluate test split if available, otherwise full matrix
    if "if_evidence_available" in matrix.columns and matrix["if_evidence_available"].sum() > 0:
        eval_scope = matrix[matrix["if_evidence_available"] == 1].copy()
    else:
        eval_scope = matrix.copy()

    anomalies = eval_scope[
        eval_scope["fused_anomaly_flag"] == 1
    ].sort_values("timestamp").reset_index(drop=True)

    if len(anomalies) == 0:
        print("No anomalies detected in the evaluated period.")
        empty_df = pd.DataFrame(columns=[
            "event_id", "start_time", "end_time", "observations", "duration_minutes",
            "mean_fused_score", "peak_fused_score", "target_sensor", "candidate_class",
            "severity", "confidence", "probable_root_cause"
        ])
        empty_df.to_csv(OUTPUT_FILE, index=False)
        print("Saved empty event fusion table to:", OUTPUT_FILE)
        return empty_df

    # Cluster consecutive anomalies within 60 minutes into events
    anomalies["gap_from_previous"] = anomalies["timestamp"].diff().dt.total_seconds() / 60
    anomalies["new_event"] = (
        anomalies["gap_from_previous"].isna() | (anomalies["gap_from_previous"] > 60)
    ).astype(int)
    anomalies["event_id"] = anomalies["new_event"].cumsum()

    def mode_or_first(series):
        ne = [str(s).strip() for s in series if pd.notna(s) and str(s).strip() != ""]
        return ne[0] if ne else ""

    agg_dict = {
        "start_time": ("timestamp", "min"),
        "end_time": ("timestamp", "max"),
        "observations": ("timestamp", "count"),
        "mean_fused_score": ("fused_anomaly_score", "mean"),
        "peak_fused_score": ("fused_anomaly_score", "max"),
        "station_system_rows": ("station_system_evidence", "sum"),
        "core_sensor_quality_rows": ("core_sensor_quality_evidence", "sum"),
        "continuity_rows": ("continuity_evidence", "sum"),
        "cross_sensor_rows": ("cross_sensor_evidence", "sum"),
        "temporal_rows": ("temporal_evidence", "sum"),
    }

    if "anomaly_score" in anomalies.columns:
        agg_dict["minimum_anomaly_score"] = ("anomaly_score", "min")
    if "anomaly_flag" in anomalies.columns:
        agg_dict["if_anomaly_rows"] = ("anomaly_flag", "sum")
    if "frozen_sensor_evidence" in anomalies.columns:
        agg_dict["frozen_sensor_rows"] = ("frozen_sensor_evidence", "sum")
    if "single_spike_anomaly" in anomalies.columns:
        agg_dict["single_spike_rows"] = ("single_spike_anomaly", "sum")
    if "consensus_rate_anomaly" in anomalies.columns:
        agg_dict["consensus_rate_rows"] = ("consensus_rate_anomaly", "sum")
    if "evidence_sources_count" in anomalies.columns:
        agg_dict["peak_evidence_sources"] = ("evidence_sources_count", "max")
    if "temp_divergent_sensor" in anomalies.columns:
        agg_dict["divergent_temp_sensor"] = ("temp_divergent_sensor", mode_or_first)
    if "rh_divergent_sensor" in anomalies.columns:
        agg_dict["divergent_rh_sensor"] = ("rh_divergent_sensor", mode_or_first)

    events = anomalies.groupby("event_id").agg(**agg_dict).reset_index()

    events["duration_minutes"] = (
        (events["end_time"] - events["start_time"]).dt.total_seconds() / 60
    )
    events["mean_fused_score"] = events["mean_fused_score"].round(4)
    events["peak_fused_score"] = events["peak_fused_score"].round(4)

    # Defaults for optional tracking columns
    for col in ["frozen_sensor_rows", "single_spike_rows", "consensus_rate_rows", "if_anomaly_rows", "peak_evidence_sources"]:
        if col not in events.columns:
            events[col] = 1 if col == "peak_evidence_sources" else 0

    events["has_station_system_evidence"] = (events["station_system_rows"] > 0).astype(int)
    events["has_core_sensor_quality"] = (events["core_sensor_quality_rows"] > 0).astype(int)
    events["has_frozen_sensor"] = (events["frozen_sensor_rows"] > 0).astype(int)
    events["has_continuity_evidence"] = (events["continuity_rows"] > 0).astype(int)
    events["has_cross_sensor_evidence"] = (events["cross_sensor_rows"] > 0).astype(int)
    events["has_single_spike"] = (events["single_spike_rows"] > 0).astype(int)
    events["has_consensus_rate"] = (events["consensus_rate_rows"] > 0).astype(int)
    events["has_temporal_evidence"] = (events["temporal_rows"] > 0).astype(int)
    events["has_if_anomaly"] = (events["if_anomaly_rows"] > 0).astype(int)

    # Output fields
    events["target_sensor"] = "MULTI_SENSOR"
    events["candidate_class"] = "UNCERTAIN"
    events["severity"] = "LOW"
    events["confidence"] = 0.50
    events["probable_root_cause"] = "UNRESOLVED_ANOMALY"

    for index, event in events.iterrows():
        station = event["has_station_system_evidence"]
        core = event["has_core_sensor_quality"]
        frozen = event["has_frozen_sensor"]
        continuity = event["has_continuity_evidence"]
        cross = event["has_cross_sensor_evidence"]
        temporal = event["has_temporal_evidence"]
        single_spike = event["has_single_spike"]
        consensus = event["has_consensus_rate"]
        if_anom = event["has_if_anomaly"]
        obs = event["observations"]
        peak_sources = event["peak_evidence_sources"]

        temp_divergent = str(event.get("divergent_temp_sensor", "")).strip()
        rh_divergent = str(event.get("divergent_rh_sensor", "")).strip()

        # Target sensor resolution
        if temp_divergent:
            target = temp_divergent
        elif rh_divergent:
            target = rh_divergent
        elif station == 1:
            target = "STATION_POWER_SYSTEM"
        elif consensus == 1 and cross == 0:
            target = "CONSENSUS_ALL_HEIGHTS"
        elif continuity == 1:
            target = "DATA_LOGGER_COMMUNICATION"
        else:
            target = "CORE_SENSORS"

        # ----------------------------------------------------
        # Diagnostic Decision Logic
        # ----------------------------------------------------
        # 1. Station/Power Failure
        if station == 1:
            cand_class = "STATION_SYSTEM_FAILURE"
            root_cause = "STATION_OR_POWER_FAILURE"
            target = "STATION_POWER_SYSTEM"
            sev = "CRITICAL" if obs >= 3 else "HIGH"
            base_conf = 0.96

        # 2. Frozen/Stuck Sensor
        elif frozen == 1 or (obs >= 4 and cross == 1 and temporal == 0 and single_spike == 0):
            cand_class = "PROBABLE_SENSOR_FAULT"
            root_cause = "FROZEN_SENSOR"
            sev = "HIGH"
            base_conf = 0.94

        # 3. Coherent Weather Extreme (Storm / Gust drop across all sensors without disagreement)
        elif (consensus == 1 or temporal == 1) and cross == 0 and core == 0 and station == 0:
            cand_class = "POSSIBLE_WEATHER_EXTREME"
            root_cause = "RAPID_COHERENT_WEATHER_EVENT"
            target = "CONSENSUS_ALL_HEIGHTS"
            sev = "MEDIUM"
            base_conf = 0.90

        # 4. Isolated Sensor Spike (Transient, 1-3 observations on single sensor without consensus)
        elif single_spike == 1 and obs <= 3 and consensus == 0:
            cand_class = "PROBABLE_SENSOR_FAULT"
            root_cause = "SENSOR_SPIKE"
            sev = "HIGH"
            base_conf = 0.92

        # 5. Calibration Drift / Persistent Disagreement
        elif cross == 1 and core == 0 and consensus == 0:
            cand_class = "PROBABLE_SENSOR_FAULT"
            root_cause = "CALIBRATION_DRIFT_OR_BIAS"
            sev = "HIGH" if obs >= 4 else "MEDIUM"
            base_conf = 0.88 if obs >= 3 else 0.78

        # 6. Invalid / Sentinel Reading (Out-of-bounds sentinel)
        elif core == 1 and cross == 1:
            cand_class = "PROBABLE_SENSOR_FAULT"
            root_cause = "INVALID_SENTINEL_READING"
            sev = "HIGH"
            base_conf = 0.95

        # 7. Physical Core Sensor Quality Issue
        elif core == 1:
            cand_class = "PROBABLE_SENSOR_FAULT"
            root_cause = "SENSOR_OR_DATA_QUALITY"
            sev = "HIGH" if continuity == 0 else "MEDIUM"
            base_conf = 0.90

        # 8. Communication Gap / Data Dropout
        elif continuity == 1 and core == 0 and cross == 0:
            cand_class = "DATA_COMMUNICATION_OUTAGE"
            root_cause = "DATA_COMMUNICATION_GAP"
            target = "DATA_LOGGER_COMMUNICATION"
            sev = "MEDIUM"
            base_conf = 0.85

        # 9. Complex / Multi-Signal Dynamic Event
        elif cross == 1 and temporal == 1:
            cand_class = "PROBABLE_SENSOR_FAULT"
            root_cause = "UNUSUAL_WEATHER_OR_SENSOR_BEHAVIOR"
            sev = "MEDIUM"
            base_conf = 0.75

        # 10. ML Statistical Outlier Only
        elif if_anom == 1:
            cand_class = "UNCERTAIN"
            root_cause = "STATISTICAL_MULTIVARIATE_OUTLIER"
            target = "MULTIVARIATE_VECTOR"
            sev = "LOW"
            base_conf = 0.58

        else:
            cand_class = "UNCERTAIN"
            root_cause = "UNRESOLVED_ANOMALY"
            sev = "LOW"
            base_conf = 0.50

        # Dynamic confidence modulation:
        # Multi-channel corroboration + observation duration factors
        src_bonus = 0.02 * min(2, max(0, peak_sources - 1))
        obs_bonus = 0.02 * min(2, obs - 1)
        final_conf = min(0.99, max(0.50, round(base_conf + src_bonus + obs_bonus, 2)))

        events.loc[index, "target_sensor"] = target
        events.loc[index, "candidate_class"] = cand_class
        events.loc[index, "severity"] = sev
        events.loc[index, "confidence"] = final_conf
        events.loc[index, "probable_root_cause"] = root_cause

    print(f"Total anomalous observations : {len(anomalies)}")
    print(f"Total anomaly events         : {len(events)}")
    print(f"Mean event confidence        : {events['confidence'].mean():.2f}")
    print(f"Mean event fused score       : {events['mean_fused_score'].mean():.4f}")

    print("\n========================================")
    print("EVENT-LEVEL CLASSIFICATION")
    print("========================================")
    print(events["candidate_class"].value_counts().to_string())

    print("\n========================================")
    print("EVENT SEVERITY BREAKDOWN")
    print("========================================")
    print(events["severity"].value_counts().to_string())

    print("\n========================================")
    print("EVENT ROOT CAUSE ATTRIBUTION")
    print("========================================")
    print(events["probable_root_cause"].value_counts().to_string())

    print("\n========================================")
    print("SAMPLE FUSED EVENTS (With Continuous Metrics)")
    print("========================================")
    display_cols = [
        "event_id", "start_time", "end_time", "observations", "mean_fused_score",
        "target_sensor", "candidate_class", "severity", "confidence", "probable_root_cause"
    ]
    print(events[display_cols].head(15).to_string(index=False))

    events.to_csv(OUTPUT_FILE, index=False)
    print(f"\nSaved upgraded event fusion dataset: {OUTPUT_FILE}")
    print("=" * 65)
    return events


if __name__ == "__main__":
    run_event_fusion()
