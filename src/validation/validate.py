import os
import sys
import pickle
import time
import warnings
from typing import Dict, List, Tuple, Any
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore", category=UserWarning)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from src.preprocessing.preprocess import load_raw_dataset, preprocess_data
from src.features.feature_engineering import StreamingFeatureExtractor, FEATURE_COLUMNS
from src.core.detector import AWSUnifiedDetector

MODELS_DIR = os.path.join(PROJECT_ROOT, "models")


def inject_comprehensive_faults(
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
        ch = np.random.choice(["temperature", "pressure", "humidity"])
        if ch == "temperature":
            injected_df.loc[idx, "temperature"] += np.random.choice([16.0, -22.0, 24.0])
        elif ch == "pressure":
            injected_df.loc[idx, "pressure"] += np.random.choice([32.0, -28.0])
        else:
            injected_df.loc[idx, "humidity"] = min(100.0, injected_df.loc[idx, "humidity"] + 45.0)

        injected_df.loc[idx, "ground_truth_fault"] = 1
        injected_df.loc[idx, "fault_type"] = "SPIKE"
        fault_events.append({"type": "SPIKE", "start_idx": idx, "end_idx": idx, "channel": ch})

    frozen_starts = np.random.choice(range(80, n_rows - 80), size=15, replace=False)
    for start in frozen_starts:
        ch = np.random.choice(["temperature", "humidity"])
        stuck_val = injected_df.loc[start, ch]
        streak_len = np.random.randint(4, 8)
        for step in range(start, min(n_rows, start + streak_len)):
            injected_df.loc[step, ch] = stuck_val
            injected_df.loc[step, "ground_truth_fault"] = 1
            injected_df.loc[step, "fault_type"] = "FROZEN_SENSOR"
        fault_events.append({"type": "FROZEN_SENSOR", "start_idx": start, "end_idx": min(n_rows - 1, start + streak_len - 1), "channel": ch})

    drift_starts = np.random.choice(range(120, n_rows - 120), size=15, replace=False)
    for start in drift_starts:
        slope = np.random.choice([0.6, 0.9, 1.2])
        drift_len = 10
        for i, step in enumerate(range(start, min(n_rows, start + drift_len))):
            injected_df.loc[step, "temperature"] += (i + 1) * slope
            injected_df.loc[step, "ground_truth_fault"] = 1
            injected_df.loc[step, "fault_type"] = "CALIBRATION_DRIFT"
        fault_events.append({"type": "CALIBRATION_DRIFT", "start_idx": start, "end_idx": min(n_rows - 1, start + drift_len - 1), "channel": "temperature"})

    comm_starts = np.random.choice(range(150, n_rows - 150), size=15, replace=False)
    for start in comm_starts:
        gap_len = np.random.randint(2, 6)
        for step in range(start, min(n_rows, start + gap_len)):
            injected_df.loc[step, "temperature"] = np.nan
            injected_df.loc[step, "ground_truth_fault"] = 1
            injected_df.loc[step, "fault_type"] = "COMMUNICATION_ERROR"
        fault_events.append({"type": "COMMUNICATION_ERROR", "start_idx": start, "end_idx": min(n_rows - 1, start + gap_len - 1), "channel": "all"})

    heatwave_starts = np.random.choice(range(200, n_rows - 200), size=10, replace=False)
    for start in heatwave_starts:
        for step in range(start, min(n_rows, start + 8)):
            injected_df.loc[step, "temperature"] = 44.5
            injected_df.loc[step, "humidity"] = 24.0
            injected_df.loc[step, "fault_type"] = "BENIGN_WEATHER_EXTREME"

    return injected_df, fault_events


def evaluate_single_detector(
    detector: AWSUnifiedDetector,
    test_df: pd.DataFrame,
    fault_events: List[Dict[str, Any]]
) -> Dict[str, Any]:
    detector.reset_history()
    t0 = time.perf_counter()
    predictions = []

    for _, row in test_df.iterrows():
        t = row["temperature"]
        rh = row["humidity"]
        p = row["pressure"]
        ts = row["timestamp"] if "timestamp" in row else None
        res = detector.diagnose_and_detect(temp=t, rh=rh, press=p, timestamp=ts)
        predictions.append(1 if res["is_anomaly"] else 0)

    elapsed_sec = max(time.perf_counter() - t0, 1e-4)
    pred_series = pd.Series(predictions)
    y_true = test_df["ground_truth_fault"].to_numpy()
    y_pred = pred_series.to_numpy()

    tp = int(((y_true == 1) & (y_pred == 1)).sum())
    fp = int(((y_true == 0) & (y_pred == 1)).sum())
    fn = int(((y_true == 1) & (y_pred == 0)).sum())
    tn = int(((y_true == 0) & (y_pred == 0)).sum())

    row_precision = round(tp / max(tp + fp, 1), 4)
    row_recall = round(tp / max(tp + fn, 1), 4)
    row_f1 = round(2 * row_precision * row_recall / max(row_precision + row_recall, 1e-4), 4)
    fpr = round(fp / max(fp + tn, 1), 4)

    matched_events = 0
    total_events = len(fault_events)
    latencies = []
    per_fault_metrics = {}

    for f_type in ["SPIKE", "FROZEN_SENSOR", "CALIBRATION_DRIFT", "COMMUNICATION_ERROR"]:
        type_events = [ev for ev in fault_events if ev["type"] == f_type]
        type_matched = 0
        type_latencies = []

        for ev in type_events:
            w_preds = pred_series.iloc[ev["start_idx"]: ev["end_idx"] + 1]
            if (w_preds == 1).any():
                type_matched += 1
                first_step = int((w_preds == 1).idxmax() - ev["start_idx"] + 1)
                type_latencies.append(first_step)

        matched_events += type_matched
        latencies.extend(type_latencies)
        type_recall = round(type_matched / max(len(type_events), 1), 4)
        mean_lat = round(float(np.mean(type_latencies)), 1) if type_latencies else 1.0

        per_fault_metrics[f_type] = {
            "total_events": len(type_events),
            "detected_events": type_matched,
            "event_recall": type_recall,
            "mean_detection_delay_steps": mean_lat
        }

    event_recall = round(matched_events / max(total_events, 1), 4)

    alert_starts = (pred_series == 1) & (pred_series.shift(1, fill_value=0) == 0)
    alert_indices = alert_starts[alert_starts].index.tolist()
    unmatched_alerts = 0
    for a_idx in alert_indices:
        in_any = any(ev["start_idx"] <= a_idx <= ev["end_idx"] for ev in fault_events)
        if not in_any:
            unmatched_alerts += 1

    event_precision = round(matched_events / max(matched_events + unmatched_alerts, 1), 4)
    event_f1 = round(2 * event_precision * event_recall / max(event_precision + event_recall, 1e-4), 4)
    mean_delay = round(float(np.mean(latencies)), 1) if latencies else 1.0

    benign_subset = test_df[test_df["fault_type"] == "BENIGN_WEATHER_EXTREME"]
    benign_false_alarms = int((pred_series.iloc[benign_subset.index] == 1).sum()) if len(benign_subset) > 0 else 0
    benign_total = len(benign_subset)

    return {
        "mode": detector.mode,
        "row_precision": row_precision,
        "row_recall": row_recall,
        "row_f1": row_f1,
        "event_precision": event_precision,
        "event_recall": event_recall,
        "event_f1": event_f1,
        "false_positive_rate": fpr,
        "mean_detection_delay": mean_delay,
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "benign_weather_false_alarms": benign_false_alarms,
        "benign_weather_total": benign_total,
        "throughput_obs_sec": int(len(test_df) / elapsed_sec),
        "evaluation_seconds": round(elapsed_sec, 2),
        "per_fault": per_fault_metrics
    }


def run_comparative_benchmark(sample_size: int = 4000) -> Dict[str, Any]:
    raw_df = load_raw_dataset()
    _, clean_df = preprocess_data(raw_df)

    split_idx = int(len(clean_df) * 0.70)
    test_clean = clean_df.iloc[split_idx: split_idx + sample_size].copy().reset_index(drop=True)

    test_injected, fault_events = inject_comprehensive_faults(test_clean)

    modes_to_test = [
        ("isolation_forest", "Baseline Production"),
        ("one_class_svm", "Boundary Comparison"),
        ("lof", "Density Comparison"),
        ("calibrated_ensemble", "Calibrated Score Fusion Ensemble")
    ]

    comparisons = []
    for mode, label in modes_to_test:
        det = AWSUnifiedDetector(mode=mode)
        metrics = evaluate_single_detector(det, test_injected, fault_events)
        metrics["label"] = label
        comparisons.append(metrics)

    return {
        "sample_size": sample_size,
        "total_fault_events": len(fault_events),
        "comparisons": comparisons
    }


if __name__ == "__main__":
    results = run_comparative_benchmark(sample_size=3000)
    print("=== MODEL COMPARISON BENCHMARK ===")
    for c in results["comparisons"]:
        print(f"[{c['mode'].upper()}] Row F1: {c['row_f1']:.3f} | Event F1: {c['event_f1']:.3f} | Delay: {c['mean_detection_delay']} steps | Speed: {c['throughput_obs_sec']:,} obs/s")
