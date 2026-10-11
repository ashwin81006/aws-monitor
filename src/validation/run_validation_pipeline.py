import os
import json
import joblib
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest


from src.features.feature_builder import compute_31_features_df

FAULTY_CLEAN = "data/processed/aws_faulty_clean.csv"
TEST_READY_OUT = "data/processed/aws_validation_test_ready.csv"
EVIDENCE_MATRIX_OUT = "data/processed/aws_validation_evidence_matrix.csv"
EVENT_FUSION_OUT = "data/processed/aws_validation_event_fusion.csv"

IF_MODEL_FILE = "models/isolation_forest.pkl"
CROSS_THRESHOLDS = "models/cross_sensor_thresholds.json"
TEMPORAL_THRESHOLDS = "models/temporal_thresholds.json"
TRAIN_MEDIANS_FILE = "models/train_medians.pkl"
FEATURE_COLS_FILE = "models/ml_feature_columns.json"


def run_validation_pipeline(model_name="isolation_forest"):
    print("=" * 60)
    print(f"     VALIDATION: RUNNING PIPELINE WITH {model_name.upper()}")
    print("=" * 60)

    # ----------------------------------------------------
    # 1. Feature Engineering (31 Clean Causal Domain Features)
    # ----------------------------------------------------
    print("\n[1/6] Building 31 clean causal domain features on fault-injected dataset...")
    raw_faulty = pd.read_csv(FAULTY_CLEAN)
    df = compute_31_features_df(raw_faulty, window_size=9)

    # ----------------------------------------------------
    # 2. Extract Test Split & ML Model Inference
    # ----------------------------------------------------
    print(f"\n[2/6] Running ML Model Inference ({model_name.upper()})...")
    split_index = int(len(df) * 0.70)
    test_features = df.iloc[split_index:].copy().reset_index(drop=True)

    with open(FEATURE_COLS_FILE, "r") as f:
        feature_columns = json.load(f)
    train_medians = joblib.load(TRAIN_MEDIANS_FILE)

    test_ml = test_features[feature_columns].copy()
    test_ml = test_ml.replace([np.inf, -np.inf], np.nan)
    test_ml = test_ml.fillna(train_medians)
    test_ml.to_csv(TEST_READY_OUT, index=False)

    scaler = joblib.load("models/scaler.pkl")
    test_ml_scaled = pd.DataFrame(scaler.transform(test_ml), columns=feature_columns)


    # Load model and predict based on selected model_name
    model_name_lower = str(model_name).lower().strip()
    if "lof" in model_name_lower or "local_outlier" in model_name_lower:
        model = joblib.load("models/lof_model.pkl")
        test_scores = model.decision_function(test_ml_scaled.values)
        test_preds = model.predict(test_ml_scaled.values)
        model_display = "LOF"
    elif "svm" in model_name_lower or "ocsvm" in model_name_lower:
        model = joblib.load("models/ocsvm_model.pkl")
        test_scores = model.decision_function(test_ml_scaled.values)
        test_preds = model.predict(test_ml_scaled.values)
        model_display = "One-Class SVM"
    else:
        model = joblib.load(IF_MODEL_FILE)
        test_scores = model.decision_function(test_ml_scaled)
        test_preds = model.predict(test_ml_scaled)
        model_display = "Isolation Forest"

    if_results = pd.DataFrame({
        "timestamp": test_features["timestamp"],
        "anomaly_score": test_scores,
        "anomaly_flag": (test_preds == -1).astype(int)
    })
    print(f"ML Model Inference: {if_results['anomaly_flag'].sum()} {model_display} anomalies detected")

    # ----------------------------------------------------
    # 3. Rule-based QC
    # ----------------------------------------------------
    print("\n[3/6] Running Rule-based QC...")
    temp_cols = [
        "AIR_TEMPERATURE1(°C at 2m height)",
        "AIR_TEMPERATURE2(°C at 4m height)",
        "AIR_TEMPERATURE3(°C at 8m height)"
    ]
    rh_cols = [
        "RELATIVE_HUMIDITY1(% at 2m height)",
        "RELATIVE_HUMIDITY2(% at 4m height)",
        "RELATIVE_HUMIDITY3(% at 8m height)"
    ]
    wind_dir_cols = ["WIND_DIRECTION1(deg at 3m height)", "WIND_DIRECTION2(deg at 6m height)", "WIND_DIRECTION3(deg at 10m height)"]
    rad_cols = ["RAD_LONG_OUT(w/m2) ", "RAD_LONG_IN(w/m2) "]
    flux_cols = ["HEAT_FLUX1(w/m2 at 0.50m height) ", "HEAT_FLUX2(w/m2 at 0.20m height)"]

    rule_df = df[["timestamp"]].copy()
    rule_df["rule_missing_core"] = df[temp_cols + rh_cols].isna().any(axis=1)
    rule_df["rule_temperature_invalid"] = (df[temp_cols] == -40).any(axis=1)
    rule_df["rule_rh_invalid"] = ((df[rh_cols] < 0) | (df[rh_cols] > 100)).any(axis=1)
    rule_df["rule_wind_direction_invalid"] = ((df[wind_dir_cols] < 0) | (df[wind_dir_cols] > 360)).any(axis=1)
    rule_df["rule_radiation_sentinel"] = (df[rad_cols] == -312).any(axis=1)
    rule_df["rule_heat_flux_sentinel"] = (df[flux_cols] == -100).any(axis=1)
    rule_df["rule_zero_battery"] = df["BATTRY_VOLTAGE(V)"] == 0
    rule_df["rule_zero_pressure"] = df["ATMOSPHERIC_PRESSURE(mbar) "] == 0
    rule_df["rule_all_temperature_zero"] = (df[temp_cols] == 0).all(axis=1)
    rule_df["rule_all_rh_zero"] = (df[rh_cols] == 0).all(axis=1)
    rule_df["rule_all_core_zero"] = rule_df["rule_all_temperature_zero"] & rule_df["rule_all_rh_zero"]
    rule_df["rule_large_time_gap"] = df["time_gap_minutes"] > 60
    rainfall_suspicious = (df["RAINFALL(mm)"] > 100) if "RAINFALL(mm)" in df.columns else False
    rule_df["rule_rainfall_suspicious"] = rainfall_suspicious

    # Vectorized frozen sensor detection
    gap_series = df["time_gap_minutes"]
    def is_series_frozen(series, min_minutes=180, exclude_val=None):
        valid = series.notna() & (series != -40)
        if exclude_val is not None:
            valid &= (series != exclude_val)
        same = (series == series.shift(1)) & valid & (gap_series <= 60)
        streak_count = same.groupby((~same).cumsum()).cumsum()
        return streak_count * 30 >= min_minutes

    temp_frozen_masks = [is_series_frozen(df[c], min_minutes=120) for c in temp_cols if c in df.columns]
    rh_frozen_masks = [is_series_frozen(df[c], min_minutes=120, exclude_val=100.0) for c in rh_cols if c in df.columns]


    rule_df["rule_temperature_frozen"] = (pd.concat(temp_frozen_masks, axis=1).any(axis=1)).astype(int) if temp_frozen_masks else 0
    rule_df["rule_rh_frozen"] = (pd.concat(rh_frozen_masks, axis=1).any(axis=1)).astype(int) if rh_frozen_masks else 0
    rule_df["rule_sensor_frozen"] = ((rule_df["rule_temperature_frozen"] == 1) | (rule_df["rule_rh_frozen"] == 1)).astype(int)

    rule_cols_list = [
        "rule_missing_core", "rule_temperature_invalid", "rule_rh_invalid",
        "rule_wind_direction_invalid", "rule_radiation_sentinel", "rule_heat_flux_sentinel",
        "rule_zero_battery", "rule_zero_pressure", "rule_all_temperature_zero",
        "rule_all_rh_zero", "rule_all_core_zero", "rule_sensor_frozen",
        "rule_large_time_gap", "rule_rainfall_suspicious"
    ]
    rule_df["rule_issue_count"] = rule_df[rule_cols_list].sum(axis=1)
    rule_df["rule_anomaly_flag"] = (rule_df["rule_issue_count"] > 0).astype(int)

    # ----------------------------------------------------
    # 4. Cross-Sensor Evidence
    # ----------------------------------------------------
    print("\n[4/6] Running Cross-Sensor Evidence...")
    with open(CROSS_THRESHOLDS, "r") as f:
        cross_thresh = json.load(f)
    t_spread_thresh = cross_thresh["temperature_spread_99th_percentile"]
    rh_spread_thresh = cross_thresh["humidity_spread_99th_percentile"]

    temp_valid = df[temp_cols].replace(-40, np.nan)
    rh_valid = df[rh_cols].where((df[rh_cols] >= 0) & (df[rh_cols] <= 100))

    t_valid_count = temp_valid.notna().sum(axis=1)
    rh_valid_count = rh_valid.notna().sum(axis=1)
    t_mean = temp_valid.mean(axis=1)
    rh_mean = rh_valid.mean(axis=1)
    t_spread = np.where(t_valid_count >= 2, temp_valid.max(axis=1) - temp_valid.min(axis=1), np.nan)
    rh_spread = np.where(rh_valid_count >= 2, rh_valid.max(axis=1) - rh_valid.min(axis=1), np.nan)

    cross_df = pd.DataFrame({
        "timestamp": df["timestamp"],
        "temperature_valid_count": t_valid_count,
        "temperature_mean": t_mean,
        "temperature_spread": t_spread,
        "humidity_valid_count": rh_valid_count,
        "humidity_mean": rh_mean,
        "humidity_spread": rh_spread
    })
    cross_df["temperature_disagreement"] = (cross_df["temperature_spread"] > t_spread_thresh).fillna(False)
    cross_df["humidity_disagreement"] = (cross_df["humidity_spread"] > rh_spread_thresh).fillna(False)
    cross_df["cross_sensor_evidence"] = (cross_df["temperature_disagreement"] | cross_df["humidity_disagreement"]).astype(int)

    # Divergent sensor isolation
    cross_df["temp_divergent_sensor"] = ""
    cross_df["rh_divergent_sensor"] = ""
    cross_df["temp_isolated_fault"] = 0
    cross_df["rh_isolated_fault"] = 0

    t_med = temp_valid.median(axis=1)
    rh_med = rh_valid.median(axis=1)

    for idx in cross_df[cross_df["temperature_disagreement"]].index:
        devs = {c: abs(temp_valid.loc[idx, c] - t_med.loc[idx]) for c in temp_cols if pd.notna(temp_valid.loc[idx, c])}

        if len(devs) >= 2:
            sorted_s = sorted(devs.items(), key=lambda x: x[1], reverse=True)
            if sorted_s[0][1] >= (t_spread_thresh * 0.5):
                cross_df.loc[idx, "temp_divergent_sensor"] = sorted_s[0][0].split("(")[0].strip()
                cross_df.loc[idx, "temp_isolated_fault"] = 1

    for idx in cross_df[cross_df["humidity_disagreement"]].index:
        devs = {c: abs(rh_valid.loc[idx, c] - rh_med.loc[idx]) for c in rh_cols if pd.notna(rh_valid.loc[idx, c])}
        if len(devs) >= 2:
            sorted_s = sorted(devs.items(), key=lambda x: x[1], reverse=True)
            if sorted_s[0][1] >= (rh_spread_thresh * 0.5):
                cross_df.loc[idx, "rh_divergent_sensor"] = sorted_s[0][0].split("(")[0].strip()
                cross_df.loc[idx, "rh_isolated_fault"] = 1



    # ----------------------------------------------------
    # 5. Temporal Evidence
    # ----------------------------------------------------
    print("\n[5/6] Running Temporal Evidence...")
    with open(TEMPORAL_THRESHOLDS, "r") as f:
        temp_thresh = json.load(f)
    t_rate_thresh = temp_thresh["temperature_rate_99th_percentile"]
    rh_rate_thresh = temp_thresh["humidity_rate_99th_percentile"]
    t_single_rate_thresh = temp_thresh.get("temperature_single_rate_99th_percentile", t_rate_thresh * 1.25)
    rh_single_rate_thresh = temp_thresh.get("humidity_single_rate_99th_percentile", rh_rate_thresh * 1.25)

    temp_df = df[["timestamp", "time_gap_minutes"]].copy()
    temp_df["previous_gap_minutes"] = temp_df["time_gap_minutes"]
    temp_df["temperature_median"] = t_med
    temp_df["humidity_median"] = rh_med

    valid_prev = (temp_df["previous_gap_minutes"] > 0) & (temp_df["previous_gap_minutes"] <= 60)
    temp_df["temperature_change"] = temp_df["temperature_median"] - temp_df["temperature_median"].shift(1)
    temp_df["humidity_change"] = temp_df["humidity_median"] - temp_df["humidity_median"].shift(1)
    temp_df["temperature_rate"] = temp_df["temperature_change"].abs() / (temp_df["previous_gap_minutes"] / 60)
    temp_df["humidity_rate"] = temp_df["humidity_change"].abs() / (temp_df["previous_gap_minutes"] / 60)
    temp_df.loc[~valid_prev, ["temperature_rate", "humidity_rate"]] = np.nan

    temp_df["temperature_rate_anomaly"] = (temp_df["temperature_rate"] > t_rate_thresh).fillna(False)
    temp_df["humidity_rate_anomaly"] = (temp_df["humidity_rate"] > rh_rate_thresh).fillna(False)
    temp_df["consensus_rate_anomaly"] = (temp_df["temperature_rate_anomaly"] | temp_df["humidity_rate_anomaly"]).astype(int)

    # Single-sensor rates
    single_t_spike = pd.Series(False, index=df.index)
    single_rh_spike = pd.Series(False, index=df.index)
    for c in temp_cols:
        rate = temp_valid[c].diff().abs() / (temp_df["previous_gap_minutes"] / 60)
        rate.loc[~valid_prev | temp_valid[c].isna() | temp_valid[c].shift(1).isna()] = np.nan
        single_t_spike |= (rate > t_single_rate_thresh).fillna(False)

    for c in rh_cols:
        rate = rh_valid[c].diff().abs() / (temp_df["previous_gap_minutes"] / 60)
        rate.loc[~valid_prev | rh_valid[c].isna() | rh_valid[c].shift(1).isna()] = np.nan
        single_rh_spike |= (rate > rh_single_rate_thresh).fillna(False)

    temp_df["temperature_single_rate_anomaly"] = single_t_spike.astype(int)
    temp_df["humidity_single_rate_anomaly"] = single_rh_spike.astype(int)
    temp_df["single_spike_anomaly"] = (single_t_spike | single_rh_spike).astype(int)
    temp_df["temporal_evidence"] = (temp_df["consensus_rate_anomaly"] | temp_df["single_spike_anomaly"]).astype(int)
    temp_df["temporal_evidence_count"] = (
        temp_df["temperature_rate_anomaly"].astype(int) +
        temp_df["humidity_rate_anomaly"].astype(int) +
        temp_df["temperature_single_rate_anomaly"] +
        temp_df["humidity_single_rate_anomaly"]
    )


    # ----------------------------------------------------
    # 6. Evidence Matrix & Event Fusion
    # ----------------------------------------------------
    print("\n[6/6] Building evidence matrix and running event fusion...")
    # Station evidence
    rule_df["station_zero_battery"] = (rule_df["rule_zero_battery"] == 1).astype(int)
    rule_df["station_zero_pressure"] = (rule_df["rule_zero_pressure"] == 1).astype(int)
    rule_df["station_all_core_zero"] = (rule_df["rule_all_core_zero"] == 1).astype(int)
    rule_df["station_coordinated_zero"] = ((rule_df["station_zero_battery"] == 1) & (rule_df["station_all_core_zero"] == 1)).astype(int)
    rule_df["station_evidence_count"] = rule_df[["station_zero_battery", "station_zero_pressure", "station_all_core_zero"]].sum(axis=1)
    rule_df["station_evidence_flag"] = (rule_df["station_evidence_count"] > 0).astype(int)
    rule_df["strong_station_evidence"] = (rule_df["station_evidence_count"] >= 2).astype(int)
    rule_df["station_system_evidence"] = rule_df["station_evidence_flag"].astype(int)
    rule_df["strong_station_system_evidence"] = rule_df["strong_station_evidence"].astype(int)
    rule_df["frozen_sensor_evidence"] = (rule_df["rule_sensor_frozen"] == 1).astype(int)
    rule_df["core_sensor_quality_evidence"] = (
        (rule_df["rule_missing_core"] == 1)
        | (rule_df["rule_temperature_invalid"] == 1)
        | (rule_df["rule_rh_invalid"] == 1)
        | (rule_df["frozen_sensor_evidence"] == 1)
    ).astype(int)
    rule_df["continuity_evidence"] = (rule_df["rule_large_time_gap"] == 1).astype(int)
    rule_df["auxiliary_channel_evidence"] = (
        (rule_df["rule_wind_direction_invalid"] == 1)
        | (rule_df["rule_radiation_sentinel"] == 1)
        | (rule_df["rule_heat_flux_sentinel"] == 1)
        | (rule_df["rule_rainfall_suspicious"] == 1)
    ).astype(int)

    matrix = rule_df.merge(cross_df, on="timestamp", how="left")
    matrix = matrix.merge(temp_df, on="timestamp", how="left")
    matrix = matrix.merge(if_results, on="timestamp", how="left")
    matrix["if_evidence_available"] = matrix["anomaly_flag"].notna().astype(int)

    # --------------------------------------------------------------------------
    # CONTINUOUS CALIBRATED SUB-SCORES GENERATION
    # --------------------------------------------------------------------------
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

    # Evidence stream counts and primary source attribution
    has_rule_stream = (matrix["score_rule"] >= 0.50).astype(int)
    has_cross_stream = (matrix["score_cross"] >= 0.50).astype(int)
    has_temp_stream = (matrix["score_temporal"] >= 0.50).astype(int)
    has_ml_stream = (matrix["score_ml"] >= 0.50).astype(int)
    matrix["evidence_sources_count"] = has_rule_stream + has_cross_stream + has_temp_stream + has_ml_stream

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

    # Observation-level trigger flag
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

    matrix.to_csv(EVIDENCE_MATRIX_OUT, index=False)
    print(f"Saved: {EVIDENCE_MATRIX_OUT}")

    # --------------------------------------------------------------------------
    # EVENT-LEVEL CLUSTERING & DYNAMIC CONFIDENCE SCORING
    # --------------------------------------------------------------------------
    eval_scope = matrix[matrix["if_evidence_available"] == 1].copy()
    anomalies = eval_scope[eval_scope["fused_anomaly_flag"] == 1].sort_values("timestamp").reset_index(drop=True)

    anomalies["gap_from_previous"] = anomalies["timestamp"].diff().dt.total_seconds() / 60
    anomalies["new_event"] = (anomalies["gap_from_previous"].isna() | (anomalies["gap_from_previous"] > 60)).astype(int)
    anomalies["event_id"] = anomalies["new_event"].cumsum()

    def mode_or_first(series):
        ne = [str(s).strip() for s in series if pd.notna(s) and str(s).strip() != ""]
        return ne[0] if ne else ""

    events = anomalies.groupby("event_id").agg(
        start_time=("timestamp", "min"),
        end_time=("timestamp", "max"),
        observations=("timestamp", "count"),
        mean_fused_score=("fused_anomaly_score", "mean"),
        peak_fused_score=("fused_anomaly_score", "max"),
        station_system_rows=("station_system_evidence", "sum"),
        core_sensor_quality_rows=("core_sensor_quality_evidence", "sum"),
        continuity_rows=("continuity_evidence", "sum"),
        cross_sensor_rows=("cross_sensor_evidence", "sum"),
        temporal_rows=("temporal_evidence", "sum"),
        minimum_anomaly_score=("anomaly_score", "min"),
        if_anomaly_rows=("anomaly_flag", "sum"),
        frozen_sensor_rows=("frozen_sensor_evidence", "sum"),
        single_spike_rows=("single_spike_anomaly", "sum"),
        consensus_rate_rows=("consensus_rate_anomaly", "sum"),
        peak_evidence_sources=("evidence_sources_count", "max"),
        divergent_temp_sensor=("temp_divergent_sensor", mode_or_first),
        divergent_rh_sensor=("rh_divergent_sensor", mode_or_first)
    ).reset_index()

    events["duration_minutes"] = (events["end_time"] - events["start_time"]).dt.total_seconds() / 60
    events["mean_fused_score"] = events["mean_fused_score"].round(4)
    events["peak_fused_score"] = events["peak_fused_score"].round(4)

    events["has_station_system_evidence"] = (events["station_system_rows"] > 0).astype(int)
    events["has_core_sensor_quality"] = (events["core_sensor_quality_rows"] > 0).astype(int)
    events["has_frozen_sensor"] = (events["frozen_sensor_rows"] > 0).astype(int)
    events["has_continuity_evidence"] = (events["continuity_rows"] > 0).astype(int)
    events["has_cross_sensor_evidence"] = (events["cross_sensor_rows"] > 0).astype(int)
    events["has_single_spike"] = (events["single_spike_rows"] > 0).astype(int)
    events["has_consensus_rate"] = (events["consensus_rate_rows"] > 0).astype(int)
    events["has_temporal_evidence"] = (events["temporal_rows"] > 0).astype(int)
    events["has_if_anomaly"] = (events["if_anomaly_rows"] > 0).astype(int)

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

        # Diagnostic decision logic
        if station == 1:
            cand_class = "STATION_SYSTEM_FAILURE"
            root_cause = "STATION_OR_POWER_FAILURE"
            target = "STATION_POWER_SYSTEM"
            sev = "CRITICAL" if obs >= 3 else "HIGH"
            base_conf = 0.96

        elif frozen == 1 or (obs >= 4 and cross == 1 and temporal == 0 and single_spike == 0):
            cand_class = "PROBABLE_SENSOR_FAULT"
            root_cause = "FROZEN_SENSOR"
            sev = "HIGH"
            base_conf = 0.94

        elif (consensus == 1 or temporal == 1) and cross == 0 and core == 0 and station == 0:
            cand_class = "POSSIBLE_WEATHER_EXTREME"
            root_cause = "RAPID_COHERENT_WEATHER_EVENT"
            target = "CONSENSUS_ALL_HEIGHTS"
            sev = "MEDIUM"
            base_conf = 0.90

        # 4. Isolated Single-Sensor Spike (Transient, 1-3 observations on single sensor without consensus)
        elif single_spike == 1 and obs <= 3 and consensus == 0:
            cand_class = "PROBABLE_SENSOR_FAULT"
            root_cause = "SENSOR_SPIKE"
            sev = "HIGH"
            base_conf = 0.92

        elif cross == 1 and core == 0 and consensus == 0:
            cand_class = "PROBABLE_SENSOR_FAULT"
            root_cause = "CALIBRATION_DRIFT_OR_BIAS"
            sev = "HIGH" if obs >= 4 else "MEDIUM"
            base_conf = 0.88 if obs >= 3 else 0.78

        elif core == 1 and cross == 1:
            cand_class = "PROBABLE_SENSOR_FAULT"
            root_cause = "INVALID_SENTINEL_READING"
            sev = "HIGH"
            base_conf = 0.95

        elif core == 1:
            cand_class = "PROBABLE_SENSOR_FAULT"
            root_cause = "SENSOR_OR_DATA_QUALITY"
            sev = "HIGH" if continuity == 0 else "MEDIUM"
            base_conf = 0.90

        elif continuity == 1 and core == 0 and cross == 0:
            cand_class = "DATA_COMMUNICATION_OUTAGE"
            root_cause = "DATA_COMMUNICATION_GAP"
            target = "DATA_LOGGER_COMMUNICATION"
            sev = "MEDIUM"
            base_conf = 0.85

        elif cross == 1 and temporal == 1:
            cand_class = "PROBABLE_SENSOR_FAULT"
            root_cause = "UNUSUAL_WEATHER_OR_SENSOR_BEHAVIOR"
            sev = "MEDIUM"
            base_conf = 0.75

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
        src_bonus = 0.02 * min(2, max(0, peak_sources - 1))
        obs_bonus = 0.02 * min(2, obs - 1)
        final_conf = min(0.99, max(0.50, round(base_conf + src_bonus + obs_bonus, 2)))

        events.loc[index, "target_sensor"] = target
        events.loc[index, "candidate_class"] = cand_class
        events.loc[index, "severity"] = sev
        events.loc[index, "confidence"] = final_conf
        events.loc[index, "probable_root_cause"] = root_cause

    events.to_csv(EVENT_FUSION_OUT, index=False)
    print(f"Saved: {EVENT_FUSION_OUT} ({len(events)} fused events)")


if __name__ == "__main__":
    import sys
    selected_model = sys.argv[1] if len(sys.argv) > 1 else "isolation_forest"
    run_validation_pipeline(selected_model)
