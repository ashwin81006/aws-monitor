import os
import json
import pandas as pd
import numpy as np


LABELS_FILE = "data/processed/aws_fault_labels.csv"
INJECTED_EVENTS_FILE = "data/processed/aws_injected_events.csv"
EVIDENCE_MATRIX_FILE = "data/processed/aws_validation_evidence_matrix.csv"
EVENT_FUSION_FILE = "data/processed/aws_validation_event_fusion.csv"

OUTPUT_EVENT_EVAL = "data/processed/aws_validation_event_evaluation.csv"
OUTPUT_ROW_EVAL = "data/processed/aws_validation_evaluation.csv"
OUTPUT_SUMMARY_JSON = "data/processed/aws_validation_metrics_summary.json"


def evaluate_validation(model_name="Isolation Forest"):
    print("=" * 60)
    print(f"   CONTROLLED VALIDATION EVALUATION ({model_name})")
    print("=" * 60)

    # Load data
    labels = pd.read_csv(LABELS_FILE)
    labels["timestamp"] = pd.to_datetime(labels["timestamp"])

    injected_events = pd.read_csv(INJECTED_EVENTS_FILE)
    injected_events["start_time"] = pd.to_datetime(injected_events["start_time"])
    injected_events["end_time"] = pd.to_datetime(injected_events["end_time"])

    matrix = pd.read_csv(EVIDENCE_MATRIX_FILE)
    matrix["timestamp"] = pd.to_datetime(matrix["timestamp"])

    fusion = pd.read_csv(EVENT_FUSION_FILE)
    fusion["start_time"] = pd.to_datetime(fusion["start_time"])
    fusion["end_time"] = pd.to_datetime(fusion["end_time"])

    # Align to test split (where IF and evaluation are active)
    split_index = int(len(labels) * 0.70)
    test_labels = labels.iloc[split_index:].copy().reset_index(drop=True)
    test_matrix = matrix[matrix["if_evidence_available"] == 1].copy().reset_index(drop=True)

    merged = pd.merge(test_labels, test_matrix, on="timestamp", how="inner")

    # ----------------------------------------------------
    # 1. Observation-Level Metrics (Fault Detection)
    # ----------------------------------------------------
    # Fault Ground Truth (only sensor/station faults count as 1; benign weather extremes count as 0)
    y_true = merged["is_fault"].values
    y_pred = merged["fused_anomaly_flag"].values

    tp = int(((y_true == 1) & (y_pred == 1)).sum())
    fp = int(((y_true == 0) & (y_pred == 1)).sum())
    tn = int(((y_true == 0) & (y_pred == 0)).sum())
    fn = int(((y_true == 1) & (y_pred == 0)).sum())

    total_obs = len(y_true)
    accuracy = (tp + tn) / total_obs if total_obs > 0 else 0.0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0

    print("\n------------------------------------------------------------")
    print("1. OBSERVATION-LEVEL METRICS (Test Set: %d rows)" % total_obs)
    print("------------------------------------------------------------")
    print(f"True Positives  (TP) : {tp}")
    print(f"False Positives (FP) : {fp} (Includes natural raw data anomalies outside injected set)")
    print(f"True Negatives  (TN) : {tn}")
    print(f"False Negatives (FN) : {fn}")
    print(f"Accuracy             : {accuracy:.4f}")
    print(f"Precision            : {precision:.4f}")
    print(f"Recall (Sensitivity) : {recall:.4f}")
    print(f"F1-Score             : {f1:.4f}")
    print(f"Specificity          : {specificity:.4f}")
    print(f"False Alarm Rate(FAR): {fpr:.4f}")

    # ----------------------------------------------------
    # 2. Event-Level Evaluation (Injected Faults & Control)
    # ----------------------------------------------------
    print("\n------------------------------------------------------------")
    print("2. FAULT-WISE EVENT DETECTION & LATENCY")
    print("------------------------------------------------------------")

    event_eval_records = []
    fault_detected_count = 0
    total_injected_faults = 0

    for _, row in injected_events.iterrows():
        f_id = row["fault_id"]
        f_type = row["fault_type"]
        f_start = row["start_time"]
        f_end = row["end_time"]
        exp_class = row["expected_class"]
        exp_cause = row["expected_root_cause"]
        exp_sev = row["expected_severity"]

        is_control = (f_type == "WEATHER_EXTREME")
        if not is_control:
            total_injected_faults += 1

        # Check rows within injection window
        sub_rows = merged[(merged["timestamp"] >= f_start) & (merged["timestamp"] <= f_end)]
        detected_rows = sub_rows[sub_rows["fused_anomaly_flag"] == 1]
        is_detected = len(detected_rows) > 0

        # Calculate Latency (minutes from start to first detected row)
        if is_detected:
            first_det_time = detected_rows["timestamp"].min()
            latency_min = (first_det_time - f_start).total_seconds() / 60
        else:
            first_det_time = None
            latency_min = np.nan

        # Overlapping fused events
        overlap_events = fusion[
            (fusion["start_time"] <= f_end) & (fusion["end_time"] >= f_start)
        ]

        if len(overlap_events) > 0:
            primary_event = overlap_events.sort_values(by=["observations", "peak_fused_score"], ascending=False).iloc[0]
            det_class = primary_event["candidate_class"]
            det_cause = primary_event["probable_root_cause"]
            det_sev = primary_event["severity"]
            det_conf = primary_event["confidence"]
            matched_eids = ",".join(overlap_events["event_id"].astype(str).tolist())

        else:
            det_class = "NOT_DETECTED"
            det_cause = "NONE"
            det_sev = "NONE"
            det_conf = 0.0
            matched_eids = ""

        # Match check
        class_matched = (det_class == exp_class)
        cause_matched = (det_cause == exp_cause)

        if not is_control and is_detected:
            fault_detected_count += 1

        event_eval_records.append({
            "fault_id": f_id,
            "fault_type": f_type,
            "injection_start": str(f_start),
            "injection_end": str(f_end),
            "injected_observations": row["observations"],
            "detected": int(is_detected),
            "first_detection": str(first_det_time) if first_det_time else "N/A",
            "detection_latency_minutes": latency_min,
            "expected_class": exp_class,
            "detected_class": det_class,
            "class_match": int(class_matched),
            "expected_root_cause": exp_cause,
            "detected_root_cause": det_cause,
            "root_cause_match": int(cause_matched),
            "detected_severity": det_sev,
            "confidence": det_conf,
            "matched_fused_event_ids": matched_eids
        })

    eval_df = pd.DataFrame(event_eval_records)
    eval_df.to_csv(OUTPUT_EVENT_EVAL, index=False)

    # Print summary table
    print(eval_df[[
        "fault_id", "fault_type", "detected", "detection_latency_minutes",
        "detected_class", "detected_root_cause", "class_match", "root_cause_match"
    ]].to_string(index=False))

    fault_detection_rate = fault_detected_count / total_injected_faults if total_injected_faults > 0 else 0.0
    print(f"\nFault Event Detection Rate : {fault_detected_count}/{total_injected_faults} ({fault_detection_rate * 100:.1f}%)")

    # Weather Extreme False Alarm Rejection Check
    wx_row = eval_df[eval_df["fault_type"] == "WEATHER_EXTREME"]
    if len(wx_row) > 0:
        wx_res = wx_row.iloc[0]
        if wx_res["detected_class"] == "POSSIBLE_WEATHER_EXTREME":
            print("\n[SUCCESS] Benign Weather Extreme was correctly classified as POSSIBLE_WEATHER_EXTREME (False Alarm Rejection: PASS)")
        else:
            print(f"\n[ALERT] Weather Extreme classified as: {wx_res['detected_class']}")

    # ----------------------------------------------------
    # 3. Controlled Benchmark Window Metrics
    # ----------------------------------------------------
    # Evaluate in 24-hour windows around each injected scenario
    window_conditions = [
        (merged["timestamp"] >= r["start_time"] - pd.Timedelta(hours=12)) &
        (merged["timestamp"] <= r["end_time"] + pd.Timedelta(hours=12))
        for _, r in injected_events.iterrows()
    ]
    window_mask = window_conditions[0]
    for c in window_conditions[1:]:
        window_mask = window_mask | c

    window_df = merged[window_mask].copy()
    w_tp = int(((window_df["is_fault"] == 1) & (window_df["fused_anomaly_flag"] == 1)).sum())
    w_fp = int(((window_df["is_fault"] == 0) & (window_df["fused_anomaly_flag"] == 1)).sum())
    w_tn = int(((window_df["is_fault"] == 0) & (window_df["fused_anomaly_flag"] == 0)).sum())
    w_fn = int(((window_df["is_fault"] == 1) & (window_df["fused_anomaly_flag"] == 0)).sum())

    w_prec = w_tp / (w_tp + w_fp) if (w_tp + w_fp) > 0 else 0.0
    w_rec = w_tp / (w_tp + w_fn) if (w_tp + w_fn) > 0 else 0.0
    w_f1 = 2 * (w_prec * w_rec) / (w_prec + w_rec) if (w_prec + w_rec) > 0 else 0.0

    # ----------------------------------------------------
    # Genuine Event Matching Precision, Recall & F1
    # ----------------------------------------------------
    test_start = test_labels["timestamp"].min()
    test_end = test_labels["timestamp"].max()

    # In-scope predicted alert events (excluding classified benign weather extremes)
    in_scope_preds = fusion[
        (fusion["end_time"] >= test_start) &
        (fusion["start_time"] <= test_end) &
        (fusion["candidate_class"] != "POSSIBLE_WEATHER_EXTREME")
    ].copy()

    gt_faults = injected_events[injected_events["fault_type"] != "WEATHER_EXTREME"]

    # Count predicted alerts that match an injected fault
    matched_pred_count = 0
    unmatched_pred_count = 0

    for _, p_row in in_scope_preds.iterrows():
        p_s = p_row["start_time"]
        p_e = p_row["end_time"]
        overlaps_gt = False
        for _, g_row in gt_faults.iterrows():
            g_s = g_row["start_time"]
            g_e = g_row["end_time"]
            if max(p_s, g_s) <= min(p_e, g_e):
                overlaps_gt = True
                break
        if overlaps_gt:
            matched_pred_count += 1
        else:
            unmatched_pred_count += 1

    total_pred_events = matched_pred_count + unmatched_pred_count
    event_recall = fault_detected_count / total_injected_faults if total_injected_faults > 0 else 0.0
    event_precision = matched_pred_count / total_pred_events if total_pred_events > 0 else 0.0
    event_f1 = (
        2 * (event_precision * event_recall) / (event_precision + event_recall)
        if (event_precision + event_recall) > 0 else 0.0
    )

    # Benchmark Window Event Matching
    in_window_preds = in_scope_preds[
        in_scope_preds.apply(
            lambda p: any(
                max(p["start_time"], r["start_time"] - pd.Timedelta(hours=12)) <=
                min(p["end_time"], r["end_time"] + pd.Timedelta(hours=12))
                for _, r in injected_events.iterrows()
            ),
            axis=1
        )
    ]
    w_matched_preds = 0
    w_unmatched_preds = 0
    for _, p_row in in_window_preds.iterrows():
        p_s = p_row["start_time"]
        p_e = p_row["end_time"]
        overlaps_gt = any(
            max(p_s, g_row["start_time"]) <= min(p_e, g_row["end_time"])
            for _, g_row in gt_faults.iterrows()
        )
        if overlaps_gt:
            w_matched_preds += 1
        else:
            w_unmatched_preds += 1

    w_event_prec = w_matched_preds / len(in_window_preds) if len(in_window_preds) > 0 else 0.0
    w_event_f1 = (
        2 * (w_event_prec * event_recall) / (w_event_prec + event_recall)
        if (w_event_prec + event_recall) > 0 else 0.0
    )

    print("\n------------------------------------------------------------")
    print("3. MULTI-LEVEL PRECISION & RECALL SUMMARY")
    print("------------------------------------------------------------")
    print(
        f"EVENT-LEVEL (TESTSET): Precision = {event_precision * 100:.1f}%, "
        f"Recall = {event_recall * 100:.1f}%, F1 = {event_f1:.4f} "
        f"(TP_events={matched_pred_count}, FP_events={unmatched_pred_count}, FN_events={total_injected_faults - fault_detected_count})"
    )
    print(
        f"EVENT-LEVEL (WINDOW):  Precision = {w_event_prec * 100:.1f}%, "
        f"Recall = {event_recall * 100:.1f}%, F1 = {w_event_f1:.4f} "
        f"(TP_events={w_matched_preds}, FP_events={w_unmatched_preds})"
    )
    print(
        f"OBSERVATION (WINDOW):  Precision = {w_prec * 100:.1f}%, "
        f"Recall = {w_rec * 100:.1f}%, F1 = {w_f1:.4f} "
        f"(TP={w_tp}, FP={w_fp}, FN={w_fn})"
    )
    print(
        f"OBSERVATION (FULL):    Precision = {precision * 100:.2f}%, "
        f"Recall = {recall * 100:.1f}%, F1 = {f1:.4f} "
        f"(FP={fp} includes raw ambient anomalies outside injection set)"
    )

    # ----------------------------------------------------
    # 4. Save Summary JSON & Row-level Evaluation
    # ----------------------------------------------------
    merged[["timestamp", "is_fault", "fault_type", "fault_id", "fused_anomaly_flag"]].to_csv(OUTPUT_ROW_EVAL, index=False)

    summary_metrics = {
        "evaluation_type": "controlled_fault_validation",
        "event_level": {
            "fault_events_injected": total_injected_faults,
            "fault_events_detected": fault_detected_count,
            "missed_fault_events": total_injected_faults - fault_detected_count,
            "predicted_alert_events": total_pred_events,
            "matched_predicted_events": matched_pred_count,
            "unmatched_predicted_events": unmatched_pred_count,
            "event_recall": round(event_recall, 4),
            "event_precision": round(event_precision, 4),
            "event_f1_score": round(event_f1, 4),
            "benchmark_window_event_precision": round(w_event_prec, 4),
            "benchmark_window_event_f1": round(w_event_f1, 4),
            "weather_extreme_rejection_passed": bool(wx_row.iloc[0]["class_match"]) if len(wx_row) > 0 else True
        },
        "benchmark_window_level": {
            "window_observations": len(window_df),
            "true_positives": w_tp,
            "false_positives": w_fp,
            "true_negatives": w_tn,
            "false_negatives": w_fn,
            "precision": round(w_prec, 4),
            "recall": round(w_rec, 4),
            "f1_score": round(w_f1, 4)
        },
        "raw_full_testset_level": {
            "total_test_observations": total_obs,
            "true_positives": tp,
            "false_positives": fp,
            "true_negatives": tn,
            "false_negatives": fn,
            "accuracy": round(accuracy, 4),
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1_score": round(f1, 4),
            "specificity": round(specificity, 4),
        }
    }
    summary_metrics["model_name"] = model_name

    eval_df.to_csv(OUTPUT_EVENT_EVAL, index=False)
    merged.to_csv(OUTPUT_ROW_EVAL, index=False)

    with open(OUTPUT_SUMMARY_JSON, "w") as f:
        json.dump(summary_metrics, f, indent=4)

    print(f"\nSaved event evaluation  : {OUTPUT_EVENT_EVAL}")
    print(f"Saved row-level eval    : {OUTPUT_ROW_EVAL}")
    print(f"Saved summary metrics   : {OUTPUT_SUMMARY_JSON}")
    print("=" * 60)
    print(f"          VALIDATION COMPLETE ({model_name})")
    print("=" * 60)
    return summary_metrics


if __name__ == "__main__":
    import sys
    m_name = sys.argv[1] if len(sys.argv) > 1 else "Isolation Forest"
    evaluate_validation(model_name=m_name)
