import os
import sys
import pickle
import warnings
from typing import Dict, List, Tuple, Any
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore", category=UserWarning)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from src.preprocessing.preprocess import load_raw_dataset, preprocess_data
from src.features.feature_engineering import StreamingFeatureExtractor, FEATURE_COLUMNS

MODELS_DIR = os.path.join(PROJECT_ROOT, "models")


def inject_faults(
    df: pd.DataFrame,
    random_seed: int = 42
) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    np.random.seed(random_seed)
    injected_df = df.copy()
    injected_df["ground_truth_fault"] = 0
    injected_df["fault_type"] = "NONE"

    n_rows = len(injected_df)
    fault_events = []

    spike_indices = np.random.choice(range(50, n_rows - 50), size=25, replace=False)
    for idx in spike_indices:
        channel = np.random.choice(["temperature", "pressure", "humidity"])
        if channel == "temperature":
            injected_df.loc[idx, "temperature"] += np.random.choice([15.0, -18.0, 22.0])
        elif channel == "pressure":
            injected_df.loc[idx, "pressure"] += np.random.choice([35.0, -30.0])
        else:
            injected_df.loc[idx, "humidity"] = min(100.0, injected_df.loc[idx, "humidity"] + 45.0)

        injected_df.loc[idx, "ground_truth_fault"] = 1
        injected_df.loc[idx, "fault_type"] = "SPIKE"
        fault_events.append({"type": "SPIKE", "start_idx": idx, "end_idx": idx, "channel": channel})

    frozen_starts = np.random.choice(range(100, n_rows - 100), size=15, replace=False)
    for start in frozen_starts:
        stuck_val = injected_df.loc[start, "temperature"]
        for step in range(start, start + 6):
            injected_df.loc[step, "temperature"] = stuck_val
            injected_df.loc[step, "ground_truth_fault"] = 1
            injected_df.loc[step, "fault_type"] = "FROZEN_SENSOR"
        fault_events.append({"type": "FROZEN_SENSOR", "start_idx": start, "end_idx": start + 5, "channel": "temperature"})

    drift_starts = np.random.choice(range(150, n_rows - 150), size=12, replace=False)
    for start in drift_starts:
        for i, step in enumerate(range(start, start + 10)):
            injected_df.loc[step, "temperature"] += (i + 1) * 0.8
            injected_df.loc[step, "ground_truth_fault"] = 1
            injected_df.loc[step, "fault_type"] = "CALIBRATION_DRIFT"
        fault_events.append({"type": "CALIBRATION_DRIFT", "start_idx": start, "end_idx": start + 9, "channel": "temperature"})

    comm_starts = np.random.choice(range(200, n_rows - 200), size=15, replace=False)
    for start in comm_starts:
        for step in range(start, start + 4):
            injected_df.loc[step, "temperature"] = np.nan
            injected_df.loc[step, "ground_truth_fault"] = 1
            injected_df.loc[step, "fault_type"] = "COMMUNICATION_ERROR"
        fault_events.append({"type": "COMMUNICATION_ERROR", "start_idx": start, "end_idx": start + 3, "channel": "all"})

    return injected_df, fault_events


def run_validation(test_sample_size: int = 4000) -> Dict[str, Any]:
    raw_df = load_raw_dataset()
    _, clean_df = preprocess_data(raw_df)

    split_idx = int(len(clean_df) * 0.70)
    test_clean = clean_df.iloc[split_idx: split_idx + test_sample_size].copy().reset_index(drop=True)

    test_injected, fault_events = inject_faults(test_clean)

    with open(os.path.join(MODELS_DIR, "isolation_forest.pkl"), "rb") as f:
        model_if = pickle.load(f)
    with open(os.path.join(MODELS_DIR, "scaler.pkl"), "rb") as f:
        scaler = pickle.load(f)

    extractor = StreamingFeatureExtractor(window_size=8)
    predictions = []

    for i, row in test_injected.iterrows():
        t = row["temperature"]
        rh = row["humidity"]
        p = row["pressure"]

        is_missing = pd.isna(t) or pd.isna(rh) or pd.isna(p)
        is_extreme_spike = False
        is_frozen = False

        if not is_missing:
            if t > 52.0 or t < 5.0 or p < 890.0 or p > 1050.0:
                is_extreme_spike = True

            if len(extractor.history) >= 4:
                recent_temps = [pt[0] for pt in extractor.history]
                if np.std(recent_temps) < 1e-3 and abs(t - recent_temps[-1]) < 1e-3:
                    is_frozen = True

            feats = extractor.push(temp=t, rh=rh, press=p)
            X_df = pd.DataFrame([feats])[FEATURE_COLUMNS]
            X_scaled = scaler.transform(X_df)
            ml_anomaly = bool(model_if.decision_function(X_scaled)[0] < 0.0)
        else:
            ml_anomaly = True

        detected = bool(is_missing or is_extreme_spike or is_frozen or ml_anomaly)
        predictions.append(1 if detected else 0)

    test_injected["predicted_alert"] = predictions

    scenario_metrics = {}
    for f_type in ["SPIKE", "FROZEN_SENSOR", "CALIBRATION_DRIFT", "COMMUNICATION_ERROR"]:
        subset = test_injected[test_injected["fault_type"] == f_type]
        tp = int(((subset["ground_truth_fault"] == 1) & (subset["predicted_alert"] == 1)).sum())
        fn = int(((subset["ground_truth_fault"] == 1) & (subset["predicted_alert"] == 0)).sum())
        recall = round(tp / max(tp + fn, 1), 4)

        event_latencies = []
        for ev in fault_events:
            if ev["type"] == f_type:
                ev_preds = test_injected.loc[ev["start_idx"]: ev["end_idx"], "predicted_alert"]
                if (ev_preds == 1).any():
                    first_detect = (ev_preds == 1).idxmax() - ev["start_idx"] + 1
                    event_latencies.append(first_detect)

        mean_latency = round(float(np.mean(event_latencies)), 1) if event_latencies else 1.0
        scenario_metrics[f_type] = {
            "injected_points": len(subset),
            "detected_points": tp,
            "recall": recall,
            "mean_latency_steps": mean_latency
        }

    matched_events = 0
    total_events = len(fault_events)
    for ev in fault_events:
        window_preds = test_injected.loc[ev["start_idx"]: ev["end_idx"], "predicted_alert"]
        if (window_preds == 1).any():
            matched_events += 1

    event_recall = round(matched_events / max(total_events, 1), 4)

    pred_series = test_injected["predicted_alert"]
    alert_starts = (pred_series == 1) & (pred_series.shift(1, fill_value=0) == 0)
    alert_indices = test_injected.index[alert_starts].tolist()

    unmatched_alert_episodes = 0
    for a_idx in alert_indices:
        in_any_fault = any(ev["start_idx"] <= a_idx <= ev["end_idx"] for ev in fault_events)
        if not in_any_fault:
            unmatched_alert_episodes += 1

    event_precision = round(matched_events / max(matched_events + unmatched_alert_episodes, 1), 4)
    event_f1 = round(2 * event_precision * event_recall / max(event_precision + event_recall, 1e-4), 4)

    y_true = test_injected["ground_truth_fault"].to_numpy()
    y_pred = test_injected["predicted_alert"].to_numpy()

    tp_total = int(((y_true == 1) & (y_pred == 1)).sum())
    fp_total = int(((y_true == 0) & (y_pred == 1)).sum())
    fn_total = int(((y_true == 1) & (y_pred == 0)).sum())
    tn_total = int(((y_true == 0) & (y_pred == 0)).sum())

    precision = round(tp_total / max(tp_total + fp_total, 1), 4)
    recall = round(tp_total / max(tp_total + fn_total, 1), 4)
    f1 = round(2 * precision * recall / max(precision + recall, 1e-4), 4)

    return {
        "precision": precision,
        "recall": recall,
        "f1_score": f1,
        "event_precision": event_precision,
        "event_recall": event_recall,
        "event_f1": event_f1,
        "total_events": total_events,
        "matched_events": matched_events,
        "unmatched_alerts": unmatched_alert_episodes,
        "tp": tp_total,
        "fp": fp_total,
        "fn": fn_total,
        "tn": tn_total,
        "scenarios": scenario_metrics,
        "total_evaluated_points": len(test_injected)
    }


if __name__ == "__main__":
    res = run_validation()
    print(f"Validation: Precision={res['precision']:.3f}, Recall={res['recall']:.3f}, F1={res['f1_score']:.3f}")
